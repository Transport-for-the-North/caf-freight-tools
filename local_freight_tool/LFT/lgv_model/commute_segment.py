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
    household_paths : tuple[Path, Path]
        - Path to the CSV containing the household projections data.
        - Path to the zone correpondence file to convert household
          data to the model zone system.
    bres_paths : tuple[Path, Path]
        - Path to the CSV containing the BRES data.
        - Path to the zone correspondence CSV for converting the
          BRES data to the model zone system.
    qs606_paths : List[Path, Path, Path]
        - Path to CSV containing QS606EW data
        - Path to CSV containing QS606UK Scottish data
        - Path to the zone correspondence CSV for converting the QS606 data to
        the model zone system
        The QS606 CSVs must have column names as defined in `QS606_HEADERS`
    commuting_inputs_path : Path
        Path to XLSX containing sheets and column names as defined in
        `COMMUTING_INPUTS_SHEET_HEADERS`.
    scotland_wales_dwellings_paths : tuple(Path, Path)
        - Path to CSV containing 2017 and 2018 dwelling numbers for Wales and
        Scotland with columns as defined in `SC_W_DWELLINGS_HEADER`.
        - Path to LAD to model zone system zone correspondence CSV for
        converting the dwellings data to the model zone system
    england_dwellings_paths : tuple(Path, Path)
        - Path to XLSX containing MHCLGC Live Table 123 dwellings data for
        England, with sheets and column names as defined in
        `E_DWELLINGS_SHEET_HEADER`.
        - Path to LAD to model zone system zone correspondence CSV for
        converting the dwellings data to the model zone system.
    ndr_business_floorspace_paths : tuple(Path, Path)
        - Path to CSV containing NDR business floorspace data from tables
        FS2.0, FS3.0, FS4.0 and FS5.0, with column names as defined in
        `BUSINESS_FLOORSPACE_HEADER`.
        - Path to LSOA to model zone system zone correspondence CSV for
        converting the business floorspace data to model zone system.

    Raises
    ------
    

    See Also
    --------
    .lgv_inputs: Module with functions for reading some inputs.
    """

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

#     def __init__(
#         self,
#         household_paths: tuple[Path, Path],
#         bres_paths: tuple[Path, Path],
#         service_trips: Path,
#         scale_factor: float,
#     ):
#         """Initilise class by checking input files exist and are expected type."""
#         # Check all given parameters
#         self._check_paths(household_paths, bres_paths, service_trips)
#         try:
#             self._scale_factor = float(scale_factor)
#         except ValueError as e:
#             raise ValueError(
#                 f"scale_factor should be a numeric type not '{type(scale_factor)}'"
#             ) from e
#         if self._scale_factor <= 0:
#             raise ValueError(f"scale_factor should be >= 0 not {self._scale_factor}")
#         # Initlise instance variables defined later
#         self.households = None
#         self.bres = None
#         self.total_trips = None
#         self._trip_proportions = None
#         self._trips = None
#         self._trip_ends = None

#     def _check_paths(
#         self,
#         household_paths: tuple[Path, Path],
#         bres_paths: tuple[Path, Path],
#         service_trips: Path,
#     ):
#         """Checks the input files exist and are the expected type."""
#         self._household_path = utilities.check_file_path(
#             household_paths[0], "Household data", ".csv", ".txt", return_path=True
#         )
#         self._household_zc = utilities.check_file_path(
#             household_paths[1], "Household lookup", ".csv", ".txt", return_path=True
#         )
#         self._bres_path = utilities.check_file_path(
#             bres_paths[0], "BRES data", ".csv", ".txt", return_path=True
#         )
#         self._bres_zc = utilities.check_file_path(
#             bres_paths[1], "BRES lookup", ".csv", ".txt", return_path=True
#         )
#         self._trips_path = utilities.check_file_path(
#             service_trips, "Service trips", ".csv", ".txt", return_path=True
#         )

#     @property
#     def inputs_summary(self) -> pd.DataFrame:
#         """pd.DataFrame : Summary table of class input parameters."""
#         return pd.DataFrame.from_dict(
#             {
#                 "Household Data Path": str(self._household_path),
#                 "Household Zone Correspondence Path": str(self._household_zc),
#                 "BRES Data Path": str(self._bres_path),
#                 "BRES Zone Correpondence Path": str(self._bres_zc),
#                 "Annual Service Trips Path": str(self._trips_path),
#                 "Scale Factor": self._scale_factor,
#             },
#             orient="index",
#             columns=["Value"],
#         )

#     def read(self):
#         """Read the input data and perform any necessary conversions.

#         Raises
#         ------
#         errors.MissingDataError
#             If segments are missing from the `service_trips` input.

#         See Also
#         --------
#         .lgv_inputs.household_projections
#             Reads and converts household input CSV.
#         .lgv_inputs.filtered_bres
#             Reads, filters and converts the BRES input CSV.
#         """
#         self.households = lgv_inputs.household_projections(
#             self._household_path, self._household_zc
#         )
#         self.households.set_index("Zone", inplace=True)
#         self.bres = lgv_inputs.filtered_bres(
#             self._bres_path, self._bres_zc, self.BRES_AGGREGATION
#         )
#         self.bres.set_index("Zone", inplace=True)
#         # Read and check service trips data
#         self.total_trips = utilities.read_csv(
#             self._trips_path,
#             "Service trips",
#             columns=self.SERVICE_TRIPS_HEADER,
#             index_col=0,
#         )
#         self.total_trips.index = self.total_trips.index.str.title().str.strip()
#         missing = [
#             s for s in self.SERVICE_TRIPS_SEGMENTS if s not in self.total_trips.index
#         ]
#         if missing:
#             raise errors.MissingDataError("Service trips", missing)
#         self.total_trips = self.total_trips.loc[self.SERVICE_TRIPS_SEGMENTS, :].copy()
#         # Factor service trips to model year
#         self.total_trips *= self._scale_factor

#     @property
#     def trip_proportions(self) -> pd.DataFrame:
#         """pd.DataFrame : Proportion of input data for each zone, with
#         zone number as index (Zone) and columns Households, Office
#         (employees) and Other (employees). Each column sums to 1.
#         """
#         if self._trip_proportions is None:
#             if self.households is None or self.bres is None:
#                 raise ValueError(
#                     "cannot calculate trip proportions until input data "
#                     "has been read, call `ServiceTripEnds.read` first"
#                 )
#             trip_data = pd.concat([self.households, self.bres], axis=1)
#             self._trip_proportions = trip_data / trip_data.sum(axis=0)
#         return self._trip_proportions

#     @property
#     def trips(self) -> pd.DataFrame:
#         """pd.DataFrame : Number of trips for each zone (index) and
#         each of the segments (columns) Residential, Office and Other.
#         """
#         if self._trips is None:
#             if self.total_trips is None:
#                 raise ValueError(
#                     "cannot calculate trips until input data has "
#                     "been read, call `ServiceTripEnds.read` first"
#                 )
#             self._trips = self.trip_proportions.copy()
#             self._trips.rename(columns={"Households": "Residential"}, inplace=True)
#             self._trips["Residential"] *= self.total_trips.at[
#                 "Residential", "Annual Service Trips"
#             ]
#             self._trips["Office"] *= self.total_trips.at[
#                 "Office", "Annual Service Trips"
#             ]
#             self._trips["Other"] *= self.total_trips.at[
#                 "All Other", "Annual Service Trips"
#             ]
#         return self._trips

#     @property
#     def trip_ends(self) -> pd.DataFrame:
#         """pd.DataFrame : Productions and Attractions trip
#         ends (columns) for all zones (index).
#         """
#         if self._trip_ends is None:
#             # Aggregate trips together
#             tot_trips = self.trips.sum(axis=1)
#             # Divide trips by 2 to get productions and attractions (both are identical)
#             self._trip_ends = pd.DataFrame(
#                 {"Productions": tot_trips / 2, "Attractions": tot_trips / 2}
#             )
#         return self._trip_ends


# # TODO Remove test code
# if __name__ == "__main__":
#     hh_path = Path(
#         r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Household Projections\UK_HH_projections_2018-MSOA.csv"
#     )
#     zc_path = Path(
#         r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\NTEM to NoHAM Lookup\NTEM_to_NoHAM_zone_correspondence-updated-20210617.csv"
#     )
#     bres_path = Path(
#         r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\BRES Data\BRES_2018_sections_GB_LSOA.csv"
#     )
#     bres_zc_path = Path(
#         r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\lsoa_datazone_to_noham_zone_correspondence_missing_zones_added.csv"
#     )
#     service_path = Path(
#         r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\LGV_service_trips-van_survey_2003.csv"
#     )
#     service_te = ServiceTripEnds(
#         (hh_path, zc_path), (bres_path, bres_zc_path), service_path, 1.51
#     )
#     service_te.read()
#     print(
#         service_te.inputs_summary,
#         service_te.households,
#         service_te.bres,
#         service_te.total_trips,
#         service_te.trip_proportions,
#         service_te.trips,
#         service_te.trip_ends,
#         sep="\n",
#     )