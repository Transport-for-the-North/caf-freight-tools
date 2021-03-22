"""

File purpose:
GUI to render README.md when clicking the Info button from main menu.

Created on: Mon Mar 22 2021

Original author: CaraLynch

"""


# User-defined imports
from utilities import Utilities

# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot, QEventLoop
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Other packages
import os
from pathlib import Path
import markdown


class InfoWindow(QtWidgets.QWidget):
    """Local Freight Tool Information window.

    Parameters
    ----------
    QtWidgets : QWidget
        Base class for user interface objects.
    """
    def __init__(self, tier_converter, readme='README.md'):
        """Initialises class

        Parameters
        ----------
        tier_converter : Class
            Tier converter class in tc_main_menu
        """
        super().__init__()
        self.tier_converter = tier_converter
        self.readme = readme
        self.initUI()

    def initUI(self):
        """Initialises UI
        """

        self.setGeometry(500, 100, 700, 800)
        self.setWindowTitle("Local Freight Tool Information")
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        self.webEngineView = QWebEngineView()
        self.loadPage()

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.webEngineView)

        self.setLayout(vbox)

        self.show()

    def loadPage(self):
        with open(self.readme, 'r') as f:
            text = f.read()
            html = markdown.markdown(text, extensions=['toc'])
            # TODO see if can add css to head
            # TODO see if can set scrollbar position to specific line position
            self.webEngineView.setHtml(html)

    def closeEvent(self, event):
        """Closes the window"""
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()