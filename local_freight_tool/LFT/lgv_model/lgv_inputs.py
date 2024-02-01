# -*- coding: utf-8 -*-
"""
    Module containing functionality for reading and pre-processing
    the LGV inputs which are used for multiple segments.
"""

##### IMPORTS #####
# Standard imports
from __future__ import annotations
import enum
import re
import string
from pathlib import Path
from typing import Any, Callable, Optional, Union

# Third party imports
import caf.toolkit
import numpy as np
import pandas as pd
from pydantic import types, dataclasses, fields

# Local imports
from .. import utilities, errors
from ..data_utils import DataPaths
from ..rezone import Rezone
from .furnessing import FurnessConstraint


##### CONSTANTS #####
HH_PROJECTIONS_HEADER = {"Area Description": str, "HHs": float}
"""Column names (and data types) for input CSV to `household_projections` function."""
BRES_HEADER: dict[str, type] = {
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
TIME_PERIOD_SHEET = "Time Period Factors"
"""Name of the Excel Worksheet containing the time period factors."""
TIME_PERIOD_COLUMNS = {
    "time_period": ("Time Period", str),
    "service": ("Service", float),
    "delivery_parcel_stem": ("Delivery Parcel Stem", float),
    "delivery_parcel_bush": ("Delivery Parcel Bush", float),
    "delivery_grocery": ("Delivery Grocery", float),
    "commuting_drivers": ("Commuting Drivers", float),
    "commuting_skilled_trades": ("Commuting Skilled Trades", float),
    "personal": ("Personal", float),
}
"""Name and dtype of the expected columns in the time period table."""
GM_PARAMS_SHEET = "Gravity Model Parameters"
"""Name of the Excel Worksheet containing the gravity model parameters."""
GM_PARAMS_COLUMNS = {
    "segment": ("Segment", str),
    "furness_type": ("Furness Constraint Type", str),
    "function": ("Cost Function", str),
    "param1": ("Cost Function Parameter 1", float),
    "param2": ("Cost Function Parameter 2", float),
    "calibrate": ("Run Calibration", str),
}
"""Name and dtype of the expected columns in the gravity model parameters table."""
LGV_SEGMENTS = [
    "service",
    "delivery_parcel_stem",
    "delivery_parcel_bush",
    "delivery_grocery",
    "commuting_drivers",
    "commuting_skilled_trades",
]
"Names of the LGV segments."
EXAMPLE_CONFIG_NAME = "LGV_config_example.yml"


##### CLASSES #####
@dataclasses.dataclass
class CommuteWarehousePaths:
    """Paths to LSOA warehouse data for the commute segment."""

    medium: types.FilePath
    low: Optional[types.FilePath] = None
    high: Optional[types.FilePath] = None


class LGVInputPaths(caf.toolkit.BaseConfig):
    """Dataclass storing paths to all the input files for the LGV model."""

    household_paths: DataPaths
    """Paths for the households data and zone correspondence."""
    bres_path: types.FilePath
    """Path to the BRES data CSV at LSOA level."""
    warehouse_path: types.FilePath
    """Path for the warehouse floorspace data CSV at LSOA level."""
    commute_warehouse_paths: CommuteWarehousePaths
    parameters_path: types.FilePath
    """Path to the LGV parameters Excel workbook."""
    qs606ew_path: types.FilePath
    """Path to the England & Wales Census Occupation data CSV."""
    qs606sc_path: types.FilePath
    """Path to the Scottish Census Occupation data CSV."""
    sc_w_dwellings_path: types.FilePath
    """Path to the Scottish and Welsh dwellings data CSV."""
    e_dwellings_path: types.FilePath
    """Path to the English dwellings data XLSX."""
    ndr_floorspace_path: types.FilePath
    """Path to the NDR Business Floorspace CSV."""
    lsoa_lookup_path: types.FilePath
    """Path to the LSOA to NoHAM zone correspondence CSV."""
    msoa_lookup_path: types.FilePath
    """Path to the MSOA to NoHAM zone correspondence CSV."""
    lad_lookup_path: types.FilePath
    """Path to the Local Authority District to NoHAM zone correspondence
    CSV"""
    model_study_area: types.FilePath
    """Path to CSV containing lookup for zones in model study area."""
    cost_matrix_path: types.FilePath
    """Path to CSV containing cost matrix, should be square matrix with
    zone numbers as column names and indices."""
    calibration_matrix_path: Optional[types.FilePath] = None
    """Path to CSV containing calibration matrix, should be square matrix
    with zone numbers as column names and indices."""
    trip_distributions_path: types.FilePath
    """Path to Excel Workbook containing all the trip cost distributions."""
    output_folder: types.DirectoryPath
    """Path to folder to save outputs to."""
    normits_pa_folder: types.DirectoryPath
    """Path to the full PA Normits matrices, should contain all non house
    bound and house bound matrices"""
    normits_to_msoa_lookup: types.FilePath
    """Normits to MSOA(NTEM) lookup, this is NoHAM to NTEM lookup as the
    results are taken after normits results are converted back to NoHAM"""
    normits_to_personal_factor: float
    """This is the factor that the personal data should have applied to
    just include van data 4% is a starting point"""
    personal_purposes: list[int] = fields.Field(
        default_factory=lambda: [3, 4, 5, 6, 7, 8, 13, 14, 15, 16, 18]
    )
    """Personal purpose types defined by Normits"""

    @classmethod
    def write_example(cls, path: Path, **examples: str) -> None:
        """Write examples to a config file.

        Parameters
        ----------
        path : Path
            Path to the YAML file to write.
        examples : str
            Fields of the config to write, any missing fields
            are filled in with their default value (if they have
            one) or 'REQUIRED' / 'OPTIONAL'.
        """
        data = {}
        for name, field in cls.__fields__.items():
            if field.default is not None:
                value = field.default
            else:
                value = "REQUIRED" if field.required else "OPTIONAL"

            data[name] = examples.get(name, value)

        example = cls.construct(**data)
        example.save_yaml(path)


InfillFunction = Callable[[np.ndarray], float]


class InfillMethod(enum.Enum):
    """Options for filling in NaN values in warehouse data."""

    MIN = "minimum"
    MEAN = "mean"
    MEDIAN = "median"
    NON_ZERO_MIN = "non-zero minimum"
    ZERO = "zero"

    @classmethod
    @property
    def method_lookup(cls) -> dict[InfillMethod, InfillFunction]:
        """Lookup for the infill functions."""
        return {
            cls.MIN: np.nanmin,
            cls.MEAN: np.nanmean,
            cls.MEDIAN: np.nanmedian,
            cls.NON_ZERO_MIN: lambda a: np.amin(a, where=a > 0, initial=np.inf),
            cls.ZERO: lambda _: 0,
        }

    def method(self) -> InfillFunction:
        """Function to calculate infilling value."""
        return self.method_lookup[self]


##### FUNCTIONS #####
def write_example_config(path: Path | None) -> None:
    """Write an example config file to given `path`."""
    if path is None:
        path = Path(EXAMPLE_CONFIG_NAME)

    commute_warehouse_doc = (
        "CSV of LSOA warehouse floorspace for commute "
        "segment ({weight} weighting), {required}"
    )

    with dataclasses.set_validation(DataPaths, False):
        with dataclasses.set_validation(CommuteWarehousePaths, False):
            example_data = dict(
                household_paths=DataPaths(
                    "LGV Households",
                    "CSV of households data",
                    "Zone correspondence CSV",
                ),
                bres_path="Path to the BRES data CSV at LSOA level",
                warehouse_path="Path for the warehouse floorspace data CSV at LSOA level",
                commute_warehouse_paths=CommuteWarehousePaths(
                    commute_warehouse_doc.format(weight="medium", required="required"),
                    commute_warehouse_doc.format(weight="low", required="optional"),
                    commute_warehouse_doc.format(weight="high", required="optional"),
                ),
                parameters_path="Path to parameters spreadsheet",
                qs606ew_path="Path to the England & Wales Census Occupation data CSV",
                qs606sc_path="Path to the Scottish Census Occupation data CSV",
                sc_w_dwellings_path="Path to the Scottish and Welsh dwellings data CSV",
                e_dwellings_path="Path to the English dwellings data XLSX",
                ndr_floorspace_path="Path to the NDR Business Floorspace CSV.",
                lsoa_lookup_path="Path to the LSOA to model zone correspondence CSV",
                msoa_lookup_path="Path to the MSOA to model zone correspondence CSV",
                lad_lookup_path="Path to the Local Authority District to "
                "model zone correspondence CSV",
                model_study_area="Path to CSV containing lookup for zones in model study area",
                cost_matrix_path="Path to CSV containing cost matrix, should "
                "be square matrix with zone numbers as column names and indices",
                calibration_matrix_path="Path to CSV containing calibration matrix, "
                "should be square matrix with zone numbers as column names and indices",
                trip_distributions_path="Path to Excel Workbook containing all the "
                "trip cost distributions",
                output_folder="Path to folder to save outputs to",
                normits_pa_folder="Path to the full PA Normits matrices, should contain all non house bound and house bound matrices",
                normits_to_msoa_lookup="Normits to MSOA lookup, this is NoHAM to MSOA lookup as the results are taken after normits results are converted back to NoHAM",
                normits_to_personal_factor="This is the factor that the personal data should have applied to just include van data 4% is a starting point",
                personal_purposes="Personal purpose types defined by Normits",
            )

    LGVInputPaths.write_example(path, **example_data)
    print(f"Written example config: {path}")


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

    # Authority and County found in TEMPro outputs as well as MSOAs
    columns = list(HH_PROJECTIONS_HEADER.keys())
    households = households.loc[~households[columns[0]].isin(["Authority", "County"]), :]

    lookup = Rezone.read(zone_lookup, None)
    rezoned = Rezone.rezoneOD(households, lookup, dfCols=(columns[0],), rezoneCols=columns[1])
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


def load_warehouse_floorspace(
    path: Path, zone_lookup: Path, infill_method: InfillMethod | None = None
) -> pd.DataFrame:
    """Load warehouse floorspace data and convert to model zone system.

    Parameters
    ----------
    path : Path
        Path to CSV containing warehouse floorspace data with
        columns: "LSOA11CD", "area".
    zone_lookup : Path
        Path to zone correspondence CSV.

    Returns
    -------
    pd.DataFrame
        Warehouse floorspace area by model zone with index ("Zone")
        containing zone ID and column ("area") containing the
        floorspace area.
    """
    lsoa_column = "LSOA11CD"
    area_column = "area"
    floorspace = utilities.read_csv(path, columns={lsoa_column: str, area_column: float})

    lookup = Rezone.read(zone_lookup, None)

    rezoned, _ = Rezone.rezone(floorspace, lookup, lsoa_column, rezoneCols=area_column)
    rezoned.rename(columns={lsoa_column: "Zone"}, inplace=True)
    grouped = rezoned.groupby("Zone").sum()

    grouped = grouped.reindex(lookup["new"].unique())
    return grouped


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
    params = utilities.read_multi_sheets(path, {LGV_PARAMETERS_SHEET: LGV_PARAMETERS_COLUMNS})[
        LGV_PARAMETERS_SHEET
    ]
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
    columns = {"zone": str, "internal": int}
    df = utilities.read_csv(path, "Model Study Area CSV", columns)
    df.loc[:, "zone"] = pd.to_numeric(df["zone"], downcast="unsigned", errors="ignore")
    df.loc[:, "internal"] = df["internal"].astype(bool)
    internal = df.loc[df.internal, "zone"].tolist()
    return set(internal)


def read_time_factors(path: Path) -> dict[str, dict[str, float]]:
    """Read time period factors from Excel Worksheet.

    Expected worksheet name given by `TIME_PERIOD_SHEET`
    and expected columns given in `TIME_PERIOD_COLUMNS`.

    Parameters
    ----------
    path : Path
        Path to the Excel workbook containing the factors.

    Returns
    -------
    dict[str, dict[str, float]]
        Dictionary of all given time periods which contains
        dictionaries for the factor (value) for each segment
        (key). Keys for the internal dictionary are the same
        as the keys in `TIME_PERIOD_COLUMNS`.
    """
    df = utilities.read_excel(
        path,
        "Time Period Table",
        columns=dict(TIME_PERIOD_COLUMNS.values()),
        sheet_name=TIME_PERIOD_SHEET,
        index_col=0,
    )
    rename = {v[0]: k for k, v in TIME_PERIOD_COLUMNS.items()}
    df.rename(columns=rename, inplace=True)
    return df.to_dict(orient="index")


def read_gm_params(path: Path) -> pd.DataFrame:
    """Reads the Gravity Model input parameters from Excel Worksheet.

    Parameters
    ----------
    path : Path
        Path to Excel workbook containing sheet with name
        `GM_PARAMS_SHEET`.

    Returns
    -------
    pd.DataFrame
        DataFrame with LGV segment as the index and the following
        columns:
        - furness_type: FurnessConstraint value,
        - function: name of cost function,
        - param1, param2: value for cost function parameters,
        - calibrate: boolean for whether or not to run calibration.

    Raises
    ------
    errors.MissingDataError
        If any of the gravity model segments are missing.
    errors.IncorrectParameterError
        If any of the columns in the table have values
        which are expected.
    """
    df = utilities.read_excel(
        path,
        "Gravity Model Parameters",
        columns=dict(GM_PARAMS_COLUMNS.values()),
        sheet_name=GM_PARAMS_SHEET,
        index_col=0,
    )
    rename = {v[0]: k for k, v in GM_PARAMS_COLUMNS.items()}
    df.rename(columns=rename, inplace=True)
    df.index = df.index.str.lower().str.strip().str.replace(r"\s+", "_", regex=True)
    # Check all segments are given
    missing = [s for s in LGV_SEGMENTS if s not in df.index]
    if missing:
        missing = [s.replace("_", " ").title() for s in missing]
        raise errors.MissingDataError("Gravity model parameters segments", missing)

    df.loc[:, "furness_type"] = df["furness_type"].str.strip().str.upper()
    df.loc[:, "function"] = (
        df["function"].str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    )
    df.loc[:, "calibrate"] = df["calibrate"].str.strip().str.lower()

    # Check parameters are allowed
    furn_rep = {c.name: c for c in FurnessConstraint}
    exp_funcs = ["tanner", "log_normal"]
    calib_true = ["yes", "y", "true"]
    calib_false = ["no", "n", "false"]
    checks = (
        ("furness_type", furn_rep),
        ("function", exp_funcs),
        ("calibrate", calib_true + calib_false),
    )
    for col, exp in checks:
        incorrect = list(df.loc[~df[col].isin(exp).values, col].unique())
        if incorrect:
            name = GM_PARAMS_COLUMNS[col][0]
            raise errors.IncorrectParameterError(
                incorrect, f"Gravity model {name}", expected=list(exp)
            )
    # Change strings to FurnessConstraint and bool
    df.loc[:, "furness_type"] = df["furness_type"].replace(furn_rep)
    df.loc[:, "calibrate"] = df["calibrate"].isin(calib_true)
    return df
