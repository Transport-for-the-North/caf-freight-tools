"""
    Module to calculate the productions and attractions for the LGV
    commuting segment in the model zone system.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path
from itertools import chain

# Third party imports
import pandas as pd

# Local imports
from .. import utilities, errors
from . import lgv_inputs


##### CLASSES #####
class CommuteTripProductionsAttractions:
    """Functionality for generating the LGV commuting segment trip productions
    and attractions.

    Parameters
    ----------
    inputs : dict
        Dictionary of paths to all required inputs. Must contain:
        - "commuting tables": Path to XLSX containing sheets and column names
        as defined in `COMMUTING_INPUTS_SHEET_HEADERS`.
        - "household projectons": Path to the CSV containing the household
        projections data by MSOA.
        - "BRES": Path to the CSV containing the BRES data by LSOA.
        - "QS606EW": Path to CSV containing QS606EW data by LSOA. Must have
        column names as defined in `QS606_HEADERS`.
        - "QS606SC": Path to CSV containing QS606UK Scottish data by datazone.
        Must have column names as defined in `QS606_HEADERS`.
        - "SC&W dwellings": Path to CSV containing 2017 and 2018 dwelling
        numbers for Wales and Scotland by LAD with columns as defined in
        `SC_W_DWELLINGS_HEADER`.
        - "E dwellings": Path to XLSX containing MHCLGC Live Table 123
        dwellings data for England by LAD, with sheets and column names as
        defined in `E_DWELLINGS_SHEET_HEADER`.
        - "NDR floorspace": Path to CSV containing NDR business floorspace
        data by LSOA from tables FS2.0, FS3.0, FS4.0 and FS5.0, with column
        names as defined in `BUSINESS_FLOORSPACE_HEADER`.
        - "LSOA lookup": Path to the zone correspondence CSV for converting
        from LSOA and Scottish datazone to the model zone system.
        - "MSOA lookup": Path to the zone correpondence file to convert
        household data to the model zone system.
        - "LAD lookup": Path to LAD to model zone system zone correspondence
        CSV.

    Raises
    ------

    See Also
    --------
    .lgv_inputs: Module with functions for reading some inputs.
    """
    INPUT_KEYS = {
        "commuting tables": ".xlsx",
        "household projectons": ".csv",
        "BRES": ".csv",
        "QS606EW": ".csv",
        "QS606SC": ".csv",
        "SC&W dwellings": ".csv",
        "E dwellings": ".xlsx",
        "NDR floorspace": ".csv",
        "LSOA lookup": ".csv",
        "MSOA lookup": ".csv",
        "LAD lookup": ".csv"
    }

    COMMUTING_INPUTS_SHEET_HEADERS = {
        "Parameters": {"Parameter": str, "Value": float},
        "Commute trips by main usage": {"Main usage": str, "Trips": float},
        "Commute trips by land use": {"Land use at trip end": str, "Trips": float},
        "Commute VOA property weightings": {
            "Weight": str,
            "SCat code": int,
            "Primary Desc Code": str,
        },
    }
    BRES_AGGREGATION = {
        "Non-Construction": [
            i
            for i in chain(
                lgv_inputs.letters_range(end="E"),
                lgv_inputs.letters_range(start="G", end="S"),
            )
        ]
    }
    QS606_HEADER = {
        "mnemonic": str,
        "All categories: Occupation": float,
        "51. Skilled agricultural and related trades": float,
        "52. Skilled metal, electrical and electronic trades": float,
        "53. Skilled construction and building trades": float,
    }
    QS606_HEADERS = {}
    S8_CATEGORIES = {
        "EW": "821. Road Transport Drivers",
        "UK": "82. Transport and mobile machine drivers and operatives",
    }
    for key in S8_CATEGORIES:
        QS606_HEADERS[key] = QS606_HEADER.copy()
        QS606_HEADERS[key][S8_CATEGORIES[key]] = float

    SC_W_DWELLINGS_HEADER = {
        "UniqueID": str,
        2017: int,
        2018: int
    }

    E_DWELLINGS_SHEET_HEADER = {
        "2018-19": {
            "Current\nONS code": str,
            "Demolitions": int,
            "Net Additions": int
        }
    }

    BUSINESS_FLOORSPACE_HEADER = {
        "AREA_CODE": str
    }
    for column_start in ["Floorspace_2017-18_", "Floorspace_2018-19_"]:
        for category in ["Retail", "Office", "Industral", "Other"]:
            BUSINESS_FLOORSPACE_HEADER[column_start + category] = float
    
    def __init__(self, input_paths: dict):
        """Initialise class by checking all input paths are in input dict and
        all input files exist"""
        missing = self.INPUT_KEYS.keys() - input_paths.keys()
        if missing:
            raise errors.MissingInputsError(missing)
        self.paths = self._check_paths(input_paths)

        # Initialise instance variables defined later
        self.params = None
        self.voa_weightings = None
        self.commute_trip_tables = None

    def _check_paths(self, input_paths):
        """Checks the input file paths are of expected type.

        Parameters
        ----------
        input_paths : Dict
            Dictionary of paths to all required inputs, with keys as specified
            in `INPUT_KEYS`.

        Returns
        -------
        paths: Dict
            Dictionary of paths to all required inputs.
        """
        paths = {}
        for key in input_paths:
            if self.INPUT_KEYS[key] == ".csv":
                paths[key] = utilities.check_file_path(input_paths[key], key, self.INPUT_KEYS[key], ".txt", return_path=True)
            else:
                paths[key] = utilities.check_file_path(input_paths[key], key, self.INPUT_KEYS[key], return_path=True)
        return paths
    
    @property
    def inputs_summary(self) -> pd.DataFrame:
        """Returns a summary table of class inputs.

        Returns
        -------
        pd.DataFrame
            Summary of inputs
        """
        return pd.DataFrame.from_dict(self.paths, orient="index", columns=["Path"])
    
    def read(self):
        """Read the input data and perform necessary conversions and rezoning.
        """
        self._read_commute_tables()

    def _read_commute_tables(self):
        """Read in commuting tables input XLSX.
        """
        commute_tables = utilities.read_multi_sheets(
            self.paths["commuting tables"],
            sheets=self.COMMUTING_INPUTS_SHEET_HEADERS)
        self.params = utilities.to_dict(
            commute_tables["Parameters"],
            "Parameter",
            ("Value", float))
        self.voa_weightings = utilities.to_dict(
            commute_tables["Commute VOA property weightings"],
            "SCat code",
            "Weight"
        )
        
        self.commute_trip_tables = {}
        for key in commute_tables.keys() - set(('Parameters', 'Commute VOA property weightings')):
            self.commute_trip_tables[key] = commute_tables[key]
