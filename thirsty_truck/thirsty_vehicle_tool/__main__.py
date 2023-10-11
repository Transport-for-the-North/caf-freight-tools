"""calls tool and passes location of config file
"""
import sys
import argparse

# add src to path before importing thirsty truck
if "thirsty_truck/src" not in sys.path:
    sys.path.append("thirsty_truck/src")

from thirsty_vehicle_tool import thirsty_vehicle

parser = argparse.ArgumentParser(description="Arguements for the thirsty vehicle tool")
parser.add_argument(
    "-c",
    "--config",
    help="Config file path",
    default="thirsty_truck\thirsty-vehicle-config.yml",
    type=str,
)
args = parser.parse_args()

thirsty_vehicle.main(args)
