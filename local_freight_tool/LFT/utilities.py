# -*- coding: utf-8 -*-
"""
Set of utilities for use in the freight tool
"""
##### IMPORTS #####
# Standard imports
import re
import logging
import os
import json
import csv
from itertools import islice
from pathlib import Path
from typing import Dict, Union

# Third-party imports
import pandas as pd
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QVBoxLayout

# Local imports
from .errors import (
    MissingParameterError,
    IncorrectParameterError,
    MissingColumnsError,
    MissingWorksheetError,
)


# Function which asks the user if they really want to trigger sys.exit()
class Utilities(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

    def closeEvent(window, event):
        reply = QtWidgets.QMessageBox.question(
            window,
            "Exit?",
            "Are you sure you want to quit?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            return True
        else:
            event.ignore()
            return False

    def add_file_selection(
        self,
        y_position,
        label_txt,
        multiple_files=False,
        directory=False,
        filetype=None,
        return_browse=False,
        box_width=380,
    ):
        def browse_file():
            if directory == True:
                selected_file = QtWidgets.QFileDialog(self).getExistingDirectory(
                    self, label_txt
                )
            else:  # looking for file(s) rather than directory
                if multiple_files == True:  # for multiple files, separate with ' % '
                    file_dialog = QtWidgets.QFileDialog(self)
                    file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
                    selected_file, _ = file_dialog.getOpenFileNames(
                        self, label_txt, None, filetype
                    )
                    selected_file = " % ".join(selected_file)
                else:
                    selected_file, _ = QtWidgets.QFileDialog(self).getOpenFileName(
                        self, label_txt, None, filetype
                    )

            # Update text box
            file_path.setText(selected_file)

        # Box which will contain the file selection
        file_path = QtWidgets.QLineEdit(self)
        file_path.setGeometry(10, y_position, box_width, 30)

        # Button to browse for the file
        browse_button = QtWidgets.QPushButton(self)
        browse_button.setText("Browse")
        browse_button.setGeometry(box_width + 20, y_position, 90, 30)
        browse_button.clicked.connect(browse_file)

        # Label with instructions
        label = QtWidgets.QLabel(self)
        label.setText(label_txt)
        label.setGeometry(10, y_position - 30, 480, 30)
        if return_browse:
            return file_path, browse_button
        else:
            return file_path

    # Some input files are tab and some are comma-separated, so this version of read_csv allows it to accept either
    def read_csv(file_name):
        # Read in the second line of the file
        with open(file_name, "r") as csv_file:
            second_line = list(islice(csv_file, 2))[1]

        # Determine if the file is tab or comma-separated
        if len(second_line.split("\t")) > 1:
            sep = "\t"
        else:
            sep = ","

        # Read in the whole file with pandas
        return pd.read_csv(file_name, sep=sep)

    # Define a function to read the tp selections back in as a list of dictionaries
    def read_tp(file_name):
        with open(file_name) as tp:
            tp = [
                {key: val for key, val in row.items()}
                for row in csv.DictReader(
                    tp, fieldnames=["name", "days", "hr_start", "hr_end"]
                )
            ]
        return tp


# Window to inform the user what stage the process is at (third interface window)
class progress_window(QtWidgets.QWidget):
    def __init__(self, title, tier_converter):
        super().__init__()
        self.title = title
        self.tier_converter = tier_converter
        self.initUI()

    def initUI(self):
        self.setGeometry(400, 500, 850, 100)
        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(10, 10, 830, 30)
        self.show()

    def closeEvent(self, event):
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()


# Window to inform the user how to use the current tool selected
class info_window(QtWidgets.QWidget):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 200, 800, 400)
        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.labelA = QtWidgets.QLabel(self)
        self.labelA.setGeometry(10, 10, 830, 30)
        self.labelA.setText("info text")
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(10, 0, 830, 30)
        self.label.setText("info text")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label.move(10, 0)
        self.label.resize(750, 300)

        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText("Back")
        back_button.setGeometry(10, 350, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)

        self.show()

    def back_button_clicked(self):
        self.hide()

    def closeEvent(self, event):
        Utilities.closeEvent(self, event)


class Loggers:
    """
    Class containing methods to create the main parent logger and any child loggers.
    """

    LOGGER_NAME = "NoHAM-FPT"

    def __init__(self, path):
        """
        Creates and sets up the main logger.

        Parameters:
            path: str
                Path to a directory for where to save the log file, or
                a path including the log file name.
        """
        # Check if path is directory
        if os.path.isdir(path):
            logFile = os.path.join(path, "NoHAM-FPT.log")
        else:
            logFile = path

        # Initiate logger
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)

        # Create file handler
        fh = logging.FileHandler(logFile)
        fh.setLevel(logging.DEBUG)
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # Create formatter
        format = logging.Formatter(
            "%(asctime)s [%(name)-30.30s] [%(levelname)-8.8s] %(message)s"
        )
        fh.setFormatter(format)
        ch.setFormatter(logging.Formatter("[%(levelname)-8.8s] %(message)s"))
        # Add handlers to logger
        for i in (ch, fh):
            self.logger.addHandler(i)

        # Write to logger
        self.logger.debug("-" * 100)
        self.logger.info("Initialised main logger.")

    def __enter__(self):
        """Called when initialising class with 'with' statement."""
        return self

    def __exit__(self, excepType, excepVal, traceback):
        """Called when exiting with statement, writes any error to the logger and closes the file."""
        # Write exception to logfile
        if excepType is not None or excepVal is not None or traceback is not None:
            self.logger.critical("Oh no a critical error occurred", exc_info=True)
        else:
            self.logger.info("Program completed without any fatal errors")
        # Closes logger
        self.logger.info("Closing log file")
        logging.shutdown()

    @classmethod
    def childLogger(klass, loggerName):
        """
        Creates a child logger.

        Parameters:
            loggerName: str
                The name of the child logger.
        Returns:
            logger: logger object
        """
        # Initialise logger
        logger = logging.getLogger(f"{klass.LOGGER_NAME}.{loggerName}")
        return logger


class Parameters:
    """
    Class for reading the parameters given and creating an empty parameter file for input.
    """

    # Class constants
    _INDENT = 4

    # Default parameters
    _TIME_PERIODS = {
        "_comment": "Time period conversion factors.",
        "AM": None,
        "IP": None,
        "PM": None,
        "OP": None,
    }
    _INPUT = {
        "_comment": "Parameters for one run of the process",
        "TIME_PERIODS": _TIME_PERIODS,
        "FILEPATH": "",
        "INPUT_FORMAT": "TSV/CSV",
        "INPUT_COLUMNS": {
            "_comment": "Names of the columns in the input data.",
            "Origin": "O",
            "Destination": "D",
            "Trips": "Annual_PCU/Annual_Tonnage",
        },
    }
    _LOOKUP = {
        "FILEPATH": "",
        "INPUT_FORMAT": "TSV/CSV",
        "INPUT_COLUMNS": {"old": "", "new": "", "splitting_factor": ""},
    }
    _ZONE_LOOKUP = {
        "_comment": "Parameters for the rezoning process, optional.",
        **_LOOKUP,
    }
    _SECTOR_LOOKUP = {
        "_comment": (
            "Parameters for the sector OD tables to be produced,"
            " for the input matrix, optional."
        ),
        **_LOOKUP,
    }
    _REZONED_SECTOR_LOOKUP = {
        "_comment": (
            "Parameters for the sector OD tables to be produced,"
            " for the rezoned and output matrices, optional."
        ),
        **_LOOKUP,
    }
    DEFAULT_PARAMETERS = {
        "_comment": (
            "Parameter file for NoHAM-FPT, can run process"
            " on multiple files at once by creating different "
            "input blocks. Input blocks can have any name."
        ),
        "LOOKUPS": {
            "ZONE_LOOKUP": _ZONE_LOOKUP,
            "SECTOR_LOOKUP": _SECTOR_LOOKUP,
            "REZONED_SECTOR_LOOKUP": _REZONED_SECTOR_LOOKUP,
        },
        "INPUT": _INPUT,
    }

    def __init__(self, path=None, params=None):
        """
        Initiate the parameters class by reading file if given, using parameters if given
        or with defaults.

        Parameters:
            path: str, optional
                Path to parameters file.
            params: dict, optional
                Dictionary containing parameters.
        """
        if not path is None:
            self.params = self.read(path)
        elif not params is None:
            self.params = dict(params)
        else:
            self.params = self.DEFAULT_PARAMETERS
        return

    @classmethod
    def read(cls, path):
        """
        Read the paramters file given, using json.

        Parameters:
            path: str
                Path to the parameters file.
        Returns:
            params: dict
                Dictionary containing all the parameters read.
        """
        # Read parameters
        with open(path, "rt") as f:
            params = json.load(f)

        return params

    def __str__(self):
        """
        Creates json string.

        Parameters:
            None
        Returns:
            params: str
                Json str dump of parameters.
        """
        return json.dumps(self.params, indent=self._INDENT)

    def write(self, path):
        """
        Write parameters to file.

        Parameters:
            path: str
                Path to write parameter file to.
        Returns:
            None
        """
        # Write parameters to file
        with open(path, "wt") as f:
            json.dump(self.params, f, indent=self._INDENT)
        return

    @staticmethod
    def checkParams(parameters, expected, name):
        """
        Checks if parameters contain expected.

        Parameters:
            parameters: dict
                Dictionary containing parameters.
            expected: iterable
                List of the expected parameters,
                keys in the dictionary.
            name: str
                Name of the parameter group being checked.
        Returns:
            params: dict
                Dictionary containing only the expected parameters.
        Raises:
            MissingParameterError: If any of the expected parameters
            are not in the dictionary.
        """
        params = {}
        for i in expected:
            if i not in parameters.keys():
                raise MissingParameterError(i, name)
            else:
                # Only keep required values
                params[i] = parameters[i]

        return params


def getSeparator(format, parameter=None):
    """
    Checks whether the given format is allowed for reading a text file,
    and gets the corresponding separator.

    Parameters:
        format: str
            The format of the text file should be.
        parameter: str, optional
            Name of the parameter that is being checked.
            Default None.
    Returns:
        separator: str
            The separator to be used when reading the file.
    Raises:
        IncorrectParameterError: If format is not of correct value
    """
    # Accepted formats
    forms = {"csv": ",", "tsv": "\t"}
    # Check what format has been given
    for key, val in forms.items():
        if format.lower() == key:
            return val
    else:
        # Raise error for wrong format given
        expected = list(forms.keys())
        raise IncorrectParameterError(format, parameter=parameter, expected=expected)


def check_file_path(
    path: Path, name: str, *extensions: str, return_path: bool = False
) -> Union[bool, Path]:
    """Check that the given `path` is an existing file.

    Also checks if the file contains the correct file
    extension, if any are given.

    Parameters
    ----------
    path : Path
        Path to be checked.
    name : str
        Name used for error messages.
    *extensions : str, optional
        Any number of extension strings to check
        e.g. ".csv", ".txt"
    return_path : bool, default False
        If True returns the Path, otherwise returns boolean
        for if the file exists and has the correct extension.

    Returns
    -------
    bool or Path
        If `return_path` then returns the `path` (as a Path
        object), otherwise returns True if the file exists
        and has the correct extension.

    Raises
    ------
    FileNotFoundError
        If the file doesn't exist, is a folder or
        isn't the correct extension.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{name} file does not exist: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{name} is a folder not a file: {path}")
    if extensions is not None:
        extensions = [s.lower() for s in extensions]
        if path.suffix.lower() not in extensions:
            msg = " or".join(", ".join(extensions).rsplit(",", 1))
            raise FileNotFoundError(
                f"{name} should be file of type {msg} not: {path.suffix}"
            )
    if return_path:
        return path
    return True


def check_folder(path: Path, name: str, create: bool = False) -> True:
    """Checks if given `path` is an existing folder.

    Can create a new folder if it doesn't already
    exist.

    Parameters
    ----------
    path : Path
        Path to check.
    name : str
        Name used for error messages.
    create : bool, optional
        Whether the folder should be created if it doesn't
        already exist, by default False

    Returns
    -------
    bool
        True if the folder already exists and
        False if the folder had to be created.

    Raises
    ------
    NotADirectoryError
        If the given `path` is a file not a folder.
    FileNotFoundError
        If the folder doesn't exist and `create` is
        False.
    """
    path = Path(path)
    if path.is_dir():
        return True
    if path.is_file():
        raise NotADirectoryError(f"{name} is a file when it should be a folder: {path}")
    if create:
        path.mkdir(parents=True)
        return False
    raise FileNotFoundError(f"{name} folder does not exist: {path}")


def read_csv(
    path: Path, name: str = None, columns: Dict = None, **kwargs
) -> pd.DataFrame:
    """Wrapper function for `pandas.read_csv` to perform additional checks.

    Checks what delimiter the file uses before reading and provides more
    detailed error messages about missing columns.

    Parameters
    ----------
    path : Path
        Path to the CSV file (can be ".csv" or ".txt").
    name : str, optional
        Human readable name of the file being read (used for error
        messages), by default None and uses the filename.
    columns : Dict, list or tuple, default None
        - List or tuple - used for usecols parameter of `pandas.read_csv`.
        - Dict - used for the dtype and usecols parameter of
          `pandas.read_csv`, where keys are column name and values are
          data type.
        - None - reads in all columns from the CSV.
    kwargs : all other keyword arguments
        Passed to `pandas.read_csv`.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the information from the CSV.

    Raises
    ------
    MissingColumnsError
        If any columns given don't exist in the CSV.
    ValueError
        If any of the columns cannot be converted to the
        given data type.
    """
    path = Path(path)
    if name is None:
        name = path.stem
    check_file_path(path, name, ".txt", ".csv")
    if "sep" not in kwargs.keys() and "delimiter" not in kwargs.keys():
        # Don't try to figure out delimiter if it is already given
        # Read in the second line of the file to determine the delimiter
        with open(path, "r") as csv_file:
            second_line = list(islice(csv_file, 2))[1]
        kwargs["sep"] = "\t" if len(second_line.split("\t")) > 1 else ","
    if isinstance(columns, (tuple, list)):
        kwargs["usecols"] = columns
    elif isinstance(columns, dict):
        kwargs["usecols"] = columns.keys()
        kwargs["dtype"] = columns
    try:
        df = pd.read_csv(path, **kwargs)
    except ValueError as err:
        match = re.match(
            r".*columns expected but not found:\s+\[((?:'[^']+',?\s?)+)\]",
            str(err),
            re.IGNORECASE,
        )
        if match:
            missing = re.findall(r"'([^']+)'", match.group(1))
            raise MissingColumnsError(name, missing) from err
        if isinstance(columns, dict):
            # Check what column can't be converted to dtypes
            kwargs.pop("dtype")
            df = pd.read_csv(path, **kwargs)
            for c, t in columns.items():
                try:
                    df[c].astype(t)
                except ValueError:
                    raise ValueError(
                        f"Column '{c}' in {name} has values "
                        f"which cannot be converted to {t}"
                    ) from err
        raise
    return df


def read_excel(
    path: Path, name: str = None, columns: Dict = None, **kwargs
) -> pd.DataFrame:
    """Wrapper function for `pandas.read_excel` to perform additional checks.

    Reads file and provides more detailed error messages about missing
    columns.

    Parameters
    ----------
    path : Path
        Path to the XLSX file.
    name : str, optional
        Human readable name of the file being read (used for error
        messages), by default None and uses the filename.
    columns : Dict, list or tuple, default None
        - List or tuple - used for usecols parameter of `pandas.read_excel`.
        - Dict - used for the dtype and usecols parameter of
          `pandas.read_excel`, where keys are column name and values are
          data type.
        - None - reads in all columns from the XLSX.
    kwargs : all other keyword arguments
        Passed to `pandas.read_excel`.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the information from the XLSX.

    Raises
    ------
    MissingColumnsError
        If any columns given don't exist in the XLSX.
    ValueError
        If any of the columns cannot be converted to the
        given data type.
    """

    path = Path(path)
    if name is None:
        name = path.stem
    check_file_path(path, name, ".xlsx")
    if isinstance(columns, (tuple, list)):
        kwargs["usecols"] = columns
    elif isinstance(columns, dict):
        kwargs["usecols"] = columns.keys()
        kwargs["dtype"] = columns

    try:
        df = pd.read_excel(path, **kwargs)
    except ValueError as err:
        match = re.match(
            r".*columns expected but not found:\s+\[((?:'[^']+',?\s?)+)\]",
            str(err),
            re.IGNORECASE,
        )
        if match:
            missing = re.findall(r"'([^']+)'", match.group(1))
            raise MissingColumnsError(name, missing) from err
        if isinstance(columns, dict):
            # Check what column can't be converted to dtypes
            kwargs.pop("dtype")
            df = pd.read_excel(path, **kwargs)
            for c, t in columns.items():
                try:
                    df[c].astype(t)
                except ValueError:
                    raise ValueError(
                        f"Column '{c}' in {name} has values "
                        f"which cannot be converted to {t}"
                    ) from err
        raise
    return df


def read_multi_sheets(path: Path, sheets: Dict, **kwargs):
    """Function to read in multiple excel sheets.

    Reads all sheets into a dictonary and provides detailed error messages
    about missing columns.

    Parameters
    ----------
    path : Path
        Path to the XLSX file.
    sheets : Dict[Dict, list or tuple]
        Dictionary of the sheets to be read, where the keys are sheet names
        and the values are used for the columns parameter of read_excel.
    kwargs : all other keyword arguments
        Passed to `pandas.read_excel` for every sheet.

    Returns
    -------
    Dict[pd.DataFrame]
        Dictionary where the keys are sheet names and values are the
        DataFrames containing the information from each sheet.

    Raises
    ------
    MissingWorksheetError
        If any sheets given don't exist in the XLSX.
    """
    path = Path(path)
    check_file_path(path, path.stem, ".xlsx")
    dfs = {}
    for sheet in sheets:
        try:
            dfs[sheet] = read_excel(
                path, name=sheet, columns=sheets[sheet], sheet_name=sheet, **kwargs
            )
        except KeyError as err:
            match = re.match(r".*Worksheet\s.*does not exist.", str(err), re.IGNORECASE)
            if match:
                raise MissingWorksheetError(path.stem, sheet) from err
            raise
        except ValueError as err:
            if str(err).lower().startswith("worksheet"):
                raise MissingWorksheetError(path.stem, sheet) from err
            raise
    return dfs


def to_dict(
    df: pd.DataFrame, key_col: str, val_col: tuple[str, type], name: str = None
):
    """Transform a dataframe to a dictionary

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with columns to transform to dictionary
    key_col : str
        Column name as string to use as keys in dictionary.
    val_col : tuple(str, type) or str
        Tuple with (column name, data type) or column name as string to
        use as values in dictionary, e.g. ("Values", float) or "Values".
    name : str, optional
        Name of dataframe to display in error message

    Raises
    ------
    ValueError
        If the value column in the dataframe is not of the expected type.

    Returns
    -------
    dict
        Dictionary with keys corresponding to elements in key_col, and
        values corresponding to elements in val_col.
    """
    dictionary = {}

    if isinstance(val_col, tuple):
        val_dtype = val_col[1]
        val_col = val_col[0]
        try:
            df[val_col] = df[val_col].astype(val_dtype)
        except ValueError as err:
            msg = f"Expected '{val_col}'"
            if name:
                msg += f"in '{name}'' "
            msg += f"to be of type '{val_dtype}'"
            raise ValueError(msg) from err

    for i in df.index:
        dictionary[df.at[i, key_col]] = df.at[i, val_col]

    return dictionary
