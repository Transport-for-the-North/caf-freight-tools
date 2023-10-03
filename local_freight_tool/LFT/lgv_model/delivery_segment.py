# -*- coding: utf-8 -*-
"""
    Module to calculate the delivery trips for the LGV model.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# Third party imports
import pandas as pd
import numpy as np
import pydantic
from pydantic import fields

# Local imports
from . import lgv_inputs
from .. import utilities, errors, data_utils


##### FUNCTIONS #####
def zone_list(value: str) -> list[int]:
    """Converts string of numbers separated by commas to list of integers.

    Parameters
    ----------
    value : str
        Comma-separated string of integers.

    Returns
    -------
    list[int]
        List of integers from the `value` string.

    Raises
    ------
    ValueError
        If any of the items in the list cannot be
        converted to integers.
    """
    if value is None:
        return None
    if isinstance(value, float):
        if np.isnan(value):
            return None
        raise TypeError(f"`value` should be string not {type(value)}")
    try:
        return [int(i) for i in value.split(",") if i.strip() != ""]
    except ValueError as error:
        raise ValueError(
            f"{value!r} cannot be converted to list of zones (integers)"
        ) from error


##### CLASSES #####
class DeliveryParameters(pydantic.BaseModel):
    """Parameters for delivery segment to read from input spreadsheet."""

    trips_parcel_stem: float = fields.Field(
        alias="Annual Trip Productions - Parcel Stem", ge=0, title="Test"
    )
    trips_parcel_bush: float = fields.Field(alias="Annual Trips - Parcel Bush", ge=0)
    trips_grocery: float = fields.Field(alias="Annual Trips - Grocery Bush", ge=0)
    b2c: float = fields.Field(alias="B2C vs B2B Weighting", ge=0, le=1)
    depots_infill: list[int] = fields.Field(
        alias="Depots Infill Zones", default_factory=list, unique_items=True
    )

    @pydantic.validator("depots_infill", pre=True)
    def _split_str(cls, value: str) -> list:  # pylint: disable=no-self-argument
        return value.split(",")


class DeliveryTripEnds:
    """Functionality for generating the LGV delivery segment trip ends.

    Parameters
    ----------
    warehouse_paths : DataPaths
        - Path to the CSV containing the warehouse floorspace data.
        - Path to the LSOA zone correspondence file to convert
          data to model zone system.
    bres_paths : DataPaths
        - Path to the CSV containing the BRES data.
        - Path to the zone correspondence CSV for converting the
          BRES data to the model zone system.
    household_paths : DataPaths
        - Path to the CSV containing the household projections data.
        - Path to the zone correspondence file to convert household
          data to the model zone system.
    parameters_path : Path
        Path to Excel Workbook containing sheet with the delivery
        segment parameters.
    year : int
        Model year, should be between 2000 and 2100.
    model_zones : pd.Series
        Full list of model zones.
    """

    BRES_AGGREGATION = {"Employees": list(lgv_inputs.letters_range(end="U"))}
    PARAMETERS_SHEET = "Delivery Segment Parameters"
    PARAMETERS_HEADER = {"Parameter": str, "Value": str}

    def __init__(
        self,
        warehouse_paths: data_utils.DataPaths,
        bres_paths: data_utils.DataPaths,
        household_paths: data_utils.DataPaths,
        parameters_path: Path,
        year: int,
        model_zones: pd.Series,
        growth_factor: float,
    ):
        """Initialise class by checking inputs files exist and are expected type."""
        self._check_paths(warehouse_paths, bres_paths, household_paths, parameters_path)
        try:
            self._year = int(year)
        except ValueError as error:
            raise ValueError(f"year should be an integer not '{type(year)}'") from error
        yr_range = (2000, 2100)
        if self._year < min(yr_range) or self._year > max(yr_range):
            raise ValueError(
                f"`year` should be between {min(yr_range)} " f"and {max(yr_range)} not {year}"
            )
        # Initialise instance variables
        self.depots = None
        self.bres = None
        self.households = None
        self.parameters = None
        self.model_zones = model_zones
        self.growth_factor = growth_factor
        self._trip_proportions = None
        self._parcel_proportions = None
        self._parcel_stem_trip_ends = None
        self._parcel_bush_trip_ends = None
        self._grocery_bush_trip_ends = None

    def _check_paths(
        self,
        warehouse_paths: data_utils.DataPaths,
        bres_paths: data_utils.DataPaths,
        household_paths: data_utils.DataPaths,
        parameters_path: Path,
    ):
        """Checks the input files exist and are the expected type."""
        extensions = (".csv", ".txt")
        for name, paths in (
            ("Warehouse", warehouse_paths),
            ("Households", household_paths),
            ("BRES", bres_paths),
        ):
            utilities.check_file_path(paths.path, f"{name} data", *extensions)
            utilities.check_file_path(paths.zc_path, f"{name} lookup", *extensions)

        self._warehouse_paths = warehouse_paths
        self._household_paths = household_paths
        self._bres_paths = bres_paths
        self._parameters_path = utilities.check_file_path(
            parameters_path, "Delivery Parameters", ".xlsx", return_path=True
        )

    @property
    def inputs_summary(self) -> pd.DataFrame:
        """pd.DataFrame : Summary table of class input parameters."""
        return pd.DataFrame.from_dict(
            {
                "Warehouse Data Path": str(self._warehouse_paths.path),
                "Warehouse Zone Correspondence Path": str(self._warehouse_paths.zc_path),
                "BRES Data Path": str(self._bres_paths.path),
                "BRES Zone Correspondence Path": str(self._bres_paths.zc_path),
                "Household Data Path": str(self._household_paths.path),
                "Household Zone Correspondence Path": str(self._household_paths.zc_path),
                "Delivery Parameters Path": str(self._parameters_path),
                "Model Year": self._year,
            },
            orient="index",
            columns=["Value"],
        )

    def _infill_depots(self, depots: pd.DataFrame) -> pd.DataFrame:
        depots = depots.copy()
        depots.columns = ["Depots"]

        if self.parameters.depots_infill is None:
            return depots

        missing = [i for i in self.parameters.depots_infill if i not in self.households.index]
        if missing:
            raise errors.MissingDataError("Households for zones", missing)

        already_zones = []
        update_zones = []
        for zone in self.parameters.depots_infill:
            if zone not in depots.index or np.isnan(depots.at[zone, "Depots"]):
                update_zones.append(zone)
            else:
                already_zones.append(zone)

        if already_zones:
            # TODO(MB) Add logging to LFT
            print(
                f"{len(already_zones)} zones already have non-zero "
                "values in warehouse data so won't be infilled"
            )

        print(f"warehouse data for {len(update_zones)} zones will be infilled")
        if len(update_zones) == 0:
            return depots

        # Calculate floorspace of depots per household
        depots_per_hh: float = np.nansum(
            depots.loc[~depots.index.isin(update_zones)].values
        ) / np.nansum(self.households.loc[~self.households.index.isin(update_zones)].values)

        new_depots: pd.DataFrame = self.households.loc[
            self.households.index.isin(update_zones)
        ].copy()
        new_depots = new_depots * depots_per_hh

        new_depots.columns = depots.columns
        depots = pd.concat([depots.drop(new_depots.index, errors="ignore"), new_depots])
        return depots.fillna(0)

    def read(self):
        """Read the input data and perform any necessary conversions.

        See Also
        --------
        read_parameters: Reads the parameters spreadsheet.
        .lgv_inputs.household_projections
            Reads and converts household input CSV.
        .lgv_inputs.filtered_bres
            Reads, filters and converts the BRES input CSV.
        """
        self.parameters = self.read_parameters(self._parameters_path, self.growth_factor)
        self.depots = lgv_inputs.load_warehouse_floorspace(
            self._warehouse_paths.path, self._warehouse_paths.zc_path
        )

        self.households = lgv_inputs.household_projections(
            self._household_paths.path, self._household_paths.zc_path
        )
        self.households.set_index("Zone", inplace=True)

        self.depots = self._infill_depots(self.depots)

        self.bres = lgv_inputs.filtered_bres(
            self._bres_paths.path, self._bres_paths.zc_path, self.BRES_AGGREGATION
        )
        self.bres.set_index("Zone", inplace=True)

    @classmethod
    def read_parameters(cls, path: Path, growth_factor: float) -> DeliveryParameters:
        """Extract expected parameters from the given spreadsheet.

        Parameters
        ----------
        path : Path
            Path to the Excel Workbook containing a sheet with
            the delivery segment parameters.

        Returns
        -------
        DeliveryParameters
            Delivery parameters with their corresponding values.

        Raises
        ------
        errors.MissingDataError
            If any parameters are missing from the spreadsheet.

        See Also
        --------
        PARAMETERS_SHEET: Expected name of the sheet in the workbook.
        PARAMETERS_HEADER: Expected column names and types in the sheet.
        """
        df = utilities.read_multi_sheets(path, {cls.PARAMETERS_SHEET: cls.PARAMETERS_HEADER})[
            cls.PARAMETERS_SHEET
        ]
        header = list(cls.PARAMETERS_HEADER)
        params: pd.Series = df.set_index(header[0])[header[1]]

        try:
            params: DeliveryParameters = DeliveryParameters.parse_obj(params.to_dict())
        except pydantic.ValidationError as error:
            raise errors.MissingDataError("Delivery Parameters", str(error)) from error

        params.trips_parcel_stem *= growth_factor
        params.trips_parcel_bush *= growth_factor
        params.trips_grocery *= growth_factor

        return params

    @property
    def trip_proportions(self) -> pd.DataFrame:
        """pd.DataFrame : Proportion of input data for each zone, with
        zone number as index (Zone) and columns Depots, Households and
        Employees. Each column sums to 1.
        """
        if self._trip_proportions is None:
            if self.depots is None or self.households is None or self.bres is None:
                raise ValueError(
                    "cannot calculate trip proportions until input data "
                    "has been read, call `DeliveryTripEnds.read` first"
                )
            trip_data = pd.concat([self.depots, self.households, self.bres], axis=1)
            self._trip_proportions = trip_data / trip_data.sum(axis=0)
            self._trip_proportions.fillna(0, inplace=True)
        return self._trip_proportions.copy()

    @property
    def parcel_proportions(self) -> pd.DataFrame:
        """pd.DataFrame : Proportion of delivery trips to be attracted
        to each zone, calculated as the weighted sum of the Households
        and Employees proportions. The business-to-customer parameter
        is used as the weighting and the final proportions are
        normalised.
        """
        if self._parcel_proportions is None:
            # Use the business-to-customer weighting when adding the proportions
            customer = self.trip_proportions["Households"] * self.parameters.b2c
            business = self.trip_proportions["Employees"] * (1 - self.parameters.b2c)
            total = customer + business
            # Normalise the total
            self._parcel_proportions = total / total.sum()
        return self._parcel_proportions.copy()

    def _check_parameters(self) -> None:
        """Raises `ValueError` if `parameters` instance variable is None."""
        if self.parameters is None:
            raise ValueError(
                "cannot calculate trip ends until input data "
                "has been read, call `DeliveryTripEnds.read` first"
            )

    @property
    def parcel_stem_trip_ends(self) -> pd.DataFrame:
        """pd.DataFrame : Trip ends for the parcel stem segment, contains
        Productions and Attractions (columns) for each Zone (index).
        """
        if self._parcel_stem_trip_ends is None:
            self._check_parameters()
            trip_ends = []
            for name, data in (
                ("Attractions", self.parcel_proportions),
                ("Productions", self.trip_proportions["Depots"]),
            ):
                trip_ends.append(self.parameters.trips_parcel_stem * data)
                if isinstance(trip_ends[-1], pd.DataFrame):
                    trip_ends[-1] = trip_ends[-1].squeeze()
                trip_ends[-1].name = name
            self._parcel_stem_trip_ends = pd.concat(trip_ends, axis=1)
            self._parcel_stem_trip_ends.fillna(0, inplace=True)

            self._parcel_stem_trip_ends = self._parcel_stem_trip_ends.reindex(
                index=pd.Index(self.model_zones), fill_value=0
            )

        return self._parcel_stem_trip_ends.copy()

    @property
    def parcel_bush_trip_ends(self) -> pd.DataFrame:
        """pd.DataFrame : Trip ends for the parcel bush segment, contains
        Origins and Destinations (columns) for each Zone (index).
        """
        if self._parcel_bush_trip_ends is None:
            self._check_parameters()
            trips = self.parameters.trips_parcel_bush * self.parcel_proportions
            self._parcel_bush_trip_ends = pd.DataFrame(
                {"Origins": trips, "Destinations": trips}
            )

            self._parcel_bush_trip_ends = self._parcel_bush_trip_ends.reindex(
                index=pd.Index(self.model_zones), fill_value=0
            )

        return self._parcel_bush_trip_ends.copy()

    @property
    def grocery_bush_trip_ends(self) -> pd.DataFrame:
        """pd.DataFrame : Trip ends for the grocery bush segment, contains
        Origins and Destinations (columns) for each Zone (index).
        """
        if self._grocery_bush_trip_ends is None:
            self._check_parameters()
            trips = self.parameters.trips_grocery * self.trip_proportions["Households"]
            if isinstance(trips, pd.DataFrame):
                trips = trips.squeeze()
            self._grocery_bush_trip_ends = pd.DataFrame(
                {"Origins": trips, "Destinations": trips}
            )

            self._grocery_bush_trip_ends = self._grocery_bush_trip_ends.reindex(
                index=pd.Index(self.model_zones), fill_value=0
            )

        return self._grocery_bush_trip_ends.copy()
