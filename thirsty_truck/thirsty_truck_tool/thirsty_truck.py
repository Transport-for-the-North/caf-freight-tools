
# standard imports
import logging
import argparse
import sys
import concurrent.futures
# third party imports
from tqdm.contrib import logging as tqdm_log
import pandas as pd

# add src to path before importing thirsty truck

if "local_freight_tool" not in sys.path:
    sys.path.append("local_freight_tool")

if "local_freight_tool" not in sys.path:
    sys.path.append("local_freight_tool")

# local imports
from thirsty_vehicle_tool import input_output_constants, tv_logging, hex_plotting, geospatial_analysis
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
    plotting_inputs:input_output_constants.PlottingInputs,
    operational:input_output_constants.Operational
)->None:
    LOG.info("Parsing LFT inputs and converting to annual PCU")
    #pcu_conversion_obj = hgv_annual_tonne_to_pcu.tonne_to_pcu(analysis_inputs.tonne_to_pcu_inputs, operational.output_folder)
    #annual_pcu = pcu_conversion_obj.total_pcus
    #TODO remove temp development import
    LOG.info("Extracted annual PCUs")
    artic = pd.read_csv("C:/Users/UKKXF022/Documents/Midlands_connect_freight/thirsty_truck_outputs/artic_total_annual_pcus.csv")
    rigid = pd.read_csv("C:/Users/UKKXF022/Documents/Midlands_connect_freight/thirsty_truck_outputs/rigid_total_annual_pcus.csv")

    od_matrices = {"Artic": artic, "Rigid": rigid}

    all_hex_bins = {}

    all_thirsty_points = []

    def process_matrix(key, matrix):
        LOG.info(f"Getting {key} thirsty points")
        thirsty_points = geospatial_analysis.get_thirsty_points(
            input_output_constants.ParsedAnalysisInputs(matrix, analysis_inputs.zone_centroids, analysis_inputs.range),
            operational.output_folder, f"thirsty_{key}_points.csv"
        )
        LOG.info(f"Creating thirsty {key} hex points")
        hex_bins = hex_plotting.hexbin_plot(thirsty_points, plotting_inputs, f"Thirsty {key} Hex Plot", operational)
        LOG.info(f"Creating thirsty {key} hex shapefile")
        hex_plotting.create_hex_shapefile(hex_bins, f"thirsty_{key}_hexs.shp", operational.output_folder)
        return key, thirsty_points, hex_bins

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_matrix, key, matrix) for key, matrix in od_matrices.items()]

        for future in concurrent.futures.as_completed(futures):
            key, thirsty_points, hex_bins = future.result()
            all_hex_bins[key] = hex_bins
            all_thirsty_points.append(thirsty_points)
    #create combined points and hexes
    combined_thirsty_points = pd.concat(all_thirsty_points)
    combined_hex_bins = hex_plotting.hexbin_plot(combined_thirsty_points, plotting_inputs, f"Thirsty {key} Hex Plot", operational)

    LOG.info(f"Creating thirsty combined hex shapefile")
    hex_plotting.create_hex_shapefile(combined_hex_bins, f"thirsty_combined_hexs.shp", operational.output_folder)
    all_hex_bins["Combined"] = combined_hex_bins
    hex_plotting.create_hex_bin_html(all_hex_bins, plotting_inputs, "Thirsty Truck Hex Map", operational)



