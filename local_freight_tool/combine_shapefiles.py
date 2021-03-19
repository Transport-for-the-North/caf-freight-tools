# -*- coding: utf-8 -*-
"""

Created on: Wed Feb 24 16:59 2021

Original author: CaraLynch

File purpose:
GUI to enable user to combine the polygon and centroid GBFM shapefiles, such
that the point zones in the centroid shapefile are transformed into polygons
by adding a small buffer radius.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QLineEdit, QDoubleSpinBox

# User-defined imports
from utilities import Utilities, info_window, progress_window
from text_info import Combine_Shapefiles_Text

# Other packages
import os
from pathlib import Path
import traceback
import textwrap
import pandas as pd
import geopandas as gpd


class CombineShapefiles(QtWidgets.QWidget):
    """Combine Shapefiles user interface.

    Parameters
    ----------
    QtWidgets : QWidget
        Base class for user interface objects.
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
        """Initialises UI
        """
        self.setGeometry(500, 200, 500, 330)
        self.setWindowTitle("Combine Shapefiles")
        self.setWindowIcon(QtGui.QIcon("icon.jpg"))

        labelD = QtWidgets.QLabel(self)
        labelD.setText("Combine GBFM Shapefiles")
        labelD.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelD.setGeometry(10, 10, 700, 30)

        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText("Info")
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)

        spacing = 60
        y = 70

        # Add file path selection fields
        self.gbfm_polygons = Utilities.add_file_selection(
            self,
            y,
            "Choose GBFM Polygons shapefile:",
            directory=False,
            filetype="Shapefile (*.shp *.SHP)",
        )
        y += spacing
        self.gbfm_centroids = Utilities.add_file_selection(
            self,
            y,
            "Choose GBFM Centroids shapefile:",
            directory=False,
            filetype="Shapefile (*.shp *.SHP)",
        )
        y += spacing
        self.outpath = Utilities.add_file_selection(
            self, y, "Choose output directory:", directory=True
        )
        # Add buffer radius spinbox
        y += 40
        self.buffer_label = QtWidgets.QLabel(self)
        self.buffer_label.setText("Buffer radius:")
        self.buffer_label.setGeometry(10, y, 80, 30)
        self.buffer_label.show()

        self.buffer_box = QDoubleSpinBox(
            self,
            suffix="m",
            decimals=2,
            maximum=10,
            minimum=0.01,
            singleStep=1,
            value=1,
        )
        self.buffer_box.move(85, y + 5)
        self.buffer_box.resize(60, 25)
        self.buffer_box.show()

        y += spacing
        run_button = QtWidgets.QPushButton(self)
        run_button.setText("Run")
        run_button.setGeometry(390, y, 100, 30)
        run_button.clicked.connect(self.run_button_clicked)

        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText("Back")
        back_button.setGeometry(10, y, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)

        self.show()

    def back_button_clicked(self):
        """Returns to tier converter main menu
        """
        self.tier_converter.show()
        self.hide()

    def closeEvent(self, event):
        """Closes the window"""
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()

    def run_button_clicked(self):
        """Initialises process once run button is clicked."""
        if (
            self.gbfm_polygons.text().strip() == ""
            or self.gbfm_centroids.text().strip() == ""
        ):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Combine GBFM Shapefiles")
            alert.setText("Error: you must specify both file paths first")
            alert.show()
        elif self.outpath.text().strip() == "":
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle("Combine GBFM Shapefiles")
            alert.setText("Error: you must specify an output folder")
            alert.show()
        else:
            # Start a progress window
            self.progress = progress_window(
                "Combine GBFM Shapefiles", self.tier_converter
            )
            self.hide()

            # Call the main process
            self.worker = background_thread(self)
            self.worker.start()

    @pyqtSlot()
    def on_click_Info(self):
        """Displays info window
        """
        self.progress = info_window("Combine GBFM Shapefiles")
        self.progress_label = self.progress.label
        self.progress_labelA = self.progress.labelA
        dedented_text = textwrap.dedent(Combine_Shapefiles_Text)
        line = textwrap.fill(dedented_text, width=140)
        self.progress_label.setText(line)
        self.progress_label.move(10, 40)
        self.progress_labelA.setText("Combine GBFM Shapefiles")
        self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.progress.show()

        def closeEvent(self, event):
            """Closes info window
            """
            Utilities.closeEvent(self, event)


class background_thread(QThread):
    """Thread which runs the combine shapefiles process

    Parameters
    ----------
    QThread
    """
    def __init__(self, CombineShapefiles):
        """Initialises class

        Parameters
        ----------
        CombineShapefiles : Class
            GUI Class
        """
        QThread.__init__(self)

        self.progress_label = CombineShapefiles.progress.label
        self.gbfm_polygons_path = Path(CombineShapefiles.gbfm_polygons.text())
        self.gbfm_centroids_path = Path(CombineShapefiles.gbfm_centroids.text())
        self.outpath = Path(CombineShapefiles.outpath.text())
        self.buffer = CombineShapefiles.buffer_box.value()

    def run(self):
        """Runs combine shapefiles process
        """
        zone_ID = "UniqueID"

        try:
            self.progress_label.setText("Reading in the shapefiles")
            gbfm_polygons = gpd.read_file(self.gbfm_polygons_path)
            gbfm_centroids = gpd.read_file(self.gbfm_centroids_path)

            # centroids file has float UniqueID, change to int
            gbfm_centroids[zone_ID] = gbfm_centroids[zone_ID].astype(int)

            self.progress_label.setText("Finding point zones")
            gbfm_points = gbfm_centroids.loc[
                ~gbfm_centroids[zone_ID].isin(gbfm_polygons[zone_ID])
            ]
            if gbfm_points.empty:
                self.progress_label.setText(
                    "No zones found in centroids file which aren't already in polygon "
                    "file, so no output file created. You may exit the program"
                )

            self.progress_label.setText("Adding buffer to points")
            gbfm_points.geometry = gbfm_points.buffer(self.buffer)

            # make sure source is clear in shapefiles
            gbfm_points.loc[:, "source"] = "centroid"
            gbfm_polygons.loc[:, "source"] = "polygon"

            self.progress_label.setText("Combining shapefiles")
            shared_columns = gbfm_points.columns[
                gbfm_points.columns.isin(gbfm_polygons.columns)
            ]
            combined_shapefile = gbfm_polygons.append(gbfm_points[shared_columns])

            out_name = self.outpath / (self.gbfm_polygons_path.stem + "-combined.shp")

            self.progress_label.setText(f"Saving to {out_name}")
            combined_shapefile.to_file(out_name)

            self.progress_label.setText(
                "Combining shapefiles process complete. You may exit the program."
            )
        except Exception as e:
            self.progress_label.setText(
                f"{e.__class__.__name__}: {e!s}.\nYou may exit the program."
            )
            traceback.print_exc()
