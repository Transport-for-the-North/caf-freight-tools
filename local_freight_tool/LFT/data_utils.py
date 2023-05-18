# -*- coding: utf-8 -*-
"""
    Module containing utility functions related to reading input
    data and storing paths.
"""

##### IMPORTS #####
# Standard imports

# Third party imports
from pydantic import dataclasses, types

# Local imports


##### CLASSES #####
@dataclasses.dataclass
class DataPaths:
    """Dataclass for storing path to data source and zone correspondence.

    Parameters
    ----------
    name : str
        Name of the data source.
    path : Path
        Path to the data source file.
    zc_path : Path
        Path to the relevant zone correspondence file.

    Raises
    ------
    FileNotFoundError
        If the data path or zone correspondence files don't exist.
    """

    name: str
    path: types.FilePath
    zc_path: types.FilePath
