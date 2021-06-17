# -*- coding: utf-8 -*-
"""
    Module containing functionality for reading and pre-processing
    the LGV inputs which are used for multiple segments.
"""

##### IMPORTS #####
# Standard imports
import re
import pprint
import string
from pathlib import Path

# Third party imports
import pandas as pd

# Local imports
from .. import utilities, errors
from ..rezone import Rezone


##### CONSTANTS #####
HH_PROJECTIONS_HEADER = {"Area Description": str, "HHs": float}
"""Column names (and data types) for input CSV to `household_projections` function."""
BRES_HEADER = {
    "Area": str,
    "mnemonic": str,
    "A : Agriculture, forestry and fishing": float,
    "B : Mining and quarrying": float,
    "C : Manufacturing": float,
    "D : Electricity, gas, steam and air conditioning supply": float,
    "E : Water supply; sewerage, waste management and remediation activities": float,
    "F : Construction": float,
    "G : Wholesale and retail trade; repair of motor vehicles and motorcycles": float,
    "H : Transportation and storage": float,
    "I : Accommodation and food service activities": float,
    "J : Information and communication": float,
    "K : Financial and insurance activities": float,
    "L : Real estate activities": float,
    "M : Professional, scientific and technical activities": float,
    "N : Administrative and support service activities": float,
    "O : Public administration and defence; compulsory social security": float,
    "P : Education": float,
    "Q : Human health and social work activities": float,
    "R : Arts, entertainment and recreation": float,
    "S : Other service activities": float,
    (
        "T : Activities of households as employers;undifferentiated "
        "goods-and services-producing activities of households for own use"
    ): float,
    "U : Activities of extraterritorial organisations and bodies": float,
}
"""Column names (and data types) for input CSV to `filtered_bres` function."""


##### FUNCTIONS #####
def household_projections(path: Path, zone_lookup: Path) -> pd.DataFrame:
    """Reads the household projections CSV and converts to model zone system.

    CSV should contain two columns with headers as defined in
    `HH_PROJECTIONS_HEADER`.

    Parameters
    ----------
    path : Path
        Path to the household projections CSV.
    zone_lookup : Path
        Path to the zone correspondence CSV.

    Returns
    -------
    pd.DataFrame
        Household projections in the model zone system with columns
        'Zone' and 'Households'.
    """
    households = utilities.read_csv(
        path, "Household projections", columns=HH_PROJECTIONS_HEADER
    )
    lookup = Rezone.read(zone_lookup, None)
    cols = list(HH_PROJECTIONS_HEADER.keys())
    rezoned = Rezone.rezoneOD(households, lookup, dfCols=(cols[0],), rezoneCols=cols[1])
    rezoned.columns = ["Zone", "Households"]
    return rezoned


def filtered_bres(
    path: Path, zone_lookup: Path, aggregation: dict[str, tuple[str]]
) -> pd.DataFrame:
    """Read and filter the ONS BRES data CSV.

    The ONS BRES data should be a CSV containing metadata in the top
    9 rows then row 10 should contain the column names (see
    `BRES_HEADER` for names and expected data types).

    Parameters
    ----------
    path : Path
        Path to the CSV containing BRES data.
    zone_lookup : Path
        Path to zone correspondence CSV.
    aggregation : dict[str, tuple[str]]
        Dictionary containing names of any industry columns
        to aggregate together, the keys should be the name
        of the new column to create and the tuple should
        contain the column letters to aggregate together e.g.
        {"agg 1": ("I", "J", "K"), "agg 2": ("M", "N")}.

    Returns
    -------
    pd.DataFrame
        BRES data with industry columns aggregated and converted
        to the model zone system, contains 'Zone' column with zone
        numbers and then one column per item in `aggregation` (key
        is the column name).
    """

    def extract_letters(name: str) -> str:
        """Extracts the industry letter from the column name."""
        match = re.match(r"^([A-Z])\s:[\w,;\- ]+$", name)
        if match:
            return match.group(1)
        return name

    bres = utilities.read_csv(path, "BRES", columns=BRES_HEADER, skiprows=9)
    # Drop any completely empty columns and any rows with missing values
    bres.dropna(axis=1, how="all", inplace=True)
    bres.dropna(axis=0, how="any", inplace=True)
    bres.rename(columns=extract_letters, inplace=True)
    bres.rename(columns={"mnemonic": "Zone"})
    # Aggregate and rename industry columns
    include = ["Zone"]
    for agg, columns in aggregation.items():
        missing = [c for c in columns if c not in bres.columns]
        if missing:
            raise errors.MissingColumnsError("BRES", missing)
        bres[agg] = bres[columns].sum(axis=1)
        include.append(agg)
    bres = bres[include].copy()

    # Convert to model zone system
    lookup = Rezone.read(zone_lookup, None)
    rezoned = Rezone.rezoneOD(bres, lookup, dfCols=("Zone",), rezoneCols=include)
    return rezoned


def letters_range(start: str = "A", end: str = "Z") -> str:
    """Iterates through all uppercase letters from `start` to `end`, inclusive.

    Parameters
    ----------
    start : str, optional
        Letter to start the iteration from (inclusive), by default "A".
    end : str, optional
        Letter to end the iteration at (inclusive), by default "Z".

    Yields
    -------
    Iterator[str]
        Single uppercase ascii letter.
    """
    letters = string.ascii_uppercase
    s = letters.find(start.upper().strip())
    e = letters.find(end.upper().strip())
    for l in letters[s : e + 1]:
        yield l


# TODO Remove test code
if __name__ == "__main__":
    hh_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Household Projections\UK_HH_projections_2018-MSOA.csv"
    )
    zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\NTEM to NoHAM Lookup\NTEM_to_NoHAM_zone_correspondence-updated-20210617.csv"
    )
    hh_proj = household_projections(hh_path, zc_path)
    print(hh_proj.head())
    bres_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\BRES Data\GB_BRES_LSOA.csv"
    )
    bres_zc_path = Path()
    bres_aggregation = {
        "office": list(letters_range("I", "P")),
        "other": list(letters_range(end="H")) + list(letters_range("Q", "U")),
        "non-construction": list(letters_range(end="E"))
        + list(letters_range("G", "U")),
    }
    pprint.pp(bres_aggregation)
    bres_data = filtered_bres(bres_path, bres_zc_path, bres_aggregation)
    print(bres_data.head())
