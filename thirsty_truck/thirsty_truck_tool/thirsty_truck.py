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

# third party imports
from tqdm.contrib import logging as tqdm_log
import pandas as pd
import geopandas as gpd

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
from LFT import hgv_annual_tonne_to_pcu

LOG_FILE = "thirsty_truck.log"
LOG = tv_logging.get_logger(__name__)


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
    annual_tonne_to_trip_folder = operational.output_folder / "annual_tonne_to_pcu_conversion"
    annual_tonne_to_trip_folder.mkdir(exist_ok=True)
    if analysis_inputs.lft_inputs is not None:
        LOG.info("Parsing LFT inputs and converting to annual PCU")
        trip_conversion_obj = hgv_annual_tonne_to_pcu.tonne_to_pcu(
            analysis_inputs.lft_inputs, annual_tonne_to_trip_folder
        )
        unformatted_od_matrices = trip_conversion_obj.total_trips
        od_matrices = {}
        key_lookup = ioc.convert_lft_keys(
            list(analysis_inputs.ranges.keys()), list(unformatted_od_matrices.keys())
        )
        for key, value in unformatted_od_matrices.items():
            od_matrices[key_lookup[key]] = value.column_matrix()

        LOG.info("Extracted annual trips")

    if analysis_inputs.od_matrices is not None:
        LOG.info("Extracting OD matrices")

        od_matrices = analysis_inputs.od_matrices

    if analysis_inputs.thirsty_points is not None:
        thirsty_points = analysis_inputs.thirsty_points

    else:
        original_keys = od_matrices.keys()
        disagg_matrices = disagg_laden_status(od_matrices, analysis_inputs.laden_status_factors)

        thirsty_points = {}

        thirsty_points_folder = operational.output_folder / "thirsty_points"

        thirsty_points_folder.mkdir(exist_ok=True)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    process_matrix,
                    key,
                    matrices,
                    analysis_inputs.zone_centroids,
                    analysis_inputs.ranges[key],
                    thirsty_points_folder,
                )
                for key, matrices in disagg_matrices.items()
            ]

            for future in concurrent.futures.as_completed(futures):
                key, temp_thirsty_points = future.result()
                thirsty_points[key] = temp_thirsty_points

        thirsty_points = aggregate_laden_status(thirsty_points, original_keys)

    thirsty_points[ioc.COMBINED_KEY] = pd.concat(list(thirsty_points.values()))

    all_hex_bins = {}

    hexbin_shapefile_folder = operational.output_folder / "hexbin_shapefiles"

    hexbin_shapefile_folder.mkdir(exist_ok=True)

    for key, value in thirsty_points.items():
        LOG.info(f"Creating thirsty {key} hexs")

        hex_bins = hex_plotting.hexbin_plot(
            value, plotting_inputs, f"Thirsty {key} Hex Plot", operational
        )

        LOG.info(f"Creating thirsty {key} hex shapefile")
        hex_plotting.create_hex_shapefile(
            hex_bins, f"thirsty_{key.lower()}_hexs.shp", hexbin_shapefile_folder
        )
        all_hex_bins[key] = hex_bins

    LOG.info("Creating thirsty truck hex map")
    hex_plotting.create_hex_bin_html(
        all_hex_bins, plotting_inputs, "Thirsty Truck Hex Map", operational
    )


def process_matrix(
    key: str,
    matrix: pd.DataFrame,
    zone_centroids: gpd.GeoDataFrame,
    range_: float,
    output_folder: pathlib.Path,
):
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
    LOG.info(f"Getting {key} thirsty points")
    thirsty_points = geospatial_analysis.get_thirsty_points(
        input_output_constants.ParsedAnalysisInputs(matrix, zone_centroids, range_),
        output_folder,
        f"thirsty_{key}_points.csv",
        key,
    )

    return key, thirsty_points

def disagg_laden_status(matrices: dict[str, pd.DataFrame], factors: pd.DataFrame)->dict[str, pd.DataFrame]:
    disagg_matrices = {}
    for key, matrix in matrices.items():
        for status in factors.index:
            f = factors.loc[status, key]
            mod_matrix = matrix.copy()
            mod_matrix["trips"] = mod_matrix["trips"]*f
            disagg_matrices[key+ioc.DISAGG_KEY_SEP+status] = mod_matrix
    return disagg_matrices

def aggregate_laden_status(thirsty_points: dict[str, gpd.GeoDataFrame], original_keys: list[str])->dict[str, gpd.GeoDataFrame]:
    split_keys = {x:x.split(ioc.DISAGG_KEY_SEP) for x in thirsty_points.keys()}
    agg_thirsty_points = {}
    for key in original_keys:
        to_agg = []
        for disagg_key, split_disagg_key in split_keys.items():
            if key in split_disagg_key:
                to_agg.append(thirsty_points[disagg_key])
        agg_thirsty_points[key] = gpd.GeoDataFrame(pd.concat(to_agg, ignore_index=True), crs=input_output_constants.CRS)
    return agg_thirsty_points
    

