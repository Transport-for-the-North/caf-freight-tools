"""
Created on: Monday Feb 15 2021

Original author: CaraLynch

File purpose:
Contains all matrix utility functions required for the tool, including 
producing a summary, rezoning a matrix, adding and factoring matrices, filling
missing zones, removing external-external trips, and converting to UFM.
"""

# User-defined imports
import zone_correspondence as zcorr

# Other packages
import geopandas as gpd
import pandas as pd

class ODMatrix:
    """O-D matrix class for creating O-D matrix objects and performing
    operations with them.
    """
    def __init__(self, filepath, columns):
        self.