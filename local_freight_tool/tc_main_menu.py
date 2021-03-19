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
from PyQt5.QtCore import pyqtSlot

# User-defined imports
from profile_builder import Profile_Builder
from annualtonne2pcu import AnnualTonne2PCU
from matrix_utilities_ui import MatrixUtilities
from gbfm2modelpcu import GBFM2ModelPCU
from lgvprocessing import LGVProcessing
from combine_shapefiles import CombineShapefiles
from producegbfmcorrespondence import ProduceGBFMCorrespondence
from deltaprocess import DeltaProcess
from utilities import Utilities, info_window
from text_info import Tier_Converter_Text
from cost_conversion import WeightedRezone

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
        self.setGeometry(500, 200, 500, 500)
        self.setWindowTitle("Local Freight Tool")
        self.setWindowIcon(QtGui.QIcon("icon.jpg"))

        labelA = QtWidgets.QLabel(self)
        labelA.setText("Local Freight Tool")
        labelA.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        labelA.setGeometry(10, 10, 700, 30)

        labelB = QtWidgets.QLabel(self)
        labelB.setText("Pre-Processing")
        labelB.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelB.setGeometry(10, 50, 700, 30)

        # Create a push button for 'info'
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("Info")
        next_button.setGeometry(400, 10, 90, 30)
        next_button.clicked.connect(self.on_click_Info)

        # Create a push buttons for menu options
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("0: Combine Centroid and Polygon Shapefiles")
        next_button.setGeometry(10, 90, 480, 30)
        next_button.clicked.connect(self.on_click_CombineShapefiles)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("1: Produce Zone Correspondence")
        next_button.setGeometry(10, 130, 480, 30)
        next_button.clicked.connect(self.on_click_ProduceGBFMCorrespondence)

        #  Create a push button for Profile Builder
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("2: Time Profile Builder")
        next_button.setGeometry(10, 170, 480, 30)
        next_button.clicked.connect(self.on_click_Profile_Builder)

        labelC = QtWidgets.QLabel(self)
        labelC.setText("Conversion")
        labelC.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelC.setGeometry(10, 200, 700, 30)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("3: HGV Annual Tonne to Annual PCU Conversion")
        next_button.setGeometry(10, 230, 480, 30)
        next_button.clicked.connect(self.on_click_AnnualTonne2PCU)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("4: HGV Annual PCU to Model Zoning and Time Periods")
        next_button.setGeometry(10, 270, 480, 30)
        next_button.clicked.connect(self.on_click_GBFM2ModelPCU)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("5: LGV Processing")
        next_button.setGeometry(10, 310, 480, 30)
        next_button.clicked.connect(self.on_click_LGVProcessing)

        labelD = QtWidgets.QLabel(self)
        labelD.setText("Utilities")
        labelD.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelD.setGeometry(10, 340, 700, 30)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("6: Matrix Utilities")
        next_button.setGeometry(10, 370, 480, 30)
        next_button.clicked.connect(self.on_click_MatrixUtilities)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("7: Delta Process")
        next_button.setGeometry(10, 410, 480, 30)
        next_button.clicked.connect(self.on_click_DeltaProcess)

        next_button = QtWidgets.QPushButton(self)
        next_button.setText("8: Cost Conversion")
        next_button.setGeometry(10, 450, 480, 30)
        next_button.clicked.connect(self.on_click_CostConversion)

        self.show()

    @pyqtSlot()
    def on_click_Profile_Builder(self):
        self.selections_window = Profile_Builder(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_Info(self):
        self.progress = info_window("Local Freight Tool Information")
        self.progress_label = self.progress.label
        self.progress_labelA = self.progress.labelA
        dedented_text = textwrap.dedent(Tier_Converter_Text)
        line = textwrap.fill(dedented_text, width=140)
        self.progress_label.setText(line)
        self.progress_label.move(10, 40)
        self.progress_labelA.setText("Local Freight Tool Information")
        self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.progress.show()

        def closeEvent(self, event):
            Utilities.closeEvent(self, event)

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
    def on_click_GBFM2ModelPCU(self):
        self.selections_window = GBFM2ModelPCU(self)
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
