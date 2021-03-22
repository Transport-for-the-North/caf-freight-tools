# -*- coding: utf-8 -*-
"""

Created on: Fri Feb 28 12:25:27 2020
Updated on: Tues Mar 16 13:53:15 2021

Original author: racs
Last update made by: cara

File purpose:
Produces profile_selection.csv that contains all information required to build
time period specific O-D trip matrices.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QCheckBox
import numpy as np
import pandas as pd
from utilities import info_window, Utilities
import textwrap
from info_window import InfoWindow


class Profile_Builder(QtWidgets.QWidget):
    """Profile Builder user interface, which enables the user to create
    Profile_Selection.csv for use in module 4.

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
        TIME_PERIODS = ["AM", "PM", "IP", "OP"]

        self.setGeometry(500, 200, 555, 70 + 24 * (10 + 14))
        self.setWindowTitle("Profile Builder")
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setText("Profile Builder")
        labelB.setGeometry(10, 5, 700, 30)

        label = QtWidgets.QLabel(self)
        label.setText(
            "Select options below to build time period specific profile, then press run. "
        )
        label.setGeometry(10, 25, 700, 30)

        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText("Info")
        Info_button.setGeometry(450, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)

        self.add_column_header(10, 50, "Name:")
        self.add_column_header(170, 50, "Day:")
        self.add_column_header(400, 50, "Hour start:")
        self.add_column_header(480, 50, "Hour end:")

        # Now set up the user input fields
        self.names = []
        self.days = []
        self.hr_starts = []
        self.hr_ends = []

        for i in range(7):

            self.names.append(QtWidgets.QLineEdit(self))
            self.names[i].setGeometry(10, 80 + 60 * i, 150, 30)
            self.hr_starts.append(QtWidgets.QComboBox(self))
            self.hr_starts[i].setGeometry(400, 80 + 60 * i, 60, 30)
            self.hr_starts[i].addItems([str(i) for i in range(24)])
            self.hr_ends.append(QtWidgets.QComboBox(self))
            self.hr_ends[i].setGeometry(480, 80 + 60 * i, 60, 30)
            self.hr_ends[i].addItems([str(i) for i in range(24)])

            if i == 0:
                self.names[i].setPlaceholderText(TIME_PERIODS[i])
                self.hr_starts[i].setCurrentIndex(7)
                self.hr_ends[i].setCurrentIndex(10)

            if i == 1:
                self.names[i].setPlaceholderText(TIME_PERIODS[i])
                self.hr_starts[i].setCurrentIndex(16)
                self.hr_ends[i].setCurrentIndex(19)
            if i == 2:
                self.names[i].setPlaceholderText(TIME_PERIODS[i])
                self.hr_starts[i].setCurrentIndex(10)
                self.hr_ends[i].setCurrentIndex(16)

            if i == 3:
                self.names[i].setPlaceholderText(TIME_PERIODS[i])
                self.hr_starts[i].setCurrentIndex(19)
                self.hr_ends[i].setCurrentIndex(0)

        self.choices = []
        for i in range(7):
            choice = []
            for j, DayOfWeek in enumerate(["M", "T", "W", "T", "F", "S", "S"]):
                day = QCheckBox(DayOfWeek, self)
                day.move(170 + 30 * (j), 75 + 60 * i)
                day.resize(32, 40)
                if (j == 0) or (j == 1) or (j == 2) or (j == 3) or (j == 4):
                    day.setChecked(True)
                choice.append(day)
            self.choices.append(choice)

        # Months
        self.add_column_header(10, 20 * (10 + 14) - 5, "Months:")

        self.months = []
        for i, month_name in enumerate(
            [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
        ):
            month = QCheckBox(month_name, self)
            month.move(10 + 45 * (i), 10 + 20 * (10 + 14))
            month.resize(50, 40)
            self.months.append(month)

        # Create output folder input
        self.outpath = Utilities.add_file_selection(
            self,
            20 + 22 * (10 + 14),
            "Select the output directory:",
            directory=True,
            box_width=430,
        )

        # Create a push button to set off the tier converter process
        go_button = QtWidgets.QPushButton(self)
        go_button.setText("Save Selection")
        go_button.setGeometry(120, 20 + 24 * (10 + 14), 420, 30)
        go_button.clicked.connect(self.go_button_clicked)

        # Create a push button to move back to the set up window
        back_button = QtWidgets.QPushButton(self)
        back_button.setText("Back")
        back_button.setGeometry(10, 20 + 24 * (10 + 14), 100, 30)
        back_button.clicked.connect(self.back_button_clicked)

        self.show()

    def add_column_header(self, x_position, y_position, header_txt):
        """Adds a label widget to the GUI.

        Parameters
        ----------
        x_position : int
            x position for widget
        y_position : int
            y position for widget
        header_txt : str
            text to display
        """
        label = QtWidgets.QLabel(self)
        label.setText(header_txt)
        label.setGeometry(x_position, y_position, 200, 30)

    def go_button_clicked(self):
        """Creates Profile_Selection.csv from selections."""
        if not self.outpath.text().strip():
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Profile Builder")
            alert.setGeometry(600, 600, 200, 200)
            alert.setText("You must specify an output directory.")
            alert.show()
        else:
            months = []
            for i, month in enumerate(self.months):
                if month.isChecked():
                    months.append(i)

            self.FullMatrix = []
            for choice in self.choices:
                RowMatrix = []
                for day in choice:
                    if day.checkState() == 2:
                        day2 = 1
                    else:
                        day2 = 0
                    RowMatrix.append(day2)
                self.FullMatrix.append(RowMatrix)

            #    Process the FullMatrix to convert to days of the week
            self.NewFullMatrix = []
            for RowMatrix in self.FullMatrix:
                NewRowMatrix = []
                for k in range(7):
                    if RowMatrix[k] == 1:
                        number = k
                    else:
                        number = None
                    if number != None:
                        NewRowMatrix.append(number)

                self.NewFullMatrix.append(NewRowMatrix)

            # Now let's generate the tp list of dictionaries
            self.tp = []  # initialise the list of lists

            for i in range(7):
                selection = {}
                selection["name"] = self.names[i].text()
                selection["days"] = self.NewFullMatrix[i]
                selection["hr_start"] = self.hr_starts[i].currentText()
                selection["hr_end"] = self.hr_ends[i].currentText()
                selection["months"] = months

                self.tp.append(selection)

            df = pd.DataFrame(self.tp)
            df["name"].replace("", np.nan, inplace=True)
            df.dropna().to_csv(
                self.outpath.text().strip() + "/Profile_Selection.csv",
                index=False,
            )

            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Profile Builder")
            alert.setGeometry(600, 600, 200, 200)
            alert.setText("Building Selected Profiles Complete")
            alert.show()

    def back_button_clicked(self):
        """Returns to tier converter main menu"""
        self.tier_converter.show()
        self.hide()

        # Function which asks the user if they really want to trigger sys.exit()

    def closeEvent(self, event):
        """Closes the profile builder window."""
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()

    @pyqtSlot()
    def on_click_Info(self):
        self.selections_window = InfoWindow(self, 'README.md')
        self.selections_window.show()