"""

Created on: Tue Feb 16 2021
Last update: Thurs Feb 25 2021

Original author: CaraLynch
Last updated by: CaraLynch

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
from info_window import InfoWindow
from matrix_utilities import ODMatrix
from rezone import Rezone

# Other packages
import textwrap
import os
import pandas as pd


class MatrixUtilities(QtWidgets.QWidget):
    """Matrix utilities user interface.

    Parameters
    ----------
    QtWidgets : QWidget
        Base class for user interface objects.
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
        self.setGeometry(500, 200, 500, 700)
        self.setWindowTitle("Matrix Utilities")
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        y = 10
        input_label = QtWidgets.QLabel(self)
        input_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        input_label.setText("Input Matrix")
        input_label.setGeometry(10, y, 700, 30)

        # Input matrix
        self.od_matrix_path = Utilities.add_file_selection(
            self,
            y + 45,
            "Select the O-D Matrix (.csv, .txt)",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
        )

        spacing = 75
        checkbox_x = 10
        CHECK_STYLE = "font-size: 13px; font-weight: bold; font-family: Arial"

        # Summary
        y += spacing + 5
        self.summary = True
        self.summary_box = QCheckBox("Summary", self)
        self.summary_box.move(checkbox_x, y)
        self.summary_box.setStyleSheet(CHECK_STYLE)
        self.summary_box.stateChanged.connect(self.summary_clickbox)
        self.summary_box.setChecked(self.summary)

        # Rezoning
        y += spacing - 50
        self.rezoning = False
        self.rezoning_box = QCheckBox("Rezoning", self)
        self.rezoning_box.move(checkbox_x, y)
        self.rezoning_box.setStyleSheet(CHECK_STYLE)
        self.rezoning_box.stateChanged.connect(self.rezoning_clickbox)

        # zone correspondence file
        (
            self.zone_correspondence_path,
            self.zone_correspondence_browse_button,
        ) = Utilities.add_file_selection(
            self,
            y + 45,
            "Select the zone correspondence file (.csv, .txt)",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )
        # set disabled until rezoning box is checked
        self.zone_correspondence_path.setDisabled(True)
        self.zone_correspondence_browse_button.setDisabled(True)

        # Matrix addition
        y += spacing
        self.addition = False
        self.addition_box = QCheckBox("Matrix Addition", self)
        self.addition_box.move(checkbox_x, y)
        self.addition_box.setStyleSheet(CHECK_STYLE)
        self.addition_box.stateChanged.connect(self.addition_clickbox)

        # Second matrix or scalar value
        (
            self.matrix_to_add_path,
            self.addition_browse_button,
        ) = Utilities.add_file_selection(
            self,
            y + 45,
            "Select the second matrix (.csv, .txt)",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )
        self.matrix_to_add_path.setDisabled(True)
        self.addition_browse_button.setDisabled(True)

        # Matrix factoring
        y += spacing
        self.factoring = False
        self.factoring_box = QCheckBox("Matrix Factoring", self)
        self.factoring_box.move(checkbox_x, y)
        self.factoring_box.setStyleSheet(CHECK_STYLE)
        self.factoring_box.stateChanged.connect(self.factoring_clickbox)

        # Second matrix or scalar value
        (
            self.matrix_factor_path,
            self.factor_browse_button,
        ) = Utilities.add_file_selection(
            self,
            y + 45,
            "Select the second matrix or input a scalar value (.csv, .txt or positive number)",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )
        self.matrix_factor_path.setDisabled(True)
        self.factor_browse_button.setDisabled(True)

        # Fill missing zones
        y += spacing
        self.fill_missing = False
        self.fill_missing_box = QCheckBox("Fill Missing Zones", self)
        self.fill_missing_box.move(checkbox_x, y)
        self.fill_missing_box.setStyleSheet(CHECK_STYLE)
        self.fill_missing_box.stateChanged.connect(self.fill_missing_clickbox)

        # Missing zones file or values
        (
            self.missing_zones_path,
            self.missing_zones_browse_button,
        ) = Utilities.add_file_selection(
            self,
            y + 45,
            "Select missing zones csv or enter zone numbers separated by commas (.csv, .txt or list of zones)",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )
        self.missing_zones_path.setDisabled(True)
        self.missing_zones_browse_button.setDisabled(True)

        # Remove external-external trips
        y += spacing
        self.remove_ee = False
        self.remove_ee_box = QCheckBox("Remove External-External Trips", self)
        self.remove_ee_box.move(checkbox_x, y)
        self.remove_ee_box.setStyleSheet(CHECK_STYLE)
        self.remove_ee_box.stateChanged.connect(self.remove_ee_clickbox)

        # External zones file or values
        (
            self.external_zones_path,
            self.external_zones_browse_button,
        ) = Utilities.add_file_selection(
            self,
            y + 45,
            "Select external zones csv or enter zone numbers separated by commas (.csv, .txt or list of zones)",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            return_browse=True,
        )
        self.external_zones_path.setDisabled(True)
        self.external_zones_browse_button.setDisabled(True)

        # Convert to UFM
        y += spacing
        self.ufm_convert = False
        self.ufm_convert_box = QCheckBox("Convert to UFM", self)
        self.ufm_convert_box.move(checkbox_x, y)
        self.ufm_convert_box.setStyleSheet(CHECK_STYLE)
        self.ufm_convert_box.stateChanged.connect(self.ufm_convert_clickbox)

        # Box for path to SATURN exes folder
        (
            self.saturn_exes_path,
            self.saturn_exes_browse_button,
        ) = Utilities.add_file_selection(
            self,
            y + 45,
            "Select path to SATURN exes folder",
            directory=True,
            return_browse=True,
        )
        self.saturn_exes_path.setDisabled(True)
        self.saturn_exes_browse_button.setDisabled(True)

        # output directory
        y += spacing
        output_label = QtWidgets.QLabel(self)
        output_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        output_label.setText("Output Folder")
        output_label.setGeometry(10, y, 125, 30)

        # Folder path for the outputs
        self.outpath = Utilities.add_file_selection(
            self, y + 45, "Select the output directory", directory=True
        )

        y += spacing + 20

        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText("Info")
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)

        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText("Back")
        back_button.setGeometry(10, y, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)

        # Create a push button to run the process
        run_button = QtWidgets.QPushButton(self)
        run_button.setText("Run")
        run_button.setGeometry(120, y, 370, 30)
        run_button.clicked.connect(self.run_button_clicked)

        self.show()

    def summary_clickbox(self, state):
        """Changes UI display and assigns summary bool according to
        whether summary checkbox is checked or not.

        Parameters
        ----------
        state : Qt.Checked
            Describes whether checkbox is checked or not.
        """
        if state == Qt.Checked:
            self.summary = True

        else:
            self.summary = False

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
            self.zone_correspondence_path.setDisabled(False)
            self.zone_correspondence_browse_button.setDisabled(False)

        else:
            self.rezoning = False
            self.zone_correspondence_path.setDisabled(True)
            self.zone_correspondence_browse_button.setDisabled(True)

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
            self.matrix_to_add_path.setDisabled(False)
            self.addition_browse_button.setDisabled(False)

        else:
            self.addition = False
            self.matrix_to_add_path.setDisabled(True)
            self.addition_browse_button.setDisabled(True)

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
            self.matrix_factor_path.setDisabled(False)
            self.factor_browse_button.setDisabled(False)

        else:
            self.factoring = False
            self.matrix_factor_path.setDisabled(True)
            self.factor_browse_button.setDisabled(True)

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
            self.missing_zones_path.setDisabled(False)
            self.missing_zones_browse_button.setDisabled(False)

        else:
            self.fill_missing = False
            self.missing_zones_path.setDisabled(True)
            self.missing_zones_browse_button.setDisabled(True)

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
            self.external_zones_path.setDisabled(False)
            self.external_zones_browse_button.setDisabled(False)

        else:
            self.remove_ee = False
            self.external_zones_path.setDisabled(True)
            self.external_zones_browse_button.setDisabled(True)

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
            self.saturn_exes_path.setDisabled(False)
            self.saturn_exes_browse_button.setDisabled(False)

        else:
            self.ufm_convert = False
            self.saturn_exes_path.setDisabled(True)
            self.saturn_exes_browse_button.setDisabled(True)

    def run_button_clicked(self):
        """Initialises process once run button is clicked."""

        # create dataframe to track processes to perform which require inputs
        processes = {
            "name": [
                "input",
                "rezoning",
                "addition",
                "factor",
                "fill missing zones",
                "remove EE trips",
                "convert to UFM",
            ],
            "execute": [
                True,
                self.rezoning,
                self.addition,
                self.factoring,
                self.fill_missing,
                self.remove_ee,
                self.ufm_convert,
            ],
            "input": [
                self.od_matrix_path.text().strip(),
                self.zone_correspondence_path.text().strip(),
                self.matrix_to_add_path.text().strip(),
                self.matrix_factor_path.text().strip(),
                self.missing_zones_path.text().strip(),
                self.external_zones_path.text().strip(),
                self.saturn_exes_path.text().strip(),
            ],
        }

        self.processes = pd.DataFrame(processes)

        # remove processes not required
        self.processes = self.processes.drop(
            self.processes.loc[self.processes.execute == False].index
        )
        self.processes = self.processes.drop(columns="execute")

        # get factor to check if negative
        factor = 0
        if "factor" in self.processes.name.values:
            factor_str = self.processes.loc[
                self.processes.name == "factor", "input"
            ].values[0]
            try:
                factor = float(factor_str)
            except:
                pass

        # Error messages
        # no processes to run
        if (len(self.processes) < 2) and (self.summary == False):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText("Error: you must specifiy a process to run")
            alert.show()
        # no input matrix
        elif self.od_matrix_path.text() == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText("Error: you must specifiy an input matrix")
            alert.show()
        # processes to run don't have required inputs
        elif len(self.processes[self.processes.input == ""]) > 0:
            inputs_required = self.processes[self.processes.input == ""].name.values
            for i in range(0, len(inputs_required)):
                if i == 0:
                    input_str = f"{inputs_required[i]}"
                elif i == len(inputs_required) - 1:
                    input_str += f" and {inputs_required[i]}"
                else:
                    input_str += f", {inputs_required[i]}"
            if len(inputs_required) == 1:
                process_str = "process"
            else:
                process_str = "processes"
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText(
                f"Error: you must specifiy the inputs for the {input_str} {process_str}."
            )
            alert.show()
        # no output folder
        elif self.outpath.text() == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText("Error: you must specifiy an output folder")
            alert.show()
        elif factor < 0:
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText("Error: the factor cannot be negative")
            alert.show()
        # run processes if no errors
        else:

            # if rezoning and another process is checked, alert that other
            # than the input matrix all other inputs need to be in the new
            # zoning system
            check_rezoned = self.rezoning & (
                self.ufm_convert & (len(self.processes.name) > 3)
                | (not self.ufm_convert & (len(self.processes.name) > 2))
            )
            if check_rezoned:
                check_rezoned_str = (
                    "When rezoning is on, only the input matrix is rezoned."
                    " All other matrices and zones must be in the new zoning"
                    " system.\nDo you wish to continue?"
                )
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Warning",
                    check_rezoned_str,
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    # Start a progress window
                    self.progress = progress_window(
                        "Matrix Utilities", self.tier_converter
                    )
                    self.hide()

                    # Call the main process
                    self.worker = background_thread(self)
                    self.worker.start()
            else:
                # Start a progress window
                self.progress = progress_window("Matrix Utilities", self.tier_converter)
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
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()

    @pyqtSlot()
    def on_click_Info(self):
        self.selections_window = InfoWindow(self, 'README.md')
        self.selections_window.show()


class background_thread(QThread):
    """Thread which runs selected matrix processes.

    Parameters
    ----------
    QThread
    """

    def __init__(self, MatrixUtilities):
        """Initialise class

        Parameters
        ----------
        MatrixUtilities : Class
            GUI class for matrix utilities
        """
        QThread.__init__(self)
        self.progress_window = MatrixUtilities.progress
        self.progress_window.resize(770, 240)
        self.progress_label = self.progress_window.label
        self.progress_label.resize(770, 235)
        self.od_matrix_path = MatrixUtilities.od_matrix_path.text()
        self.outpath = MatrixUtilities.outpath.text()
        self.summary = MatrixUtilities.summary
        self.processes = MatrixUtilities.processes

    def run(self):
        """Runs matrix processes"""
        try:
            # keep track of changes to matrix and outputs to log
            matrix_changes = 0
            self.processes["completed"] = "no"
            self.processes["note"] = ""

            # read in the O-D matrix and create an ODMatrix instance
            progress_text = "Reading in input matrix"
            self.progress_label.setText(progress_text)
            progress_lines = 1
            self.progress_label.setText(progress_text)
            try:
                od_matrix = ODMatrix.read_OD_file(self.od_matrix_path)
            except ValueError as e:
                msg = f"{e}"
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, msg, progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                self.processes.loc[self.processes.name == "input", "note"] = msg
                raise ValueError(msg)

            od_matrix_name = od_matrix.name
            self.processes.loc[self.processes.name == "input", "completed"] = "yes"

            if self.summary:
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, "\nSummarising input matrix", progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                print("####\nSummarising input")
                summary_dict = {"Input": od_matrix.summary()}

            if "rezoning" in self.processes.name.values:
                print("####\nRezoning")
                progress_text, progress_lines = self.update_progress_string(
                    progress_text,
                    f"\nRezoning OD matrix and saving to {self.outpath}/{od_matrix.name}_rezoned.csv",
                    progress_lines + 1,
                )
                self.progress_label.setText(progress_text)
                try:
                    zone_correspondence_path = self.processes.loc[
                        self.processes.name == "rezoning", "input"
                    ].values[0]
                    od_matrix = od_matrix.rezone(zone_correspondence_path)
                    if self.summary:
                        summary_dict["Rezoned"] = od_matrix.summary()
                    if (
                        ("convert to UFM" in self.processes.name.values)
                        & (len(self.processes.name) > 3)
                    ) | (
                        ("convert to UFM" not in self.processes.name.values)
                        & (len(self.processes.name) > 2)
                    ):
                        print("Saving rezoned matrix")
                        od_matrix.export_to_csv(
                            f"{self.outpath}/{od_matrix.name}_rezoned.csv"
                        )
                    matrix_changes = matrix_changes + 1
                    self.processes.loc[
                        self.processes.name == "rezoning", "completed"
                    ] = "yes"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\nRezoning complete.", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    print("Rezone complete")
                except FileNotFoundError as e:
                    # any errors
                    msg = "Rezoning unsuccessful, zone correspondence lookup not found"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "rezoning", "note"
                    ] = "zone correspondence lookup not found"
                    raise FileNotFoundError(msg) from e
                except Exception as e:
                    msg = f"Rezoning unsuccessful, {e.__class__.__name__} occurred - {e!s}"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "rezoning", "note"
                    ] = f"{e!s}"
                    raise Exception(msg) from e

            if "addition" in self.processes.name.values:
                print("####\nAddition")
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, "\nPerforming matrix addition", progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                try:
                    matrix_2_path = self.processes.loc[
                        self.processes.name == "addition", "input"
                    ].values[0]
                    matrix_2 = ODMatrix.read_OD_file(matrix_2_path)
                    od_matrix = od_matrix + matrix_2
                    if self.summary:
                        summary_dict["Addition"] = od_matrix.summary()
                    matrix_changes += 1
                    self.processes.loc[
                        self.processes.name == "addition", "completed"
                    ] = "yes"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, "\nAddition complete.", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    print("Addition complete")
                except FileNotFoundError as e:
                    msg = (
                        "Error: could not find second matrix csv. Addition unsuccessful"
                    )
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "addition", "note"
                    ] = "second matrix csv not found"
                    raise FileNotFoundError(msg) from e
                except Exception as e:
                    msg = f"Error: addition unsuccessful, {e.__class__.__name__} occurred - {e}"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "addition", "note"
                    ] = f"{e}"
                    raise Exception(msg) from e

            if "factor" in self.processes.name.values:
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, "\nFactoring OD matrix", progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                print("####\nFactoring O-D matrix")
                try:
                    factor_str = self.processes.loc[
                        self.processes.name == "factor", "input"
                    ].values[0]
                    print("Checking whether factor is scalar or matrix")
                    try:
                        factor = float(factor_str)
                    except:
                        print("Reading in matrix factor")
                        factor = ODMatrix.read_OD_file(factor_str)
                    print("Factoring matrix")
                    od_matrix = od_matrix * factor
                    if self.summary:
                        summary_dict["Factored"] = od_matrix.summary()
                    matrix_changes += 1
                    self.processes.loc[
                        self.processes.name == "factor", "completed"
                    ] = "yes"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, "\nFactoring complete.", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                except Exception as e:
                    msg = f"Error: factoring unsuccessful, {e.__class__.__name__} occurred - {e}"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[self.processes.name == "factor", "note"] = f"{e}"
                    raise Exception(msg) from e

            if "fill missing zones" in self.processes.name.values:
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, "\nFilling missing zones", progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                print("####\nFilling missing zones")
                try:
                    missing_zones_str = self.processes.loc[
                        self.processes.name == "fill missing zones", "input"
                    ].values[0]

                    # see if have been given file or list of zones
                    if os.path.isfile(missing_zones_str):
                        print("Missing zones are file")
                        whitespace, header_row = ODMatrix.check_file_header(
                            missing_zones_str
                        )
                        print("Reading in file")
                        missing_zones = pd.read_csv(
                            missing_zones_str,
                            delim_whitespace=whitespace,
                            header=header_row,
                            usecols=[0],
                            names=["zone_id"],
                        )
                        missing_zones = list(missing_zones.zone_id)
                    else:
                        print("Missing zones are list")
                        missing_zones = [
                            x.strip() for x in missing_zones_str.split(",")
                        ]
                        # check if zones names are integers or strings
                        try:
                            missing_zones = [int(x) for x in missing_zones]
                        except ValueError:
                            print("Zone names are strings")
                    print("Filling missing zones")
                    od_matrix = od_matrix.fill_missing_zones(missing_zones)
                    if self.summary:
                        summary_dict["Fill missing zones"] = od_matrix.summary()
                    matrix_changes += 1
                    self.processes.loc[
                        self.processes.name == "fill missing zones", "completed"
                    ] = "yes"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, "\nMissing zones added.", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    print("Missing zones added")
                except ValueError as e:
                    msg = "Error: Missing zones are neither a file nor a comma-separated list."
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "fill missing zones", "note"
                    ] = "missing zones are neither a file nor a comma-separated list"
                    raise ValueError(msg) from e
                except Exception as e:
                    msg = f"Error: filling missing zones unsuccessful, {e.__class__.__name__} occured - {e}"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "fill missing zones", "note"
                    ] = f"{e}"
                    raise Exception(msg) from e

            if "remove EE trips" in self.processes.name.values:
                try:
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, "\nRemoving EE trips", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    print("####\nRemoving External-External trips")
                    external_zones_str = self.processes.loc[
                        self.processes.name == "remove EE trips", "input"
                    ].values[0]
                    # see if have been given file or list of zones
                    if os.path.isfile(external_zones_str):
                        print(f"External zones given as file: {external_zones_str}")
                        whitespace, header_row = ODMatrix.check_file_header(
                            external_zones_str
                        )
                        external_zones = pd.read_csv(
                            external_zones_str,
                            delim_whitespace=whitespace,
                            header=header_row,
                            usecols=[0],
                            names=["zone_id"],
                        )
                        external_zones = list(external_zones.zone_id)
                    else:
                        external_zones = [
                            x.strip() for x in external_zones_str.split(",")
                        ]
                        # check if zones names are integers or strings
                        try:
                            external_zones = [int(x) for x in external_zones]
                        except ValueError:
                            print("Zone names are strings")
                        print(f"External zones given as list: {external_zones}")
                    od_matrix = od_matrix.remove_external_trips(external_zones)
                    if self.summary:
                        summary_dict["Remove EE trips"] = od_matrix.summary()
                    matrix_changes += 1
                    self.processes.loc[
                        self.processes.name == "remove EE trips", "completed"
                    ] = "yes"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, "\nEE trips removed.", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    print("E-E trips removal complete.")
                except ValueError as e:
                    msg = "Error: External zones are neither a file nor a comma-separated list."
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "remove EE trips", "note"
                    ] = "external zones are neither a file nor a comma-separated list"
                    raise ValueError(msg) from e
                except Exception as e:
                    msg = f"Error: Remove external-external trips unsuccessful, {e.__class__.__name__} occured - {e}"
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, f"\n{msg}", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.loc[
                        self.processes.name == "remove EE trips", "note"
                    ] = f"{e}"
                    raise Exception(msg) from e

            # if there have been changes to the o-d matrix, save the output
            print(f"Matrix changes: {matrix_changes}")
            if matrix_changes > 0:
                # reset to original name
                od_matrix.name = od_matrix_name
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, "\nSaving output matrix to csv", progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                print("Saving output to csv")
                od_matrix.export_to_csv(
                    f"{self.outpath}/{od_matrix.name}_processed.csv"
                )

            if "convert to UFM" in self.processes.name.values:
                progress_text, progress_lines = self.update_progress_string(
                    progress_text, "\nConverting to UFM", progress_lines + 1
                )
                self.progress_label.setText(progress_text)
                saturn_exes_path = self.processes.loc[
                    self.processes.name == "convert to UFM", "input"
                ].values[0]
                # check this is the path to a folder
                if os.path.isdir(saturn_exes_path):
                    try:
                        ufm_path = od_matrix.export_to_ufm(saturn_exes_path, self.outpath)
                        self.processes.loc[
                            self.processes.name == "convert to UFM", "completed"
                        ] = "yes"
                        progress_text, progress_lines = self.update_progress_string(
                            progress_text, f"\nUFM saved to {ufm_path}", progress_lines + 1
                        )
                        self.progress_label.setText(progress_text)
                    except Exception as e:
                        msg = f"Error: Convert to UFM unsuccessful {e.__class__.__name__} occured - {e}"
                        progress_text, progress_lines = self.update_progress_string(
                            progress_text, f"\n{msg}", progress_lines + 1
                        )
                        self.progress_label.setText(progress_text)
                        self.processes.loc[
                            self.processes.name == "convert to UFM", "note"
                        ] = f"{e}"
                else:
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text,
                        "Error: SATURN EXES path given is not a folder. Conversion process couldn't complete.",
                        progress_lines + 1,
                    )
                    self.processes.loc[
                        self.processes.name == "convert to UFM", "note"
                    ] = "SATURN EXES path is not a folder"
                    self.progress_label.setText(progress_text)
        except Exception as e:
            print(f"{e.__class__.__name__}: {e}")
        finally:
            # create log file for matrix summaries and processes information
            log_file = f"{self.outpath}/matrix_info.xlsx"
            with pd.ExcelWriter(log_file, engine="openpyxl") as writer:
                if len(self.processes.name) > 0:
                    progress_text, progress_lines = self.update_progress_string(
                        progress_text, "\nSaving process log", progress_lines + 1
                    )
                    self.progress_label.setText(progress_text)
                    self.processes.to_excel(writer, sheet_name="inputs", index=False)
                    if self.summary:
                        try:
                            summary_df = pd.DataFrame.from_dict(
                                summary_dict, orient="index"
                            )
                            summary_df.to_excel(
                                writer, sheet_name="summary", index=True
                            )
                        except UnboundLocalError as e:
                            msg = f"Error: {e}"
                            progress_text, progress_lines = self.update_progress_string(
                                progress_text, msg, progress_lines + 1
                            )

            msg = (
                f"\nMatrix operations complete, all outputs saved to "
                f"{self.outpath}.\nYou may exit the program, check"
                f" matrix_info.xlsx for more information."
            )
            print(msg)
            progress_text, progress_lines = self.update_progress_string(
                progress_text, msg, progress_lines + 2
            )
            self.progress_label.setText(progress_text)

    @staticmethod
    def update_progress_string(progress_text, new_line, line_counter, line_limit=20):
        """
        Updates the progress string to display in the progress window with the
        allowed number of lines.

        Parameters
        ----------
        progress_text : str
            Current progress text
        new_line : str
            New line to add to progress text
        line_counter : int
            Number of lines in progress texy
        line_limit : int, optional
            Number of lines displayed in progress window, by default 3

        Returns
        -------
        progress_text: str
            Updated progress_text with new line added and correct number of
            lines
        line_counter: int
            Number of lines in updated progress_text
        """
        if line_counter > line_limit:
            progress_text = new_line
            line_counter = 1
        else:
            progress_text += new_line

        return progress_text, line_counter
