# -*- coding: utf-8 -*-
"""
    Module containing functionality for reading and pre-processing
    the LGV inputs which are used for multiple segments.
"""

##### IMPORTS #####
# Standard imports
import re
import string
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Any, Union

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from .. import utilities, errors
from ..data_utils import DataPaths
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
    "eff_date",
    "from_date",
    "to_date",
]
"""Column names to read from the VOA ratings list file."""
VOA_FILL_FUNCTIONS = {
    "minimum": np.nanmin,
    "mean": np.nanmean,
    "median": np.nanmedian,
    "non-zero minimum": lambda a: np.amin(a, where=a > 0, initial=np.inf),
}
"""Options for filling in NaN values in VOA data."""
LGV_PARAMETERS_SHEET = "Parameters"
"""Name of the sheet containing the main LGV parameters."""
LGV_PARAMETERS_COLUMNS = {"Parameter": str, "Value": float}
"""Column names in the `LGV_PARAMETERS_SHEET`."""
LGV_PARAMETERS = {
    "lgv_growth": "LGV growth",
    "avg_new_house_size": "Average new house size",
    "scotland_soc82_ratio": "Scotland SOC821/SOC82",
    "year": "Model Year",
}
"""Names of the parameters (values) expected and their internal code name (keys)."""


##### CLASSES #####
@dataclass(frozen=True)
class LGVInputPaths:
    """Dataclass storing paths to all the input files for the LGV model."""

    household_paths: DataPaths = None
    """Paths for the households data and zone correspondence."""
    bres_paths: DataPaths = None
    """Paths for the BRES data and zone correspondence."""
    voa_paths: DataPaths = None
    """Paths for the VOA data and zone correspondence."""
    parameters_path: Path = None
    """Path to the LGV parameters Excel workbook."""
    qs606ew_path: Path = None
    """Path to the England & Wales Census Occupation data CSV."""
    qs606sc_path: Path = None
    """Path to the Scottish Census Occupation data CSV."""
    sc_w_dwellings_path: Path = None
    """Path to the Scottish and Welsh dwellings data CSV."""
    e_dwellings_path: Path = None
    """Path to the English dwellings data XLSX."""
    ndr_floorspace_path: Path = None
    """Path to the NDR Business Floorspace CSV."""
    lsoa_lookup_path: Path = None
    """Path to the LSOA to NoHAM zone correspondence
    CSV"""
    msoa_lookup_path: Path = None
    """Path to the MSOA to NoHAM zone correspondence
    CSV"""
    lad_lookup_path: Path = None
    """Path to the Local Authority District to NoHAM zone correspondence
    CSV"""
    model_study_area: Path = None
    """Path to CSV containing lookup for zones in model study area."""
    cost_matrix_path: Path = None
    """Path to CSV containing cost matrix, should be square matrix with
    zone numbers as column names and indices."""
    calibration_matrix_path: Path = None
    """Path to CSV containing calibration matrix, should be square matrix
    with zone numbers as column names and indices."""
    trip_distributions_path: Path = None
    """Path to Excel Workbook containing all the trip cost distributions."""
    output_folder: Path = None
    """Path to folder to save outputs to."""

    def asdict(self) -> dict[str, Path]:
        """Return class attributes as a dictionary."""
        attrs = {}
        for nm in dir(self):
            if nm.startswith("_"):
                continue
            a = getattr(self, nm)
            if not callable(a):
                attrs[nm] = a
        return attrs

    def __post_init__(self):
        # Check if all input files exist
        for nm, value in self.asdict().items():
            if isinstance(value, DataPaths) or value is None:
                # DataPaths instances should already have been checked
                continue
            if nm == "output_folder":
                utilities.check_folder(value, nm, True)
            else:
                utilities.check_file_path(value, nm)

    def __str__(self) -> str:
        s = [f"{self.__class__.__name__}("]
        for nm, value in self.asdict().items():
            s.append(f"{nm}={value}")
        return "\n\t".join(s) + "\n)"


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
    path: Path,
    zone_lookup: Union[Path, pd.DataFrame],
    aggregation: dict[str, tuple[str]],
) -> pd.DataFrame:
    """Read and filter the ONS BRES data CSV.

    The ONS BRES data should be a CSV containing metadata in the top
    9 rows then row 10 should contain the column names (see
    `BRES_HEADER` for names and expected data types).

    Parameters
    ----------
    path : Path
        Path to the CSV containing BRES data.
    zone_lookup : Path or pd.DataFrame
        Path to zone correspondence CSV or zone lookup dataframe.
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
    if isinstance(zone_lookup, pd.DataFrame):
        lookup = zone_lookup
    else:
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
    path: Path,
    scat_codes: Union[Sequence[int], pd.DataFrame],
    zone_lookup: Path,
    year: int = None,
    fill_func: str = "minimum",
) -> pd.DataFrame:
    """Reads VOA NDR ratings list entries file and filters based on `scat_codes`.

    The input file should be a text file (.csv or .txt) with no header
    row and uses '*' to separate columns.

    Parameters
    ----------
    path : Path
        Path to the VOA ratings list file.
    scat_codes : Sequence[int] or pd.DataFrame
        List of SCAT code numbers to include in returned DataFrame or
        dataframe with SCAT codes for for indices and weightings in `Weight`
        column.
    zone_lookup : Path
        Path to the lookup between the VOA postcodes and the model
        zone system, expects 3 columns containing postcode, model
        zone number and splitting factor information in that order.
    year : int, optional
        The model year, used for filtering the VOA data. Data isn't
        filtered by date if `year` isn't given.
    fill_func : str, default = 'min'
        The function to use for filling in any NaN values in the
        `rateable_value` column. Can be any function defined in
        `VOA_FILL_FUNCTIONS`.

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

    weightings = None
    # if weightings, normalise then and extract scat codes
    if isinstance(scat_codes, pd.DataFrame):
        weightings = scat_codes / scat_codes.sum()
        scat_codes = scat_codes.index
    voa_data = voa_data.loc[voa_data["scat_num"].isin(scat_codes)].copy()
    # Use from_date for any missing eff_date and convert to date objects
    nan_date = voa_data["eff_date"].isna()
    voa_data.loc[nan_date, "eff_date"] = voa_data.loc[nan_date, "from_date"].copy()
    voa_data.drop(columns=["from_date"], inplace=True)
    for c in ("eff_date", "to_date"):
        voa_data[c] = pd.to_datetime(voa_data[c])
    # Make sure depot is active from before model year to after model
    # year (inclusive), include NaT values for both
    if year:
        date_mask = (
            (voa_data["eff_date"].dt.year <= year) | voa_data["eff_date"].isna()
        ) & ((voa_data["to_date"].dt.year >= year) | voa_data["to_date"].isna())
        voa_data = voa_data.loc[date_mask].copy()

    lookup = Rezone.read(zone_lookup, None)
    # Convert post code columns to uppercase and remove all whitespace
    lookup.iloc[:, 0] = (
        lookup.iloc[:, 0].str.upper().str.replace(r"\s+", "", regex=True)
    )
    voa_data["postcode"] = (
        voa_data["postcode"].str.upper().str.replace(r"\s+", "", regex=True)
    )
    # Infill any NaN rateable_values with the average
    nan_value = voa_data["rateable_value"].isna()
    if nan_value.sum() > 0:
        try:
            func = VOA_FILL_FUNCTIONS[fill_func.strip().lower()]
            fill = func(voa_data["rateable_value"].values)
        except KeyError as e:
            raise ValueError(
                "`fill_func` should be one of "
                f"{list(VOA_FILL_FUNCTIONS.keys())} not {fill_func!r}"
            ) from e
        warnings.warn(
            f"{nan_value.sum()} rows in VOA input have no information for "
            f"'rateable_value' so infilling with the {fill_func} ({fill:.1f})",
            RuntimeWarning,
        )
        voa_data.loc[nan_value, "rateable_value"] = fill

    # Weight rateable value if required according to scat number
    if not weightings is None:
        voa_data = voa_data[["postcode", "rateable_value", "scat_num"]].merge(
            weightings, left_on="scat_num", right_on=weightings.index, how="left"
        )
        voa_data["weighted_rateable_value"] = (
            voa_data["rateable_value"] * voa_data["Weight"]
        )
        voa_data = voa_data[["postcode", "weighted_rateable_value"]].rename(
            columns={"weighted_rateable_value": "rateable_value"}
        )

    # Use postcode lookup to aggregate rateable_value to model zones
    # and warn user of any missing postcodes
    rezoned, missing = Rezone.rezone(
        voa_data[["postcode", "rateable_value"]],
        lookup,
        "postcode",
        rezoneCols="rateable_value",
    )
    if not missing.empty:
        nan_pc = missing.postcode.isna()
        warnings.warn(
            f"{nan_pc.sum()} rows in VOA input don't have a postcode and "
            f"{len(missing) - nan_pc.sum()} rows in VOA input have postcodes "
            "which can't be found in the lookup: "
            + ", ".join(missing.loc[~nan_pc, "postcode"].tolist())
            + " These rows are ignored."
        )
        rezoned.dropna(subset=["postcode"], inplace=True)
    rezoned.rename(columns={"postcode": "zone"}, inplace=True)
    rezoned["zone"] = pd.to_numeric(
        rezoned["zone"], errors="ignore", downcast="integer"
    )
    return rezoned.groupby("zone", as_index=False).sum()


def lgv_parameters(path: Path) -> dict[str, Any]:
    """Read the LGV Parameters sheet from the Excel workbook.

    Parameters
    ----------
    path : Path
        Path to the Excel workbook containing `LGV_PARAMETERS_SHEET`.

    Returns
    -------
    dict[str, Any]
        Dictionary of all the generic LGV parameters.

    Raises
    ------
    LFT.errors.MissingDataError
        If any expected parameters are missing.

    See Also
    --------
    LGV_PARAMETERS_SHEET
    LGV_PARAMETERS_COLUMNS
    LGV_PARAMETERS
    """
    params = utilities.read_multi_sheets(
        path, {LGV_PARAMETERS_SHEET: LGV_PARAMETERS_COLUMNS}
    )[LGV_PARAMETERS_SHEET]
    params = utilities.to_dict(params, *LGV_PARAMETERS_COLUMNS, name="LGV Parameters")
    missing = []
    out_params = {}
    for key, nm in LGV_PARAMETERS.items():
        try:
            out_params[key] = params[nm]
        except KeyError:
            missing.append(nm)
    if missing:
        raise errors.MissingDataError("LGV Parameters", missing)
    return out_params


def read_study_area(path: Path) -> set:
    """Reads model study area CSV.

    Parameters
    ----------
    path : Path
        Path to CSV containing columns 'zone' and
        'internal'.

    Returns
    -------
    set[int]
        Set of zone numbers for all zones
        inside the study area.

    Notes
    -----
    The CSV should contain two columns:
    - zone: the zone number
    - internal: a value of 1 or 0 for whether
      the zone is in the study area or not

    Any zones not given are assumed to be outside
    the study area.
    """
    columns = {"zone": int, "internal": int}
    df = utilities.read_csv(path, "Model Study Area CSV", columns)
    df["internal"] = df["internal"].astype(bool)
    internal = df.loc[df.internal, "zone"].tolist()
    return set(internal)
