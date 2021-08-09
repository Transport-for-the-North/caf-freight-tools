"""
    Module to calculate the productions and attractions for the LGV
    commuting segment in the model zone system.
"""

##### IMPORTS #####
# Standard imports
from itertools import chain
import re

# Third party imports
import pandas as pd

# Local imports
from .. import utilities, errors
from ..rezone import Rezone
from . import lgv_inputs


##### CLASSES #####
class CommuteTripEnds:
    """Functionality for generating the LGV commuting segment trip productions
    and attractions.

    Parameters
    ----------
    inputs : dict
        Dictionary of paths to all required inputs. Must contain:
        - "commuting tables": Path to XLSX containing sheets and column names
        as defined in `COMMUTING_INPUTS_SHEET_HEADERS`.
        - "household projectons": Path to the CSV containing the household
        projections data by MSOA.
        - "BRES": Path to the CSV containing the BRES data by LSOA.
        - "QS606EW": Path to CSV containing QS606EW data by LSOA. Must have
        column names as defined in `QS606_HEADERS`.
        - "QS606SC": Path to CSV containing QS606UK Scottish data by datazone.
        Must have column names as defined in `QS606_HEADERS`.
        - "SC&W dwellings": Path to CSV containing 2017 and 2018 dwelling
        numbers for Wales and Scotland by LAD with columns as defined in
        `SC_W_DWELLINGS_HEADER`.
        - "E dwellings": Path to XLSX containing MHCLGC Live Table 123
        dwellings data for England by LAD, with sheets and column names as
        defined in `E_DWELLINGS_SHEET_HEADER`.
        - "NDR floorspace": Path to CSV containing NDR business floorspace
        data by LSOA from tables FS2.0, FS3.0, FS4.0 and FS5.0, with column
        names as defined in `BUSINESS_FLOORSPACE_HEADER`.
        - "LSOA lookup": Path to the zone correspondence CSV for converting
        from LSOA and Scottish datazone to the model zone system.
        - "MSOA lookup": Path to the zone correpondence file to convert
        household data to the model zone system.
        - "LAD lookup": Path to LAD to model zone system zone correspondence
        CSV.

    Raises
    ------

    See Also
    --------
    .lgv_inputs: Module with functions for reading some inputs.
    """

    INPUT_KEYS = {
        "commuting tables": ".xlsx",
        "household projections": ".csv",
        "BRES": ".csv",
        "QS606EW": ".csv",
        "QS606SC": ".csv",
        "SC&W dwellings": ".csv",
        "E dwellings": ".xlsx",
        "NDR floorspace": ".csv",
        "VOA": ".csv",
        "LSOA lookup": ".csv",
        "MSOA lookup": ".csv",
        "LAD lookup": ".csv",
        "Postcodes": ".csv",
    }

    COMMUTING_INPUTS_SHEET_HEADERS = {
        "Parameters": {"Parameter": str, "Value": float},
        "Commute trips by main usage": {"Main usage": str, "Trips": float},
        "Commute trips by land use": {"Land use at trip end": str, "Trips": float},
        "Commute VOA property weightings": {
            "Weight": float,
            "SCat code": int,
        },
    }
    BRES_AGGREGATION = {
        "Non-Construction": list(
            chain(
                lgv_inputs.letters_range(end="E"),
                lgv_inputs.letters_range(start="G", end="S"),
            )
        )
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
        "SC": "82. Transport and mobile machine drivers and operatives",
    }
    for key in S8_CATEGORIES:
        QS606_HEADERS[key] = QS606_HEADER.copy()
        QS606_HEADERS[key][S8_CATEGORIES[key]] = float

    E_DWELLINGS_HEADER = [
        "Current\nONS code",
        "Lower and Single Tier Authority Data",
        "Demolitions",
        "Net Additions",
    ]
    E_DWELLINGS_NEW_COLS = {"Current\nONS code": "zone"}

    BUSINESS_FLOORSPACE_HEADER = {"AREA_CODE": str}
    BUSINESS_FLOORSPACE_RENAME = {"AREA_CODE": "zone"}
    BUSINESS_CATEGORIES = ["Retail", "Office", "Industrial", "Other"]
    BUSINESS_FLOORSPACE_REMOVE_ROWS = ["K", "E9", "W9", "E1"]

    HH_PROJECTIONS_HEADER = {"Area Description": str, "HHs": float, "Jobs": float}
    HH_RENAME = {"Area Description": "zone", "HHs": "households", "Jobs": "jobs"}

    def __init__(self, input_paths: dict):
        """Initialise class by checking all input paths are in input dict and
        all input files exist"""
        missing = self.INPUT_KEYS.keys() - input_paths.keys()
        if missing:
            raise errors.MissingInputsError(missing)
        self.paths = self._check_paths(input_paths)

        # Initialise instance variables defined later
        self.params = {}
        self.voa_weightings = None
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

    def _check_paths(self, input_paths):
        """Checks the input file paths are of expected type.

        Parameters
        ----------
        input_paths : Dict
            Dictionary of paths to all required inputs, with keys as specified
            in `INPUT_KEYS`.

        Returns
        -------
        paths: Dict
            Dictionary of paths to all required inputs.
        """
        paths = {}
        for key in input_paths:
            if self.INPUT_KEYS[key] == ".csv":
                paths[key] = utilities.check_file_path(
                    input_paths[key],
                    key,
                    self.INPUT_KEYS[key],
                    ".txt",
                    return_path=True,
                )
            else:
                paths[key] = utilities.check_file_path(
                    input_paths[key], key, self.INPUT_KEYS[key], return_path=True
                )
        return paths

    @property
    def inputs_summary(self) -> pd.DataFrame:
        """Returns a summary table of class inputs.

        Returns
        -------
        pd.DataFrame
            Summary of inputs
        """
        return pd.DataFrame.from_dict(self.paths, orient="index", columns=["Path"])

    def _read_commute_tables(self):
        """Read in commuting tables input XLSX."""
        # read in XLSX
        commute_tables = utilities.read_multi_sheets(
            self.paths["commuting tables"], sheets=self.COMMUTING_INPUTS_SHEET_HEADERS
        )

        # write the input parameters to a dictionary
        self.params = utilities.to_dict(
            commute_tables["Parameters"], "Parameter", ("Value", float)
        )
        self.params["Model Year"] = int(self.params["Model Year"])

        # assign VOA weightings
        voa_weightings = commute_tables["Commute VOA property weightings"]
        voa_weightings.index = voa_weightings["SCat code"]
        self.voa_weightings = voa_weightings[["Weight"]]

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

        self.commute_trips_land_use = utilities.to_dict(
            commute_tables["Commute trips by land use"],
            key_col="Land use at trip end",
            val_col=("Trips", int),
        )

    def _read_zone_lookups(self):
        for key in self.paths:
            if key.endswith("lookup"):
                self.zone_lookups[key] = Rezone.read(self.paths[key], None)

    def _read_qs606(self):
        """Read in and rezone Census occupation data."""

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

        # If haven't yet read in parameters and zone lookups, read in
        if not self.params:
            self._read_commute_tables()

        if not self.zone_lookups:
            self._read_zone_lookups()

        # Read in both E&W and Scottish data
        qs606 = {}
        for key in self.S8_CATEGORIES:
            qs606[key] = (
                (
                    utilities.read_csv(
                        self.paths[f"QS606{key}"],
                        columns=self.QS606_HEADERS[key],
                        skiprows=7,
                        skipfooter=5,
                        engine="python",
                    )
                )
                .dropna(axis=1, how="all")
                .dropna(axis=0, how="any")
            )
            qs606[key] = qs606[key].rename(columns=rename_cols)

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
            self.zone_lookups["LSOA lookup"],
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
        sheet = f"{self.params['Model Year']}-{self.params['Model Year'] - 2000 + 1}"
        e_dwellings = (
            utilities.read_excel(
                self.paths["E dwellings"],
                columns=self.E_DWELLINGS_HEADER,
                skiprows=3,
                sheet_name=sheet,
            )
            .dropna(axis=1, how="all")
            .dropna(axis=0, how="any")
            .rename(columns=self.E_DWELLINGS_NEW_COLS)
            .drop(axis=1, labels=["Lower and Single Tier Authority Data"])
        )
        for col in ["Demolitions", "Net Additions"]:
            try:
                e_dwellings[col] = e_dwellings[col].astype(float)
            except ValueError as err:
                match = re.match(
                    r"could not convert \w+ to float", str(err), re.IGNORECASE
                )
                if match:
                    raise errors.NonNumericDataError(
                        name=f"{self.paths['E dwellings'].stem} column",
                        non_numeric=str(col),
                    )
                raise

        # Calculate total additional construction (net additions + demolitions)
        e_dwellings["additional dwellings"] = (
            e_dwellings["Net Additions"] + 2 * e_dwellings["Demolitions"]
        )

        # Calculate ratio of additional construction over net additional dwellings
        additional_net_ratio = (
            e_dwellings["additional dwellings"].sum()
            / e_dwellings["Net Additions"].sum()
        )

        # Read in Welsh and Scottish dwellings data
        sc_w_header = {
            "zone": str,
            str(self.params["Model Year"]): int,
            str(self.params["Model Year"] + 1): int,
        }
        sc_w_dwellings = utilities.read_csv(
            self.paths["SC&W dwellings"], columns=sc_w_header
        )

        # Calculate additional construction
        sc_w_dwellings.loc[:, "additional dwellings"] = (
            sc_w_dwellings.loc[:, str(self.params["Model Year"] + 1)]
            - sc_w_dwellings.loc[:, str(self.params["Model Year"])]
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
            self.zone_lookups["LAD lookup"],
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

        # Get years for NDR business floorspace columns from Model Year
        for column_start in [
            f"Floorspace_{self.params['Model Year']-1}-{str(self.params['Model Year'])[2:]}_",
            f"Floorspace_{self.params['Model Year']}-{int(str(self.params['Model Year'])[2:])+1}_",
        ]:
            for category in self.BUSINESS_CATEGORIES:
                self.BUSINESS_FLOORSPACE_HEADER[column_start + category] = float

        # Read in NDR data
        ndr = utilities.read_csv(
            self.paths["NDR floorspace"], columns=self.BUSINESS_FLOORSPACE_HEADER
        ).rename(columns=self.BUSINESS_FLOORSPACE_RENAME)

        # Remove rows that are not LAD
        conditional = ndr.zone.str.startswith(self.BUSINESS_FLOORSPACE_REMOVE_ROWS[0])
        for row in self.BUSINESS_FLOORSPACE_REMOVE_ROWS[1:]:
            conditional = conditional | ndr.zone.str.startswith(row)
        ndr = ndr[~conditional]

        # distinguish columns by year
        previous_yr = [
            col for col in ndr.columns if str(self.params["Model Year"] - 1) in col
        ]
        current_yr = [
            col for col in ndr.columns if str(self.params["Model Year"]) in col
        ]

        # sort lists alphabetically to ensure they are in the same category order
        previous_yr.sort()
        current_yr.sort()

        # Calculate floorspace differences
        for i, col in enumerate(current_yr):
            ndr.loc[:, f"{col.split('_')[-1]}"] = (
                ndr.loc[:, col] - ndr.loc[:, previous_yr[i]]
            ).abs()

        # Sum all differences
        ndr["floorspace"] = ndr[self.BUSINESS_CATEGORIES].sum(axis=1)

        # only include relevant columns
        ndr = ndr[["zone", "floorspace"]]

        # rezone to model zone system
        return Rezone.rezoneOD(
            ndr,
            self.zone_lookups["LAD lookup"],
            dfCols=(ndr.columns[0],),
            rezoneCols=ndr.columns[1:],
        )

    def _read_household_projections(self):
        """Reads in household projections data."""
        households = utilities.read_csv(
            self.paths["household projections"],
            name="Household projections",
            columns=self.HH_PROJECTIONS_HEADER,
        ).rename(columns=self.HH_RENAME)

        # get sum of jobs
        self.TEMPro_data["EW jobs"] = households[
            households.zone.str.startswith("E") | households.zone.str.startswith("W")
        ].jobs.sum()

        # get Scottish jobs data
        scottish_jobs = households[["zone", "jobs"]][
            households.zone.str.startswith("S")
        ]

        # rezone to model zone system
        if not self.zone_lookups:
            self._read_zone_lookups()

        self.TEMPro_data["S jobs"] = Rezone.rezoneOD(
            scottish_jobs,
            self.zone_lookups["MSOA lookup"],
            dfCols=(scottish_jobs.columns[0],),
            rezoneCols=scottish_jobs.columns[1:],
        )
        # Job data is not required for households
        households.drop(axis=1, labels=["jobs"], inplace=True)
        self.TEMPro_data["households"] = Rezone.rezoneOD(
            households,
            self.zone_lookups["MSOA lookup"],
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
            self.paths["BRES"], self.zone_lookups["LSOA lookup"], self.BRES_AGGREGATION
        ).rename(columns={"Zone": "zone"})
        bres.index = bres["zone"]
        bres["factor"] = (
            bres[self.BRES_AGGREGATION.keys()]
            / bres[self.BRES_AGGREGATION.keys()].sum()
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
                * self.params["LGV growth"]
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

        # calculate skilled attractions
        skilled_attractions = {}
        for key in self.commute_trips_land_use:
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
        if self.voa_weightings is None:
            self._read_commute_tables()
        voa_data = lgv_inputs.voa_ratings_list(
            self.paths["VOA"],
            self.voa_weightings,
            self.paths["Postcodes"],
            year=self.params["Model Year"],
            fill_func="non-zero minimum",
        )
        voa_data.index = voa_data["zone"]
        voa_data.drop(axis=1, labels=["zone"], inplace=True)
        voa_data["trips"] = (voa_data / voa_data.sum()) * self.commute_trips_land_use[
            "Employment"
        ]

        return voa_data[["trips"]]

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
        ) = trip_attractions["Drivers"].align(
            trip_attractions["Skilled trades"], join="outer", fill_value=0
        )

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
