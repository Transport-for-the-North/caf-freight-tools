# -*- coding: utf-8 -*-
"""
    Module containing classes for custom PtQt5 widgets.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path
from typing import Union, List

# Third party imports
from PyQt5 import QtWidgets, QtGui


##### CLASSES #####
class FileInput(QtWidgets.QWidget):
    """Labelled text input box for file paths with button to open file select window.

    Parameters
    ----------
    label_text : str
        Text to be displayed in the widget label.
    multiple_files : bool, optional
        Whether or not multiple files can be selected, by default False.
    directory : bool, optional
        Whether or not the input expected is a folder, by default False
    filetype : str, optional
        The filetype(s) to show in the file select window (does nothing if
        `directory` is True), by default None. If string provided isn't a
        key for `FILETYPES` then it will be passed directly to
        `QtWidgets.QFileDialog`.
    label_format: QtGui.QFont, optional
        The font of the label, by default None
    """

    FILETYPES = {
        "excel": "Excel Workbook (*.xlsx)",
        "csv": "Comma-separated values (*.csv *.txt)",
    }

    def __init__(
        self,
        label_text: str,
        multiple_files: bool = False,
        directory: bool = False,
        filetype: str = None,
        label_format: QtGui.QFont = None,
    ):
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.label_text = str(label_text)
        self.multiple_files = bool(multiple_files)
        self.directory = bool(directory)
        if isinstance(filetype, str):
            self.filetype = self.FILETYPES.get(filetype.lower(), filetype)
        else:
            self.filetype = None

        label = QtWidgets.QLabel(self.label_text)
        if label_format:
            label.setFont(label_format)
        self.file_path = QtWidgets.QLineEdit()
        self.file_path.setFixedHeight(30)
        self.browse_button = QtWidgets.QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        self.browse_button.setMaximumWidth(90)
        self.browse_button.setFixedHeight(30)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(label, 0, 0, 1, 2)
        grid.addWidget(self.file_path, 1, 0, 1, 1)
        grid.addWidget(self.browse_button, 1, 1, 1, 1)
        self.setLayout(grid)

    def browse_file(self):
        """Open file dialog window to select file or folder.

        The specific dialog window opened is dependant on the
        arguments passed when initialising the class.
        """
        if self.directory:
            selected_file = QtWidgets.QFileDialog(self).getExistingDirectory(
                self, self.label_text
            )
        else:
            if self.multiple_files:  # for multiple files, separate with ' % '
                file_dialog = QtWidgets.QFileDialog(self)
                file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
                selected_file, _ = file_dialog.getOpenFileNames(
                    self, self.label_txt, None, self.filetype
                )
                selected_file = " % ".join(selected_file)
            else:
                selected_file, _ = QtWidgets.QFileDialog(self).getOpenFileName(
                    self, self.label_text, None, self.filetype
                )

        self.file_path.setText(selected_file)

    def get(self) -> Union[Path, str, None]:
        """Returns the path provided in the input box.

        Returns
        -------
        Union[Path, str, None]
            Converts the text to a Path object if `multiple_files`
            is False, otherwise returns a string with '%' separating the file
            paths. If the input box is blank, returns None.
        """
        if self.file_path.text().strip() == "":
            return None
        if self.multiple_files:
            return self.file_path.text()
        path = Path(self.file_path.text())
        if self.directory and not path.is_dir():
            raise NotADirectoryError(
                f"{self.label_text} doesn't exist (or isn't a folder): {path}"
            )
        if not self.directory and not path.is_file():
            raise FileNotFoundError(f"{self.label_text} doesn't exist: {path}")
        return path


class NumberInput(QtWidgets.QWidget):
    """Labelled number input spin box.

    Parameters
    ----------
    label_text : str
        The text for labelling the widget.
    value : Union[int, float]
        The default/starting value of the spin box.
    min_ : Union[int, float]
        The minimum value allowed.
    max_ : Union[int, float]
        The maximum value allowed.
    decimals : int, optional
        The number of decimal places allowed, by default 0
    step : int, optional
        The increment size when the up or down buttons
        are clicked, by default 1
    label_format: QtGui.QFont, optional
        The font of the label, by default None
    """

    def __init__(
        self,
        label_text: str,
        value: Union[int, float],
        min_: Union[int, float],
        max_: Union[int, float],
        decimals: int = 0,
        step: int = 1,
        label_format: QtGui.QFont = None,
    ):
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.decimals = int(decimals)
        self.label = QtWidgets.QLabel(label_text)
        if label_format:
            self.label.setFont(label_format)
        self.spin_box = QtWidgets.QDoubleSpinBox(
            minimum=min_, maximum=max_, decimals=decimals, singleStep=step, value=value
        )
        self.spin_box.setFixedHeight(30)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.label, 0, 0, 1, 1)
        grid.addWidget(self.spin_box, 0, 1, 1, 1)
        self.setLayout(grid)

    def get(self) -> Union[int, float]:
        """Return the number from the spin box.

        Returns
        -------
        Union[int, float]
            The number in the spin box as an integer
            if `decimals` is 0 and a float otherwise.
        """
        if self.decimals == 0:
            return int(self.spin_box.value())
        return float(self.spin_box.value())

    def disable(self):
        """Disable widget"""
        self.label.setDisabled(True)
        self.spin_box.setDisabled(True)

    def enable(self):
        """Enable widget"""
        self.label.setDisabled(False)
        self.spin_box.setDisabled(False)


class RadioButtons(QtWidgets.QWidget):
    """Labelled radio buttons widget.

    Parameters
    ----------
    label_text : str
        Text to be displayed in the widget label.
    button_names : List[str]
        Names of radio buttons.
    label_format : QtGui.QFont, optional
        The font of the label, by default None
    button_format : QtGui.QFont, optional
        The font of the button labels, by default None
    """

    def __init__(
        self,
        label_text: str,
        button_names: List[str],
        label_format: QtGui.QFont = None,
        button_format: QtGui.QFont = None,
    ):
        super().__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.buttons_names = button_names
        self.label = QtWidgets.QLabel(label_text)
        if label_format:
            self.label.setFont(label_format)
        self.buttons = []
        for button_name in button_names:
            self.buttons.append(QtWidgets.QRadioButton(button_name))

        grid = QtWidgets.QGridLayout()
        i = 0
        grid.addWidget(self.label, 0, i, 1, 1)
        for button in self.buttons:
            i += 1
            if button_format:
                button.setFont(button_format)
            grid.addWidget(button, 0, i, 1, 1)
        self.setLayout(grid)

    def get(self) -> List[bool]:
        """Get the state of the radio buttons.
        Returns
        -------
        save_state: List[bool]
            State if radio buttons
        """
        save_state = []
        for button in self.buttons:
            save_state.append(button.isChecked())
        return save_state

    def load(self, values: List[bool]):
        """Load state.

        Parameters
        ----------
        values : List[bool]
            State to load.
        """
        for index in range(len(self.buttons)):
            self.buttons[index].setChecked(values[index])

    def reset(self):
        """Resets the radio buttons so only the first button is checked."""
        for index in range(len(self.buttons)):
            if index == 0:
                self.buttons[index].setChecked(True)
            else:
                self.buttons[index].setChecked(False)

    def disable(self):
        """Disable widget"""
        self.label.setDisabled(True)
        for button in self.buttons:
            button.setDisabled.setDisabled(True)

    def enable(self):
        """Enable widget"""
        self.label.setDisabled(False)
        for button in self.buttons:
            button.setDisabled.setDisabled(False)
