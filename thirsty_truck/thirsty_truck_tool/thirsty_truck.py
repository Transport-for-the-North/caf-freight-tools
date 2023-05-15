
# standard imports
import logging
import argparse
import sys

# third party imports
from tqdm.contrib import logging as tqdm_log

# add src to path before importing thirsty truck

if "local_freight_tool" not in sys.path:
    sys.path.append("local_freight_tool")

if "local_freight_tool" not in sys.path:
    sys.path.append("local_freight_tool")

# local imports
from thirsty_vehicle_tool import input_output_constants
from thirsty_truck_tool import thirsty_truck_logging, ioc
from LFT import hgv_annual_tonne_to_pcu

LOG_FILE = "thirsty_truck.log"
LOG = logging.getLogger(__package__)


def main(args: argparse.Namespace) -> None:
    """initilises Logging and calls run

    Parameters
    ----------
    args : argparse.Namespace
        command line arguement inputs
    """
    with thirsty_truck_logging.ThirstyTruckLog() as thirsty_truck_log:
        with tqdm_log.logging_redirect_tqdm([thirsty_truck_log.logger]):
            run(thirsty_truck_log, args)

def run(log: thirsty_truck_logging.ThirstyTruckLog, args: argparse.Namespace) -> None:

    config = ioc.ThristyTruckConfig.load_yaml(args.config)
    config.operational.output_folder.mkdir(exist_ok=True)

    log.add_file_handler(config.operational.output_folder / LOG_FILE)