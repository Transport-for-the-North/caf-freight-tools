"""

File purpose:
GUI for process to split GBFM HGV annual tonnage matrices into rigid and artic
matrices, and convert to PCUs, then saves to output files.

Created on: Wed Mar 24 2021

Original author: CaraLynch

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, QThread, Qt
from PyQt5.QtWidgets import QCheckBox


# User-defined imports
from utilities import Utilities, progress_window
from info_window import InfoWindow
from matrix_utilities import ODMatrix
from hgv_annual_tonne_to_pcu import TonneToPCU

# Other packages
from pathlib import Path
import pandas as pd
import time
from datetime import timedelta


class TonneToPCUInterface(QtWidgets.QWidget):
    """Annual tonnes to PCU user interface.

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
        self.setGeometry(500, 200, 500, 740)
        self.setWindowTitle("HGV Annual Tonne to PCU")
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        y = 10
        label = QtWidgets.QLabel(self)
        label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        label.setText("HGV Annual Tonne to PCU")
        label.setGeometry(10, y, 700, 30)

        # Input HGV matrices
        y += 30
        hgv_label = QtWidgets.QLabel(self)
        hgv_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        hgv_label.setText("Inputs")
        hgv_label.setGeometry(10, y, 700, 30)

        label_spacing = 50
        y += label_spacing

        input_text = {
            "domestic_bulk_port": "domestic and bulk port matrix",
            "unitised_eu_imports": "unitised EU imports matrix",
            "unitised_eu_exports": "unitised EU exports matrix",
            "unitised_non_eu": "unitised non-EU imports and exports matrix",
            "ports": "ports lookup file",
            "distance_bands": "vehicle trips per 1000 tonnes by distance band file",
            "gbfm_distance_matrix": "GBFM distance matrix",
            "port_traffic_proportions": "port traffic trips per 1000 tonnes file",
            "pcu_factors": "PCU factors file",
        }
        input_spacing = 60
        self.inputs = {}
        for key in input_text.keys():
            self.inputs[key] = Utilities.add_file_selection(
                self,
                y,
                f"Select the {input_text[key]} (.csv, .txt)",
                filetype="Comma-separated Values (*.csv *.CSV *.txt *.TXT)",
            )
            y += input_spacing
        y -= 20
        # output directory
        output_label = QtWidgets.QLabel(self)
        output_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        output_label.setText("Output Folder")
        output_label.setGeometry(10, y, 125, 30)

        # Folder path for the outputs
        self.outpath = Utilities.add_file_selection(
            self, y + 45, "Select the output directory", directory=True
        )

        y += input_spacing + 30

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

    def run_button_clicked(self):
        """Initialises process once run button is clicked."""
        self.outpath = self.outpath.text().strip()
        for key in self.inputs.keys():
            self.inputs[key] = self.inputs[key].text().strip()

        # show alert if not all inputs have been given
        if "" in self.inputs.values():
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("HGV Annual Tonne to PCU")
            alert.setText("Error: you must specific all input files")
            alert.show()
        # show alert if output folder has not been given
        elif self.outpath == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("HGV Annual Tonne to PCU")
            alert.setText("Error: you must specifiy an output folder")
            alert.show()
        # run processes if no errors
        else:
            self.progress = progress_window(
                "HGV Annual Tonne to PCU", self.tier_converter
            )
            self.hide()

            # Call the main process
            self.worker = background_thread(self)
            self.worker.start()

    def back_button_clicked(self):
        """Returns to tier converter main menu"""
        self.tier_converter.show()
        self.hide()

    def closeEvent(self, event):
        """Closes the HGV Annual Tonne to PCU window."""
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()

    @pyqtSlot()
    def on_click_Info(self):
        self.selections_window = InfoWindow(self, "README.md")
        self.selections_window.show()


class background_thread(QThread):
    """Thread which runs the HGV annual tonne to annual PCU conversion
    process.

    Parameters
    ----------
    QThread
    """

    def __init__(self, TonneToPCUInterface):
        """Initialise class

        Parameters
        ----------
        MatrixUtilities : Class
            GUI class for matrix utilities
        """
        QThread.__init__(self)
        self.progress_window = TonneToPCUInterface.progress
        self.progress_window.resize(770, 130)
        self.progress_label = self.progress_window.label
        self.progress_label.resize(770, 125)
        self.inputs = TonneToPCUInterface.inputs
        self.outpath = Path(f"{TonneToPCUInterface.outpath}")

    def run(self):
        """Runs matrix processes"""
        try:
            start = time.perf_counter()
            progress_df = pd.DataFrame(
                {
                    "Process": [
                        "Read inputs",
                        "Perform conversion",
                        "Generate summaries",
                        "Save output matrices",
                    ],
                    "Completed": ["no"] * 4,
                    "Error": [""] * 4,
                }
            )
            self.progress_text = ""
            self.progress_lines = 0
            self.update_progress_string("\nReading inputs")
            hgv = TonneToPCU(self.inputs)
            self.inputs["output_folder"] = str(self.outpath)
            i = 0
            progress_df.loc[i, "Completed"] = "yes"
            self.update_progress_string("\nRunning conversion process")
            hgv.run_conversion()
            i += 1
            progress_df.loc[i, "Completed"] = "yes"
            self.update_progress_string("\nSummarising input and output matrices")
            summary_df = hgv.summary_df()
            i += 1
            progress_df.loc[i, "Completed"] = "yes"
            self.update_progress_string(
                f"\nSaving output PCU matrices to\n{self.outpath}", lines_to_add=2
            )
            hgv.save_pcu_outputs(self.outpath)
            i += 1
            progress_df.loc[i, "Completed"] = "yes"
        except Exception as e:
            self.update_progress_string(f"{e}")
            progress_df.loc[i, "Error"] = str(e)
        finally:
            # create log file for matrix summaries and processes information
            log_file = self.outpath / Path("tonne_to_pcu_log.xlsx")
            with pd.ExcelWriter(log_file, engine="openpyxl") as writer:
                try:
                    progress_df.to_excel(writer, sheet_name="process", index=False)
                    inputs_df = pd.DataFrame.from_dict(
                        self.inputs, orient="index", columns=["path"]
                    )
                    inputs_df.index.name = "file"
                    inputs_df.to_excel(writer, sheet_name="inputs", index=True)
                    summary_df.to_excel(
                        writer, sheet_name="matrix_summaries", index=True
                    )
                    hgv.inputs["distance_bands"].to_excel(
                        writer, sheet_name="distance_bands", index=False
                    )
                    hgv.inputs["port_traffic_proportions"].to_excel(
                        writer, sheet_name="port_traffic", index=False
                    )
                    hgv.inputs["pcu_factors"].to_excel(
                        writer, sheet_name="pcu_factors", index=False
                    )
                except UnboundLocalError as e:
                    msg = f"Error: {e}"
                    self.update_progress_string(msg)
            msg = (
                f"Time taken: {timedelta(seconds = time.perf_counter() - start)}"
                f"\nAnnual tonnes to annual PCU complete, all outputs saved to "
                f"{self.outpath}.\nYou may exit the program, check"
                f" tonne_to_pcu_log.xlsx for more information.\n"
            )
            self.update_progress_string(msg, lines_to_add=3)

    def update_progress_string(self, text_to_add, lines_to_add=1, line_limit=10):
        """
        Updates the progress window to display a new line within the allowed
        number of lines.

        Parameters
        ----------
        text_to_add : str
            New text to add to progress window
        lines_to_add: int
            Lines of text in text_to_add
        line_limit : int, optional
            Number of lines displayed in progress window, by default 20
        """
        print(text_to_add)

        if self.progress_lines + lines_to_add > line_limit:
            self.progress_text = text_to_add
            self.progress_lines = 1
        else:
            self.progress_text += text_to_add
            self.progress_lines += lines_to_add

        self.progress_label.setText(self.progress_text)
