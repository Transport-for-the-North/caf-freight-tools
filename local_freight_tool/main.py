# -*- coding: utf-8 -*-
"""
    Main script for running the whole Local Freight Tool (LFT).
"""

##### IMPORTS #####
# Standard imports
import sys

# Third party imports
from PyQt5 import QtWidgets

# Local imports
from LFT import PackageChecker, tier_converter


##### MAIN #####
if __name__ == "__main__":
    PackageChecker().check_versions()

    # Run the full Local Freight Tool
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    tc = tier_converter()
    sys.exit(app.exec_())
