"""
Freight model tier converter tool. Translates Great Britain Freight Model
(GBFM) output matrices to matrices with model-specific time period and zoning
system.
"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, Qt

# Local imports
from .profile_builder import Profile_Builder
from .hgv_annual_tonne_to_pcu_ui import TonneToPCUInterface
from .matrix_utilities_ui import MatrixUtilities
from .lgv_model.lgv_model_ui import LGVModelUI
from .combine_shapefiles import CombineShapefiles
from .zone_correspondence_ui import ZoneCorrespondenceUi
from .forecast_ui import ForecastUI
from .utilities import Utilities
from .cost_conversion import WeightedRezone
from .time_period_conversion_ui import TimeConversionUI
from .info_window import InfoWindow
from .data_utils import local_path

# Other packages

#########################################################################

# Main interface window
class tier_converter(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 200, 500, 540)
        self.setWindowTitle("Local Freight Tool")
        self.setWindowIcon(QtGui.QIcon(str(local_path("icon.png"))))

        logo_label = QtWidgets.QLabel(self)
        logo_image = QtGui.QPixmap(str(local_path('TFN_title.png')))
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
        next_button.setText("0: Combine Point and Polygon Shapefiles")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_CombineShapefiles)

        y += sep
        next_button = QtWidgets.QPushButton(self)
        next_button.setText("1: Produce Zone Correspondence")
        next_button.setGeometry(10, y, 480, 30)
        next_button.clicked.connect(self.on_click_ZoneCorrespondence)

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
        next_button.setText("5: LGV Model")
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
    def on_click_ZoneCorrespondence(self):
        self.selections_window = ZoneCorrespondenceUi(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_AnnualTonne2PCU(self):
        self.selections_window = TonneToPCUInterface(self)
        self.hide()
        self.selections_window.show()

    @pyqtSlot()
    def on_click_LGVProcessing(self):
        self.selections_window = LGVModelUI(self)
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
        self.selections_window = ForecastUI(self)
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
