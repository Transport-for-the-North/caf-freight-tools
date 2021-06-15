# -*- coding: utf-8 -*-
"""
    Main module for running the whole Local Freight Tool (LFT).
"""

##### IMPORTS #####
# Standard imports
import sys

# Third party imports
from PyQt5 import QtWidgets

# Local imports
from package_check import PackageChecker
from tc_main_menu import tier_converter


##### MAIN #####
# Check package versions before starting application
pc = PackageChecker()
pc.check_versions()

# Run the full Local Freight Tool
app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
tc = tier_converter()
sys.exit(app.exec_())
