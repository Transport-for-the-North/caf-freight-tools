# -*- coding: utf-8 -*-
"""
    Module containing utility functions related to reading input
    data and storing paths.
"""

##### IMPORTS #####
# Standard imports
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Union

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


##### FUNCTIONS #####
def local_path(path: Union[Path, str]) -> Path:
    """Check if running from pyinstaller bundle and update path.

    Updates path by prepending `sys._MEIPASS` only if running
    within pyinstaller bundle.

    Parameters
    ----------
    path : Union[Path, str]
        Path to the local data file.

    Returns
    -------
    Path
        Path with `sys._MEIPASS` prepended if running
        from pyinstaller bundle, otherwise converted
        to Path object and return original path.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / path
    return Path(path)
