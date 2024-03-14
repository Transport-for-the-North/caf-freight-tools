"""
    Module to calculate the productions and attractions for the LGV
    commuting segment in the model zone system.
"""

##### IMPORTS #####
# Standard imports
from itertools import chain
import pathlib
import re
from typing import Optional, Union

# Third party imports
import numpy as np
import pandas as pd
import pydantic
from pydantic import fields

# Local imports
from .. import utilities, errors
from ..rezone import Rezone
from . import lgv_inputs

##### CONSTANTS #####
BUSINESS_FLOORSPACE_HEADER: dict[str, type] = {"AREA_CODE": str}
BUSINESS_FLOORSPACE_RENAME = {"AREA_CODE": "zone"}
BUSINESS_CATEGORIES = ["Retail", "Office", "Industrial", "Other"]
BUSINESS_FLOORSPACE_REMOVE_ROWS = ["K", "E9", "W9", "E1"]
E_DWELLINGS_HEADER = [
    "Current\nONS code",
    "Lower and Single Tier Authority Data",
    "Demolitions",
    "Net Additions",
]
E_DWELLINGS_NEW_COLS = {"Current\nONS code": "zone"}

QS606_BASE_HEADERS = {
    "mnemonic": str,
    "All categories: Occupation": float,
    "51. Skilled agricultural and related trades": float,
    "52. Skilled metal, electrical and electronic trades": float,
    "53. Skilled construction and building trades": float,
}
QS606_HEADERS: dict[str, dict[str, type]] = {
    "EW": {**QS606_BASE_HEADERS, "821. Road Transport Drivers": float},
    "SC": {
        **QS606_BASE_HEADERS,
        "82. Transport and mobile machine drivers and operatives": float,
    },
}
QS606_HEADER_FOOTER = {"EW": (8, 5), "SC": (7, 5)}


##### CLASSES #####
class WarehouseParameters(pydantic.BaseModel):
    """Parameters for warehouse data used in commute segment."""

    medium: Optional[float] = fields.Field(alias="Weighting - Medium")
    high: Optional[float] = fields.Field(alias="Weighting - High")
    low: Optional[float] = fields.Field(alias="Weighting - Low")
    zone_infill: list[Union[int, str]] = fields.Field(
        alias="Model Zone Infill", default_factory=list
    )
    infill_method: Optional[lgv_inputs.InfillMethod] = fields.Field(
        None, alias="Zone Infill Method"
    )

    @pydantic.validator("zone_infill", pre=True)
    def _split_str(cls, value: str) -> list:  # pylint: disable=no-self-argument
        return value.split(",")


class CommuteTripEnds:
    """Functionality for generating the LGV commuting segment trip productions
    and attractions.

    Parameters
    ----------
    inputs : LGVInputPaths
        Dataclass storing paths to all the input files for the LGV model.
    model_zones : pd.Series
        Full list of model zones.

    See Also
    --------
    .lgv_inputs: Module with functions for reading some inputs.
    """

    COMMUTING_INPUTS_SHEET_HEADERS = {
        "Parameters": {"Parameter": str, "Value": float},
        "Commute trips by main usage": {"Main usage": str, "Trips": float},
        "Commute trips by land use": {"Land use at trip end": str, "Trips": float},
        "Commute Warehouse Parameters": {"Parameter": str, "Value": str},
        "Delivery Segment Parameters": {"Parameter": str, "Value": str},
    }

    BRES_AGGREGATION = {
        "Non-Construction": list(
            chain(
                lgv_inputs.letters_range(end="E"),
                lgv_inputs.letters_range(start="G", end="S"),
            )
        )
    }

    HH_PROJECTIONS_HEADER = {"Area Description": str, "HHs": float, "Jobs": float}
    HH_RENAME = {"Area Description": "zone", "HHs": "households", "Jobs": "jobs"}

    def __init__(self, input_paths: lgv_inputs.LGVInputPaths, model_zones: pd.Series):
        """Initialise class by checking all input paths are in input dict and
        all input files exist"""
        self.paths = input_paths
        self.model_zones = model_zones

        self.params = {}
        self.warehouse_parameters: WarehouseParameters | None = None
        self.zone_lookups = {}
        self.commute_trips_main_usage = {}
        self.commute_trips_land_use = {}
        self.trip_productions = None
        self.TEMPro_data = {}
        self.attractor_factors = {}
        self.ATTRACTION_FUNCTIONS = {
            "Construction": self._calc_construction_factors,
            "Residential": self._calc_residential_factors,
            "Employment": self._calc_employment_factors,
            "Skilled trades": self._estimate_skilled_attractions,
            "Drivers": self._estimate_driver_attractions,
        }
        self.trip_attractions = None
        self.trip_ends = {}
        self.infill_zones = []

    @property
    def inputs_summary(self) -> pd.DataFrame:
        """Returns a summary table of class inputs.

        Returns
        -------
        pd.DataFrame
            Summary of inputs
        """
        return pd.DataFrame.from_dict(self.paths.dict(), orient="index", columns=["Path"])

    def _read_commute_tables(self):
        """Read in commuting tables input XLSX."""
        commute_tables = utilities.read_multi_sheets(
            self.paths.parameters_path, sheets=self.COMMUTING_INPUTS_SHEET_HEADERS
        )

        # TODO Create a pydantic dataclass to store / validate the parameters
        self.params = utilities.to_dict(
            commute_tables["Parameters"], "Parameter", ("Value", float)
        )
        self.params["Model Year"] = int(self.params["Model Year"])

        sheet = "Commute Warehouse Parameters"
        headers = list(self.COMMUTING_INPUTS_SHEET_HEADERS[sheet])
        warehouse_params: pd.Series = commute_tables[sheet].set_index(headers[0])[headers[1]]
        self.warehouse_parameters = WarehouseParameters.parse_obj(warehouse_params.to_dict())

        # write the commute trips by main usage to a dictionary
        commute_trips_main_usage = utilities.to_dict(
            commute_tables["Commute trips by main usage"],
            key_col="Main usage",
            val_col=("Trips", int),
        )
        self.commute_trips_main_usage["Drivers"] = commute_trips_main_usage["G"]
        self.commute_trips_main_usage["Skilled trades"] = (
            commute_trips_main_usage["S"] + commute_trips_main_usage["C"]
        )

        self.commute_trips_main_usage = {
            k: v * self.params["LGV growth"] for k, v in self.commute_trips_main_usage.items()
        }
        print(f"Grown {self.commute_trips_main_usage=}")

        self.commute_trips_land_use = utilities.to_dict(
            commute_tables["Commute trips by land use"],
            key_col="Land use at trip end",
            val_col=("Trips", int),
        )

        self.commute_trips_land_use = {
            k: v * self.params["LGV growth"] for k, v in self.commute_trips_land_use.items()
        }
        print(f"Grown {self.commute_trips_land_use=}")

    def _read_zone_lookups(self):
        for key, value in self.paths.dict().items():
            key = key.lower()
            if key.endswith("lookup") or key.endswith("lookup_path"):
                name = re.sub(r"[\s_]+|path", " ", key).strip()
                self.zone_lookups[name] = Rezone.read(value, None)

    def _read_qs606(self):
        """Read in and rezone Census occupation data."""
        # If haven't yet read in parameters and zone lookups, read in
        if not self.params:
            self._read_commute_tables()

        if not self.zone_lookups:
            self._read_zone_lookups()

        qs606 = read_qs606(self.paths.qs606ew_path, self.paths.qs606sc_path)

        # Scottish data doesn't include SOC821, so calculate from SOC82
        qs606["SC"]["821"] = qs606["SC"]["82"] * self.params["Scotland SOC821/SOC82"]

        # Combine the data for England, Wales and Scotland
        qs606uk = pd.concat([qs606["EW"], qs606["SC"].drop(axis=1, labels=["82"])])

        # Combine columns into skilled trades (SOC51, 52, 53) and drivers (SOC821)
        qs606uk["Skilled trades"] = qs606uk[
            [col for col in qs606uk.columns if col.startswith("5")]
        ].sum(axis=1)
        qs606uk = qs606uk.rename(columns={"821": "Drivers"})
        qs606uk = qs606uk[["zone", "total", "Skilled trades", "Drivers"]]

        # Rezone to model zone system
        cols = qs606uk.columns
        return Rezone.rezoneOD(
            qs606uk,
            self.zone_lookups["lsoa lookup"],
            dfCols=(cols[0],),
            rezoneCols=cols[1:],
        )

    def _read_dwellings_data(self):
        """Read in, calculate and rezone additional dwellings data.

        Returns
        -------
        pd.DataFrame
            Additional dwellings data in model zone system.
        """

        # Read in additional dwellings data for England
        if not self.params:
            self._read_commute_tables()

        e_dwellings, _ = read_english_dwellings(
            self.paths.e_dwellings_path, self.params["Model Year"]
        )

        # Calculate total additional construction (net additions + demolitions)
        e_dwellings["additional dwellings"] = (
            e_dwellings["Net Additions"] + 2 * e_dwellings["Demolitions"]
        )

        # Calculate ratio of additional construction over net additional dwellings
        additional_net_ratio = (
            e_dwellings["additional dwellings"].sum() / e_dwellings["Net Additions"].sum()
        )

        sc_w_dwellings, _ = read_sc_w_dwellings(
            self.paths.sc_w_dwellings_path, self.params["Model Year"]
        )

        # Calculate additional construction
        sc_w_dwellings.loc[:, "additional dwellings"] = (
            sc_w_dwellings.loc[:, str(self.params["Model Year"])]
            - sc_w_dwellings.loc[:, str(self.params["Model Year"] - 1)]
        ) * additional_net_ratio

        # Concatenate the dwellings data
        cols = ["zone", "additional dwellings"]
        dwellings = pd.concat([e_dwellings[cols], sc_w_dwellings[cols]], axis=0)

        # Convert to floorspace
        dwellings["floorspace"] = (
            dwellings["additional dwellings"] * self.params["Average new house size"]
        )

        dwellings.drop(axis=1, labels=["additional dwellings"], inplace=True)

        # rezone dwellings data from LAD to model zone system
        cols = dwellings.columns

        # Assign to floorspace dictionary
        return Rezone.rezoneOD(
            dwellings,
            self.zone_lookups["lad lookup"],
            dfCols=(cols[0],),
            rezoneCols=cols[1:],
        )

    def _read_ndr(self):
        """Reads in NDR Business floorspace data, calculates additional
        floorspace and rezoned to model zone system.

        Returns
        -------
        pd.DataFrame
            Dataframe with NDR additional floorspace data for England and Wales
        """

        # Check input parameters have been read in
        if not self.params:
            self._read_commute_tables()

        ndr, _ = read_ndr_floorspace(self.paths.ndr_floorspace_path, self.params["Model Year"])

        # distinguish columns by year
        previous_yr = [col for col in ndr.columns if str(self.params["Model Year"] - 1) in col]
        current_yr = [col for col in ndr.columns if str(self.params["Model Year"]) in col]

        # sort lists alphabetically to ensure they are in the same category order
        previous_yr.sort()
        current_yr.sort()

        # Calculate floorspace differences
        for i, col in enumerate(current_yr):
            ndr.loc[:, f"{col.split('_')[-1]}"] = (
                ndr.loc[:, col] - ndr.loc[:, previous_yr[i]]
            ).abs()

        # Sum all differences
        ndr["floorspace"] = ndr[BUSINESS_CATEGORIES].sum(axis=1)

        # only include relevant columns
        ndr = ndr[["zone", "floorspace"]]

        # rezone to model zone system
        return Rezone.rezoneOD(
            ndr,
            self.zone_lookups["lad lookup"],
            dfCols=(ndr.columns[0],),
            rezoneCols=ndr.columns[1:],
        )

    def _read_household_projections(self):
        """Reads in household projections data."""
        households = utilities.read_csv(
            self.paths.household_paths.path,
            name="Household projections",
            columns=self.HH_PROJECTIONS_HEADER,
        ).rename(columns=self.HH_RENAME)

        # Authority and County found in TEMPro outputs as well as MSOAs
        households = households.loc[~households["zone"].isin(["Authority", "County"]), :]

        # get sum of jobs
        self.TEMPro_data["EW jobs"] = households[
            households.zone.str.startswith("E") | households.zone.str.startswith("W")
        ].jobs.sum()

        # get Scottish jobs data
        scottish_jobs = households[["zone", "jobs"]][households.zone.str.startswith("S")]

        # rezone to model zone system
        if not self.zone_lookups:
            self._read_zone_lookups()

        self.TEMPro_data["S jobs"] = Rezone.rezoneOD(
            scottish_jobs,
            self.zone_lookups["msoa lookup"],
            dfCols=(scottish_jobs.columns[0],),
            rezoneCols=scottish_jobs.columns[1:],
        )
        # Job data is not required for households
        households.drop(axis=1, labels=["jobs"], inplace=True)
        self.TEMPro_data["households"] = Rezone.rezoneOD(
            households,
            self.zone_lookups["msoa lookup"],
            dfCols=(households.columns[0],),
            rezoneCols=households.columns[1:],
        )

    def _calc_construction_factors(self):
        """Calculates the total change in sqm in residential and business
        floorspace and uses it to calculate construction attractor factors
        """
        # get residential floorspace
        residential_floorspace = self._read_dwellings_data()

        # get business floorspace for England and Wales
        ndr_floorspace = self._read_ndr()

        # Estimate Scottish business floorspace from job data
        if not self.TEMPro_data:
            self._read_household_projections()

        scottish_floorspace = self.TEMPro_data["S jobs"].copy()
        scottish_floorspace.loc[:, "floorspace"] = (
            scottish_floorspace["jobs"]
            * ndr_floorspace.floorspace.sum()
            / self.TEMPro_data["EW jobs"]
        )
        scottish_floorspace = scottish_floorspace[["zone", "floorspace"]]

        # combine all floorspace differences
        floorspace = (
            pd.concat([residential_floorspace, ndr_floorspace, scottish_floorspace])
            .groupby("zone")
            .sum()
        )
        self.attractor_factors["Construction"] = (floorspace / floorspace.sum()).rename(
            columns={"floorspace": "factor"}
        )

    def _calc_residential_factors(self):
        """Calculates residential attractor factors from TEMPro households
        data.
        """
        if not self.TEMPro_data:
            self._read_household_projections()
        households = self.TEMPro_data["households"]
        households.index = households["zone"]
        households["factor"] = households["households"] / households["households"].sum()
        self.attractor_factors["Residential"] = households[["factor"]]

    def _calc_employment_factors(self):
        """Calculates employment attractor factors from BRES data"""
        if not self.zone_lookups:
            self._read_zone_lookups()
        bres = lgv_inputs.filtered_bres(
            self.paths.bres_path, self.zone_lookups["lsoa lookup"], self.BRES_AGGREGATION
        ).rename(columns={"Zone": "zone"})
        bres.index = bres["zone"]
        bres["factor"] = (
            bres[self.BRES_AGGREGATION.keys()] / bres[self.BRES_AGGREGATION.keys()].sum()
        )
        self.attractor_factors["Employment"] = bres[["factor"]]

    def estimate_productions(self):
        """Reads in files and estimates trip productions by zone and employment
        segment"""
        qs606uk = self._read_qs606()
        # TODO review calc to check for 1/3

        # Calculate total occupation numbers for Skilled trades and Drivers
        totals = qs606uk.drop(axis=1, labels=["zone", "total"]).sum()

        # Create trip productions df
        self.trip_productions = qs606uk[["zone"]]

        # perform trip production calculation
        for occupation in self.commute_trips_main_usage:
            self.trip_productions.loc[:, occupation] = (
                0.5
                * qs606uk.loc[:, occupation]
                * self.commute_trips_main_usage[occupation]
                / totals[occupation]
            )

        self.trip_productions.index = self.trip_productions["zone"]
        self.trip_productions.drop(columns=["zone"], inplace=True)
        self.trip_productions["Total"] = self.trip_productions.sum(axis=1)

    def _estimate_skilled_attractions(self):
        """Estimates trip attractions for skilled trades.

        Returns
        -------
        pd.DataFrame
            DataFrame of trip attractions with zones as indices and a "trips"
            column.
        """
        # check for commute trip data by land use at trip end
        if not self.commute_trips_land_use:
            self._read_commute_tables()

        # check for any missing attractor factors
        factors_missing = [
            x for x in self.commute_trips_land_use if x not in self.attractor_factors
        ]
        if factors_missing:
            for category in factors_missing:
                self.ATTRACTION_FUNCTIONS[category]()

        # calculate skilled attractions, using just residential and construction
        # because employment is used for drivers
        skilled_attractions = {}
        for key in ["Residential", "Construction"]:
            skilled_attractions[key] = (
                self.commute_trips_land_use[key] * self.attractor_factors[key]
            )

        skilled_attractions = sum(skilled_attractions.values()).rename(
            columns={"factor": "trips"}
        )

        return skilled_attractions

    def _estimate_driver_attractions(self):
        """Estimates trip attractions for Drivers

        Returns
        -------
        pd.DataFrame
            DataFrame of trip attractions with zones as indices and a "trips"
            column.
        """
        if self.warehouse_parameters is None:
            self._read_commute_tables()

        data_paths = [
            (
                "medium",
                self.paths.commute_warehouse_paths.medium,
                self.warehouse_parameters.medium,
            ),
            ("low", self.paths.commute_warehouse_paths.low, self.warehouse_parameters.low),
            ("high", self.paths.commute_warehouse_paths.high, self.warehouse_parameters.high),
        ]
        factored_data = []

        for name, path, weight in data_paths:
            if path is None and name == "medium":
                raise errors.MissingInputsError("commute warehouse path (medium)")
            if path is None:
                continue
            if weight is None:
                raise errors.MissingInputsError(f"commute warehouse {name} weighting factor")

            data = lgv_inputs.load_warehouse_floorspace(path, self.paths.lsoa_lookup_path)
            data = data * weight
            factored_data.append(data)

        warehouse_floorspace = pd.concat(factored_data, axis=1)

        # Sum will fill Nans with 0 but we need to keep Nan in rows which are all Nan for infilling
        all_nans: pd.Series = warehouse_floorspace.isna().all(axis=1)
        warehouse_floorspace: pd.Series = warehouse_floorspace.sum(axis=1, skipna=True)
        warehouse_floorspace.loc[all_nans] = np.nan

        if self.warehouse_parameters.zone_infill and all_nans.sum() > 0:
            if self.warehouse_parameters.infill_method is None:
                raise ValueError(
                    f"{len(self.warehouse_parameters.zone_infill)} zones "
                    "provided for infilling but no infill method is given"
                )

            infill_function = self.warehouse_parameters.infill_method.method()
            infill_value = infill_function(warehouse_floorspace.dropna().values)

        else:
            infill_value = 0

        warehouse_floorspace = warehouse_floorspace.fillna(infill_value)

        trips = (
            warehouse_floorspace / warehouse_floorspace.sum()
        ) * self.commute_trips_land_use["Employment"]

        return trips.to_frame("trips")

    def estimate_attractions(self):
        """Estimates trip attractions"""
        if not self.commute_trips_main_usage:
            self._read_commute_tables()

        trip_attractions = {}
        for category in self.commute_trips_main_usage:
            trip_attractions[category] = self.ATTRACTION_FUNCTIONS[category]()

        # align matrices
        (
            trip_attractions["Drivers"],
            trip_attractions["Skilled trades"],
        ) = trip_attractions[
            "Drivers"
        ].align(trip_attractions["Skilled trades"], join="outer", fill_value=0)

        self.trip_attractions = sum(trip_attractions.values()).rename(
            columns={"trips": "Total"}
        )
        for col in trip_attractions:
            self.trip_attractions[col] = trip_attractions[col]["trips"]

    def calc_trip_ends(self):
        """Takes production and attraction dataframes with skilled trades and
        drivers as columns and zones as indices and creates skilled trade and
        driver trip dataframes with productions and attractions as columns and
        zones as indices.
        """
        if self.trip_productions is None:
            self.estimate_productions()
        if self.trip_attractions is None:
            self.estimate_attractions()
        for soc in ["Skilled trades", "Drivers"]:
            self.trip_ends[soc] = pd.concat(
                [
                    self.trip_productions[soc],
                    self.trip_attractions[soc],
                ],
                axis=1,
            )
            self.trip_ends[soc].columns = ["Productions", "Attractions"]

            self.trip_ends[soc] = self.trip_ends[soc].reindex(
                index=pd.Index(self.model_zones), fill_value=0
            )

    @property
    def productions(self) -> pd.DataFrame:
        """pd.DataFrame : Trip productions for each zone (index) and
        with columns Total, Skilled trades and Drivers
        """
        if self.trip_productions is None:
            self.estimate_productions()
        return self.trip_productions

    @property
    def attractions(self) -> pd.DataFrame:
        """pd.DataFrame : Trip productions for each zone (index) and
        with columns Total, Skilled trades and Drivers
        """
        if self.trip_attractions is None:
            self.estimate_attractions()
        return self.trip_attractions

    @property
    def trips(self) -> pd.DataFrame:
        """Dict[pd.DataFrame] : dictionary with keys Skilled trades and
        Drivers, with values being the trip dataframes, each with productions
        and attractions as columns and zones as indices."""
        if not self.trip_ends:
            self.calc_trip_ends()
        return self.trip_ends


##### FUNCTIONS #####
def read_ndr_floorspace(
    path: pathlib.Path,
    model_year: int,
    rename_columns: dict[str, str] = BUSINESS_FLOORSPACE_RENAME,
) -> tuple[pd.DataFrame, list[str]]:
    # TODO Write docstring
    zone_col = "AREA_CODE"
    columns = BUSINESS_FLOORSPACE_HEADER.copy()

    data_columns = {}
    for column_start in [
        f"Floorspace_{model_year-1}-{str(model_year)[2:]}_",
        f"Floorspace_{model_year}-{str(model_year + 1)[2:]}_",
    ]:
        for category in BUSINESS_CATEGORIES:
            data_columns[column_start + category] = float
    columns.update(data_columns)

    ndr = utilities.read_csv(path, columns=columns).rename(columns=rename_columns)

    if zone_col in rename_columns:
        zone_col = rename_columns[zone_col]

    # Remove rows that are not LAD
    conditional = ndr[zone_col].str.startswith(BUSINESS_FLOORSPACE_REMOVE_ROWS[0])
    for row in BUSINESS_FLOORSPACE_REMOVE_ROWS[1:]:
        conditional = conditional | ndr[zone_col].str.startswith(row)
    ndr = ndr[~conditional]

    return ndr, list(data_columns.keys())


def read_sc_w_dwellings(path: pathlib.Path, model_year: int) -> tuple[pd.DataFrame, list[str]]:
    # TODO Write docstring
    data_columns = [str(model_year - i) for i in (0, 1)]
    sc_w_header = {"zone": str, **dict.fromkeys(data_columns, int)}
    sc_w_dwellings = utilities.read_csv(path, columns=sc_w_header)
    return sc_w_dwellings, data_columns


def read_english_dwellings(
    path: pathlib.Path,
    model_year: int,
    rename_columns: dict[str, str] = E_DWELLINGS_NEW_COLS,
    drop_lad_name: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    sheet = f"{model_year}-{model_year - 2000 + 1}"
    dwellings = (
        utilities.read_excel(
            path,
            columns=E_DWELLINGS_HEADER,
            skiprows=3,
            sheet_name=sheet,
        )
        .dropna(axis=1, how="all")
        .dropna(axis=0, how="any")
        .rename(columns=rename_columns)
    )

    if drop_lad_name:
        dwellings.drop(axis=1, labels=["Lower and Single Tier Authority Data"], inplace=True)

    data_columns = ["Demolitions", "Net Additions"]
    for col in data_columns:
        try:
            dwellings.loc[:, col] = dwellings[col].astype(float)
        except ValueError as err:
            match = re.match(r"could not convert \w+ to float", str(err), re.IGNORECASE)
            if match:
                raise errors.NonNumericDataError(
                    name=f"{path.stem} column", non_numeric=str(col)
                )
            raise

    return dwellings, data_columns


def read_qs606(
    ew_path: pathlib.Path, sc_path: pathlib.Path, rename: bool = True
) -> dict[str, pd.DataFrame]:
    def rename_cols(name: str) -> str:
        """Renames the occupation data columns"""
        match = re.match("^(5[1-3])|(82)[1]?", name)
        if match:
            return match.group(0)
        if name.startswith("mnemonic"):
            return "zone"
        if name.startswith("All"):
            return "total"
        return name

    qs606: dict[str, pd.DataFrame] = {}
    for key, path in (("EW", ew_path), ("SC", sc_path)):
        qs606[key] = (
            utilities.read_csv(
                path,
                columns=QS606_HEADERS[key],
                skiprows=QS606_HEADER_FOOTER[key][0],
                skipfooter=QS606_HEADER_FOOTER[key][1],
                engine="python",
            )
            .dropna(axis=1, how="all")
            .dropna(axis=0, how="any")
        )

        if rename:
            qs606[key] = qs606[key].rename(columns=rename_cols)

    return qs606
