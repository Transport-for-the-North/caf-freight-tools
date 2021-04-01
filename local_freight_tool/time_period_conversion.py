# -*- coding: utf-8 -*-
"""
    Module to convert matrices from annual PCUs into the model
    time period and zone system.
"""

##### IMPORTS #####
# Standard imports
import calendar
import time
import itertools
import re
import traceback
import os
from pathlib import Path
from typing import Dict, List, Callable, Union

# Third party imports
import numpy as np
import pandas as pd

# Local imports
import errors
import utilities as utils
import matrix_utilities as mu


##### CLASSES #####
class TimeProfiles:
    """Class for reading and extracting the time profile data,

    This class will read the time profiles CSV created by the
    `profile_builder` module and extract the hours, days and
    months for each time period. This class can be passed to
    `HGVProfiles.time_period_factor` to calculate factors for
    each time period.

    Parameters
    ----------
    path : Path
        Path to the time profiles CSV, should contain the
        following columns: name, days, hr_start, hr_end and
        months.

    Raises
    ------
    FileNotFoundError
        If the path provided doesn't exist or isn't a CSV,
        or TXT, file.

    See Also
    --------
    - `HGVProfiles.time_period_factor` for using the information
      within this class to create factors for converting annual
      PCUs into time period PCUs.
    - `profile_builder.ProfileBuilder` which creates a UI to allow
      the user to create the time profiles input file.
    """

    NAME = "Time Period Profiles"
    EXPECTED_COLUMNS = ["name", "days", "hr_start", "hr_end", "months"]
    """List of the columns required in the input file."""

    def __init__(self, path: Path):
        self.path = Path(path)
        utils.check_file_path(path, "Time profiles", ".csv", ".txt")
        self._time_periods = None

    def read_input(self) -> Dict[str, Dict[str, List]]:
        """Read the CSV file and produce a dictionary of the time period data.

        Returns
        -------
        Dict[str, Dict[str, List]]
            Contains key / value pairs for each time period where the key is
            the time period name and the value is another dictionary
            containing the following:
            - hours: list of integer hours for the time period e.g. [12, 13]
            - days: list of lowercase day names e.g. ["monday"]
            - months: list of lowercase month names e.g. ["january"]
        """

        def str_list(s: str, column: str, tp: str) -> List[str]:
            """Convert a string representation of a list to a list."""
            ls = re.sub(r"\[|\]", "", s).split(",")
            # Remove any empty strings from list
            ls = [s.strip() for s in ls if s.strip() != ""]
            if ls == []:
                raise errors.MissingDataError(
                    self.NAME, f"no {column} found for time period '{tp}'"
                )
            return ls

        def check_hr(h: int, col: str, tp: str):
            """Checks if `h` is an integer between 0 and 23."""
            err = (
                f"'{col}' should be between a number 0 - "
                f"23 for time period '{tp}' not: {h}"
            )
            try:
                h = int(h)
            except ValueError as e:
                raise ValueError(err.format(c=c, nm=nm, h=h)) from e
            if h < 0 or h > 23:
                raise ValueError(err.format(c=c, nm=nm, h=h))
            return h

        df = pd.read_csv(self.path)
        missing = [c for c in self.EXPECTED_COLUMNS if c not in df.columns]
        if missing:
            raise errors.MissingColumnsError(self.NAME, missing)

        periods = {}
        for _, row in df.iterrows():
            nm = str(row["name"])
            hrs = []
            for c in ("hr_start", "hr_end"):
                hrs.append(check_hr(row[c], c, nm))
            if hrs[1] < hrs[0]:
                hours = list(range(hrs[0], 24)) + list(range(0, hrs[1]))
            else:
                hours = list(range(*hrs))

            days = str_list(row["days"], "days", nm)
            days = [calendar.day_name[int(i)].lower() for i in days]
            months = str_list(row["months"], "months", nm)
            # calendar.month_name starts with empty string so adding 1 to index
            months = [calendar.month_name[int(i) + 1].lower() for i in months]
            periods[nm] = {"hours": hours, "days": days, "months": months}

        return periods

    @property
    def time_periods(self) -> Dict[str, Dict[str, List]]:
        """Dictionary of time period information.

        Returns
        -------
        Dict[str, Dict[str, List]]
            Contains key / value pairs for each time period where
            the key is the time period name and the value is another
            dictionary containing the following:
            - hours: list of integer hours for the time period e.g. [12, 13]
            - days: list of lowercase day names e.g. ["monday"]
            - months: list of lowercase month names e.g. ["january"]

        See Also
        --------
        `TimeProfiles.read_input` which gets this information from
        the input file.
        """
        if self._time_periods is None:
            self._time_periods = self.read_input()
        return self._time_periods

    def __str__(self) -> str:
        return str(self.time_periods)


class HGVProfiles:
    """Class which calculates average HGV time profile distribution.

    This expected the HGV time distribution profiles to be provided
    at both monthly and weekly/daily level for different road types,
    along with a road type distribution for rigid and articulated vehicles.

    Parameters
    ----------
    path : Path
        Path to Excel Workbook which contains a separate sheet for
        each distribution profile.
    year : int
        The year the HGV data is from, used for calculating the
        number of weeks in each month.

    Raises
    ------
    FileNotFoundError
        If the path provided isn't to an existing Excel Workbook file.
    """

    EXPECTED_PROFILES = ["TRA0305", "TRA3105", "WEEKLY_PROFILE"]
    """Required HGV distribution profiles for calculating time period factors."""
    TRA0305_EXPECTED_ROADS = ["motorways", "rural roads", "urban roads"]
    """Road types required from TRA0305 data in distribution profiles."""
    WEEKLY_EXPECTED_ROADS = [
        "motorways",
        "rural 'a' roads",
        "urban 'a' roads",
        "rural minor roads",
        "urban minor roads",
    ]
    """Road types expecting in WEEKLY HGV profile input."""
    TRA3105_ROAD_TYPES = {
        "motorways": ["motorways"],
        "rural roads": ["all rural 'a' roads", "minor rural roads"],
        "urban roads": ["all urban 'a' roads", "minor urban roads"],
        "rural 'a' roads": ["all rural 'a' roads"],
        "rural minor roads": ["minor rural roads"],
        "urban 'a' roads": ["all urban 'a' roads"],
        "urban minor roads": ["minor urban roads"],
    }
    """Road types expected in TRA3105 input file which will be aggregated together."""
    NAME = "HGV Profiles"

    def __init__(self, path: Path, year: int):
        self.path = Path(path)
        utils.check_file_path(path, "HGV profiles", ".xlsx")
        self._tra0305 = None
        self._tra3105 = None
        self._weekly = None
        self._monthly_avg = None
        self._weekly_avg = None
        self._num_weeks = None
        self.year = int(year)

    def read_tra3105(self) -> pd.DataFrame:
        """Reads the TRA3105 data from the provided Excel Workbook.

        Expects a sheet called TRA3105, which contains the following
        columns: Road Type, Rigid, Articulated and All HGVs.

        Returns
        -------
        pd.DataFrame
            TRA3105 data with 'road_type' as the index and columns named rigid,
            artic and all_hgvs, which contain vehicle split percentages.

        Raises
        ------
        errors.MissingDataError
            If any required road types aren't given see
            `HGVProfiles.TRA3105_ROAD_TYPES`.
        """
        sheet = "TRA3105"
        df = read_excel(self.path, sheet, self.NAME)

        rename = {
            "Road Type": "road_type",
            "Rigid": "rigid",
            "Articulated": "artic",
            "All HGVs": "all_hgvs",
        }
        df = rename_columns(df, rename, sheet)

        df.dropna(axis=0, how="any", inplace=True)
        for c in ["rigid", "artic", "all_hgvs"]:
            df[c] = pd.to_numeric(df[c])
        df["road_type"] = df["road_type"].str.lower().str.strip()
        # Check all required road types are given
        expected = list(itertools.chain.from_iterable(self.TRA3105_ROAD_TYPES.values()))
        missing = [i for i in expected if i not in df["road_type"].tolist()]
        if missing:
            raise errors.MissingDataError(f"{sheet} road types", missing)
        # Aggregate road types together to get only TRA3105_ROAD_TYPES
        df.set_index("road_type", inplace=True)
        for r, ls in self.TRA3105_ROAD_TYPES.items():
            df.loc[r] = df.loc[ls].sum()
        return df.loc[self.TRA3105_ROAD_TYPES.keys()]

    def read_tra0305(self) -> pd.DataFrame:
        """Reads the TRA0305 data from the given Excel Workbook.

        Expects a sheet called TRA0305 which contains the following
        columns: Road Type, Month and HGV.

        Returns
        -------
        pd.DataFrame
            TRA0305 data with columns: road_type, month and hgv.

        Raises
        ------
        errors.MissingDataError
            If any required road types or months are missing.
        """
        sheet = "TRA0305"
        df = read_excel(self.path, sheet, self.NAME)

        # Check required columns are present and rename them
        rename = {
            "Road Type": "road_type",
            "Month": "month",
            "HGV": "hgv",
        }
        df = rename_columns(df, rename, sheet)

        df["road_type"] = df["road_type"].fillna(method="ffill")
        df.dropna(axis=0, how="any", inplace=True)
        df["road_type"] = df["road_type"].str.lower()
        df = df.loc[df["road_type"].isin(self.TRA0305_EXPECTED_ROADS)]
        if df.empty:
            raise errors.MissingDataError(
                f"{sheet} road type", self.TRA0305_EXPECTED_ROADS
            )

        df["month"] = (
            df["month"].str.lower().str.split(pat=" ", n=1, expand=True).iloc[:, 0]
        )
        df["hgv"] = pd.to_numeric(df["hgv"])

        # Check required road type and month combinations are present
        months = [m.lower() for m in calendar.month_name if m != ""]
        missing = []
        for road in self.TRA0305_EXPECTED_ROADS:
            if road not in df["road_type"].tolist():
                missing.append(f"{road} - all")
                continue
            month_data = df.loc[df["road_type"] == road, "month"].tolist()
            for m in months:
                if m not in month_data:
                    missing.append(f"{road} - {m}")
        if missing:
            raise errors.MissingDataError(f"{sheet} road type and months", missing)
        return df

    def read_weekly_profile(self) -> pd.DataFrame:
        """Reads weekly profile data from given Excel Workbook.

        Expects sheet named WEEKLY PROFILE which contains columns:
        Road Type, Time and then Monday - Sunday for Articulated
        and Rigid vehicles.

        Returns
        -------
        pd.DataFrame
            Weekly/daily HGV time distribution data with columns
            road_type, time and then each day of the week and vehicle
            type e.g. artic-monday, ... rigid-sunday.

        Raises
        ------
        errors.MissingDataError
            If any required road types and times aren't given.
        """
        NAME = "WEEKLY PROFILE"
        df = read_excel(self.path, NAME, NAME, header=[0, 1])

        # Remove Unnamed column names, flatten headers and rename columns
        df.rename(
            columns=lambda x: "" if x.lower().startswith("unnamed:") else x,
            inplace=True,
        )
        df.columns = [" ".join(str(s) for s in c).strip() for c in df.columns.tolist()]
        rename = {"Road Type": "road_type", "Time": "time"}
        d_cols = {
            f"{c} {d}": f"{c.lower()[:5]}-{d.lower()}"
            for c in ("Articulated", "Rigid")
            for d in calendar.day_name
        }
        rename.update(d_cols)
        df = rename_columns(df, rename, NAME)

        # Check all required road types are present
        df["road_type"] = df["road_type"].fillna(method="ffill").str.lower()
        df.dropna(axis=0, how="any", inplace=True)
        df = df.loc[df["road_type"].isin(self.WEEKLY_EXPECTED_ROADS)]
        if df.empty:
            raise errors.MissingDataError(
                f"{NAME} road type", self.WEEKLY_EXPECTED_ROADS
            )

        # Check all times are present for each road type
        fmt = lambda x: f"{x!s:0>2.2}:00" if x < 24 else "00:00"
        times = [f"{fmt(i)}-{fmt(i+1)}" for i in range(24)]
        missing = []
        for road in self.WEEKLY_EXPECTED_ROADS:
            if road not in df["road_type"].tolist():
                missing.append(f"{road} - all")
                continue
            time_data = df.loc[df["road_type"] == road, "time"].tolist()
            for t in times:
                if t not in time_data:
                    missing.append(f"{road} - {t}")
        if missing:
            raise errors.MissingDataError(f"{NAME} road type and times", missing)

        return df

    @property
    def tra3105(self) -> pd.DataFrame:
        """DataFrame of TRA3105 data.

        TRA3105 data with 'road_type' as the index and columns named rigid,
        artic and all_hgvs, which contain vehicle split percentages.

        See Also
        --------
        `HGVProfile.read_tra3105` which reads the data.
        """
        if self._tra3105 is None:
            self._tra3105 = self.read_tra3105()
        return self._tra3105

    @property
    def tra0305(self) -> pd.DataFrame:
        """DataFrame with TRA0305 data.

        Contains columns: road_type, month and hgv.

        See Also
        --------
        `HGVProfile.read_tra0305` which reads the data.
        """
        if self._tra0305 is None:
            self._tra0305 = self.read_tra0305()
        return self._tra0305

    @property
    def weekly(self) -> pd.DataFrame:
        """DataFrame with weekly/daily time profile distribution data.

        Weekly/daily HGV time distribution data contains columns
        road_type, time and then each day of the week and vehicle
        type e.g. artic-monday, ... rigid-sunday.

        See Also
        --------
        `HGVProfile.read_weekly_profile` which reads the data.
        """
        if self._weekly is None:
            self._weekly = self.read_weekly_profile()
        return self._weekly

    def calc_monthly_average(self) -> pd.DataFrame:
        """Calculate the weighted average monthly distribution from TRA0305 data.

        Uses the road type distribution from the TRA3105 data as the
        weightings for the average.

        Returns
        -------
        pd.DataFrame
            DataFrame containing HGV distributions for all months (index),
            with one column (hgv).
        """
        data = []
        weights = []
        for road in self.tra0305["road_type"].unique():
            df = self.tra0305.loc[self.tra0305["road_type"] == road, ["month", "hgv"]]
            df.set_index("month", inplace=True)
            data.append(df)
            weights.append(self.tra3105.loc[road, "all_hgvs"])
        data = pd.concat(data, axis=1)
        avg = np.average(data.values, axis=1, weights=weights)
        return pd.DataFrame(avg, index=data.index, columns=["hgv"])

    def calc_weekly_average(self) -> pd.DataFrame:
        """Calculate the weekly/daily weighted average.

        Uses the road type distribution from the TRA3105 data as the
        weightings for the average, different weightings are used for
        the rigid and artic columns.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the distributions for each vehicle type
            and each day with time as the index and columns
            artic-monday, ... rigid-sunday.
        """
        averages = []
        # Use different weightings for artic and rigid vehicles
        for veh in ("artic", "rigid"):
            cols = [c for c in self.weekly.columns if c.startswith(veh)]
            data = []
            weights = []
            for road in self.weekly["road_type"].unique():
                df = self.weekly.loc[self.weekly["road_type"] == road, ["time"] + cols]
                df.set_index("time", inplace=True)
                data.append(df.sort_index())
                weights.append(self.tra3105.loc[road, veh])
            # Caculate weighted average of road types and convert to dataframe
            avg = np.average(data, axis=0, weights=weights)
            avg = pd.DataFrame(avg, index=data[0].index, columns=data[0].columns)
            averages.append(avg)
        df = pd.concat(averages, axis=1).reset_index()
        # Create integer time index
        df.rename(columns={"time": "time_str"}, inplace=True)
        pat = r"^(\d{2}):\d{2}-\d{2}:\d{2}$"
        df["time"] = pd.to_numeric(
            df["time_str"].str.replace(pat, r"\1", regex=True), downcast="integer"
        )
        return df.set_index("time")

    @property
    def monthly_avg(self) -> pd.DataFrame:
        """Weighted average monthly HGV distribution.

        DataFrame containing HGV distributions for all
        months (index), with one column (hgv).

        See Also
        --------
        `HGVProfiles.calc_monthly_average` which is used to calculate
        the weighted average.
        """
        if self._monthly_avg is None:
            self._monthly_avg = self.calc_monthly_average()
        return self._monthly_avg

    @property
    def weekly_avg(self) -> pd.DataFrame:
        """Weighted average weekly/daily HGV distribution.

        DataFrame containing the distributions for each vehicle type
        and each day with time as the index and columns
        artic-monday, ... rigid-sunday.

        See Also
        --------
        `HGVProfiles.calc_weekly_average` which is used to calculate
        the weighted average.
        """
        if self._weekly_avg is None:
            self._weekly_avg = self.calc_weekly_average()
        return self._weekly_avg

    @property
    def num_weeks(self) -> Dict[str, float]:
        """Dictionary containing the average number of weeks in each month.

        Data is calculated for a single year.

        Returns
        -------
        Dict[str, float]
            Keys are the lowercase name of each month, with the values
            as the mean number of weeks in that month.
        """
        if self._num_weeks is None:
            get_days = lambda m: calendar.monthrange(self.year, m)[1]
            n_weeks = {}
            for i, m in enumerate(calendar.month_name):
                if m != "":
                    n_weeks[m.lower()] = get_days(i) / 7
            self._num_weeks = n_weeks
        return self._num_weeks

    def calc_tp_factor(
        self, hours: List[int], days: List[str], months: List[str]
    ) -> Dict[str, float]:
        """Calculate factor for a single time period.

        Different factors are calculated for articulated and rigid HGVs.

        Parameters
        ----------
        hours : List[int]
            List of the hours included in the time period e.g. [7, 8, 9].
        days : List[str]
            List of lowercase day names e.g. ["monday", "tuesday"].
        months : List[str]
            List of lowercase month names e.g. ["january", "february"].

        Returns
        -------
        Dict[str, float]
            Dictionary of time period factors for both vehicle
            types contains keys: artic and rigid.
        """
        avg_month = self.monthly_avg.loc[months, "hgv"].mean()
        avg_weeks = np.mean([self.num_weeks[m] for m in months])
        factors = {}
        for veh in ("artic", "rigid"):
            veh_days = [f"{veh}-{d}" for d in days]
            avg_day = self.weekly_avg.loc[hours, veh_days].mean(axis=1)
            avg_hours = avg_day.mean()
            f = (avg_month / 1200) * (1 / avg_weeks) * (avg_hours / 700)
            factors[veh] = f
        return factors

    def time_period_factors(
        self, profiles: TimeProfiles
    ) -> Dict[str, Dict[str, float]]:
        """Calculate factors for each time period in `profiles`.

        Two factors are calculated for each time period,
        one for artic and one for rigid HGVs.

        Parameters
        ----------
        profiles : TimeProfiles
            Instance of `TimeProfiles` class containing
            the time period information.

        Returns
        -------
        Dict[str, Dict[str, float]]
            Dictionary containing factors for each time period with keys
            corresponding to the time period and each value a dictionary
            containing factors for both artic and rigid HGVs. For example:
            {"AM": {"artic": 0.1, "rigid": 0.5}}

        See Also
        --------
        `HGVProfiles.calc_tp_factor` which will calculate the
        factors for a single time period.
        """
        factors = {}
        for nm, data in profiles.time_periods.items():
            f = self.calc_tp_factor(**data)
            factors[nm] = f
        return factors


##### FUNCTIONS #####
def read_excel(path: Path, sheet: str, name: str, **kwargs) -> pd.DataFrame:
    """Reads a single sheet from an Excel Workbook.

    Parameters
    ----------
    path : Path
        Path to the Excel Workbook, must be an .xlsx file.
    sheet : str
        Name of the sheet to read.
    name : str
        Name of the data being read, for error messages.
    kwargs : keyword arguments
        Keyword arguments to pass to `pd.read_excel`.

    Returns
    -------
    pd.DataFrame
        The data from the sheet of the Excel Workbook.

    Raises
    ------
    errors.MissingWorksheetError
        If the `sheet` given doesn't exist in the workbook.
    """
    try:
        return pd.read_excel(path, sheet_name=sheet, engine="openpyxl", **kwargs)
    except ValueError as e:
        if str(e).lower().startswith("worksheet"):
            raise errors.MissingWorksheetError(name, sheet) from e
        raise ValueError(f"{name}: {e}") from e


def rename_columns(df: pd.DataFrame, rename: Dict[str, str], name: str) -> pd.DataFrame:
    """Rename columns in a DataFrame and check if any are missing.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to be renamed/checked.
    rename : Dict[str, str]
        Columns to be renamed.
    name : str
        Name of DataFrame being renamed/checked, used if
        any errors are raised.

    Returns
    -------
    pd.DataFrame
        The input DataFrame with renamed columns.

    Raises
    ------
    errors.MissingColumnsError
        If any columns provided in `rename` aren't in the DataFrame.
    """
    missing = [c for c in rename if c not in df.columns]
    if missing:
        raise errors.MissingColumnsError(name, missing)
    return df[rename.keys()].rename(columns=rename)


def check_parameter_paths(
    output_folder: Path,
    profile_path: Path,
    time_profile_path: Path,
    artic_matrix: Path,
    rigid_matrix: Path,
) -> Dict[str, Path]:
    """Checks that all parameters provided are existing files.

    All input files are checked to make sure they exist and are the
    correct type, the `output_folder` is created if it doesn't already exist.

    Parameters
    ----------
    output_folder : Path
        Path to the folder for saving the outputs, it will
        be created if it doesn't already exist.
    profile_path : Path
        Path to the Excel Workbook containing the HGV distribution profiles.
    time_profile_path : Path
        Path to the CSV file containing the time period information.
    artic_matrix : Path
        Path to the CSV containing the articulated HGV matrix in PCUs.
    rigid_matrix : Path
        Path to the CSV containing the rigid HGV matrix in PCUs.

    Returns
    -------
    Dict[str, Path]
        Dictionary containing all the paths (values) with readable
        names (keys) for use in output log spreadsheet.
    """
    utils.check_folder(output_folder, "Output", create=True)
    inputs = {
        "HGV Profiles": profile_path,
        "Time Profiles": time_profile_path,
        "Articulated Matrix": artic_matrix,
        "Rigid Matrix": rigid_matrix,
    }
    extensions = ((".xlsx",), (".csv", ".txt"), (".csv", ".txt"), (".csv", ".txt"))
    for (nm, p), ext in zip(inputs.items(), extensions):
        utils.check_file_path(p, nm, *ext)
    inputs["Output Folder"] = output_folder
    return inputs


def to_time_period(
    matrices: Dict[str, mu.ODMatrix],
    factors: Dict[str, float],
    output_folder: Path,
    zone_correspondence_path: Path,
    time_per: str,
    message_hook: Callable = print,
) -> Dict[str, Dict[str, Union[float, str]]]:
    """Converts matrices to given `time_per`, rezones and aggregates them together.

    Expects a rigid and artic ODMatrix to be provided which will be
    combined into a single HGV matrix for the model zone system and
    time period. Creates the following 5 output CSVs:
    - time period matrices for both vehicle types;
    - rezoned versions of the above matrices; and
    - HGV matrix containing aggregation of the rezoned matrices.

    Parameters
    ----------
    matrices : Dict[str, mu.ODMatrix]
        Dictionary containing ODMatrix instances for artic and
        rigid HGVs, in PCUs.
    factors : Dict[str, float]
        Time period factors for converting from annual PCUs to time
        period PCUs for each matrix in `matrices` (artic and rigid).
    output_folder : Path
        Path to the folder to save the outputs to, must already exist.
    zone_correspondence_path : Path
        Path to the zone correspondence lookup CSV.
    time_per : str
        Name of the time period being converted to, used for naming
        the output files.
    message_hook : Callable, optional
        Function for writing messages, by default print

    Returns
    -------
    Dict[str, Dict[str, Union[float, str]]]
        Dictionary containing summaries of the matrices
        (`ODMatrix.summary`) for each stage of the process.

    Raises
    ------
    errors.MissingDataError
        If either artic or rigid are not provided in `matrices`,
        or if time period factors aren't provided for both.
    """
    missing = [v for v in ("artic", "rigid") if v not in matrices]
    if missing:
        raise errors.MissingDataError("matrices", missing)

    rezoned = {}
    summaries = {}
    for veh, mat in matrices.items():
        message_hook(f"Factoring and rezoning {veh} - {time_per}")
        f = factors.get(veh, None)
        if f is None:
            raise errors.MissingDataError(f"time period factors - {time_per}", veh)
        tp_mat = mat * f
        tp_mat.name = f"{time_per}_HGV_{veh}"
        summaries[f"{veh.title()} - {time_per}"] = tp_mat.summary()
        tp_mat.export_to_csv(output_folder / (tp_mat.name + ".csv"))

        rezoned[veh] = tp_mat.rezone(zone_correspondence_path)
        rezoned[veh].name = f"{time_per}_HGV_{veh}-rezoned"
        summaries[f"{veh.title()} - {time_per} - Rezoned"] = rezoned[veh].summary()
        rezoned[veh].export_to_csv(output_folder / (rezoned[veh].name + ".csv"))
    del tp_mat

    message_hook(f"Combining artic and rigid matrices for {time_per}")
    combined = rezoned["artic"] + rezoned["rigid"]
    combined.name = f"{time_per}_HGV_combined"
    summaries[f"Combined - {time_per}"] = combined.summary()
    combined.export_to_csv(output_folder / (combined.name + ".csv"))
    message_hook(f"Finished processing {time_per}")
    return summaries


def process_matrices(
    matrix_paths: Dict[str, Path],
    factors: Dict[str, Dict[str, float]],
    output_folder: Path,
    zone_correspondence_path: Path,
    message_hook: Callable = print,
) -> Dict[str, Dict[str, Union[str, float]]]:
    """Converts matrices to model time periods and zone system.

    Creates a combined HGV matrix for each time period which is the
    aggregation of the artic and rigid matrices after they've been
    converted to the model zone system.

    Parameters
    ----------
    matrix_paths : Dict[str, Path]
        Paths to the rigid and artic matrix CSVs in annual PCUs.
    factors : Dict[str, Dict[str, float]]
        Time period factors (values) with names (keys), where the value
        contains 2 factors one for artic and one for rigid HGVs.
    output_folder : Path
        Path to an existing folder to save the outputs to.
    zone_correspondence_path : Path
        Path to the zone correspondence lookup file to convert matrices
        to the model zone system.
    message_hook : Callable, optional
        Function for writing message, by default print

    Returns
    -------
    Dict[str, Dict[str, Union[str, float]]]
        Dictionary containing summaries of the matrices
        (`ODMatrix.summary`) for each stage of the process.

    Raises
    ------
    errors.BaseLocalFreightError
        If the is an error reading either of the input matrix CSV files.

    See Also
    --------
    `to_time_periods` which converts the rigid and artic matrices to
    a single time period and performs the aggregation.
    """
    mat_summary = {}
    matrices = {}
    for veh, path in matrix_paths.items():
        message_hook(f"Reading {veh} matrix")
        try:
            matrices[veh] = mu.ODMatrix.read_OD_file(path)
            mat_summary[f"Input {veh.title()}"] = matrices[veh].summary()
        except Exception as e:
            mat_summary[f"Input {veh.title()}"] = {
                "Comment": f"{e.__class__.__name__}: {e}"
            }
    errs = [v for v in ("artic", "rigid") if matrices.get(v, None) is None]
    if errs:
        msg = "matrix" if len(errs) == 1 else "matrices"
        raise errors.BaseLocalFreightError(
            f"Error reading input {msg}: {', '.join(errs)}"
        )

    for tp, curr_factors in factors.items():
        try:
            summaries = to_time_period(
                matrices,
                curr_factors,
                output_folder,
                zone_correspondence_path,
                tp,
                message_hook=message_hook,
            )
            mat_summary.update(summaries)
        except Exception as e:
            traceback.print_exc()
            msg = f"{e.__class__.__name__}: {e}"
            mat_summary[tp] = {"Comment": msg}
            message_hook(f"{tp} {msg}")

    return mat_summary


def write_log(
    path: Path,
    inputs: Dict[str, Union[str, int, Path]],
    hgv_profiles: HGVProfiles,
    factors: Dict[str, Dict[str, float]],
    matrix_summary: Dict[str, Dict[str, float]],
    message_hook: Callable = print,
):
    """Writes parameters and summaries to Excel Workbook.

    Parameters
    ----------
    path : Path
        Path to the Excel Workbook to create.
    inputs : Dict[str, Union[str, int, Path]]
        Contains all the paths (values) with readable names (keys) for
        use in output log spreadsheet, from `check_parameter_paths`.
    hgv_profiles : HGVProfiles
        Instance of `HGVProfiles` containing all the
        information on the HGV distributions.
    factors : Dict[str, Dict[str, float]]
        Dictionary containing factors for each time period with keys
        corresponding to the time period and each value a dictionary
        containing factors for both artic and rigid HGVs, from
        `HGVProfiles.time_period_factors`.
    matrix_summary : Dict[str, Dict[str, float]]
        Dictionary containing summaries of the matrices (`ODMatrix.summary`)
        for each stage of the process, from `process_matrices`.
    message_hook : Callable, optional
        Function for writing messages, by default print
    """
    message_hook(f"Writing {path}")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        msg = "Log for the time period conversion module for the Local Freight Tool"
        df = pd.DataFrame({"Notes": msg}, index=[1])
        df.to_excel(writer, sheet_name="Notes")
        if inputs:
            inputs_df = pd.DataFrame.from_dict(
                inputs, orient="index", columns=["Parameter Value"]
            )
            inputs_df.to_excel(writer, sheet_name="Input Parameters")
        if hgv_profiles:
            hgv_profiles.monthly_avg.to_excel(writer, sheet_name="Monthly Avg Profile")
            hgv_profiles.weekly_avg.to_excel(writer, sheet_name="Weekly Avg Profile")
        if factors:
            factors_df = pd.DataFrame.from_dict(factors, orient="index")
            factors_df.to_excel(writer, sheet_name="Time Period Factors")
        if matrix_summary:
            mat_sum_df = pd.DataFrame.from_dict(matrix_summary, orient="index")
            mat_sum_df.to_excel(writer, sheet_name="Matrix Summaries")
    message_hook(f"Opening {path}")
    os.startfile(path.resolve())


def main(
    output_folder: Path,
    profile_path: Path,
    time_profile_path: Path,
    year: int,
    artic_matrix: Path,
    rigid_matrix: Path,
    zone_correspondence_path: Path,
    message_hook: Callable = print,
):
    """Convert annual PCU rigid and artic matrices into time periods.

    Parameters
    ----------
    output_folder : Path
        Path to a folder where all the output files will be
        saved, will be created if it doesn't already exist.
    profile_path : Path
        Path to the Excel Workbook containing the HGV distribution
        profiles tables.
    time_profile_path : Path
        Path to the CSV containing the time period information.
    year : int
        Year that the model is being ran for, only used for
        calculating the average number of weeks in a month.
    artic_matrix : Path
        Path to the articulated matrix CSV in annual PCUs.
    rigid_matrix : Path
        Path to the rigid matrix CSV in annual PCUs.
    zone_correspondence_path : Path
        Path to the zone correspondence lookup CSV.
    message_hook : Callable, optional
        Function for writing messages, by default print
    """
    start_time = time.perf_counter()
    hgv_profiles = None
    try:
        log_sheets = {}
        # Check input paramters and add to dictionary for logging
        log_sheets["inputs"] = check_parameter_paths(
            output_folder, profile_path, time_profile_path, artic_matrix, rigid_matrix
        )
        log_sheets["inputs"]["Year"] = year

        # Calculate weighted average distributions
        message_hook("Processing HGV profiles")
        hgv_profiles = HGVProfiles(profile_path, year)
        # Read time profiles data and calculate factors
        message_hook("Processing time profiles")
        time_profiles = TimeProfiles(time_profile_path)
        message_hook("Calculating time period factors")
        factors = hgv_profiles.time_period_factors(time_profiles)

        # Read matrices and apply factors
        log_sheets["matrix_summary"] = process_matrices(
            {"artic": artic_matrix, "rigid": rigid_matrix},
            factors,
            output_folder,
            zone_correspondence_path,
            message_hook=message_hook,
        )

        # Write log file
        log_sheets["factors"] = time_profiles.time_periods.copy()
        for tp, vals in log_sheets["factors"].items():
            vals.update(factors.get(tp, {}))
    except Exception as e:
        message_hook(f"{e.__class__.__name__}: {e}")
        raise
    finally:
        try:
            write_log(
                output_folder / "time_period_conversion_log.xlsx",
                log_sheets.get("inputs", None),
                hgv_profiles,
                log_sheets.get("factors", None),
                log_sheets.get("matrix_summary", None),
                message_hook=message_hook,
            )
        except Exception as e:
            message_hook(f"Error writing log spreadsheet - {e.__class__.__name__}: {e}")
            raise

    time_taken = time.perf_counter() - start_time
    if time_taken < 60:
        tt_str = f"{time_taken:.1f}s"
    else:
        mins, secs = divmod(time_taken, 60)
        tt_str = f"{mins:.0f}m {secs:.0f}s"
    message_hook(f"Time period conversion done in {tt_str}")
