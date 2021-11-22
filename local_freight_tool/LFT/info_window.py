"""
GUI to render README.md when clicking the Info button from main menu.

The introduction, images and zone correspondence calculations are removed.
"""

##### IMPORTS #####
# Standard imports


# Third party imports
import markdown
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5 import QtWebEngineWidgets

# Local imports
from .utilities import Utilities
from .data_utils import local_path


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
    r"td, th {"
    r"  border-left: 1px solid grey;"
    r"  border-right: 1px solid grey;"
    r"  padding: 10px;"
    r"}"
    r"th {"
    r"  border-bottom: 2px solid black"
    r"}"
    r"table {"
    r"  font-size: 14px;"
    r"  border: 2px solid black;"
    r"  text-align: left;"
    r"  border-collapse: collapse;"
    r"}"
    r"a {"
    r"  color: black;"
    r"}"
    r"</style>"
    r"</head>"
    r"<body>"
)
"""HTML stylesheet for display in the info window"""


class InfoWindow(QtWidgets.QWidget):
    """Local Freight Tool Information window.
    Parameters
    ----------
    QtWidgets : QWidget
        Base class for user interface objects.
    """

    def __init__(
        self,
        tier_converter,
        readme="README.md",
        include=[
            (
                "## 0: Combine Point and Polygon Shapefiles\n",
                "### Zone Correspondence Calculations\n",
            ),
            ("#### Missing Zones\n", "end"),
        ],
    ):
        """Initialises class
        Parameters
        ----------
        tier_converter : Class
            Tier converter class in tc_main_menu
        readme : string
            Readme filename
        include : list, optional
            List of tuples with start and end lines as strings to include in
            info window. Default is everything is included except the
            Introduction and Zone Correspondence Calculations.
        """
        super().__init__()
        self.tier_converter = tier_converter
        self.readme = local_path(readme)
        self.include = include
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
        starts = []
        ends = []
        for elements in self.include:
            if elements[0] == "start":
                starts.append(0)
            else:
                try:
                    starts.append(lines.index(elements[0]))
                except:
                    starts.append(0)
            if elements[1] == "end":
                ends.append(len(lines))
            else:
                try:
                    ends.append(lines.index(elements[1]))
                except:
                    ends.append(len(lines))
        include_lines = []
        for i in range(len(starts)):
            include_lines += lines[starts[i] : ends[i]]
        text = "[TOC]\n"
        for line in include_lines:
            if not ((line.startswith("![")) | (line.startswith("<!"))):
                text += line
            if line == "### Zone Correspondence Calculations\n":
                text += "See user guide for detailed information.\n"
        html = STYLESHEET
        html += markdown.markdown(
            text,
            extensions=[
                "markdown.extensions.tables",
                "markdown.extensions.toc",
            ],
        )
        self.page.setHtml(html)

    def closeEvent(self, event):
        """Closes the window"""
        close = Utilities.closeEvent(self, event)
