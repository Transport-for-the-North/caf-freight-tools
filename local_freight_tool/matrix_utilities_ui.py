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
from matrix_utilities import ODMatrix
from rezone import Rezone

# Other packages
import textwrap
import os
import pandas as pd

# TODO add try-excepts and message if things failed

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
        self.setGeometry(500, 320, 500, 700)
        self.setWindowTitle("Matrix Utilities")
        self.setWindowIcon(QtGui.QIcon("icon.jpg"))

        y = 10
        input_label = QtWidgets.QLabel(self)
        input_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        input_label.setText("Input Matrix")
        input_label.setGeometry(10, y, 700, 30)

        # Input matrix
        self.od_matrix_path = Utilities.add_file_selection(
            self, y+45, "Select the O-D Matrix csv",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )

        spacing = 75
        checkbox_x = 10
        label_x = 30

        # Summary
        y += spacing + 5
        summary_label = QtWidgets.QLabel(self)
        summary_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        summary_label.setText("Summary")
        summary_label.setGeometry(label_x, y, 100, 30)

        # Checkbox
        self.summary = False
        self.summary_box = QCheckBox(self)
        self.summary_box.move(checkbox_x, y)
        self.summary_box.resize(30, 30)
        self.summary_box.stateChanged.connect(self.summary_clickbox)


        # Rezoning
        y += spacing - 50
        rezoning_label = QtWidgets.QLabel(self)
        rezoning_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        rezoning_label.setText("Rezoning")
        rezoning_label.setGeometry(label_x, y, 100, 30)

        # Checkbox
        self.rezoning = False
        self.rezoning_box = QCheckBox(self)
        self.rezoning_box.move(checkbox_x, y)
        self.rezoning_box.resize(30, 30)
        self.rezoning_box.stateChanged.connect(self.rezoning_clickbox)

        # zone correspondence file
        self.zone_correspondence_path = Utilities.add_file_selection(
            self, y+45, "Select the zone correspondence file",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )
        # set disabled until rezoning box is checked
        self.zone_correspondence_path.setDisabled(True)

        # Matrix addition
        y += spacing
        addition_label = QtWidgets.QLabel(self)
        addition_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        addition_label.setText("Matrix Addition")
        addition_label.setGeometry(label_x, y, 100, 30)

        # Checkbox
        self.addition = False
        self.addition_box = QCheckBox(self)
        self.addition_box.move(checkbox_x, y)
        self.addition_box.resize(30, 30)
        self.addition_box.stateChanged.connect(self.addition_clickbox)

        # Second matrix or scalar value
        self.matrix_to_add_path = Utilities.add_file_selection(
            self,y+45, "Select the second matrix",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )
        self.matrix_to_add_path.setDisabled(True)

        # Matrix factoring
        y += spacing
        factor_label = QtWidgets.QLabel(self)
        factor_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        factor_label.setText("Matrix Factoring")
        factor_label.setGeometry(label_x, y, 120, 30)

        # Checkbox
        self.factoring = False
        self.factoring_box = QCheckBox(self)
        self.factoring_box.move(checkbox_x, y)
        self.factoring_box.resize(30, 30)
        self.factoring_box.stateChanged.connect(self.factoring_clickbox)

        # Second matrix or scalar value
        self.matrix_factor_path = Utilities.add_file_selection(
            self, y+45, "Select the second matrix or input a scalar value",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )
        self.matrix_factor_path.setDisabled(True)

        # Fill missing zones
        y += spacing
        fill_missing_label = QtWidgets.QLabel(self)
        fill_missing_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        fill_missing_label.setText("Fill Missing Zones")
        fill_missing_label.setGeometry(label_x, y, 125, 30)

        # Checkbox
        self.fill_missing = False
        self.fill_missing_box = QCheckBox(self)
        self.fill_missing_box.move(checkbox_x, y)
        self.fill_missing_box.resize(30, 30)
        self.fill_missing_box.stateChanged.connect(self.fill_missing_clickbox)

        # Missing zones file or values
        self.missing_zones_path = Utilities.add_file_selection(
            self, y+45, "Select missing zones csv or enter zone numbers separated by commas",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )
        self.missing_zones_path.setDisabled(True)
        
        
        # Remove external-external trips
        y += spacing
        remove_ee_label = QtWidgets.QLabel(self)
        remove_ee_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        remove_ee_label.setText("Remove EE trips")
        remove_ee_label.setGeometry(label_x, y, 125, 30)

        # Checkbox
        self.remove_ee = False
        self.remove_ee_box = QCheckBox(self)
        self.remove_ee_box.move(checkbox_x, y)
        self.remove_ee_box.resize(30, 30)
        self.remove_ee_box.stateChanged.connect(self.remove_ee_clickbox)

        # External zones file or values
        self.external_zones_path = Utilities.add_file_selection(
            self, y+45, "Select external zones csv or enter zone numbers separated by commas",
            filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)"
        )
        self.external_zones_path.setDisabled(True)

        # Convert to UFM
        y += spacing
        ufm_label = QtWidgets.QLabel(self)
        ufm_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        ufm_label.setText("Convert to UFM")
        ufm_label.setGeometry(label_x, y, 125, 30)

        # Checkbox
        self.ufm_convert = False
        self.ufm_convert_box = QCheckBox(self)
        self.ufm_convert_box.move(checkbox_x, y)
        self.ufm_convert_box.resize(30, 30)
        self.ufm_convert_box.stateChanged.connect(self.ufm_convert_clickbox)

        # Box for path to SATURN exes folder
        self.saturn_exes_path = Utilities.add_file_selection(
            self, y+45, "Select path to SATURN exes folder",
            directory=True
        )
        self.saturn_exes_path.setDisabled(True)
        
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
            "Select the output directory",
            directory=True)
        
        y+= spacing + 20

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

        else:
            self.rezoning = False
            self.zone_correspondence_path.setDisabled(True)

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

        else:
            self.factoring = False
            self.matrix_to_add_path.setDisabled(True)

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

        else:
            self.factoring = False
            self.matrix_factor_path.setDisabled(True)

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

        else:
            self.fill_missing = False
            self.missing_zones_path.setDisabled(True)
    
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

        else:
            self.remove_ee = False
            self.external_zones_path.setDisabled(True)
    
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

        else:
            self.ufm_convert = False
            self.saturn_exes_path.setDisabled(True)

    def run_button_clicked(self):
        """Initialises process once run button is clicked."""
        
        # create dataframe to track processes to perform which require inputs
        processes = {
            'name': ['rezoning', 'addition', 'factor', 'fill missing zones', 'remove EE trips', 'convert to UFM'],
            'execute': [self.rezoning, self.addition, self.factoring, self.fill_missing, self.remove_ee, self.ufm_convert],
            'input': [self.zone_correspondence_path.text(), self.matrix_to_add_path.text(),
            self.matrix_factor_path.text(), self.missing_zones_path.text(), self.external_zones_path.text(),
            self.saturn_exes_path.text()]
        }

        self.processes = pd.DataFrame(processes)

        # remove processes not required
        self.processes = self.processes.drop(self.processes.loc[self.processes.execute == False].index)
        self.processes = self.processes.drop(columns='execute')

        # Error messages
        # no processes to run
        if (len(self.processes) < 1) and (self.summary == False):
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
                    input_str = f'{inputs_required[i]}'
                elif i == len(inputs_required) - 1:
                    input_str += f' and {inputs_required[i]}'
                else:
                    input_str += f', {inputs_required[i]}'
            if len(inputs_required) == 1:
                process_str = 'process'
            else:
                process_str = 'processes'
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText(f"Error: you must specifiy the inputs for the {input_str} {process_str}.")
            alert.show()
        # no output folder
        elif self.outpath.text() == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Matrix Utilities")
            alert.setText("Error: you must specifiy an output folder")
            alert.show()
        # run processes if no errors
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

    def __init__(self, MatrixUtilities):
        """Initialise class

        Parameters
        ----------
        MatrixUtilities : Class
            GUI class for matrix utilities
        """
        QThread.__init__(self)

        self.progress_label = MatrixUtilities.progress.label
        self.od_matrix_path = MatrixUtilities.od_matrix_path.text()
        self.outpath = MatrixUtilities.outpath.text()
        self.summary = MatrixUtilities.summary
        self.processes = MatrixUtilities.processes
        

    def run(self):
        """Runs matrix processes"""

        # create log file for matrix summaries and processes information
        log_file = f"{self.outpath}/matrix_info.xlsx"
        writer = pd.ExcelWriter(log_file, engine="openpyxl")

        # read in the O-D matrix and create an ODMatrix instance
        self.progress_label.setText("Reading in input matrix")
        od_matrix = ODMatrix.read_OD_file(self.od_matrix_path)

        # keep track of changes to matrix and outputs to log
        matrix_changes = 0
        self.processes['completed'] = 'no'

        if self.summary:
            self.progress_label.setText("Summarising input matrix")
            print("Summarising input")
            input_summary = od_matrix.summary()
            input_summary = pd.DataFrame(data=input_summary.values(), index=input_summary.keys(), columns=['Value'])
            input_summary.to_excel(writer, sheet_name="input_summary")
            writer.save()

        if 'rezoning' in self.processes.name.values:
            self.progress_label.setText(f"Rezoning OD matrix and saving to {self.outpath}/{od_matrix.name}_rezoned.csv")
            try:
                zone_correspondence_path = self.processes.loc[self.processes.name == 'rezoning', 'input'][0]
                od_matrix = od_matrix.rezone(zone_correspondence_path)
                od_matrix.export_to_csv(f"{self.outpath}/{od_matrix.name}_rezoned.csv")
                matrix_changes += 1
                self.processes.loc[self.processes.name == 'rezoning', 'completed'] = 'yes'
            except:
            # any errors
                self.progress_label.setText("Rezoning unsuccessful")
        
        if 'addition' in self.processes.name.values:
            self.progress_label.setText("Performing matrix addition")
            try:
                matrix_2_path = self.processes.loc[self.processes.name == 'addition', 'input'][0]
                matrix_2 = ODMatrix.read_OD_file(self.od_matrix_path)
                od_matrix = od_matrix + matrix_2
                matrix_changes += 1
                self.processes.loc[self.processes.name == 'addition', 'completed'] = 'yes'
            except:
                self.progress_label.setText("Addition unsuccessful")
        
        if 'factor' in self.processes.name.values:
            self.progress_label.setText("Factoring OD matrix")
            try:
                factor_str = self.processes.loc[self.processes.name == 'factor', 'input'][0]
                try:
                    factor = float(factor_str)
                except:
                    factor = ODMatrix.read_OD_file(factor_str)
                od_matrix = od_matrix * factor
                matrix_changes += 1
                self.processes.loc[self.processes.name == 'factor', 'completed'] = 'yes'
            except:
                self.progress_label.setText("Factoring unsuccessful")
        
        if 'fill missing zones' in self.processes.name.values:
            self.progress_label.setText("Filling missing zones")
            try:
                missing_zones_str = self.processes.loc[self.processes.name == 'fill missing zones', 'input'][0]
                
                # see if have been given file or list of zones
                if os.path.isfile(missing_zones_str):
                    whitespace, header_row = ODMatrix.check_file_header(missing_zones_str)
                    missing_zones = pd.read_csv(missing_zones_str, delim_whitespace=whitespace, header=header_row, usecols=[0], names=['zone_id'])
                    missing_zones = list(missing_zones.zone_id)
                else:
                    missing_zones = [int(x) for x in missing_zones_str.split(',')]
                
                od_matrix = od_matrix.fill_missing_zones(missing_zones)
                matrix_changes += 1
                self.processes.loc[self.processes.name == 'fill missing zones', 'completed'] = 'yes'
            except:
                self.progress_label.setText("Fill missing zones unsuccessful")
        
        if 'remove EE trips' in self.processes.name.values:
            try:
                self.progress_label.setText("Removing EE trips")
                external_zones_str = self.processes.loc[self.processes.name == 'remove EE trips', 'input'][0]
                # see if have been given file or list of zones
                if os.path.isfile(external_zones_str):
                    whitespace, header_row = ODMatrix.check_file_header(missing_zones_str)
                    external_zones = pd.read_csv(external_zones_str, delim_whitespace=whitespace, header=header_row, usecols=[0], names=['zone_id'])
                    external_zones = list(external_zones.zone_id)
                else:
                    external_zones = [int(x) for x in external_zones_str.split(',')]
                
                od_matrix = od_matrix.remove_external_trips(external_zones)
                matrix_changes += 1
                self.processes.loc[self.processes.name == "remove EE trips", 'completed'] = 'yes'
            except:
                self.progress_label.setText("Removing EE trips unsuccessful")

        # if there have been changes to the o-d matrix, save the output
        if (('rezoning' in self.processes.name.values) & matrix_changes > 1) | (('rezoning' not in self.processes.name.values) & matrix_changes > 0):
            self.progress_label.setText("Saving output matrix to csv")
            od_matrix.export_to_csv(f"{self.outpath}/{od_matrix.name}_operations_applied.csv")

        # if summary is checked, produced summary of output matrix
        if self.summary & (matrix_changes > 0):
            self.progress_label.setText("Summarising output")
            print("Summarising output")
            output_summary = od_matrix.summary()
            output_summary = pd.DataFrame(data=output_summary.values(), index=output_summary.keys(), columns=['Value'])
            output_summary.to_excel(writer, sheet_name="output_summary")
            writer.save()
        
        if 'convert to UFM' in self.processes.name.values:
            self.progress_label.setText("Converting to UFM")
            saturn_exes_path = self.processes.loc[self.processes.name == 'convert to UFM', 'input'][0]
            # check this is the path to a folder
            if os.path.isdir(saturn_exes_path):
                ufm_path = od_matrix.export_to_ufm(saturn_exes_path, self.outpath)
                self.processes.loc[self.processes.name == 'convert to UFM', 'completed'] = 'yes'
                self.progress_label.setText(f"UFM saved to {ufm_path}")
            else:
                self.progress_label.setText("Error: SATURN EXES path given is not a folder. Conversion process couldn't complete.")

        if len(self.processes.name) > 0:
            self.progress_label.setText("Saving process log")
            self.processes.to_excel(writer, sheet_name="inputs", index=False)
            writer.save()

        self.progress_label.setText(
            "Matrix operations complete. You may exit the program."
        )