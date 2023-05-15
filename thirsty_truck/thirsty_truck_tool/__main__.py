"""calls tool and passes location of config file
"""
import sys
import argparse

if "thirsty_truck" not in sys.path:
    sys.path.append("thirsty_truck")

# add src to path before importing thirsty truck
from thirsty_truck_tool import thirsty_truck

parser = argparse.ArgumentParser(description="Arguements for the thirsty truck tool")
parser.add_argument(
    "-c",
    "--config",
    help="Config file path",
    default="thirsty-truck-config.yml",
    type=str,
)
args = parser.parse_args()

thirsty_truck.main(args)
