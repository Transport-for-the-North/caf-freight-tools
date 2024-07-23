# -*- coding: utf-8 -*-
"""
    Module to calculate the productions and attractions for the LGV
    service segment in the model zone system.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# Third party imports
import pandas as pd

# Local imports
from .. import utilities, errors, data_utils
from . import lgv_inputs


##### CLASSES #####
class ServiceTripEnds:
    """Functionality for generating the LGV service segment trip ends.

    Parameters
    ----------
    household_paths : LFT.data_utils.DataPaths
        Paths to the CSVs containing the household projections data and
        the relevant zone correspondence.
    bres_paths : LFT.data_utils.DataPaths
        Paths to the CSVs containing the BRES data and the relevant
        zone correpondence.
    service_trips : Path
        Path to Excel workbook containing 'Annual Service Trips'
        sheet which should contain column names as defined in
        `SERVICE_TRIPS_HEADER` and segments contained in
        `SERVICE_TRIPS_SEGMENTS`.
    scale_factor : float
        Factor for scaling the service trips to the model year.
    model_zones : pd.Series
        Full list of model zones.

    Raises
    ------
    ValueError
        If `scale_factor` isn't a positive numeric value.
    """

    BRES_AGGREGATION = {
        "Office": list(lgv_inputs.letters_range("I", "P")),
        "Other": list(lgv_inputs.letters_range(end="H"))
        + list(lgv_inputs.letters_range("Q", "U")),
    }
    SERVICE_TRIPS_HEADER = {"Segment": str, "Annual Service Trips": int}
    SERVICE_TRIPS_SEGMENTS = ("Residential", "Office", "All Other")
    SERVICE_TRIPS_SHEET = "Annual Service Trips"

    def __init__(
        self,
        household_paths: data_utils.DataPaths,
        bres_paths: data_utils.DataPaths,
        service_trips: Path,
        scale_factor: float,
        model_zones: pd.Series,
    ):
        """Initialise class by checking input files exist and are expected type."""
        # Check all given parameters
        self._check_paths(household_paths, bres_paths, service_trips)
        try:
            self._scale_factor = float(scale_factor)
        except ValueError as e:
            raise ValueError(
                f"scale_factor should be a numeric type not '{type(scale_factor)}'"
            ) from e
        if self._scale_factor <= 0:
            raise ValueError(f"scale_factor should be >= 0 not {self._scale_factor}")
        # Initlise instance variables defined later
        self.households = None
        self.bres = None
        self.total_trips = None
        self.model_zones = model_zones
        self._trip_proportions = None
        self._trips = None
        self._trip_ends = None

    def _check_paths(
        self,
        household_paths: data_utils.DataPaths,
        bres_paths: data_utils.DataPaths,
        service_trips: Path,
    ):
        """Checks the input files exist and are the expected type."""
        extensions = (".csv", ".txt")
        for nm, paths in (("Households", household_paths), ("BRES", bres_paths)):
            utilities.check_file_path(paths.path, f"{nm} data", *extensions)
            utilities.check_file_path(paths.zc_path, f"{nm} lookup", *extensions)
        self._household_paths = household_paths
        self._bres_paths = bres_paths
        self._trips_path = utilities.check_file_path(
            service_trips, "Service trips", ".xlsx", return_path=True
        )

    @property
    def inputs_summary(self) -> pd.DataFrame:
        """pd.DataFrame : Summary table of class input parameters."""
        return pd.DataFrame.from_dict(
            {
                "Household Data Path": str(self._household_paths.path),
                "Household Zone Correspondence Path": str(self._household_paths.zc_path),
                "BRES Data Path": str(self._bres_paths.path),
                "BRES Zone Correpondence Path": str(self._bres_paths.zc_path),
                "Annual Service Trips Path": str(self._trips_path),
                "Scale Factor": self._scale_factor,
            },
            orient="index",
            columns=["Value"],
        )

    def read(self):
        """Read the input data and perform any necessary conversions.

        Raises
        ------
        errors.MissingDataError
            If segments are missing from the `service_trips` input.

        See Also
        --------
        .lgv_inputs.household_projections
            Reads and converts household input CSV.
        .lgv_inputs.filtered_bres
            Reads, filters and converts the BRES input CSV.
        """
        self.households = lgv_inputs.household_projections(
            self._household_paths.path, self._household_paths.zc_path
        )
        self.households.set_index("Zone", inplace=True)
        self.bres = lgv_inputs.filtered_bres(
            self._bres_paths.path, self._bres_paths.zc_path, self.BRES_AGGREGATION
        )
        self.bres.set_index("Zone", inplace=True)
        # Read and check service trips data
        self.total_trips = utilities.read_multi_sheets(
            self._trips_path,
            {self.SERVICE_TRIPS_SHEET: self.SERVICE_TRIPS_HEADER},
            index_col=0,
        )[self.SERVICE_TRIPS_SHEET]
        self.total_trips.index = self.total_trips.index.str.title().str.strip()
        missing = [s for s in self.SERVICE_TRIPS_SEGMENTS if s not in self.total_trips.index]
        if missing:
            raise errors.MissingDataError("Service trips", missing)
        self.total_trips = self.total_trips.loc[self.SERVICE_TRIPS_SEGMENTS, :].copy()
        # Factor service trips to model year
        self.total_trips *= self._scale_factor

    @property
    def trip_proportions(self) -> pd.DataFrame:
        """pd.DataFrame : Proportion of input data for each zone, with
        zone number as index (Zone) and columns Households, Office
        (employees) and Other (employees). Each column sums to 1.
        """
        if self._trip_proportions is None:
            if self.households is None or self.bres is None:
                raise ValueError(
                    "cannot calculate trip proportions until input data "
                    "has been read, call `ServiceTripEnds.read` first"
                )
            trip_data = pd.concat([self.households, self.bres], axis=1)
            self._trip_proportions = trip_data / trip_data.sum(axis=0)
        return self._trip_proportions

    @property
    def trips(self) -> pd.DataFrame:
        """pd.DataFrame : Number of trips for each zone (index) and
        each of the segments (columns) Residential, Office and Other.
        """
        if self._trips is None:
            if self.total_trips is None:
                raise ValueError(
                    "cannot calculate trips until input data has "
                    "been read, call `ServiceTripEnds.read` first"
                )
            self._trips = self.trip_proportions.copy()
            self._trips.rename(columns={"Households": "Residential"}, inplace=True)
            self._trips["Residential"] *= self.total_trips.at[
                "Residential", "Annual Service Trips"
            ]
            self._trips["Office"] *= self.total_trips.at["Office", "Annual Service Trips"]
            self._trips["Other"] *= self.total_trips.at["All Other", "Annual Service Trips"]
        return self._trips

    @property
    def trip_ends(self) -> pd.DataFrame:
        """pd.DataFrame : Productions and Attractions trip
        ends (columns) for all zones (index).
        """
        if self._trip_ends is None:
            # Aggregate trips together
            tot_trips = self.trips.sum(axis=1)
            # Divide trips by 2 to get productions and attractions (both are identical)
            self._trip_ends = pd.DataFrame(
                {"Productions": tot_trips / 2, "Attractions": tot_trips / 2}
            )

            self._trip_ends = self._trip_ends.reindex(
                index=pd.Index(self.model_zones), fill_value=0
            )

        return self._trip_ends
