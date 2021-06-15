# -*- coding: utf-8 -*-
"""
    Module for checking that the correct Python packages have been installed.
"""

##### IMPORTS #####
# Standard imports
import sys
import re
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

# Third party imports
import yaml
import packaging.version
import numpy as np
import pandas as pd
import openpyxl
import geopandas as gpd
import jinja2
import markdown
from PyQt5.Qt import PYQT_VERSION_STR


##### CLASSES #####
class PackageChecker:
    """Class which compares installed package versions against environment file.

    Parameters
    ----------
    env_path : Path, optional
        Path to the environment YAML file, by
        default None uses `DEFAULT_FILE`.
    """

    DEFAULT_FILE = Path("environment.yml")

    def __init__(self, env_path: Path = None):
        self._versions = None
        self._expected = None
        self.env_path = self.DEFAULT_FILE if env_path is None else Path(env_path)
        self.env_list = self.read_environment()

    def read_environment(self) -> List[str]:
        """Read the environment file and extract the dependencies list.

        Returns
        -------
        List[str]
            List of packages and their version as strings
            e.g. python>=3.9

        Raises
        ------
        FileNotFoundError
            If the environment file doesn't exist.
        yaml.YAMLError
            If there is a problem parsing the YAML file.
        ValueError
            If there is no dependency information in the
            environment file.
        """
        if not self.env_path.exists():
            raise FileNotFoundError(f"Environment file doesn't exist - {self.env_path}")
        with open(self.env_path, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error reading environment file: {e}") from e
        deps = data.get("dependencies")
        if deps is None:
            raise ValueError(
                "Dependency information is missing from the environment file"
            )
        return deps

    def _parse_expected(self) -> Dict[str, Tuple[str, packaging.version.Version]]:
        """Parse the list of dependencies and convert to `Version` objects.

        Returns
        -------
        Dict[str, Tuple[str, packaging.version.Version]]
            Dictionary containing names of all expected packages (keys)
            and tuples which contain string representation of the version
            comparison, e.g. '>=', and the version number as a `Version`
            object.
        """
        pattern = (
            r"(\w+)"  # package name
            # optional comparator and version number
            r"(?:([>=<]{1,2})"  # comparator
            r"(\d+(?:\.\d+){0,2}))?"  # version number string
        )
        expected_versions = {}
        invalid = []
        for s in self.env_list:
            match = re.match(pattern, s)
            if match is None:
                invalid.append(s)
            else:
                if match.group(3) is None:
                    ver = None
                else:
                    ver = packaging.version.parse(match.group(3))
                expected_versions[match.group(1)] = (match.group(2), ver)
        return expected_versions

    @property
    def expected(self) -> Dict[str, Tuple[str, packaging.version.Version]]:
        """Expected package versions.

        Returns
        -------
        Dict[str, Tuple[str, packaging.version.Version]]
            Dictionary containing names of all expected packages (keys)
            and tuples which contain string representation of the version
            comparison, e.g. '>=', and the version number as a `Version`
            object.
        """
        if self._expected is None:
            self._expected = self._parse_expected()
        return self._expected

    @property
    def versions(self) -> Dict[str, packaging.version.Version]:
        """Gets the installed version of all required packages.

        Returns
        -------
        Dict[str, packaging.version.Version]
            Dictionary containing the package name (key)
            and the installed version as a `Version` object.
        """
        if self._versions is None:
            self._versions = {
                "python": sys.version.split("|")[0].strip(),
                "pyqt": PYQT_VERSION_STR,
                "openpyxl": openpyxl.__version__,
                "pandas": pd.__version__,
                "geopandas": gpd.__version__,
                "jinja2": jinja2.__version__,
                "markdown": markdown.__version__,
                "numpy": np.__version__,
                "packaging": packaging.__version__,
                "pyyaml": yaml.__version__,
            }
        return self._versions

    def check_versions(self):
        """Checks the installed package `versions` against the `expected`.

        Raises
        ------
        ImportError
            If any of the installed packages aren't the correct
            version.

        Warns
        -----
        UserWarning
            If the installed package version cannot be found for
            an expected package.
        """
        incorrect = []
        for k, (comp, exp) in self.expected.items():
            ver = self.versions.get(k)
            if ver is None:
                warnings.warn(
                    f"'{k}' version should be {comp}{exp} but is unknown", UserWarning
                )
                continue
            if exp is None:
                continue

            ver = packaging.version.parse(ver)
            msg = f"'{k}' version should be {comp}{exp} but instead is {ver}"
            if comp == "=":
                if exp != ver:
                    incorrect.append(msg)
            elif comp == ">=":
                if ver < exp:
                    incorrect.append(msg)
            elif comp == "<=":
                if ver > exp:
                    incorrect.append(msg)
            else:
                incorrect.append(f"unknown version comparison ({comp}) for {k}")

        if incorrect:
            raise ImportError("\n".join(["package versions"] + incorrect))
