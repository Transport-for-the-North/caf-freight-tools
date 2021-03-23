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
from pathlib import Path
from typing import Dict

# Third party imports
import numpy as np
import pandas as pd

# Local imports
import errors


##### CONSTANTS #####


##### CLASSES #####
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

    Raises
    ------
    FileNotFoundError
        If the path provided isn't to an existing Excel Workbook
        file.
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

    def __init__(self, path: Path):
        self.path = Path(path)
        if (
            not self.path.exists()
            or not self.path.is_file()
            or self.path.suffix.lower() != ".xlsx"
        ):
            raise FileNotFoundError(
                f"HGV profiles file is no an existing Excel Workbook: {path}"
            )
        self._tra0305 = None
        self._tra3105 = None
        self._weekly = None
        self._monthly_avg = None
        self._weekly_avg = None

    def read_tra3105(self) -> pd.DataFrame:
        """Reads the TRA3105 data from the provided Excel Workbook.

        Expects a sheet called TRA3105, which contains the following
        columns: Road Type, Rigid, Articulated and All HGVs.

        Returns
        -------
        pd.DataFrame
            TRA3105 data with 'road_type' as the index and columns
            named rigid, artic and all_hgvs, which contain vehicle
            split percentages.

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

        TRA3105 data with 'road_type' as the index and columns
        named rigid, artic and all_hgvs, which contain vehicle
        split percentages.

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
            DataFrame containing the distributions for each
            vehicle type and each day with time as the index
            and columns artic-monday, ... rigid-sunday.
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
        return pd.concat(averages, axis=1)

    @property
    def monthly_avg(self):
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
    def weekly_avg(self):
        """Weighted average weekly/daily HGV distribution.

        DataFrame containing the distributions for each
        vehicle type and each day with time as the index
        and columns artic-monday, ... rigid-sunday.

        See Also
        --------
        `HGVProfiles.calc_weekly_average` which is used to calculate
        the weighted average.
        """
        if self._weekly_avg is None:
            self._weekly_avg = self.calc_weekly_average()
        return self._weekly_avg


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
        If any columns provided in `rename` aren't in
        the DataFrame.
    """
    missing = [c for c in rename if c not in df.columns]
    if missing:
        raise errors.MissingColumnsError(name, missing)
    return df[rename.keys()].rename(columns=rename)


def main(profile_path: Path, output_folder: Path):
    output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True, parents=True)

    # Calculate weighted average distributions and write to file
    hgv_profiles = HGVProfiles(profile_path)
    out = output_folder / (hgv_profiles.NAME + ".xlsx")
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        hgv_profiles.monthly_avg.to_excel(writer, sheet_name="Monthly Average")
        hgv_profiles.weekly_avg.to_excel(writer, sheet_name="Weekly Average")


##### MAIN #####
if __name__ == "__main__":
    # TODO remove paths used for testing
    data_folder = Path(r"U:\Lot3_LFT\HGV_inputs")
    data_folder = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\01 - Task 1\Input Datasets"
    )
    out_folder = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\01 - Task 1\Test Outputs\Time Period Conversion"
    )
    input_file = data_folder / "time_period_conversion_inputs.xlsx"

    start = time.perf_counter()
    main(input_file, out_folder)
    print(f"Time taken: {time.perf_counter() - start}s")
