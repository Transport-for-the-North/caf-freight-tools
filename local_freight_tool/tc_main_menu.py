"""

Created on: Wed Feb 26 09:32:01 2020
Updated on: Wed Dec 23 14:12:46 2020

Original author: racs
Last update made by: cara

File purpose:
Freight model tier converter tool. Translates Great Britain Freight Model
(GBFM) output matrices to matrices with model-specific time period and zoning
system.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, Qt

# User-defined imports
from profile_builder import Profile_Builder
from annualtonne2pcu import AnnualTonne2PCU
from matrix_utilities_ui import MatrixUtilities
from lgvprocessing import LGVProcessing
from combine_shapefiles import CombineShapefiles
from producegbfmcorrespondence import ProduceGBFMCorrespondence
from deltaprocess import DeltaProcess
from utilities import Utilities, info_window
from text_info import Tier_Converter_Text
from cost_conversion import WeightedRezone
from time_period_conversion_ui import TimeConversionUI
from info_window import InfoWindow

# Other packages
import sys
import textwrap

#########################################################################

# Main interface window
class tier_converter(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 200, 500, 540)
        self.setWindowTitle("Local Freight Tool")
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        logo_label = QtWidgets.QLabel(self)
        logo_image = QtGui.QPixmap('TFN_title.png')
        logo_image = logo_image.scaled(168, 40, Qt.KeepAspectRatio, Qt.FastTransformation)
        logo_label.setGeometry(320, 10, 168, 40)
        logo_label.setPixmap(logo_image)

        labelA = QtWidgets.QLabel(self)
        labelA.setText("Local Freight Tool")
        labelA.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Bold))
        labelA.setGeometry(10, 10, 700, 40)

        y = 60
        sep = 40
        labelB = QtWidgets.QLabel(self)
        labelB.setText("Pre-Processing")
        labelB.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelB.setGeometry(10, y, 700, 30)

        # Create a push button for 'info'
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("Info")
        next_button.setGeometry(400, y, 90, 30)
        next_button.clicked.connect(self.on_click_Info)

        y += sep
        # Create a push buttons for menu options
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("0: Combine Centroid and Polygon Shapefiles")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_CombineShapefiles)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("1: Produce Zone Correspondence")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_ProduceGBFMCorrespondence)

        y += sep
        #  Create a push button for Profile Builder
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("2: Time Profile Builder")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_Profile_Builder)

        y += sep
        labelC = QtWidgets.QLabel(self)
        labelC.setText("Conversion")
        labelC.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelC.setGeometry(10, y, 700, 30)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("3: HGV Annual Tonne to Annual PCU Conversion")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_AnnualTonne2PCU)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("4: HGV Annual PCU to Model Zoning and Time Periods")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_time_period_conv)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("5: LGV Processing")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_LGVProcessing)

        y += sep
        labelD = QtWidgets.QLabel(self)
        labelD.setText("Utilities")
        labelD.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelD.setGeometry(10, y, 700, 30)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("6: Matrix Utilities")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_MatrixUtilities)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("7: Delta Process")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_DeltaProcess)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("8: Cost Conversion")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_CostConversion)

        self.show()

    @pyqtSlot()
    def on_click_Profile_Builder(self):
        self.selections_window = Profile_Builder(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_Info(self):
        self.selections_window = InfoWindow(self, 'README.md')
        self.selections_window.show()

    @pyqtSlot()
    def on_click_CombineShapefiles(self):
        self.selections_window = CombineShapefiles(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_ProduceGBFMCorrespondence(self):
        self.selections_window = ProduceGBFMCorrespondence(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_AnnualTonne2PCU(self):
        self.selections_window = AnnualTonne2PCU(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_LGVProcessing(self):
        self.selections_window = LGVProcessing(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_time_period_conv(self):
        self.selections_window = TimeConversionUI(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_MatrixUtilities(self):
        self.selections_window = MatrixUtilities(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_DeltaProcess(self):
        self.selections_window = DeltaProcess(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_CostConversion(self):
        self.selections_window = WeightedRezone(self)
        self.hide()
        self.selections_window.show()

    # Function which asks the user if they really want to trigger sys.exit()
    def closeEvent(self, event):
        Utilities.closeEvent(self, event)


# =============================================================================
# Main
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    tc = tier_converter()
    sys.exit(app.exec_())
