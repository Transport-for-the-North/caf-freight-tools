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
            lines = f.readlines()
        try:
            intro_end = lines.index('## Profile Builder\n')
        except:
            intro_end = 0
        try:
            calcs_start = lines.index('### Zone Correspondence Calculations\n') + 1
            calcs_end = lines.index('#### Missing Zones\n')
        except:
            calcs_start = 0
            calcs_end = 0
        text = '[TOC]\n'
        # TODO MAKE IT SO CAN'T ALLOW EXTERNAL LINKS - webbrowser.open()??
        for line in (lines[intro_end:calcs_start] + lines[calcs_end:]):
            if not ((line.startswith('![')) | (line.startswith('<!'))):
                text += line
            if line == '### Zone Correspondence Calculations\n':
                text += 'See user guide for detailed information.\n'
        html = STYLESHEET
        html += markdown.markdown(text, extensions=['tables', 'toc'])
        self.webEngineView.setHtml(html)
        
        

    def closeEvent(self, event):
        """Closes the window"""
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()