# -*- coding: utf-8 -*-
"""
    Module to calculate the productions and attractions for the LGV
    service segment in the model zone system.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# Third party imports

# Local imports
from .. import utilities, errors
from . import lgv_inputs


##### CLASSES #####
class ServiceTripEnds:
    """Functionality for generating the LGV service segment trip ends.

    Parameters
    ----------
    household_paths : tuple[Path, Path]
        - Path to the CSV containing the household projections data.
        - Path to the zone correpondence file to convert household
          data to the model zone system.
    bres_paths : tuple[Path, Path]
        - Path to the CSV containing the BRES data.
        - Path to the zone correspondence CSV for converting the
          BRES data to the model zone system.
    service_trips : Path
        Path to CSV containing service trips data should contain
        column names as defined in `SERVICE_TRIPS_HEADER` and
        segments contained in `SERVICE_TRIPS_SEGMENTS`.
    scale_factor : float
        Factor for scaling the service trips to the model year.

    Raises
    ------
    ValueError
        If `scale_factor` isn't a positive numeric value.

    See Also
    --------
    .lgv_inputs: Module with functions for reading some inputs.
    """

    BRES_AGGREGATION = {
        "office": list(lgv_inputs.letters_range("I", "P")),
        "other": list(lgv_inputs.letters_range(end="H"))
        + list(lgv_inputs.letters_range("Q", "U")),
    }
    SERVICE_TRIPS_HEADER = {"Segment": str, "Annual Service Trips": int}
    SERVICE_TRIPS_SEGMENTS = ("Residential", "Office", "All Other")

    def __init__(
        self,
        household_paths: tuple[Path, Path],
        bres_paths: tuple[Path, Path],
        service_trips: Path,
        scale_factor: float,
    ):
        """Initilise class by checking input files exist and are expected type."""
        self._household_path = utilities.check_file_path(
            household_paths[0], "Household data", ".csv", ".txt", return_path=True
        )
        self._household_zc = utilities.check_file_path(
            household_paths[1], "Household lookup", ".csv", ".txt", return_path=True
        )
        self._bres_path = utilities.check_file_path(
            bres_paths[0], "BRES data", ".csv", ".txt", return_path=True
        )
        self._bres_zc = utilities.check_file_path(
            bres_paths[1], "BRES lookup", ".csv", ".txt", return_path=True
        )
        self._trips_path = utilities.check_file_path(
            service_trips, "Service trips", ".csv", ".txt", return_path=True
        )
        try:
            self._scale_factor = float(scale_factor)
        except ValueError as e:
            raise ValueError(
                f"scale_factor should be a numeric type not '{type(scale_factor)}'"
            ) from e
        if self._scale_factor <= 0:
            raise ValueError(f"scale_factor should be >= 0 not {self._scale_factor}")
        self.households = None
        self.bres = None
        self.total_trips = None

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
            self._household_path, self._household_zc
        )
        self.bres = lgv_inputs.filtered_bres(
            self._bres_path, self._bres_zc, self.BRES_AGGREGATION
        )
        # Read and check service trips data
        self.total_trips = utilities.read_csv(
            self._trips_path,
            "Service trips",
            columns=self.SERVICE_TRIPS_HEADER,
            index_col=0,
        )
        self.total_trips.index = self.total_trips.index.str.title().str.strip()
        missing = [
            s for s in self.SERVICE_TRIPS_SEGMENTS if s not in self.total_trips.index
        ]
        if missing:
            raise errors.MissingDataError("Service trips", missing)
        self.total_trips = self.total_trips.loc[self.SERVICE_TRIPS_SEGMENTS, :].copy()
        # Factor service trips to model year
        self.total_trips *= self._scale_factor


# TODO Remove test code
if __name__ == "__main__":
    hh_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Household Projections\UK_HH_projections_2018-MSOA.csv"
    )
    zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\NTEM to NoHAM Lookup\NTEM_to_NoHAM_zone_correspondence-updated-20210617.csv"
    )
    bres_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\BRES Data\BRES_2018_sections_GB_LSOA.csv"
    )
    bres_zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\lsoa_datazone_to_noham_zone_correspondence_missing_zones_added.csv"
    )
    service_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\LGV_service_trips-van_survey_2003.csv"
    )
    service_te = ServiceTripEnds(
        (hh_path, zc_path), (bres_path, bres_zc_path), service_path, 1.51
    )
    service_te.read()
    print(service_te.households, service_te.bres, service_te.total_trips, sep="\n")
