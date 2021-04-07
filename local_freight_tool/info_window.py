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
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5 import QtWebEngineWidgets

# Other packages
import markdown

STYLESHEET = (
    r"<head>"
    r"<style>"
    r"body {"
    r"  background-color: White;"
    r"  font-family: Arial;"
    r"}"
    r"h1 {"
    r"  color: DarkBlue;"
    r"  font-size: 24px;"
    r"}"
    r"h2 {"
    r"  color: DarkBlue;"
    r"  font-size: 20px;"
    r"}"
    r"h3 {"
    r"  color: DarkBlue;"
    r"  font-size: 17px;"
    r"}"
    r"h4 {"
    r"  color: DarkBlue;"
    r"  font-size: 15px;"
    r"}"
    r"h5 {"
    r"  color: DarkBlue;"
    r"  font-size: 14px;"
    r"}"
    r"p {"
    r"  font-size: 14px;"
    r"}"
    r"li {"
    r"  font-size: 14px;"
    r"}"
    r"table {"
    r"  font-size: 14px;"
    r"  border: 1px solid black;"
    r"  padding: 10px;"
    r"  text-align: left;"
    r"}"
    r"a {"
    r"  color: black;"
    r"}"
    r"</style>"
    r"</head>"
    r"<body>"
)


class InfoWindow(QtWidgets.QWidget):
    """Local Freight Tool Information window.
    Parameters
    ----------
    QtWidgets : QWidget
        Base class for user interface objects.
    """

    def __init__(self, tier_converter, readme="README.md"):
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
        """Initialises UI"""

        self.setGeometry(500, 100, 800, 800)
        self.setWindowTitle("Local Freight Tool Information")
        self.setWindowIcon(QtGui.QIcon("icon.png"))

        # self.webEngineView = QWebEngineView()
        self.view = QtWebEngineWidgets.QWebEngineView()
        self.page = QtWebEngineWidgets.QWebEnginePage()
        self.loadPage()
        self.view.setPage(self.page)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        # vbox.addWidget(self.webEngineView)
        vbox.addWidget(self.view)

        self.setLayout(vbox)

        self.show()

    def loadPage(self):
        """Loads the readme as an HTML webpage for display with
        QWebEngineView.
        """
        with open(self.readme, "r") as f:
            lines = f.readlines()
        try:
            intro_end = lines.index("## Profile Builder\n")
        except:
            intro_end = 0
        try:
            calcs_start = lines.index("### Zone Correspondence Calculations\n") + 1
            calcs_end = lines.index("#### Missing Zones\n")
        except:
            calcs_start = 0
            calcs_end = 0
        text = "[TOC]\n"
        # TODO MAKE IT SO CAN'T ALLOW EXTERNAL LINKS - webbrowser.open()??
        for line in lines[intro_end:calcs_start] + lines[calcs_end:]:
            if not ((line.startswith("![")) | (line.startswith("<!"))):
                text += line
            if line == "### Zone Correspondence Calculations\n":
                text += "See user guide for detailed information.\n"
        html = STYLESHEET
        html += markdown.markdown(text, extensions=["tables", "toc"])
        self.page.setHtml(html)

    def closeEvent(self, event):
        """Closes the window"""
        close = Utilities.closeEvent(self, event)
