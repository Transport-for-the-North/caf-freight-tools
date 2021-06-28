# -*- coding: utf-8 -*-
"""
    Module to calculate the delivery trips for the LGV model.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path
from typing import Callable

# Third party imports
import pandas as pd

# Local imports
from . import lgv_inputs
from .. import utilities, errors


##### CLASSES #####
class DeliveryTripEnds:
    """Functionality for generating the LGV delivery segment trip ends.

    Parameters
    ----------
    voa_paths : tuple[Path, Path]
        - Path to the CSV containing the VOA rateable values data.
        - Path to the postcode zone correspondence file to convert
          VOA data to model zone system.
    bres_paths : tuple[Path, Path]
        - Path to the CSV containing the BRES data.
        - Path to the zone correspondence CSV for converting the
          BRES data to the model zone system.
    household_paths : tuple[Path, Path]
        - Path to the CSV containing the household projections data.
        - Path to the zone correpondence file to convert household
          data to the model zone system.
    parameters_path : Path
        Path to Excel Workbook containing sheet with the delivery
        segment parameters.
    year : int
        Model year, should be between 2000 and 2100.
    """

    BRES_AGGREGATION = {"Employees": list(lgv_inputs.letters_range(end="U"))}
    VOA_SCAT_CODES = (217, 267)
    PARAMETERS_SHEET = "Delivery Segment Parameters"
    PARAMETERS_HEADER = {"Parameter": str, "Value": str}
    PARAMETERS: dict[str, tuple[str, Callable]] = {
        "trips_parcel_stem": ("Annual Trip Productions - Parcel Stem", float),
        "trips_parcel_bush": ("Annual Trips - Parcel Bush", float),
        "trips_grocery": ("Annual Trips - Grocery Bush", float),
        "b2c": ("B2C vs B2B Weighting", float),
        "length_parcel_stem": ("Annual Trip Length - Parcel Stem (kms)", float),
        "length_parcel_bush": ("Annual Trip Length - Parcel Bush (kms)", float),
        "length_grocery": ("Annual Trip Length - Grocery (kms)", float),
        "intra_parcel": ("Intra-Zonal Proportions - Parcel", float),
        "intra_grocery": ("Intra-Zonal Proportions - Grocery", float),
        "bush_cut_off": ("Bush Cut-off (kms)", float),
        "voa_fill_func": ("VOA Infill Function", str),
    }

    def __init__(
        self,
        voa_paths: tuple[Path, Path],
        bres_paths: tuple[Path, Path],
        household_paths: tuple[Path, Path],
        parameters_path: Path,
        year: int,
    ):
        """Initialise class by checking inputs files exist and are expected type."""
        self._check_paths(voa_paths, bres_paths, household_paths, parameters_path)
        try:
            self._year = int(year)
        except ValueError as e:
            raise ValueError(f"year should be an integer not '{type(year)}'") from e
        yr_range = (2000, 2100)
        if self._year < min(yr_range) or self._year > max(yr_range):
            raise ValueError(
                f"`year` should be between {min(yr_range)} "
                f"and {max(yr_range)} not {year}"
            )
        # Initialise instance variables
        self.depots = None
        self.bres = None
        self.households = None
        self.parameters = None
        self._trip_proportions = None
        self._parcel_proportions = None
        self._parcel_stem_trip_ends = None
        self._parcel_bush_trip_ends = None
        self._grocery_bush_trip_ends = None

    def _check_paths(
        self,
        voa_paths: tuple[Path, Path],
        bres_paths: tuple[Path, Path],
        household_paths: tuple[Path, Path],
        parameters_path: Path,
    ):
        """Checks the input files exist and are the expected type."""
        self._voa_path = utilities.check_file_path(
            voa_paths[0], "VOA data", ".csv", ".txt", return_path=True
        )
        self._voa_zc = utilities.check_file_path(
            voa_paths[1], "VOA lookup", ".csv", ".txt", return_path=True
        )
        self._bres_path = utilities.check_file_path(
            bres_paths[0], "BRES data", ".csv", ".txt", return_path=True
        )
        self._bres_zc = utilities.check_file_path(
            bres_paths[1], "BRES lookup", ".csv", ".txt", return_path=True
        )
        self._household_path = utilities.check_file_path(
            household_paths[0], "Household data", ".csv", ".txt", return_path=True
        )
        self._household_zc = utilities.check_file_path(
            household_paths[1], "Household lookup", ".csv", ".txt", return_path=True
        )
        self._parameters_path = utilities.check_file_path(
            parameters_path, "Delivery Parameters", ".xlsx", return_path=True
        )

    @property
    def inputs_summary(self) -> pd.DataFrame:
        """pd.DataFrame : Summary table of class input parameters."""
        return pd.DataFrame.from_dict(
            {
                "VOA Data Path": str(self._voa_path),
                "VOA Zone Correpondence Path": str(self._voa_zc),
                "BRES Data Path": str(self._bres_path),
                "BRES Zone Correpondence Path": str(self._bres_zc),
                "Household Data Path": str(self._household_path),
                "Household Zone Correspondence Path": str(self._household_zc),
                "Delivery Parameters Path": str(self._parameters_path),
                "Model Year": self._year,
            },
            orient="index",
            columns=["Value"],
        )

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
        self.parameters = self.read_parameters(self._parameters_path)
        self.depots = lgv_inputs.voa_ratings_list(
            self._voa_path,
            self.VOA_SCAT_CODES,
            self._voa_zc,
            year=self._year,
            fill_func=self.parameters["voa_fill_func"],
        )
        self.depots.rename(
            columns={"rateable_value": "Depots", "zone": "Zone"}, inplace=True
        )
        self.depots.set_index("Zone", inplace=True)
        self.households = lgv_inputs.household_projections(
            self._household_path, self._household_zc
        )
        self.households.set_index("Zone", inplace=True)
        self.bres = lgv_inputs.filtered_bres(
            self._bres_path, self._bres_zc, self.BRES_AGGREGATION
        )
        self.bres.set_index("Zone", inplace=True)

    @classmethod
    def read_parameters(cls, path: Path) -> dict[str, float]:
        """Extract expected `PARAMETERS` from the given spreadsheet.

        Parameters
        ----------
        path : Path
            Path to the Excel Workbook containing a sheet with
            the delivery segment parameters.

        Returns
        -------
        dict[str, float]
            Contains keys from `PARAMETERS` list with their
            corresponding value from the input file.

        Raises
        ------
        errors.MissingDataError
            If any of `PARAMETERS` cannot be found in the input
            worksheet.

        See Also
        --------
        PARAMETERS: Lists all required parameter names and types
            (values) and internal names (keys).
        PARAMETERS_SHEET: Expected name of the sheet in the workbook.
        PARAMETERS_HEADER: Expected column names and types in the sheet.
        """
        df = utilities.read_multi_sheets(
            path, {cls.PARAMETERS_SHEET: cls.PARAMETERS_HEADER}
        )[cls.PARAMETERS_SHEET]
        df["Parameter"] = df["Parameter"].str.lower().str.strip()
        df.set_index("Parameter", inplace=True)
        params = {}
        missing = []
        for nm, (p, type_func) in cls.PARAMETERS.items():
            try:
                # All values for type_func are callable
                # pylint: disable=not-callable
                params[nm] = type_func(df.at[p.lower().strip(), "Value"])
            except KeyError:
                missing.append(p)
            except ValueError as e:
                raise errors.IncorrectParameterError(
                    df.at[p.lower().strip(), "Value"],
                    parameter=p,
                    # All values for type_func have __name__
                    expected=type_func.__name__,  # pylint: disable=no-member
                ) from e
        if missing:
            raise errors.MissingDataError("Delivery Parameters", missing)
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
            customer = self.trip_proportions["Households"] * self.parameters["b2c"]
            business = self.trip_proportions["Employees"] * (1 - self.parameters["b2c"])
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
            for nm, data in (
                ("Attractions", self.parcel_proportions),
                ("Productions", self.depots),
            ):
                trip_ends.append(self.parameters["trips_parcel_stem"] * data)
                if isinstance(trip_ends[-1], pd.DataFrame):
                    trip_ends[-1] = trip_ends[-1].squeeze()
                trip_ends[-1].name = nm
            self._parcel_stem_trip_ends = pd.concat(trip_ends, axis=1)
            self._parcel_stem_trip_ends.fillna(0, inplace=True)
        return self._parcel_stem_trip_ends.copy()

    @property
    def parcel_bush_trip_ends(self) -> pd.DataFrame:
        """pd.DataFrame : Trip ends for the parcel bush segment, contains
        Origins and Destinations (columns) for each Zone (index).
        """
        if self._parcel_bush_trip_ends is None:
            self._check_parameters()
            trips = self.parameters["trips_parcel_bush"] * self.parcel_proportions
            self._parcel_bush_trip_ends = pd.DataFrame(
                {"Origins": trips, "Destinations": trips}
            )
        return self._parcel_bush_trip_ends.copy()

    @property
    def grocery_bush_trip_ends(self) -> pd.DataFrame:
        """pd.DataFrame : Trip ends for the grocery bush segment, contains
        Origins and Destinations (columns) for each Zone (index).
        """
        if self._grocery_bush_trip_ends is None:
            self._check_parameters()
            trips = self.parameters["trips_grocery"] * self.households
            if isinstance(trips, pd.DataFrame):
                trips = trips.squeeze()
            self._grocery_bush_trip_ends = pd.DataFrame(
                {"Origins": trips, "Destinations": trips}
            )
        return self._grocery_bush_trip_ends.copy()
