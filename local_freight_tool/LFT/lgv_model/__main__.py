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
from ..tc_main_menu import tier_converter
from .lgv_model_ui import LGVModelUI


##### MAIN #####
# Check package versions before starting application
pc = PackageChecker()
pc.check_versions()

# Run the full Local Freight Tool
app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")

lgv = LGVModelUI()
sys.exit(app.exec_())
