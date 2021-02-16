"""

Created on: Tue Feb 16 2021

Original author: Cara

File purpose:
Gui to enable user to access utility functions relevant to O-D matrices,
including rezoning, addition, factoring, filling in missing zones, removing
external-external trips and converting to UFM.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, QThread, Qt
from PyQt5.QtWidgets import QLineEdit, QCheckBox, QDoubleSpinBox


# User-defined imports
from utilities import Utilities, info_window, progress_window
from text_info import Matrix_Utilities_Text
import zone_correspondence as zcorr

# Other packages
import textwrap
import os


class MatrixUtilities(QtWidgets.QWidget):
    """Matrix utilities user interface.

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
        self.setGeometry(500, 320, 500, 670)
        self.setWindowTitle("Matrix Utilities")
        self.setWindowIcon(QtGui.QIcon("icon.jpg"))

        y = 10
        input_label = QtWidgets.QLabel(self)
        input_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        input_label.setText("Input Matrix")
        input_label.setGeometry(10, y, 700, 30)

        # Input matrix
        self.od_matrix_path = Utilities.add_file_selection(
            self, y+45, "Select the O-D Matrix csv:",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )

        spacing = 75

        # Rezoning
        y += spacing + 5
        rezoning_label = QtWidgets.QLabel(self)
        rezoning_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        rezoning_label.setText("Rezoning")
        rezoning_label.setGeometry(10, y, 100, 30)

        # Checkbox
        self.rezoning = False
        self.rezoning_box = QCheckBox(self)
        self.rezoning_box.move(140, y)
        self.rezoning_box.resize(30, 30)
        self.rezoning_box.stateChanged.connect(self.rezoning_clickbox)

        # zone correspondence file
        self.zone_correspondence_path = Utilities.add_file_selection(
            self, y+45, "Select the zone correspondence file:",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )

        # Matrix addition
        y += spacing
        addition_label = QtWidgets.QLabel(self)
        addition_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        addition_label.setText("Matrix Addition")
        addition_label.setGeometry(10, y, 100, 30)

        # Checkbox
        self.addition = False
        self.addition_box = QCheckBox(self)
        self.addition_box.move(140, y)
        self.addition_box.resize(30, 30)
        self.addition_box.stateChanged.connect(self.addition_clickbox)

        # Second matrix or scalar value
        self.matrix_to_add_path = Utilities.add_file_selection(
            self,y+45, "Select the second matrix or input a scalar value:",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )

        # Matrix factoring
        y += spacing
        factor_label = QtWidgets.QLabel(self)
        factor_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        factor_label.setText("Matrix Factoring")
        factor_label.setGeometry(10, y, 120, 30)

        # Checkbox
        self.factoring = False
        self.factoring_box = QCheckBox(self)
        self.factoring_box.move(140, y)
        self.factoring_box.resize(30, 30)
        self.factoring_box.stateChanged.connect(self.factoring_clickbox)

        # Second matrix or scalar value
        self.matrix_factor_path = Utilities.add_file_selection(
            self, y+45, "Select the second matrix or input a scalar value:",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )

        # Fill missing zones
        y += spacing
        fill_missing_label = QtWidgets.QLabel(self)
        fill_missing_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        fill_missing_label.setText("Fill Missing Zones")
        fill_missing_label.setGeometry(10, y, 125, 30)

        # Checkbox
        self.fill_missing = False
        self.fill_missing_box = QCheckBox(self)
        self.fill_missing_box.move(140, y)
        self.fill_missing_box.resize(30, 30)
        self.fill_missing_box.stateChanged.connect(self.fill_missing_clickbox)

        # Missing zones file or values
        self.missing_zones_path = Utilities.add_file_selection(
            self, y+45, "Select missing zones csv or enter zone numbers",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )
        
        
        # Remove external-external trips
        y += spacing
        remove_ee_label = QtWidgets.QLabel(self)
        remove_ee_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        remove_ee_label.setText("Remove EE trips")
        remove_ee_label.setGeometry(10, y, 125, 30)

        # Checkbox
        self.remove_ee = False
        self.remove_ee_box = QCheckBox(self)
        self.remove_ee_box.move(140, y)
        self.remove_ee_box.resize(30, 30)
        self.remove_ee_box.stateChanged.connect(self.remove_ee_clickbox)

        # External zones file or values
        self.external_zones_path = Utilities.add_file_selection(
            self, y+45, "Select external zones csv or enter zone numbers",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )

        # Convert to UFM
        y += spacing
        ufm_label = QtWidgets.QLabel(self)
        ufm_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        ufm_label.setText("Convert to UFM")
        ufm_label.setGeometry(10, y, 125, 30)

        # Checkbox
        self.ufm_convert = False
        self.ufm_convert_box = QCheckBox(self)
        self.ufm_convert_box.move(140, y)
        self.ufm_convert_box.resize(30, 30)
        self.ufm_convert_box.stateChanged.connect(self.ufm_convert_clickbox)

        # Box for path to SATURN exes folder
        self.saturn_exes_path = Utilities.add_file_selection(
            self, y+45, "Select path to SATURN exes folder",
            directory=True
        )
        
        # output directory
        y += spacing
        output_label = QtWidgets.QLabel(self)
        output_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        output_label.setText("Output Folder")
        output_label.setGeometry(10, y, 125, 30)


        # Folder path for the outputs
        self.outpath = Utilities.add_file_selection(
            self,
            y+45,
            "Select the output directory:",
            directory=True)
        

        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText("Info")
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)

        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText("Back")
        back_button.setGeometry(10, 630, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)

        # Create a push button to run the process
        run_button = QtWidgets.QPushButton(self)
        run_button.setText("Run")
        run_button.setGeometry(120, 630, 370, 30)
        run_button.clicked.connect(self.run_button_clicked)

        self.show()

    def rezoning_clickbox(self, state):
        """Changes UI display and assigns rezoning bool according to
        whether rezoning checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.rezoning = True

        else:
            self.rezoning = False

    def addition_clickbox(self, state):
        """Changes UI display and assigns addition bool according to
        whether matrix addition checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.addition = True

        else:
            self.factoring = False

    def factoring_clickbox(self, state):
        """Changes UI display and assigns factoring bool according to
        whether matrix factoring checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.factoring = True

        else:
            self.factoring = False

    def fill_missing_clickbox(self, state):
        """Changes UI display and assigns fill missing zones bool according to
        whether fill missing zones checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.fill_missing = True

        else:
            self.fill_missing = False
    
    def remove_ee_clickbox(self, state):
        """Changes UI display and assigns remove ee bool according to
        whether fill remove ee trips checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.remove_ee = True

        else:
            self.remove_ee = False
    
    def ufm_convert_clickbox(self, state):
        """Changes UI display and assigns UFM convert bool according to
        whether convert to UFM checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.ufm_convert = True

        else:
            self.ufm_convert = False

    def run_button_clicked(self):
        """Initialises process once run button is clicked."""

        # Error messages when not enough inputs or wrong file types
        if self.first_zones_path.text() == "" or self.second_zones_path.text() == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText("Error: you must specify both zone system shapefiles first")
            alert.show()

        else:
            # Start a progress window
            self.progress = progress_window("Matrix Utilities")
            self.hide()

            # Call the main process
            self.worker = background_thread(self)
            self.worker.start()

    def back_button_clicked(self):
        """Returns to tier converter main menu"""
        self.tier_converter.show()
        self.hide()

    def closeEvent(self, event):
        """Closes the matrix utilities window."""
        Utilities.closeEvent(self, event)

    @pyqtSlot()
    def on_click_Info(self):
        """Displays info window"""
        self.progress = info_window("Matrix Utilities")
        self.progress_label = self.progress.label
        self.progress_labelA = self.progress.labelA
        dedented_text = textwrap.dedent(Matrix_Utilities_Text).strip()
        line = textwrap.fill(dedented_text, width=140)
        self.progress_label.setText(line)
        self.progress_label.move(10, 40)
        self.progress_labelA.setText("Matrix Utilities")
        self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.progress.show()

        def closeEvent(self, event):
            """Closes info window"""
            Utilities.closeEvent(self, event)


class background_thread(QThread):
    """Thread which calls functions from matrix_utilities

    Parameters
    ----------
    QThread
    """

    def __init__(self, ProduceGBFMCorrespondence):
        """Initialise class

        Parameters
        ----------
        ProduceGBFMCorrespondence : Class
            GUI class for matrix utilities
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

        self.progress_label.setText(
            "Applying the zone correspondence process\
        ..."
        )
        self.zone_correspondence = zcorr.main_zone_correspondence(
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
            "Matrix operations complete. You may exit the program."
        )