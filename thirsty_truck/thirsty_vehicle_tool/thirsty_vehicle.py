"""
Thristy Truck Tool:
processes OD matrix, zone centroids and vehicle range into a hexbin
heatmap which indicates where the vehicle will run out of fuel/power

Kieran Fishwick: kieran.fishwick@wsp.com
"""
# standard imports
import logging
import argparse

# third party imports
from tqdm.contrib import logging as tqdm_log

# local imports
from thirsty_vehicle_tool import input_output_constants, tv_logging, geospatial_analysis, hex_plotting

LOG_FILE = "thirsty_vehicle.log"
LOG = tv_logging.get_logger(__package__)


def main(args: argparse.Namespace) -> None:
    """initilises Logging and calls run

    Parameters
    ----------
    args : argparse.Namespace
        command line arguement inputs
    """
    with tv_logging.ThirstyVehicleLog("Thirsty Vehicle Tool") as thirsty_truck_log:
        with tqdm_log.logging_redirect_tqdm([thirsty_truck_log.logger]):
            run(thirsty_truck_log, args)


def run(log: tv_logging.ThirstyVehicleLog, args: argparse.Namespace) -> None:
    """parses config, set up logging and passes inputs to tool

    inputs: reads in config, parses file paths to inputs and passes this to tool
    logging: initialises logging file

    Parameters
    ----------
    log : utilities.ThirstyTruckLog
        logging class
    args : argparse.Namespace
        command line arguement inputs
    """
    config = input_output_constants.ThirstyVehicleConfig.load_yaml(args.config)
    config.operational.output_folder.mkdir(exist_ok=True)

    log.add_file_handler(config.operational.output_folder / LOG_FILE)

    config.convert_to_m()

    analysis_inputs = config.analysis_inputs.parse_analysis_inputs()
    plotting_inputs = config.plotting_inputs.parse_plotting_inputs(config.operational)

    thirsty_vehicle_process(analysis_inputs, plotting_inputs, config.operational)


def thirsty_vehicle_process(
    analysis_inputs: input_output_constants.ParsedAnalysisInputs,
    plotting_inputs: input_output_constants.ParsedPlottingInputs,
    operational: input_output_constants.Operational,
) -> None:
    """handles thirsty truck process taking in data inputs

    creates thirsty points 

    Parameters
    ----------
    thirsty_vehicle_inputs : input_outputs.ParsedInputs
        parsed inputs for the tool
    operational : input_outputs.Operational
        operational tool inputs
    """

    thirsty_points = geospatial_analysis.get_thirsty_points(
        analysis_inputs, operational.output_folder
    )
    #create hexbins object and create png
    hex_bins = hex_plotting.hexbin_plot(
        thirsty_points,
        plotting_inputs,
        "Thirsty Truck Hex Map",
        operational,
    )
    #html plot
    hex_plotting.create_hex_bin_html(
        hex_bins,
        plotting_inputs,
        "Thirsty Truck Hex Map",
        operational,)
    #create hex shapefile
    hex_plotting.create_hex_shapefile(
        hex_bins,
        "Thirsty_Truck_Hex.shp",
        operational.output_folder/"thristy_truck_hex",
        )
