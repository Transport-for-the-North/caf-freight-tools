"""
    GUI functionality for the LGV model
"""

##### IMPORTS #####
# Standard imports
import pprint
import traceback

# Third party imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal, Qt, QThread

# Local imports
from .. import ui_widgets as ui
from ..utilities import Utilities, progress_window
from ..info_window import InfoWindow
from .lgv_model import main
from .lgv_inputs import LGVInputPaths, DataPaths, CommuteWarehousePaths


class LGVModelUI(QtWidgets.QWidget):
    """The user interface for the LGV model functionality.

    Parameters
    ----------
    tier_converter : tc_main_menu.tier_converter, optional
        Local Freight Tool main menu instance, default is None
    """

    def __init__(self, tier_converter=None):
        super().__init__()
        self.name = "LGV Model"
        self.tier_converter = tier_converter
        self.progress = None
        self.worker = None
        self.info_window = None
        self.init_ui()

    def init_ui(self):
        """Initilises the UI window and all the widgets."""
        self.setGeometry(500, 120, 700, 550)
        self.setWindowTitle(self.name)
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setWindowTitle(self.name + " - Error")
        self.error_dialog.setMinimumSize(600, 100)
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)

        label = QtWidgets.QLabel("LGV Model")
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
            "hh_data": ui.FileInput("Household projections CSV", filetype="CSV"),
            "hh_zc": ui.FileInput(
                "Household projections zone correspondence CSV", filetype="CSV"
            ),
            "bres_path": ui.FileInput("BRES data by LSOA", filetype="CSV"),
            "warehouse_path": ui.FileInput("Warehouse Floorspace by LSOA", filetype="CSV"),
            "commute_warehouse_paths_medium": ui.FileInput(
                "Warehouse Floorspace by LSOA for Commute - Medium Weighting",
                filetype="CSV",
            ),
            "commute_warehouse_paths_high": ui.FileInput(
                "Warehouse Floorspace by LSOA for Commute - High Weighting (optional)",
                filetype="CSV",
            ),
            "commute_warehouse_paths_low": ui.FileInput(
                "Warehouse Floorspace by LSOA for Commute - Low Weighting (optional)",
                filetype="CSV",
            ),
            "parameters_path": ui.FileInput("LGV parameters spreadsheet", filetype="excel"),
            "trip_distributions_path": ui.FileInput(
                "Trip distributions spreadsheet", filetype="excel"
            ),
            "qs606ew_path": ui.FileInput(
                "Census Occupation data for England and Wales (QS606EW) CSV",
                filetype="CSV",
            ),
            "qs606sc_path": ui.FileInput(
                "Census Occupation data for Scotland (QS606UK) CSV", filetype="CSV"
            ),
            "sc_w_dwellings_path": ui.FileInput(
                "Dwellings data for Wales and Scotland CSV", filetype="CSV"
            ),
            "e_dwellings_path": ui.FileInput(
                "Dwellings data for England spreadsheet", filetype="excel"
            ),
            "ndr_floorspace_path": ui.FileInput(
                "NDR Business floorspace data CSV", filetype="CSV"
            ),
            "lsoa_lookup_path": ui.FileInput(
                "LSOA to model zone correspondence CSV", filetype="CSV"
            ),
            "msoa_lookup_path": ui.FileInput(
                "MSOA to model zone correspondence CSV", filetype="CSV"
            ),
            "lad_lookup_path": ui.FileInput(
                "LAD to model zone correspondence CSV", filetype="CSV"
            ),
            "model_study_area": ui.FileInput(
                "Lookup for zones in model  study area CSV", filetype="CSV"
            ),
            "cost_matrix_path": ui.FileInput("Cost matrix CSV", filetype="CSV"),
            "calibration_matrix_path": ui.FileInput(
                "Calibration matrix CSV (optional)", filetype="CSV"
            ),
            "output_folder": ui.FileInput("Output Folder", directory=True),
        }

        grid = QtWidgets.QGridLayout()
        grid.addWidget(label, 0, 0, 1, 1, Qt.AlignLeft)
        grid.addWidget(info_button, 0, 2, 1, 1, Qt.AlignRight)
        i = 1
        j = 0
        for w in self.input_widgets.values():
            grid.addWidget(w, i, j, 1, 1)
            if j == 0:
                j = 2
            else:
                i += 1
                j = 0

        row = len(self.input_widgets) + 2
        if self.tier_converter:
            grid.addWidget(back_button, row, 0, 1, 1, Qt.AlignLeft)
        grid.addWidget(run_button, row, 2, 1, 1, Qt.AlignRight)
        self.setLayout(grid)
        if not self.tier_converter:
            self.show()

    def get(self) -> LGVInputPaths:
        """Get all the parameters provided in the UI.

        Returns
        -------
        LGVInputPaths
            Input paths for running LGV model.
        """
        preprocessed_keys = (
            "hh_data",
            "hh_zc",
            "commute_warehouse_paths_medium",
            "commute_warehouse_paths_high",
            "commute_warehouse_paths_low",
        )
        paths = {}
        paths["household_paths"] = DataPaths(
            "LGV Households",
            self.input_widgets["hh_data"].get(),
            self.input_widgets["hh_zc"].get(),
        )
        paths["commute_warehouse_paths"] = CommuteWarehousePaths(
            medium=self.input_widgets["commute_warehouse_paths_medium"].get(),
            high=self.input_widgets["commute_warehouse_paths_high"].get(),
            low=self.input_widgets["commute_warehouse_paths_low"].get(),
        )
        for key, widget in self.input_widgets.items():
            if key in preprocessed_keys:
                continue
            paths[key] = widget.get()

        return LGVInputPaths(**paths)

    def on_click_run(self):
        """Get the input parameters and initialise the progress window and worker.

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
            if self.tier_converter:
                self.tier_converter.show()

    def on_click_info(self):
        """Display help menu."""
        if not self.tier_converter:
            self.info_window = InfoWindow(
                self,
                "README.md",
                include=[("## 5: LGV Model\n", "## 6: Matrix Utilities\n")],
            )
        else:
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
    """Worker thread for running the `main` function from `lgv_model`.

    Parameters
    ----------
    lgv_model_ui : LGVModelUI
        Instance of the parent `LGVModelUI` class, to
        get progress window information from.
    parameters : Dict[str, Union[Path, int]]
        Input parameters from the GUI passed directly to the
        `main` function.
    """

    LINE_LIMIT = 1
    PROGRESS_WIDTH = 800
    error = pyqtSignal(str, str)

    def __init__(self, lgv_model_ui: LGVModelUI, parameters: LGVInputPaths):
        super().__init__()
        self.ui_window = lgv_model_ui
        self.parameters = parameters
        self.progress_window = self.ui_window.progress
        height = self.LINE_LIMIT * 15
        self.progress_window.resize(self.PROGRESS_WIDTH, height)
        self.progress_window.label.resize(self.PROGRESS_WIDTH, height)
        self.progress_lines = 0
        self.progress_text = ""

    def run(self):
        """Runs the `main` function with the parameters from the UI.

        Catches any exceptions produced by the function and displays them
        in the progress window and emits them to the `error` signal.
        """
        try:
            main(self.parameters, message_hook=self.update_progress)
        except Exception as error:
            tb = traceback.format_exc()
            msg = f"Critical error - {error.__class__.__name__}: {error}"
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
