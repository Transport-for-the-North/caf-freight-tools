"""Thristy truck process
Takes annual tonnage to a thirsty truck hex map
imports LFT and thirsty vehicle
Kieran Fishwick: kieran.fishwick@wsp.com
"""
# standard imports
import argparse
import sys
import concurrent.futures
import pathlib
import os
from datetime import datetime
from typing import Optional

# third party imports
from tqdm.contrib import logging as tqdm_log
import pandas as pd
import geopandas as gpd
from caf.toolkit import translation

# add src to path before importing thirsty truck

if "local_freight_tool" not in sys.path:
    sys.path.append("local_freight_tool")

if "LFT" not in sys.path:
    sys.path.append("LFT")

# local imports
from thirsty_vehicle_tool import (
    input_output_constants,
    tv_logging,
    hex_plotting,
    geospatial_analysis,
)
from thirsty_truck_tool import ioc
from LFT import hgv_annual_tonne_to_pcu, matrix_utilities

LOG_FILE = "thirsty_truck.log"
LOG = tv_logging.get_logger(__name__)

ZONE_ADDITION = 1000000


def main(args: argparse.Namespace) -> None:
    """initilises Logging and calls run

    Parameters
    ----------
    args : argparse.Namespace
        command line arguement inputs
    """
    with tv_logging.ThirstyVehicleLog("Thirsty Truck Tool") as thirsty_truck_log:
        with tqdm_log.logging_redirect_tqdm([thirsty_truck_log.logger]):
            run(thirsty_truck_log, args)


def run(log: tv_logging.ThirstyVehicleLog, args: argparse.Namespace) -> None:
    """handles creating file handeler reading and parsing the config file
    before passing inputs to processes

    Parameters
    ----------
    log : tv_logging.ThirstyVehicleLog
        Logging class
    args : argparse.Namespace
        keyword arguments from tool call
    """
    config = ioc.ThristyTruckConfig.load_yaml(args.config)
    config.operational.output_folder.mkdir(exist_ok=True)

    log.add_file_handler(config.operational.output_folder / LOG_FILE)

    config.convert_to_m(input_output_constants.TO_M_FACTOR)

    analysis_inputs = config.analysis_inputs.parse_analysis_inputs()
    plotting_inputs = config.plotting_inputs.parse_plotting_inputs(config.operational)
    # write input summary
    username = os.getlogin()
    date_time = datetime.now()
    date_time = date_time.strftime("%d/%m/%Y %H:%M:%S")
    input_summary = (
        f"\nRun Metadata\nUser - {username}\nDate and Time of Run - {date_time}\n"
    )
    input_summary += "\nInputs\n"
    input_summary += config.operational.create_input_summary()
    input_summary += config.analysis_inputs.create_input_summary()
    input_summary += config.plotting_inputs.create_input_summary()
    input_output_constants.write_txt(
        config.operational.output_folder / "input_summary.txt", input_summary
    )
    LOG.info(input_summary)

    thirsty_truck(analysis_inputs, plotting_inputs, config.operational)


def thirsty_truck(
    analysis_inputs: ioc.ParsedAnalysisInputs,
    plotting_inputs: input_output_constants.PlottingInputs,
    operational: input_output_constants.Operational,
) -> None:
    """combines processes to create the thirsty truck process

    combines elements of the the thirsty vehicle tool and LFT

    Parameters
    ----------
    analysis_inputs : ioc.ParsedAnalysisInputs
        parsed analysis inputs from the config file
    plotting_inputs : input_output_constants.PlottingInputs
        parsed plotting inputs from the config file
    operational : input_output_constants.Operational
        operational inputs from the config file
    """
    # handle LFT input
    annual_tonne_to_trip_folder = (
        operational.output_folder / "annual_tonne_to_pcu_conversion"
    )

    od_matrices_folder = operational.output_folder / "od_matrices"
    # ensure the directory exists
    annual_tonne_to_trip_folder.mkdir(exist_ok=True)
    od_matrices_folder.mkdir(exist_ok=True)
    # parse LFT inputs and convert to PCUs/Trips
    translate = True
    if analysis_inputs.lft_inputs is not None:
        LOG.info("Parsing LFT inputs and converting to annual PCU")
        trip_conversion_obj = hgv_annual_tonne_to_pcu.tonne_to_pcu(
            analysis_inputs.lft_inputs, annual_tonne_to_trip_folder
        )
        # get trips
        unformatted_od_matrices = trip_conversion_obj.total_trips
        od_matrices = {}
        # convert keys to match the case of the input keys (must match text)
        # key_lookup = ioc.convert_lft_keys(
        #    list(analysis_inputs.ranges.keys()), list(unformatted_od_matrices.keys())
        # )
        for key, value in unformatted_od_matrices.items():
            if (analysis_inputs.original_zoning != analysis_inputs.target_zoning) and (
                analysis_inputs.original_zoning != "undefined"
                and analysis_inputs.target_zoning != "undefined"
            ):
                od_matrices[key] = translate_matrix(
                    value.column_matrix(),
                    analysis_inputs.zone_translation,
                    analysis_inputs.original_zoning,
                    analysis_inputs.target_zoning,
                    "origin",
                    "destination",
                    "trips",
                )

                # output file in new zoning system
                input_output_constants.write_to_csv(
                    od_matrices_folder / f"{key}_{analysis_inputs.target_zoning}.csv",
                    od_matrices[key],
                )

                # if translation has already been done, don't do it again
                translate = False

        LOG.info("Extracted annual trips")

    # get matrices if they exist
    if analysis_inputs.od_matrices is not None:
        LOG.info("Extracting OD matrices")
        od_matrices = analysis_inputs.od_matrices
        # TODO check zone system

    # get thirsty points if they exist
    if analysis_inputs.thirsty_points is not None:
        thirsty_points = analysis_inputs.thirsty_points

    # if no thirsty points given generate from matrices
    else:
        # check/translate zone system

        # save keys pre-disaggregation

        traget_matrices = {}

        if (
            (analysis_inputs.original_zoning != analysis_inputs.target_zoning)
            and (
                analysis_inputs.original_zoning != "undefined"
                and analysis_inputs.target_zoning != "undefined"
            )
            and translate
        ):
            for key, value in od_matrices.items():
                LOG.info(f"Translating {key} matrix")
                traget_matrices[key] = translate_matrix(
                    value,
                    analysis_inputs.zone_translation,
                    analysis_inputs.original_zoning,
                    analysis_inputs.target_zoning,
                    "origin",
                    "destination",
                    "trips",
                )

        else:
            traget_matrices = od_matrices

        zone_name_lookup = None

        matrices = {}

        for key, value in traget_matrices.items():
            LOG.info(f"renaming {key} matrix zones")

            # if lookup is undefined, make one
            if zone_name_lookup is None:
                zones = value["origin"].unique()
                zone_name_lookup = pd.DataFrame(
                    {"new": zones + ZONE_ADDITION}, index=zones
                ).to_dict()["new"]

            value.loc[:, ["origin", "destination"]] = value.loc[
                :, ["origin", "destination"]
            ].replace(zone_name_lookup)

            matrices[key] = value

        # find zone connectors and nodes to apply lookup to
        network = analysis_inputs.analysis_network
        network.loc[:, ["a", "b"]] = network[["a", "b"]].astype(int)

        nodes = analysis_inputs.analysis_network_nodes

        zone_connector_indices = network.loc[network["Type"] == "ZC"].index
        zones_indices = nodes.loc[nodes["Type"] == "zone"].index

        network.loc[zone_connector_indices, ["a", "b"]] = network.loc[
            zone_connector_indices, ["a", "b"]
        ].replace(zone_name_lookup)
        nodes.loc[zones_indices, "n"] = nodes.loc[zones_indices, "n"].replace(
            zone_name_lookup
        )

        original_keys = matrices.keys()

        # disaggregate by laden status
        disagg_matrices = disagg_laden_status(
            matrices, analysis_inputs.laden_status_factors
        )

        thirsty_points = {}

        # create od routes and thirsty points folder
        od_routes_folder = operational.output_folder / "od_routes"
        thirsty_points_folder = operational.output_folder / "thirsty_points"

        thirsty_points_folder.mkdir(exist_ok=True)

        thirsty_points = get_freight_thirsty_points(
            od_routes_folder,
            disagg_matrices,
            analysis_inputs.ranges,
            network,
            nodes,
        )

        # aggregate thirsty points by laden status
        thirsty_points = aggregate_laden_status(thirsty_points, original_keys)

    thirsty_points[ioc.COMBINED_KEY] = pd.concat(list(thirsty_points.values()))

    for key, points in thirsty_points.items():
        points.to_file(thirsty_points_folder / f"{key}_thirsty_points.shp")
    # create hex bins

    all_hex_bins = {}

    hexbin_shapefile_folder = operational.output_folder / "hexbin_shapefiles"

    hexbin_shapefile_folder.mkdir(exist_ok=True)

    for key, value in thirsty_points.items():
        LOG.info(f"Creating thirsty {key} hexs")
        # create and save hexbin png plot and create HexTilling object
        hex_bins = hex_plotting.hexbin_plot(
            value, plotting_inputs, f"Thirsty {key} Hex Plot", operational
        )
        # create and save shapefile
        LOG.info(f"Creating thirsty {key} hex shapefile")
        hex_plotting.create_hex_shapefile(
            hex_bins, f"thirsty_{key.lower()}_hexs.shp", hexbin_shapefile_folder
        )

        all_hex_bins[key] = hex_bins

    # create hex plot html
    LOG.info("Creating thirsty truck hex map")
    hex_plotting.create_hex_bin_html(
        all_hex_bins, plotting_inputs, "Thirsty Truck Hex Map", operational
    )


def get_freight_thirsty_points(
    od_lines: pathlib.Path | list[str],
    matrices: dict[str, pd.DataFrame],
    ranges: dict[str, pd.DataFrame],
    network: gpd.GeoDataFrame,
    nodes: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """wrapper for get_thirsty_points (also returns key)

    Parameters
    ----------
    key : str
        dictionary key of matrix
    matrix : pd.DataFrame
        od matrix
    zone_centroids : gpd.GeoDataFrame
        centroids of the zone system used in the matrix
    range_ : float
        range of vehicles in OD matrix
    output_folder : pathlib.Path
        path to folder to save intermediary outputs


    Returns
    -------
    tuple(str, gpd.GeoDataFrame)
        key and thirsty points
    """
    if isinstance(od_lines, pathlib.Path):
        LOG.info("Creating OD lines")
        # create od pairs using a matrix - these should be the same in each matrix so the matrix we choose is arbitrary
        arbitrary_matrix = list(matrices.values())[0]
        od_pairs = arbitrary_matrix[["origin", "destination"]]
        od_lines_paths = geospatial_analysis.create_od_lines(
            od_pairs,
            "Thirsty Truck Shortest Path",
            network,
            nodes,
            od_lines,
            False,
        )
    else:
        od_lines_paths = od_lines

    LOG.info(f"Getting thirsty points")

    for key, matrix in matrices:
        filtered_od_matrix = matrix.loc[matrix["trips"] != 0]
        thirsty_points = geospatial_analysis.create_thirsty_points_in_parallel(
            od_lines_paths,
            filtered_od_matrix,
            network,
            ranges[key],
            f"Thirsty Points {key}: ",
        )

    return thirsty_points


def disagg_laden_status(
    matrices: dict[str, pd.DataFrame], factors: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """disaggregate the matrices by laden status

    creates new key by vehicle type and laden status seperated by
    ioc.DISAGG_KEY_SEP

    Parameters
    ----------
    matrices : dict[str, pd.DataFrame]
        matrices to disaggregate
    factors : pd.DataFrame
        factors to disaggregate matrices by

    Returns
    -------
    dict[str, pd.DataFrame]
        disaggregated matrices
    """
    disagg_matrices = {}
    for key, matrix in matrices.items():
        for status in factors.index:
            # find laden factor
            f = factors.loc[status, key]
            mod_matrix = matrix.copy()
            mod_matrix["trips"] = mod_matrix["trips"] * f
            # create new key structure
            disagg_matrices[key + ioc.DISAGG_KEY_SEP + status] = mod_matrix
    return disagg_matrices


def aggregate_laden_status(
    thirsty_points: dict[str, gpd.GeoDataFrame], original_keys: list[str]
) -> dict[str, gpd.GeoDataFrame]:
    """aggregates the laden statuses

    assumes the thirsty points have keys generated from disagg_laden_status
    will split the keys using the defined key seperator
    will join by the original_keys found in the split keys

    Parameters
    ----------
    thirsty_points : dict[str, gpd.GeoDataFrame]
        thirsty points with disaggregated keys to aggregates
    original_keys : list[str]
        keys to aggregate by

    Returns
    -------
    dict[str, gpd.GeoDataFrame]
        aggregated thirsty points
    """
    # create split key lookup
    split_keys = {x: x.split(ioc.DISAGG_KEY_SEP) for x in thirsty_points.keys()}
    agg_thirsty_points = {}

    for key in original_keys:
        to_agg = []
        for disagg_key, split_disagg_key in split_keys.items():
            if key in split_disagg_key:
                to_agg.append(thirsty_points[disagg_key])
        agg_thirsty_points[key] = gpd.GeoDataFrame(
            pd.concat(to_agg, ignore_index=True), crs=input_output_constants.CRS
        )
    return agg_thirsty_points


def long_to_square(
    matrix: pd.DataFrame, origin_col: str, destination_col: str, trips_col: str
):
    square_matrix = matrix.pivot(
        index=origin_col, columns=destination_col, values=trips_col
    )
    return square_matrix


def square_to_long(
    square_matrix: pd.DataFrame, origin_col: str, destination_col: str, trips_col: str
):
    # Reset the index to create a DataFrame with columns 'o', 'd', and 'trips'
    matrix = square_matrix.reset_index()
    # Melt the DataFrame to get the original format
    melted_matrix = pd.melt(
        matrix, id_vars=origin_col, var_name=destination_col, value_name=trips_col
    )
    return melted_matrix


def translate_matrix(
    matrix: pd.DataFrame,
    zone_translation: pd.DataFrame,
    from_zoning: str,
    to_zoning: str,
    origin_col: str,
    destination_col: str,
    trips_col: str,
) -> pd.DataFrame:
    # pivot to square as toolkit doesnt accept long matrices
    square_matrix = long_to_square(matrix, origin_col, destination_col, trips_col)
    translated_sqaure_matrix = translation.pandas_matrix_zone_translation(
        matrix=square_matrix,
        translation=zone_translation,
        translation_from_col=f"{from_zoning}_id",
        translation_to_col=f"{to_zoning}_id",
        translation_factors_col=f"{from_zoning}_to_{to_zoning}",
    )
    # pivot back to long
    translated_long_matrix = square_to_long(
        translated_sqaure_matrix, f"{to_zoning}_id", destination_col, trips_col
    )
    translated_long_matrix.rename(columns={f"{to_zoning}_id": "origin"}, inplace=True)
    return translated_long_matrix
