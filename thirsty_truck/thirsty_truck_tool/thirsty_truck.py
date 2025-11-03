"""Thirsty truck process
Takes annual tonnage to a thirsty truck hex map
imports LFT and thirsty vehicle
Louis Fisher: louis.fisher@wsp.com
"""
# standard imports
import argparse
import sys
import concurrent.futures
import pathlib
import os
import rlcompleter
from datetime import datetime
from typing import Optional

# third party imports
from tqdm.contrib import logging as tqdm_log
import pandas as pd
import geopandas as gpd
import pdb
from caf.toolkit import translation

# add src to path before importing thirsty truck

if "local_freight_tool" not in sys.path:
    sys.path.append("./local_freight_tool/LFT")

# if "LFT" not in sys.path:
#     sys.path.append("LFT")

# local imports
from thirsty_truck.thirsty_vehicle_tool import (
    input_output_constants,
    tv_logging,
    hex_plotting,
    geospatial_analysis,
)
from thirsty_truck_tool import ioc
from local_freight_tool.LFT import hgv_annual_tonne_to_pcu, matrix_utilities


LOG_FILE = "thirsty_truck.log"
LOG = tv_logging.get_logger(__name__)
KEYS = []
ZONE_ADDITION = 1000000


def main(args: argparse.Namespace) -> None:
    """initilises Logging and calls run

    Parameters
    ----------
    args : argparse.Namespace
        command line argument inputs
    """
    with tv_logging.ThirstyVehicleLog("Thirsty Truck Tool") as thirsty_truck_log:
        with tqdm_log.logging_redirect_tqdm([thirsty_truck_log.logger]):
            run(thirsty_truck_log, args)


def run(log: tv_logging.ThirstyVehicleLog, args: argparse.Namespace) -> None:
    """handles creating file handler reading and parsing the config file
    before passing inputs to processes

    Parameters
    ----------
    log : tv_logging.ThirstyVehicleLog
        Logging class
    args : argparse.Namespace
        keyword arguments from tool call
    """
    
    config = ioc.ThirstyTruckConfig.load_yaml(args.config)
    config.operational.output_folder.mkdir(exist_ok=True)

    if config.operational.run_LFT == True and config.operational.run_FEDZ == False:
        run_type = "LFT"
    if config.operational.run_LFT == False and config.operational.run_FEDZ == True:
        run_type = "FEDZ"
    if config.operational.run_LFT == True and config.operational.run_FEDZ == True:
        run_type = "Both"
    
    KEYS.append(config.analysis_inputs.vehicle_keys)

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
    LOG.info(input_summary)
    input_output_constants.write_txt(config.operational.output_folder / "input_summary.txt", input_summary)
    thirsty_truck(analysis_inputs, plotting_inputs, config.operational, run_type)   
        


def thirsty_truck(
    analysis_inputs: ioc.ParsedAnalysisInputs,
    plotting_inputs: input_output_constants.PlottingInputs,
    operational: input_output_constants.Operational,
    toggle: str
) -> None:
    """Combines processes to create the thirsty truck process.

    Combines elements of the the thirsty vehicle tool and LFT.

    Parameters
    ----------
    analysis_inputs : ioc.ParsedAnalysisInputs
        parsed analysis inputs from the config file
    plotting_inputs : input_output_constants.Plotti ngInputs
        parsed plotting inputs from the config file
    operational : input_output_constants.Operational
        operational inputs from the config file
    toggle: determines which processes to run
    """
    if toggle != "FEDZ":   
        # handle LFT input
        annual_tonne_to_trip_folder = (
            operational.output_folder / "annual_tonne_to_pcu_conversion"
        )

        od_matrices_folder = operational.output_folder / "od_matrices"
        economic_geographies_folder = operational.output_folder / "economic_geographies"
        # ensure the directory exists
        annual_tonne_to_trip_folder.mkdir(exist_ok=True)
        od_matrices_folder.mkdir(exist_ok=True)
        economic_geographies_folder.mkdir(exist_ok=True)
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
##########################################################################################
            
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

                target_matrices = {}
                
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
                        target_matrices[key] = translate_matrix(
                            value,
                            analysis_inputs.zone_translation,
                            analysis_inputs.original_zoning,
                            analysis_inputs.target_zoning,
                            "origin",
                            "destination",
                            "trips",
                        )

                        input_output_constants.write_to_csv(
                                od_matrices_folder / f"{key}_{analysis_inputs.target_zoning}.csv",
                                target_matrices[key],
                            )


                else:
                    target_matrices = od_matrices

                zone_name_lookup = None

                matrices = {}

        if analysis_inputs.economic_geographies_toggle:
            LOG.info(f"creating economic geographies outputs")
            industry_data_by_zone = analysis_inputs.industries
            operational_hours = analysis_inputs.operational_hours
            general_haulage_factor = analysis_inputs.general_haulage_factor
            industry_data_by_zone["N"] = industry_data_by_zone["N"].astype(str)
            for key, od_matrix in od_matrices.items():
                od_matrix[['origin', 'destination']] = od_matrix[['origin', 'destination']].astype(str)
                od_matrix["trips"] = od_matrix["trips"].astype(float)
                economic_geographies(industry_data_by_zone, operational_hours, key, od_matrix, general_haulage_factor, economic_geographies_folder)

    # Thirsty Vehicle starts here
    if toggle != "LFT":
        zone_name_lookup = None
        matrices = {}

        for key, value in target_matrices.items():
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

        # # find zone connectors and nodes to apply lookup to
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

        # create od routes and thirsty points folder
        if analysis_inputs.od_lines is None:
            od_lines = operational.output_folder / "od_routes"
            thirsty_points_folder = operational.output_folder / "thirsty_points"
            thirsty_points_folder = operational.output_folder / "thirsty_points"
            od_lines.mkdir(exist_ok=True)

        else:
            od_lines = analysis_inputs.od_lines
        

        thirsty_points_folder.mkdir(exist_ok=True)

        thirsty_points = get_freight_thirsty_points(
            od_lines,
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
) -> dict[str, gpd.GeoDataFrame]:
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
            True,
        )
    else:
        od_lines_paths = od_lines

    LOG.info(f"Getting thirsty points")
    thirsty_point_outputs = {}
    for key, matrix in matrices.items():
        key = key.lower()
        filtered_od_matrix = matrix.loc[matrix["trips"] != 0]
        thirsty_points = geospatial_analysis.create_thirsty_points_in_parallel(
            od_lines_paths,
            filtered_od_matrix,
            network,
            ranges[key],
            f"Thirsty Points {key}: ",
        )
        thirsty_points.reset_index(drop=True, inplace=True)
        # tidy up columns and set new geometry

        thirsty_points = gpd.GeoDataFrame(thirsty_points, geometry="geometry")
        thirsty_points.crs = input_output_constants.CRS

        thirsty_point_outputs[key] = thirsty_points
    
    return thirsty_point_outputs


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
            f = factors.loc[status, key.lower()]
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
            if key in split_disagg_key or key.lower() in split_disagg_key:
                to_agg.append(thirsty_points[disagg_key])
        agg_thirsty_points[key] = gpd.GeoDataFrame(pd.concat(to_agg, ignore_index=True), crs=input_output_constants.CRS)
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

def economic_geographies(industries: pd.DataFrame, operational_hours: pd.DataFrame, veh_weight_class: str, od_matrix: pd.DataFrame, general_haulage_factor: float, eg_output_folder: pathlib.Path) -> pd.DataFrame.to_csv:

    time_period_durations = {"AM":3,"IP":6,"PM":3,"OP":12}

    if veh_weight_class not in ["artic", "rigid"]:
        aggregated_output = False
        operational_hours = operational_hours.loc[operational_hours['Key'] == veh_weight_class]
        operational_hours = operational_hours.drop(columns=["Key"])
        operational_hours = operational_hours.set_index(["TP"])
        operational_hours = operational_hours.loc[:, (operational_hours != 0).any(axis=0)]
        ind_names = list(operational_hours)
        operational_hours["General Haulage"] = 1

        factors = pd.merge(od_matrix, industries, left_on='origin', right_on='N',how='left')
        factors = factors.drop(columns='N')
        factors = factors.set_index(['origin', 'destination'])
        factors = factors.fillna(1 / (len(factors.columns)-1))
        factors = factors.mul(factors['trips'], axis=0)
        factors = factors.drop(columns='trips')
        factors = factors[factors.columns.intersection(list(ind_names))]
        factors["General Haulage"] = factors.sum(axis=1)*(1-general_haulage_factor)
        factors.loc[:, factors.columns != 'General Haulage'] = factors.loc[:, factors.columns != 'General Haulage']*general_haulage_factor

    else:
        aggregated_output = True
        od_matrix = od_matrix.set_index(['origin', 'destination'])
        operational_hours['Key'] = operational_hours['Key'].str.lower()
        operational_hours = operational_hours[operational_hours['Key'].str.contains(veh_weight_class)]
        operational_hours = operational_hours.drop(columns=["Key"])
        operational_hours = operational_hours.groupby("TP").sum()
        operational_hours['Total'] = operational_hours.sum(axis=1)
        operational_hours = operational_hours[operational_hours.columns.intersection(["Total"])]

    for time_period, row in operational_hours.iterrows():
        print(f"Multiplying Trips by {time_period} Operational Hour Factors for {veh_weight_class}")
        if aggregated_output:  
            divisor = time_period_durations[time_period]
        else:
            divisor = 1
        output = od_matrix * row.to_numpy() / divisor
        output_name = f"{time_period}_{veh_weight_class}"
        print(f"Saving to {output_name}.csv")
        output.to_csv(eg_output_folder / pathlib.Path(f"{output_name}.csv"))


