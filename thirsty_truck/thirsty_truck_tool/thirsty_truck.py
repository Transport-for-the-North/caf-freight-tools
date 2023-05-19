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

if "local_freight_tool" not in sys.path:
    sys.path.append("local_freight_tool")

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
    LOG.info("Parsing LFT inputs and converting to annual PCU")

    #handle LFT input

    if analysis_inputs.lft_inputs is not None:
        trip_conversion_obj = hgv_annual_tonne_to_pcu.tonne_to_pcu(
            analysis_inputs.lft_inputs, operational.output_folder
        )
        od_matrices = trip_conversion_obj.total_trips
        for key, value in od_matrices.items():
            od_matrices[key]= value.column_matrix()
        LOG.info("Extracted annual trips")

    if analysis_inputs.od_matrices is not None:
        LOG.info("Extracting OD matrices")

        od_matrices = analysis_inputs.od_matrices

    if analysis_inputs.thirsty_points is not None:
        thirsty_points = analysis_inputs.thirsty_points

    else:
        thirsty_points = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    process_matrix,
                    key,
                    matrix,
                    analysis_inputs.zone_centroids,
                    analysis_inputs.range,
                    operational.output_folder,
                )
                for key, matrix in od_matrices.items()
            ]

            for future in concurrent.futures.as_completed(futures):
                key, temp_thirsty_points = future.result()
                thirsty_points[key] = temp_thirsty_points

    thirsty_points["Combined"] = pd.concat(list(thirsty_points.values()))

    all_hex_bins = {}

    for key, value in thirsty_points.items():

        LOG.info(f"Creating thirsty {key} hex shapefile")
        hex_bins = hex_plotting.hexbin_plot(
            value, plotting_inputs, f"Thirsty {key} Hex Plot", operational
        )

        hex_plotting.create_hex_shapefile(
            hex_bins, f"thirsty_{key.lower()}_hexs.shp", operational.output_folder
        )
        all_hex_bins[key] = hex_bins
    hex_plotting.create_hex_bin_html(
        all_hex_bins, plotting_inputs, "Thirsty Truck Hex Map", operational
    )


def process_matrix(
    key: str,
    matrix: pd.DataFrame,
    zone_centroids: gpd.GeoDataFrame,
    range: float,
    output_folder: pathlib.Path,
):
    """wrapper for get_thirsty_points (also returns key)

    Parameters
    ----------
    key : str
        dictionary key of matrix
    matrix : pd.DataFrame
        od matrix

    Returns
    -------
    tuple(str, gpd.GeoDataFrame)
        key and thirsty points
    """
    LOG.info(f"Getting {key} thirsty points")
    thirsty_points = geospatial_analysis.get_thirsty_points(
        input_output_constants.ParsedAnalysisInputs(matrix, zone_centroids, range),
        output_folder,
        f"thirsty_{key}_points.csv",
    )

    return key, thirsty_points
