# -*- coding: utf-8 -*-
"""
    GUI functionality for the time period conversion module.
"""

##### IMPORTS #####
# Standard imports
import pprint
import traceback
from pathlib import Path
from typing import Union, Dict

# Third party imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, Qt, QThread

# Local imports
import ui_widgets as ui
import time_period_conversion as tp_conv
import errors
from utilities import Utilities, progress_window
from info_window import InfoWindow


##### CLASSES #####
class TimeConversionUI(QtWidgets.QWidget):
    """The user interface for the time period conversion functionality.

    Parameters
    ----------
    tier_converter : tc_main_menu.tier_converter
        Local Freight Tool main menu instance.
    """

    def __init__(self, tier_converter):
        super().__init__()
        self.name = "HGV Annual PCU to Time Period PCU"
        self.tier_converter = tier_converter
        self.progress = None
        self.worker = None
        self.info_window = None
        self.init_ui()

    def init_ui(self):
        """Initilises the UI window and all the widgets."""
        self.setGeometry(500, 200, 500, 500)
        self.setWindowTitle(self.name)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setWindowTitle(self.name + " - Error")
        self.error_dialog.setMinimumSize(600, 100)
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)

        label = QtWidgets.QLabel("HGV Annual PCU to Time Period PCU Conversion")
        label.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        info_button = QtWidgets.QPushButton("Info")
        info_button.setMaximumWidth(50)
        info_button.setFixedHeight(30)
        info_button.clicked.connect(self.on_click_info)
        back_button = QtWidgets.QPushButton("Back")
        back_button.setFixedHeight(30)
        back_button.clicked.connect(self.on_click_back)
        run_button = QtWidgets.QPushButton("Run")
        run_button.setFixedHeight(30)
        run_button.clicked.connect(self.on_click_run)

        self.input_widgets = {
            "profile_path": ui.FileInput(
                "HGV Distributions Excel Workbook", filetype="excel"
            ),
            "time_profile_path": ui.FileInput("Time Periods CSV", filetype="csv"),
            "year": ui.NumberInput("Model Year", value=2018, min_=2000, max_=2100),
            "artic_matrix": ui.FileInput(
                "Articulated Annual PCUs Matrix CSV", filetype="csv"
            ),
            "rigid_matrix": ui.FileInput(
                "Rigid Annual PCUs Matrix CSV", filetype="csv"
            ),
            "zone_correspondence_path": ui.FileInput(
                "Zone Correpondence CSV", filetype="csv"
            ),
            "output_folder": ui.FileInput("Output Folder", directory=True),
        }

        grid = QtWidgets.QGridLayout()
        grid.addWidget(label, 0, 0, 1, 1, Qt.AlignLeft)
        grid.addWidget(info_button, 0, 1, 1, 1, Qt.AlignRight)
        for i, w in enumerate(self.input_widgets.values()):
            grid.addWidget(w, i + 1, 0, 1, 2)
        row = len(self.input_widgets) + 2
        grid.addWidget(back_button, row, 0, 1, 1, Qt.AlignLeft)
        grid.addWidget(run_button, row, 1, 1, 1, Qt.AlignRight)
        self.setLayout(grid)

    def get(self) -> Dict[str, Union[Path, int]]:
        """Get all the parameters provided in the UI.

        Returns
        -------
        Dict[str, Union[Path, int]]
            Dictionary containing all the parameters (keys)
            and their values, contains the following keys:
            profile_path, time_profile_path, year, artic_matrix
            rigid_matrix, zone_correspondence_path and output_folder.

        Raises
        ------
        errors.MissingDataError
            If any of the parameters aren't provided.
        """
        params = {}
        missing = []
        for nm, widget in self.input_widgets.items():
            params[nm] = widget.get()
            if params[nm] is None:
                missing.append(widget.label_text)
        if missing:
            raise errors.MissingDataError("input parameters", missing)
        return params

    def on_click_run(self):
        """Get the input parameters and intialise the progress window and worker.

        If any errors occur during getting the parameters or initialisation
        then an error box is shown and the worker thread isn't started.
        """
        try:
            params = self.get()
            pprint.pp(params)
            self.progress = progress_window(self.name, self.tier_converter)
            self.hide()
            self.worker = Worker(self, params)
            self.worker.error.connect(self.show_error)
        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            msg = f"{e.__class__.__name__}: {e}"
            self.show_error(msg, tb)
        else:
            self.worker.start()

    def on_click_back(self):
        """Returns to tier converter main menu"""
        self.tier_converter.show()
        self.hide()

    def closeEvent(self, event):
        """Closes the time period conversion window."""
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()

    def on_click_info(self):
        """Display help menu."""
        self.info_window = InfoWindow(self, "README.md")
        self.info_window.show()

    def show_error(self, msg: str, details: str = None):
        """Display an error message box.

        Parameters
        ----------
        msg : str
            Text to be displayed in the message box.
        details : str, optional
            Longer text which can be displayed in a show
            details tab, by default None.
        """
        self.error_dialog.setText(msg)
        self.error_dialog.setDetailedText(details)
        self.error_dialog.show()


class Worker(QThread):
    """Worker thread for running the `main` function from `time_period_conversion`.

    Parameters
    ----------
    time_conv_ui : TimeConversionUI
        Instance of the parent `TimeConversionUI` class, to
        get progress window information from.
    parameters : Dict[str, Union[Path, int]]
        Input parameters from the GUI passed direction to the
        `main` function.
    """

    LINE_LIMIT = 20
    PROGRESS_WIDTH = 800
    error = pyqtSignal(str, str)

    def __init__(
        self, time_conv_ui: TimeConversionUI, parameters: Dict[str, Union[Path, int]]
    ):
        super().__init__()
        self.ui_window = time_conv_ui
        self.parameters = parameters
        self.progress_window = self.ui_window.progress
        height = self.LINE_LIMIT * 15
        self.progress_window.resize(self.PROGRESS_WIDTH, height)
        self.progress_window.label.resize(self.PROGRESS_WIDTH, height)
        self.progress_lines = 0
        self.progress_text = ""

    def run(self):
        """Runs the `tp_conv.main` function with the parameters from the UI.

        Catches any exceptions produced by the function and displays them
        in the progress window and emits them to the `error` signal.
        """
        try:
            tp_conv.main(**self.parameters, message_hook=self.update_progress)
        except Exception as e:
            tb = traceback.format_exc()
            msg = f"Critical error - {e.__class__.__name__}: {e}"
            self.update_progress(msg)
            self.error.emit(msg, tb)

    def update_progress(self, text: str):
        """Update progress window label with given `text`.

        Adds `text` as a new line to the window, resets the
        window if the number of lines exceeds `LINE_LIMIT`.

        Parameters
        ----------
        text : str
            Text to be added to progress window.
        """
        print(text)
        if self.progress_lines >= self.LINE_LIMIT:
            self.progress_lines = 0
            self.progress_text = ""
        self.progress_lines += 1
        self.progress_text += text.strip() + "\n"
        self.progress_window.label.setText(self.progress_text)
