"""
GUI functionality for forecasting module
"""

##### IMPORTS #####
# Standard imports
import traceback
from pathlib import Path
from typing import Union, Dict

# Third party imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, Qt, QThread

# Local imports
import ui_widgets as ui
from forecast import ForecastDemand
import errors
from utilities import Utilities, progress_window
from info_window import InfoWindow

##### CLASSES #####
class ForecastUI(QtWidgets.QWidget):
    """The user interface for the delta process functionality.

    Parameters
    ----------
    tier_converter : tc_main_menu.tier_converter
        Local Freight Tool main menu instance.
    """

    def __init__(self, tier_converter):
        super().__init__()
        self.name = "Delta Process"
        self.tier_converter = tier_converter
        self.progress = None
        self.worker = None
        self.info_window = None
        self.KEYS = ["k1", "k2"]
        self.init_ui()

    def init_ui(self):
        """Initilises the UI window and all the widgets."""
        FONT = "Arial"
        FONT_SIZE = 10

        self.setGeometry(500, 200, 500, 500)
        self.setWindowTitle(self.name)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setWindowTitle(self.name + " - Error")
        self.error_dialog.setMinimumSize(600, 100)
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)

        label = QtWidgets.QLabel(self.name)
        label.setFont(QtGui.QFont(FONT, FONT_SIZE + 2, QtGui.QFont.Bold))
        info_button = QtWidgets.QPushButton("Info")
        info_button.setMaximumWidth(50)
        info_button.setFixedHeight(30)
        font_format = QtGui.QFont(FONT, FONT_SIZE)
        info_button.setFont(font_format)
        info_button.clicked.connect(self.on_click_info)
        back_button = QtWidgets.QPushButton("Back")
        back_button.setFixedHeight(30)
        back_button.clicked.connect(self.on_click_back)
        back_button.setFont(font_format)
        run_button = QtWidgets.QPushButton("Run")
        run_button.setFixedHeight(30)
        run_button.clicked.connect(self.on_click_run)
        run_button.setFont(font_format)

        button_format = QtGui.QFont(FONT, FONT_SIZE - 1)
        self.input_widgets = {
            "model_base": ui.FileInput(
                "Model Base Year Demand Matrix CSV",
                filetype="csv",
                label_format=font_format,
            ),
            "processed_base": ui.FileInput(
                "Processed Base Year Demand Matrix CSV",
                filetype="csv",
                label_format=font_format,
            ),
            "processed_forecast": ui.FileInput(
                "Processed Forecast Year Demand Matrix CSV",
                filetype="csv",
                label_format=font_format,
            ),
            "growth_mode": ui.RadioButtons(
                "Growth Mode:",
                ["Standard", "Exceptional"],
                label_format=font_format,
                button_format=button_format,
            ),
            "k1": ui.NumberInput(
                "K<sub>1</sub> Weighting",
                value=1.0,
                min_=0.0,
                max_=2.0,
                decimals=2,
                step=0.1,
                label_format=font_format,
            ),
            "k2": ui.NumberInput(
                "K<sub>2</sub> Weighting",
                value=1.0,
                min_=0.0,
                max_=2.0,
                decimals=2,
                step=0.1,
                label_format=font_format,
            ),
            "output_folder": ui.FileInput(
                "Output Folder", directory=True, label_format=font_format
            ),
        }

        for key in self.KEYS:
            self.input_widgets[key].disable()
        self.input_widgets["growth_mode"].reset()
        for button in self.input_widgets["growth_mode"].buttons:
            button.toggled.connect(lambda: self.toggle_radio_buttons(button))

        grid = QtWidgets.QGridLayout()
        grid.addWidget(label, 0, 0, 1, 1, Qt.AlignLeft)
        grid.addWidget(info_button, 0, 1, 1, 1, Qt.AlignRight)
        for i, w in enumerate(self.input_widgets.values()):
            grid.addWidget(w, i + 1, 0, 1, 2)
        row = len(self.input_widgets) + 2
        grid.addWidget(back_button, row, 0, 1, 1, Qt.AlignLeft)
        grid.addWidget(run_button, row, 1, 1, 1, Qt.AlignRight)
        self.setLayout(grid)

    def toggle_radio_buttons(self, button: QtWidgets.QRadioButton):
        """Disables and enables k value inputs as growth mode radio buttons
        are toggled.

        Parameters
        ----------
        button : QtWidgets.QRadioButton
            Radio button widget
        """
        if ((button.text() == "Standard") & (button.isChecked())) | (
            (button.text() != "Standard") & (not button.isChecked())
        ):
            for k in self.KEYS:
                self.input_widgets[k].disable()
        else:
            for k in self.KEYS:
                self.input_widgets[k].enable()

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
    """Worker thread for running the forecasting process.

    Parameters
    ----------
    forecast_ui: ForecastUI
        Instance of the parent `ForecastUI` class, to
        get progress window information from.
    parameters : Dict[str, Union[Path, int]]
        Input parameters from the GUI.
    """

    LINE_LIMIT = 20
    PROGRESS_WIDTH = 800
    error = pyqtSignal(str, str)

    def __init__(
        self, forecast_ui: ForecastUI, parameters: Dict[str, Union[Path, int]]
    ):
        super().__init__()
        self.ui_window = forecast_ui
        self.matrix_paths = {}
        for key in ["model_base", "processed_base", "processed_forecast"]:
            self.matrix_paths[key] = parameters[key]
        if parameters["growth_mode"][0]:
            self.growth_mode = "standard"
            self.k1 = None
            self.k2 = None
        else:
            self.growth_mode = "exceptional"
            self.k1 = parameters["k1"]
            self.k2 = parameters["k2"]
        self.output_folder = parameters["output_folder"]
        self.progress_window = self.ui_window.progress
        height = self.LINE_LIMIT * 15
        self.progress_window.resize(self.PROGRESS_WIDTH, height)
        self.progress_window.label.resize(self.PROGRESS_WIDTH, height)
        self.progress_lines = 0
        self.progress_text = ""

    def run(self):
        """Initialises the ForecastDemand class with the parameters from the
        UI and runs the `main` function.
        """
        try:
            forecaster = ForecastDemand(
                self.matrix_paths,
                self.output_folder,
                growth_mode=self.growth_mode,
                k1=self.k1,
                k2=self.k2,
                message_hook=self.update_progress,
            )
            forecaster.main()
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
