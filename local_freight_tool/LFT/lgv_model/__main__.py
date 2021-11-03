"""
    Main module for running the LGV model.
"""

##### IMPORTS #####
# Standard imports
import sys

# Third party imports
from PyQt5 import QtWidgets

# Local imports
from ..package_check import PackageChecker
from .lgv_model_ui import LGVModelUI
from .lgv_model import lgv_arg_parser, LGVConfig, main


##### MAIN #####
# Check package versions before starting application
pc = PackageChecker()
pc.check_versions()

# Check if commandline arguments are given
parser = lgv_arg_parser()
args = parser.parse_args()
if args.example:
    LGVConfig.write_example(args.config_file)
elif args.config_file is not None:
    # Run the LGV model without displaying the UI if config is given
    config_file = LGVConfig(args.config_file)
    main(config_file.input_paths)
else:
    # Run the LGV model UI if config isn't given
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    lgv = LGVModelUI()
    sys.exit(app.exec_())
