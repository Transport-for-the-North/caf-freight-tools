# -*- coding: utf-8 -*-
"""
    Module containing utility functions related to reading input
    data and storing paths.
"""

##### IMPORTS #####
# Standard imports
from dataclasses import dataclass
from pathlib import Path

# Third party imports

# Local imports
from .utilities import check_file_path


##### CLASSES #####
@dataclass
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
    path: Path
    zc_path: Path

    def __post_init__(self):
        """Check that both paths given exist."""
        for nm, p in (("data", self.path), ("zone correspondence", self.zc_path)):
            check_file_path(p, f"{self.name} {nm}")
