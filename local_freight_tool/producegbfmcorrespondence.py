# -*- coding: utf-8 -*-
"""

Created on: Tue Mar  3 09:56:44 2020
Updated on: Wed Dec 23 15:31:50 2020

Original author: racs
Last update made by: cara

File purpose:
Produces zone_correspondence.csv which can be used within the GBFM Annual PCU
to Model Time Period PCU tool to convert the GBFM zoning system to a model
zoning system.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, QThread, Qt
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QDoubleSpinBox


# User-defined imports
from utilities import Utilities, info_window, progress_window
from text_info import ProduceGBFMCorrespondence_Text
import zone_correspondence as zcorr

# Other packages
import textwrap
import os


class ProduceGBFMCorrespondence(QtWidgets.QWidget):
    """Produce GBFM correspodence user interface.

    Parameters
    ----------
    QtWidgets : QWidget
        Base class for user interfact objects.
    """

    def __init__(self, tier_converter):
        """Initialises class

        Parameters
        ----------
        tier_converter : Class
            Tier converter class in tc_main_menu
        """
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()

    def initUI(self):
        """Initialises UI"""
        self.setGeometry(500, 320, 510 + 110, 540)
        self.setWindowTitle("Zone Correspondence Tool")
        self.setWindowIcon(QtGui.QIcon("icon.jpg"))

        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setText("Zone Correspondence Tool")
        labelB.setGeometry(10, 10, 700, 30)

        # Add file path and name selection fields
        # Zone 1
        self.labelZ1 = QtWidgets.QLabel(self)
        self.labelZ1.setText("Zone 1 name (defaults to GBFM):")
        self.x1 = 10
        self.y1 = 45
        self.labelZ1.setGeometry(self.x1, self.y1, 200, 25)
        self.labelZ1.show()

        self.textbox_zone1 = QLineEdit(self)
        self.textbox_zone1.move(self.x1, self.y1 + 25)
        self.textbox_zone1.resize(235, 30)

        self.yspace = 60
        self.y2 = self.y1 + 80
        self.first_zones_path = Utilities.add_file_selection(
            self,
            self.y2,
            "Select the first zone system shapefile:",
            filetype="Shapefile (*.shp *.SHP)",
        )

        # Zone 2
        self.labelZ2 = QtWidgets.QLabel(self)
        self.labelZ2.setText("Zone 2 name (defaults to NoHAM):")
        self.x2 = 260
        self.labelZ2.setGeometry(self.x2, self.y1, 200, 25)
        self.labelZ2.show()

        self.textbox_zone2 = QLineEdit(self)
        self.textbox_zone2.move(self.x2 - 5, self.y1 + 25)
        self.textbox_zone2.resize(235, 30)

        self.second_zones_path = Utilities.add_file_selection(
            self,
            self.y2 + self.yspace,
            "Select the second zone system shapefile:",
            filetype="Shapefile (*.shp *.SHP)",
        )

        # Add file paths to LSOA data

        (
            self.lsoa_shapefile_path,
            self.lsoa_shapefile_browse,
        ) = Utilities.add_file_selection(
            self,
            self.y2 + self.yspace * 5,
            "Select the LSOA shapefile:",
            filetype="Shapefile (*.shp *.SHP)",
            return_browse=True,
        )
        self.lsoa_data_path, self.lsoa_data_browse = Utilities.add_file_selection(
            self,
            self.y2 + self.yspace * 4,
            "Select the LSOA data csv:",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )

        # Add file path to point zone list
        self.point_zones, self.point_zones_browse = Utilities.add_file_selection(
            self,
            self.y2 + self.yspace * 3,
            "(Optional) Select second zone system (e.g. NoHAM) point zone csv:",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )

        # Disable these boxes until point handling is checked
        self.lsoa_data_path.setDisabled(True)
        self.lsoa_data_browse.setDisabled(True)
        self.lsoa_shapefile_path.setDisabled(True)
        self.lsoa_shapefile_browse.setDisabled(True)
        self.point_zones.setDisabled(True)
        self.point_zones_browse.setDisabled(True)

        # TODO add default file here, will update add_file_selection in utilities

        # Folder path for the outputs
        self.outpath = Utilities.add_file_selection(
            self,
            self.y2 + self.yspace * 2,
            "Select the output directory:",
            directory=True,
        )

        self.x3 = 510
        # Add numerical input boxes for tolerance
        self.uppertolbox = QDoubleSpinBox(
            self,
            suffix="%",
            decimals=1,
            maximum=100,
            minimum=85,
            singleStep=0.5,
            value=99,
        )
        self.uppertolbox.move(self.x3, 375)
        self.uppertolbox.resize(60, 25)
        self.uppertolbox.show()

        # Add instructions for tolerance
        self.labeluptol = QtWidgets.QLabel(self)
        self.labeluptol.setText("Tolerance:")
        self.labeluptol.setGeometry(self.x3, 350, 400, 30)
        self.labeluptol.show()

        # disable tolerance until rounding and point handling are selected
        self.labeluptol.setDisabled(True)
        self.uppertolbox.setDisabled(True)

        # Add numerical input box for point tolerance
        self.pointtolbox = QDoubleSpinBox(
            self,
            suffix="%",
            decimals=0,
            maximum=100,
            minimum=85,
            singleStep=1,
            value=95,
        )
        self.pointtolbox.move(self.x3, 425)
        self.pointtolbox.resize(60, 25)

        # Add instructions for point tolerance
        self.labelpointtol = QtWidgets.QLabel(self)
        self.labelpointtol.setText("Point tolerance:")
        self.labelpointtol.setGeometry(self.x3, 400, 400, 30)
        self.labelpointtol.show()

        # disable this box until point handling is checked
        self.labelpointtol.setDisabled(True)
        self.pointtolbox.setDisabled(True)

        # Create checkboxes for rounding and point handling
        # point handling
        self.point_handling = False
        self.pointhandlingbox = QCheckBox("Point handling", self)
        self.pointhandlingbox.move(self.x3, 95)
        self.pointhandlingbox.resize(200, 40)
        self.pointhandlingbox.stateChanged.connect(self.point_handling_clickbox)

        # rounding
        self.rounding = False
        self.roundingbox = QCheckBox("Rounding", self)
        self.roundingbox.move(self.x3, 65)
        self.roundingbox.resize(200, 40)
        self.roundingbox.stateChanged.connect(self.rounding_clickbox)

        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText("Info")
        Info_button.setGeometry(520, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)

        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText("Back")
        back_button.setGeometry(10, 500, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)

        # Create a push button to run the process
        run_button = QtWidgets.QPushButton(self)
        run_button.setText("Run")
        run_button.setGeometry(140, 500, 450, 30)
        run_button.clicked.connect(self.run_button_clicked)

        self.show()

    def point_handling_clickbox(self, state):
        """Changes UI display and assigns point_handling bool according to
        whether point handling checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.point_handling = True
            self.lsoa_data_path.setDisabled(False)
            self.lsoa_data_browse.setDisabled(False)
            self.lsoa_shapefile_path.setDisabled(False)
            self.lsoa_shapefile_browse.setDisabled(False)
            self.labelpointtol.setDisabled(False)
            self.labeluptol.setDisabled(False)
            self.uppertolbox.setDisabled(False)
            self.point_zones.setDisabled(False)
            self.point_zones_browse.setDisabled(False)
            self.pointtolbox.setDisabled(False)

        else:
            self.point_handling = False
            self.lsoa_data_path.setDisabled(True)
            self.lsoa_data_browse.setDisabled(True)
            self.lsoa_shapefile_path.setDisabled(True)
            self.lsoa_shapefile_browse.setDisabled(True)
            self.labelpointtol.setDisabled(True)
            self.point_zones.setDisabled(True)
            self.point_zones_browse.setDisabled(True)
            self.pointtolbox.setDisabled(True)

            if not self.rounding:
                self.labeluptol.setDisabled(True)
                self.uppertolbox.setDisabled(True)

    def rounding_clickbox(self, state):
        """Changes UI display and assigns rounding bool according to
        whether rounding checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.rounding = True
            self.uppertolbox.setDisabled(False)
            self.labeluptol.setDisabled(False)
        else:
            self.rounding = False
            if not self.point_handling:
                self.uppertolbox.setDisabled(True)
                self.labeluptol.setDisabled(True)

    def run_button_clicked(self):
        """Initialises process once run button is clicked."""
        # get file extensions for all file path inputs
        name, zone_1_shp = os.path.splitext(self.first_zones_path.text())
        name, zone_2_shp = os.path.splitext(self.second_zones_path.text())

        name, lsoa_data_csv = os.path.splitext(self.lsoa_data_path.text())
        name, lsoa_shp = os.path.splitext(self.lsoa_shapefile_path.text())
        name, point_csv = os.path.splitext(self.point_zones.text())

        # Error messages when not enough inputs or wrong file types
        if self.first_zones_path.text() == "" or self.second_zones_path.text() == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Zone Correspondence Tool")
            alert.setText("Error: you must specify both zone system shapefiles first")
            alert.show()

        elif (zone_1_shp != ".shp") | (zone_2_shp != ".shp"):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Zone Correspondence Tool")
            alert.setText(
                "Error: the zone system shapefiles specified are not .shp files"
            )
            alert.show()

        elif os.path.isdir(self.outpath.text()) == False:
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Zone Correspondence Tool")
            alert.setText("Error: you must specify an output directory")
            alert.show()

        elif self.point_handling & (
            (self.lsoa_data_path.text() == "") | (self.lsoa_shapefile_path.text() == "")
        ):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Zone Correspondence Tool")
            alert.setText(
                "Error: you must specify LSOA shapefile and data \
            when point handling is on"
            )
            alert.show()

        elif self.point_handling & ((lsoa_data_csv != ".csv") | (lsoa_shp != ".shp")):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Zone Correspondence Tool")
            alert.setText(
                "Error: the LSOA zones file specified must be in .shp format,\
                 and the LSOA data must be in .csv format."
            )
            alert.show()

        elif (
            self.point_handling
            & (self.point_zones.text() != "")
            & (point_csv != ".csv")
        ):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Zone Correspondence Tool")
            alert.setText("Error: the point zone file specified is not a csv.")
            alert.show()

        else:
            # Start a progress window
            self.progress = progress_window("Zone Correspondence Tool")
            self.hide()

            # Call the main process
            self.worker = background_thread(self)
            self.worker.start()

    def back_button_clicked(self):
        """Returns to tier converter main menu"""
        self.tier_converter.show()
        self.hide()

    def closeEvent(self, event):
        """Closes the zone correspondence window."""
        Utilities.closeEvent(self, event)

    @pyqtSlot()
    def on_click_Info(self):
        """Displays info window"""
        self.progress = info_window("Zone Correspondence Tool")
        self.progress_label = self.progress.label
        self.progress_labelA = self.progress.labelA
        dedented_text = textwrap.dedent(ProduceGBFMCorrespondence_Text).strip()
        line = textwrap.fill(dedented_text, width=140)
        self.progress_label.setText(line)
        self.progress_label.move(10, 40)
        self.progress_labelA.setText("Produce GBFM Zone Correspondence")
        self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.progress.show()

        def closeEvent(self, event):
            """Closes info window"""
            Utilities.closeEvent(self, event)


class background_thread(QThread):
    """Thread which calls functions from
    zone_correspondence.main_zone_correspondence.

    Parameters
    ----------
    QThread
    """

    def __init__(self, ProduceGBFMCorrespondence):
        """Initialise class

        Parameters
        ----------
        ProduceGBFMCorrespondence : Class
            GUI class for zone correspondence
        """
        QThread.__init__(self)

        self.progress_label = ProduceGBFMCorrespondence.progress.label
        self.first_zones_path = ProduceGBFMCorrespondence.first_zones_path.text()
        self.second_zones_path = ProduceGBFMCorrespondence.second_zones_path.text()
        self.textbox_zone1 = ProduceGBFMCorrespondence.textbox_zone1.text()
        self.textbox_zone2 = ProduceGBFMCorrespondence.textbox_zone2.text()
        self.lsoa_shapefile_path = ProduceGBFMCorrespondence.lsoa_shapefile_path.text()
        self.lsoa_data_path = ProduceGBFMCorrespondence.lsoa_data_path.text()
        self.outpath = ProduceGBFMCorrespondence.outpath.text()
        self.point_zones = ProduceGBFMCorrespondence.point_zones.text()
        self.tolerance = (ProduceGBFMCorrespondence.uppertolbox.value()) / 100.0
        self.point_tolerance = (ProduceGBFMCorrespondence.pointtolbox.value()) / 100.0
        self.point_handling = ProduceGBFMCorrespondence.point_handling
        self.rounding = ProduceGBFMCorrespondence.rounding

    def run(self):
        """Runs zone correspondence"""
        if self.textbox_zone1 == "" or self.textbox_zone2 == "":
            self.zone1_name = "gbfm"
            self.zone2_name = "noham"
        else:
            self.zone1_name = str(self.textbox_zone1)
            self.zone2_name = str(self.textbox_zone2)

        self.progress_label.setText("Applying the zone correspondence process...")

        log_file, zone_1_missing, zone_2_missing = zcorr.main_zone_correspondence(
            self.first_zones_path,
            self.second_zones_path,
            zone_1_name=self.zone1_name,
            zone_2_name=self.zone2_name,
            tolerance=self.tolerance,
            point_zones_path=self.point_zones,
            out_path=self.outpath,
            point_handling=self.point_handling,
            lsoa_shapefile_path=self.lsoa_shapefile_path,
            lsoa_data_path=self.lsoa_data_path,
            rounding=self.rounding,
        )

        self.progress_label.setText(
            f"Zone correspondence complete. There are {zone_1_missing} unmatched {self.zone1_name} zones and {zone_2_missing} unmatched {self.zone2_name} zones.\nCheck {log_file}. You may now exit the tool."
        )
