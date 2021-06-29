# -*- coding: utf-8 -*-
"""
    Module containing the high level functions for running the LGV model.
"""

##### IMPORTS #####
# Standard imports
import configparser
from pathlib import Path

# Third party imports

# Local imports
from ..data_utils import DataPaths


##### CLASSES #####
class LGVConfig(configparser.ConfigParser):
    """Handles reading the config file for the LGV model.

    Parameters
    ----------
    path : Path
        Path to the config file to read.

    Raises
    ------
    configparser.NoSectionError
        If the config file doesn't contain the
        `SECTION`.
    """

    SECTION = "LGV File Paths"
    """Name of the required section."""
    OPTIONS = (
        "households data",
        "households zone correspondence",
        "bres data",
        "bres zone correspondence",
        "voa data",
        "voa zone correspondence",
        "lgv parameters",
    )
    """Names of the expected options."""
    household_paths: DataPaths = None
    """Paths for the households data and zone correspondence."""
    bres_paths: DataPaths = None
    """Paths for the BRES data and zone correspondence."""
    voa_paths: DataPaths = None
    """Paths for the VOA data and zone correspondence."""
    parameters_path: Path = None
    """Path to the LGV parameters Excel workbook."""

    def __init__(self, path: Path):
        """Initialises the class by reading the given file."""
        super().__init__()
        self.read(path)
        if not self.has_section(self.SECTION):
            raise configparser.NoSectionError(
                f"LGV config ({path.name}) doesn't contain section {self.SECTION!r}"
            )
        self.household_paths = DataPaths(
            "LGV Households",
            self.getpath(self.SECTION, self.OPTIONS[0]),
            self.getpath(self.SECTION, self.OPTIONS[1]),
        )
        self.bres_paths = DataPaths(
            "LGV BRES",
            self.getpath(self.SECTION, self.OPTIONS[2]),
            self.getpath(self.SECTION, self.OPTIONS[3]),
        )
        self.voa_paths = DataPaths(
            "LGV VOA",
            self.getpath(self.SECTION, self.OPTIONS[4]),
            self.getpath(self.SECTION, self.OPTIONS[5]),
        )
        self.parameters_path = self.getpath(self.SECTION, self.OPTIONS[6])

    def getpath(self, section: str, option: str, **kwargs) -> Path:
        """Gets the `option` from `section` and converts it to a Path object.

        Parameters
        ----------
        section : str
            Name of the config section.
        option : str
            Name of the config option.

        Returns
        -------
        Path
            Path object for the given `option`.
        """
        return Path(self.get(section, option, **kwargs))

    @classmethod
    def write_example(cls, path: Path):
        """Write example of the config file, with no values.

        Parameters
        ----------
        path : Path
            Path to write the example config file too,
            will be overwritten if already exists.
        """
        config = configparser.ConfigParser()
        config[cls.SECTION] = {k: "" for k in cls.OPTIONS}
        with open(path, "wt") as f:
            config.write(f)

    def __str__(self) -> str:
        return f"""
        {__name__}.{self.__class__.__name__}
            {self.household_paths=}
            {self.bres_paths=}
            {self.voa_paths=}
            {self.parameters_path=}
        """
