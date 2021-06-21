# -*- coding: utf-8 -*-
"""
    Module containing functionality for reading and pre-processing
    the LGV inputs which are used for multiple segments.
"""

##### IMPORTS #####
# Standard imports
import re
import string
from pathlib import Path
from typing import Sequence

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
VOA_RATINGS_LIST_COLUMNS = {
    "entry_number": int,
    "billing_authority_code": str,
    "NDR_code": str,
    "BA_ref": str,
    "description_code": str,
    "description": str,
    "UARN": str,
    "property_identifier": str,
    "firms_name": str,
    "num_or_name": str,
    "street": str,
    "town": str,
    "post_district": str,
    "county": str,
    "postcode": str,
    "eff_date": str,
    "composite_indicator": str,
    "rateable_value": float,
    "settlement_code": str,
    "assessment_ref": str,
    "alteration_date": str,
    "scat_code": str,
    "sub_street_3": str,
    "sub_street_2": str,
    "sub_street_1": str,
    "case_num": str,
    "from_date": str,
    "to_date": str,
    "unknown": str,
}
"""Column names and types for the VOA ratings list data."""
VOA_RATINGS_LIST_INCLUDE = [
    "entry_number",
    "description_code",
    "description",
    "UARN",
    "property_identifier",
    "postcode",
    "rateable_value",
    "scat_code",
]
"""Column names to read from the VOA ratings list file."""

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

    bres = utilities.read_csv(path, "BRES", columns=BRES_HEADER, skiprows=8)
    # Drop any completely empty columns and any rows with missing values
    bres.dropna(axis=1, how="all", inplace=True)
    bres.dropna(axis=0, how="any", inplace=True)
    bres.rename(columns=extract_letters, inplace=True)
    ZONE_COL = "Zone"
    bres.rename(columns={"mnemonic": ZONE_COL}, inplace=True)
    # Aggregate and rename industry columns
    include = [ZONE_COL]
    for agg, columns in aggregation.items():
        missing = [c for c in columns if c not in bres.columns]
        if missing:
            raise errors.MissingColumnsError("BRES", missing)
        bres[agg] = bres[list(columns)].sum(axis=1)
        include.append(agg)
    bres = bres[include].copy()

    # Convert to model zone system
    include.remove(ZONE_COL)
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


def voa_ratings_list(
    path: Path, scat_codes: Sequence[int], zone_lookup: Path
) -> pd.DataFrame:
    """Reads VOA NDR ratings list entries file and filters based on `scat_codes`.

    The input file should be a text file (.csv or .txt) with no header
    row and uses '*' to separate columns.

    Parameters
    ----------
    path : Path
        Path to the VOA ratings list file.
    scat_codes : Sequence[int]
        List of SCAT code numbers to include in returned DataFrame.
    zone_lookup : Path
        Path to the lookup between the VOA postcodes and the model
        zone system, expects 3 columns containing postcode, model
        zone number and splitting factor information in that order.

    Returns
    -------
    pd.DataFrame
        Rateable value for each model zone contains columns:
        'zone' and 'rateable_value'.

    See Also
    --------
    VOA_RATINGS_LIST_COLUMNS : Column names and data types for all
        columns in the VOA input file.
    VOA_RATINGS_LIST_INCLUDE : List of column names to read from
        the file.
    LFT.utilities.read_csv : Function used for reading the input file.
    """
    inc_columns = {
        k: v
        for k, v in VOA_RATINGS_LIST_COLUMNS.items()
        if k in VOA_RATINGS_LIST_INCLUDE
    }
    # File has some carriage-return characters in the middle of some
    # lines so need to make sure the lineterminator is just line feed
    voa_data = utilities.read_csv(
        path,
        name="VOA ratings list",
        columns=inc_columns,
        delimiter="*",
        header=None,
        names=VOA_RATINGS_LIST_COLUMNS.keys(),
        lineterminator="\n",
    )
    # Extract number from SCAT code and use for filtering
    voa_data.insert(
        voa_data.columns.get_loc("scat_code") + 1,
        "scat_num",
        pd.to_numeric(
            voa_data["scat_code"].str.extract(r"(\d+)\w", expand=False),
            downcast="integer",
        ),
    )
    voa_data = voa_data.loc[voa_data["scat_num"].isin(scat_codes)].copy()
    # Use postcode lookup to aggregate rateable_value to model zones
    lookup = Rezone.read(zone_lookup, None)
    # Convert post code columns to uppercase and remove all whitespace
    lookup.iloc[:, 0] = lookup.iloc[:, 0].str.upper().str.replace(r"\s+", "", regex=True)
    voa_data["postcode"] = voa_data["postcode"].str.upper().str.replace(r"\s+", "", regex=True)
    rezoned = Rezone.rezoneOD(
        voa_data[["postcode", "rateable_value"]],
        lookup,
        ("postcode",),
        rezoneCols=["rateable_value"],
    )
    rezoned.rename(columns={"postcode": "zone"}, inplace=True)
    return rezoned


# TODO Remove test code
if __name__ == "__main__":
    voa_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\VOA Data\uk-englandwales-ndr-2017-listentries-compiled-epoch-0024-baseline-csv\uk-englandwales-ndr-2017-listentries-compiled-epoch-0024-baseline-csv.csv"
    )
    zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Postcode to NoHAM Lookup\postcode_to_noham_zone_correspondence.csv"
    )
    ratings_data = voa_ratings_list(voa_path, {267, 217}, zc_path)
    print(ratings_data)
