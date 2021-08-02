# -*- coding: utf-8 -*-
"""
    Module for running the LGV model.
"""

##### IMPORTS #####
# Standard imports
import argparse
import configparser
import io
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from ..data_utils import DataPaths
from .lgv_inputs import (
    lgv_parameters,
    LGVInputPaths,
    read_study_area,
    read_time_factors,
    read_gm_params,
)
from .service_segment import ServiceTripEnds
from .delivery_segment import DeliveryTripEnds
from .commute_segment import CommuteTripEnds
from .gravity_model import CalibrateGravityModel, calculate_vehicle_kms
from .furnessing import annual_pa_to_od


##### CONSTANTS #####
TRIP_DISTRIBUTION_SHEETS = {
    "service": "Service",
    "delivery_parcel_stem": "Delivery",
    "delivery_parcel_bush": "Delivery Bush",
    "delivery_grocery": "Delivery Bush",
    "commuting_drivers": "Commuting",
    "commuting_skilled_trades": "Commuting",
}
"""Name of sheet in trip distributions file for each segment."""
PA_MATRICES = [
    "service",
    "delivery_parcel_stem",
    "commuting_drivers",
    "commuting_skilled_trades",
]
"""List of matrices which are in PA format and will be converted to OD."""

##### CLASSES #####
class LGVConfig(configparser.ConfigParser):
    """Handles reading the config file for the LGV model.

    Parameters
    ----------
    path : Path
        Path to the config file to read.

    Raises
    ------
    configparser.NoSectionError
        If the config file doesn't contain the
        `SECTION`.
    """

    SECTION = "LGV File Paths"
    """Name of the required section."""
    OPTIONS = {
        "hh_data": "households data",
        "hh_zc": "households zone correspondence",
        "bres_data": "bres data",
        "bres_zc": "bres zone correspondence",
        "voa_data": "voa data",
        "voa_zc": "voa zone correspondence",
        "parameters_path": "lgv parameters",
        "qs606ew_path": "QS606EW",
        "qs606sc_path": "QS606SC",
        "sc_w_dwellings_path": "SC&W dwellings",
        "e_dwellings_path": "E dwellings",
        "ndr_floorspace_path": "NDR floorspace",
        "lsoa_lookup_path": "LSOA lookup",
        "msoa_lookup_path": "MSOA lookup",
        "lad_lookup_path": "LAD lookup",
        "output_folder": "output folder",
        "model_study_area": "model study area",
        "cost_matrix_path": "Cost Matrix",
        "calibration_matrix_path": "Calibration Matrix",
        "trip_distributions_path": "Trip Distributions Spreadsheet",
    }
    """Names of the expected options in config file (values), keys are for internal use."""
    input_paths: LGVInputPaths = None
    """Paths to all the input files required for the LGV model."""
    EXAMPLE_NAME: str = "LGV_config_example.ini"
    """Name of the example config file which is written, if path isn't given."""

    def __init__(self, path: Path):
        """Initialises the class by reading the given file."""
        super().__init__()
        self.read(path)
        if not self.has_section(self.SECTION):
            raise configparser.NoSectionError(
                f"LGV config ({path.name}) doesn't contain section {self.SECTION!r}"
            )
        paths = {}
        paths["household_paths"] = DataPaths(
            "LGV Households",
            self.getpath(self.SECTION, self.OPTIONS["hh_data"]),
            self.getpath(self.SECTION, self.OPTIONS["hh_zc"]),
        )
        paths["bres_paths"] = DataPaths(
            "LGV BRES",
            self.getpath(self.SECTION, self.OPTIONS["bres_data"]),
            self.getpath(self.SECTION, self.OPTIONS["bres_zc"]),
        )
        paths["voa_paths"] = DataPaths(
            "LGV VOA",
            self.getpath(self.SECTION, self.OPTIONS["voa_data"]),
            self.getpath(self.SECTION, self.OPTIONS["voa_zc"]),
        )
        # All parameters in ignore are handled separately
        ignore = ("hh_data", "hh_zc", "bres_data", "bres_zc", "voa_data", "voa_zc")
        optional = ("calibration_matrix_path",)
        for nm, option_name in self.OPTIONS.items():
            if nm in ignore:
                continue
            if nm in optional:
                paths[nm] = self.getpath(self.SECTION, option_name, fallback=None)
            else:
                paths[nm] = self.getpath(self.SECTION, option_name)
        self.input_paths = LGVInputPaths(**paths)

    def getpath(self, section: str, option: str, **kwargs) -> Path:
        """Gets the `option` from `section` and converts it to a Path object.

        Parameters
        ----------
        section : str
            Name of the config section.
        option : str
            Name of the config option.

        Returns
        -------
        Path
            Path object for the given `option`.
        """
        item = self.get(section, option, **kwargs)
        if item:
            return Path(item)
        return item

    @classmethod
    def write_example(cls, path: Path = None):
        """Write example of the config file, with no values.

        Parameters
        ----------
        path : Path
            Path to write the example config file too,
            will be overwritten if already exists.
        """
        if path is None:
            path = Path(cls.EXAMPLE_NAME)
        elif path.is_dir():
            path = path / cls.EXAMPLE_NAME
        config = configparser.ConfigParser()
        config[cls.SECTION] = {k: "" for k in cls.OPTIONS}
        with open(path, "wt") as f:
            config.write(f)
        print(f"Example config written: {path}")

    def __str__(self) -> str:
        paths_str = str(self.input_paths).replace("\n", "\n\t")
        return f"{self.__class__.__name__}\n\t{self.SECTION} = {paths_str}"


class LGVInputsUI:
    """Handles reading UI inputs for the LGV Model.

    Parameters
    ----------
    Dict[str, Path]
        Dictionary containing all the parameters (keys)
        and their values, contains the following keys:
        hh_data, hh_zc, bres_data, bres_zc, voa_data,
        voa_zc, parameters_path, trip_distributions_path,
        qs606ew_path, qs606sc_path, sc_w_dwellings_path,
        e_dwellings_path, ndr_floorspace_path, lsoa_lookup_path,
        msoa_lookup_path, lad_lookup_path, model_study_area,
        cost_matrix_path, calibration_matrix_path and output_folder.
    """

    input_paths: LGVInputPaths = None
    """Paths to all the input files required for the LGV model."""

    def __init__(self, parameters: dict):
        """Initialises the class by creating LGVInputsPaths instance
        from parameters dictionary."""
        paths = {}
        paths["household_paths"] = DataPaths(
            "LGV Households",
            parameters["hh_data"],
            parameters["hh_zc"],
        )
        paths["bres_paths"] = DataPaths(
            "LGV BRES",
            parameters["bres_data"],
            parameters["bres_zc"],
        )
        paths["voa_paths"] = DataPaths(
            "LGV VOA",
            parameters["voa_data"],
            parameters["voa_zc"],
        )
        # All parameters in ignore are handled separately
        ignore = ("hh_data", "hh_zc", "bres_data", "bres_zc", "voa_data", "voa_zc")
        optional = ("calibration_matrix_path",)
        for key in parameters:
            if key in ignore:
                continue
            if key in optional:
                paths[key] = parameters[key]
            else:
                paths[key] = parameters[key]
        self.input_paths = LGVInputPaths(**paths)


@dataclass
class LGVTripEnds:
    """Dataclass to store the trip end data for all segments.

    Aligns all the trip end matrices to include all zones
    present in at least one DataFrame, any missing zones
    are filled with 0 trip ends for that DataFrame.
    """

    service: pd.DataFrame
    """Service Productions and Attractions trip ends
    (columns) for all zones (index).
    """
    delivery_parcel_stem: pd.DataFrame
    """Delivery parcel stem Productions and Attractions
    trip ends (columns) for all zones (index).
    """
    delivery_parcel_bush: pd.DataFrame
    """Delivery parcel bush Origins and Destinations
    trip ends (columns) for all zones (index).
    """
    delivery_grocery: pd.DataFrame
    """Delivery grocery bush Origins and Destinations
    trip ends (columns) for all zones (index).
    """
    commuting_drivers: pd.DataFrame
    """Commuting Productions and Attractions trip ends (columns) for Drivers
    (SOC821) for all zones (index).
    """
    commuting_skilled_trades: pd.DataFrame
    """Commuting Productions and Attractions trip ends (columns) for Skilled
    trades (SOCs 51, 52, 53) for all zones (index).
    """
    zones: np.ndarray = field(init=False)
    """Array of all zones, used as index for all trip end dataframes."""

    def __post_init__(self):
        """Reindex all trip end dataframes to contain all zones."""
        dataframes = (
            "service",
            "delivery_parcel_stem",
            "delivery_parcel_bush",
            "delivery_grocery",
            "commuting_drivers",
            "commuting_skilled_trades",
        )
        index = pd.Int64Index([])
        for nm in dataframes:
            index = index.union(getattr(self, nm).index)
        self.zones = index.values
        for nm in dataframes:
            df = getattr(self, nm).reindex(index, fill_value=0)
            # Fill any other NaNs with 0s
            df.fillna(0, inplace=True)
            setattr(self, nm, df)

    def asdict(self) -> dict[str, pd.DataFrame]:
        """Return copies of class attributes as a dictionary."""
        attrs = (
            "service",
            "delivery_parcel_stem",
            "delivery_parcel_bush",
            "delivery_grocery",
            "commuting_drivers",
            "commuting_skilled_trades",
            "zones",
        )
        return {a: getattr(self, a).copy() for a in attrs}

    def __str__(self) -> str:
        msg = [f"{self.__class__.__name__}("]
        for attr in self.asdict():
            if attr == "zones":
                val = getattr(self, attr)
                msg.append(f"{attr}={type(val)}<length {len(val)}><dtype {val.dtype}>")
                continue
            buf = io.StringIO()
            getattr(self, attr).info(buf=buf)
            msg.append(f"{attr}=" + buf.getvalue().replace("\n", "\n\t\t").strip())
        return "\n\t".join(msg) + "\n)"

    def __repr__(self) -> str:
        return str(self)


@dataclass
class LGVMatrices:
    """Dataclass to store the trip matrices for all segments.

    Aligns all the trip matrices to include all zones present
    in at least one DataFrame, any missing zones are filled
    with 0 trips for that DataFrame. Calculates `combined`
    matrix by summing the individual segment matrices.
    """

    service: pd.DataFrame
    """Service trips matrix, with zone numbers
    for columns and indices."""
    delivery_parcel_stem: pd.DataFrame
    """Delivery parcel stem trips matrix, with zone numbers
    for columns and indices."""
    delivery_parcel_bush: pd.DataFrame
    """Delivery parcel bush trips matrix, with zone numbers
    for columns and indices."""
    delivery_grocery: pd.DataFrame
    """Delivery grocery bush trips matrix, with zone numbers
    for columns and indices."""
    commuting_drivers: pd.DataFrame
    """Commuting drivers (SOC821) trips matrix, with zone numbers
    for columns and indices."""
    commuting_skilled_trades: pd.DataFrame
    """Commuting skilled trades (SOCs 51, 52, 53) trips matrix,
    with zone numbers for columns and indices."""
    combined: pd.DataFrame = field(init=False)
    """Trips matrix for all combined segments, with zone numbers
    for columns and indices."""
    zones: np.ndarray = field(init=False)
    """Array of all zones, used as index for all trip end dataframes."""

    def __post_init__(self):
        """Reindex all trip end dataframes to contain all zones.

        Sum invidual matrices together to get `combined` matrix.
        """
        dataframes = (
            "service",
            "delivery_parcel_stem",
            "delivery_parcel_bush",
            "delivery_grocery",
            "commuting_drivers",
            "commuting_skilled_trades",
        )
        index = pd.Int64Index([])
        for nm in dataframes:
            index = index.union(getattr(self, nm).index)
            index = index.union(getattr(self, nm).columns)
        self.zones = index.values
        for nm in dataframes:
            df = getattr(self, nm).reindex(index, fill_value=0)
            df = df.reindex(index, axis=1, fill_value=0)
            # Fill any other NaNs with 0s
            df.fillna(0, inplace=True)
            setattr(self, nm, df)
        self.combined = (
            self.service
            + self.delivery_parcel_stem
            + self.delivery_parcel_bush
            + self.delivery_grocery
            + self.commuting_drivers
            + self.commuting_skilled_trades
        )

    def asdict(self) -> dict[str, pd.DataFrame]:
        """Return copies of class attributes as a dictionary."""
        attrs = (
            "service",
            "delivery_parcel_stem",
            "delivery_parcel_bush",
            "delivery_grocery",
            "commuting_drivers",
            "commuting_skilled_trades",
            "combined",
            "zones",
        )
        return {a: getattr(self, a).copy() for a in attrs}

    def __str__(self) -> str:
        msg = f"{self.__class__.__name__}("
        ls = []
        for nm, df in self.asdict().items():
            ls.append(f"{nm}=Matrix{df.shape}")
        msg += ", ".join(ls)
        msg += ")"
        return msg

    def __repr__(self) -> str:
        return str(self)


##### FUNCTIONS #####
def calculate_trip_ends(
    input_paths: LGVInputPaths,
    output_folder: Path,
    lgv_growth: float,
    year: int,
    message_hook: Callable = print,
) -> LGVTripEnds:
    """Calculates the LGV trip ends for all segments.

    Parameters
    ----------
    input_paths : LGVInputPaths
        Paths to all the input files.
    output_folder : Path
        Path to folder to save trip ends to.
    lgv_growth : float
        Model year LGV growth factor.
    year : int
        Model year.
    message_hook : Callable, optional
        Function for writing messages, by default print

    Returns
    -------
    LGVTripEnds
        Trip end dataframes for each segment.

    See Also
    --------
    .service_segment.ServiceTripEnds: Calculates service trip ends.
    .delivery_segment.DeliveryTripEnds: Calculates delivery trip ends.
    LGVTripEnds: Stores all trip end DataFrames.
    """
    output_folder.mkdir(exist_ok=True)
    # Calculate the service trip ends and save output
    message_hook("Calculating Service trip ends")
    service = ServiceTripEnds(
        input_paths.household_paths,
        input_paths.bres_paths,
        input_paths.parameters_path,
        lgv_growth,
    )
    service.read()
    service.trip_ends.to_csv(output_folder / "service_trip_ends.csv")

    # Calculate the delivery trip ends and save outputs
    message_hook("Calculating Delivery trip ends")
    delivery = DeliveryTripEnds(
        input_paths.voa_paths,
        input_paths.bres_paths,
        input_paths.household_paths,
        input_paths.parameters_path,
        year,
    )
    delivery.read()
    delivery.parcel_stem_trip_ends.to_csv(
        output_folder / "delivery_parcel_stem_trip_ends.csv"
    )
    delivery.parcel_bush_trip_ends.to_csv(
        output_folder / "delivery_parcel_bush_trip_ends.csv"
    )
    delivery.grocery_bush_trip_ends.to_csv(
        output_folder / "delivery_grocery_trip_ends.csv"
    )

    # Calculate commuting trip ends and save output
    message_hook("Calculating Commuting trip ends")
    commute = CommuteTripEnds(
        {
            "commuting tables": input_paths.parameters_path,
            "household projections": input_paths.household_paths.path,
            "BRES": input_paths.bres_paths.path,
            "QS606EW": input_paths.qs606ew_path,
            "QS606SC": input_paths.qs606sc_path,
            "SC&W dwellings": input_paths.sc_w_dwellings_path,
            "E dwellings": input_paths.e_dwellings_path,
            "NDR floorspace": input_paths.ndr_floorspace_path,
            "VOA": input_paths.voa_paths.path,
            "LSOA lookup": input_paths.lsoa_lookup_path,
            "MSOA lookup": input_paths.msoa_lookup_path,
            "LAD lookup": input_paths.lad_lookup_path,
            "Postcodes": input_paths.voa_paths.zc_path,
        }
    )
    commute_trips = commute.trips
    for key in commute_trips:
        commute_trips[key].to_csv(output_folder / Path(f"commute_{key}_trip_ends.csv"))

    message_hook("\tDone with trip ends")
    return LGVTripEnds(
        service=service.trip_ends,
        delivery_parcel_stem=delivery.parcel_stem_trip_ends,
        delivery_parcel_bush=delivery.parcel_bush_trip_ends,
        delivery_grocery=delivery.grocery_bush_trip_ends,
        commuting_drivers=commute_trips["Drivers"],
        commuting_skilled_trades=commute_trips["Skilled trades"],
    )


def _calibrate_gm(
    trip_ends: pd.DataFrame,
    name: str,
    input_paths: LGVInputPaths,
    gm_params: pd.DataFrame,
    internals: set,
    message_hook: Callable = print,
) -> CalibrateGravityModel:
    """Internal function used in `run_gravity_model` for running the GM with calibration."""
    calibrate = gm_params.loc[name, "calibrate"]
    message_hook(f"Running Gravity Model: {name}, with calibration {calibrate}")
    calib_gm = CalibrateGravityModel(
        trip_ends,
        input_paths.cost_matrix_path,
        (input_paths.trip_distributions_path, TRIP_DISTRIBUTION_SHEETS[name]),
        input_paths.calibration_matrix_path,
        internal_zones=internals,
    )
    calib_gm.calibrate_gravity_model(
        function=gm_params.loc[name, "function"],
        init_params=tuple(gm_params.loc[name, ["param1", "param2"]]),
        calibrate=calibrate,
        constraint=gm_params.loc[name, "furness_type"],
    )
    message_hook("\tFinished, now writing outputs")
    return calib_gm


def run_gravity_model(
    input_paths: LGVInputPaths,
    trip_ends: LGVTripEnds,
    output_folder: Path,
    message_hook: Callable = print,
) -> LGVMatrices:
    """Run the gravity model calibration for each segment.

    Parameters
    ----------
    input_paths : LGVInputPaths
        Paths to all inputs files.
    trip_ends : LGVTripEnds
        Trip ends for each segment.
    output_folder : Path
        Path to folder to save outputs.
    message_hook : Callable, optional
        Function for writing messages, by default print

    Returns
    -------
    LgvMatrices
        Trip matrices for each segment and combined.
    """
    internals = read_study_area(input_paths.model_study_area)
    gm_params = read_gm_params(input_paths.parameters_path)
    matrices = {}
    for name, te in trip_ends.asdict().items():
        if name == "zones":
            continue
        try:
            calib_gm = _calibrate_gm(
                te, name, input_paths, gm_params, internals, message_hook
            )
        except Exception as e:
            message_hook(f"\t{e.__class__.__name__}: {e}")
            continue

        output_folder.mkdir(exist_ok=True)
        # Check if segment outputs a PA matrix which needs to be converted
        if name in PA_MATRICES:
            # Save PA matrix to CSV and convert to OD dataframe
            message_hook("\tConverting PA to OD")
            calib_gm.trip_matrix.to_csv(output_folder / (name + "-trip_matrix-PA.csv"))
            matrices[name] = annual_pa_to_od(
                calib_gm.trip_matrix.values,
                calib_gm.trip_ends.attractions.values,
                calib_gm.trip_ends.productions.values,
            )
            matrices[name] = pd.DataFrame(
                matrices[name],
                index=calib_gm.trip_matrix.index,
                columns=calib_gm.trip_matrix.columns,
            )
            # Calculate trip distributions for OD
            col = "OD whole matrix proportions"
            calib_gm.trip_distribution[col] = calib_gm._normalised_distribution(
                matrices[name], internal_area=False
            )
        else:
            matrices[name] = calib_gm.trip_matrix

        # Save the annual matrix, TLD graph and Excel summary file
        calib_gm.plot_distribution(output_folder / (name + "-distribution.pdf"))
        matrices[name].to_csv(output_folder / (name + "-trip_matrix-OD.csv"))
        with pd.ExcelWriter(output_folder / (name + "-GM_log.xlsx")) as writer:
            df = pd.DataFrame.from_dict(calib_gm.results.asdict(), orient="index")
            df.to_excel(writer, sheet_name="Calibration Results", header=False)
            df = pd.DataFrame.from_dict(
                calib_gm.furness_results.asdict(), orient="index"
            )
            df.to_excel(writer, sheet_name="Furnessing Results", header=False)
            calib_gm.trip_distribution.to_excel(
                writer, sheet_name="Trip Distribution", index=False
            )
            if name in PA_MATRICES:
                vehicle_kms = calculate_vehicle_kms(
                    calib_gm.trip_matrix, calib_gm.costs, internals
                )
                vehicle_kms.to_excel(writer, sheet_name="Vehicle Kilometres (PA)")
            vehicle_kms = calculate_vehicle_kms(
                matrices[name], calib_gm.costs, internals
            )
            vehicle_kms.to_excel(writer, sheet_name="Vehicle Kilometres")
        message_hook("\tFinished writing")

    return LGVMatrices(**matrices)


def matrix_time_periods(
    matrices: LGVMatrices, factors_path: Path, output_folder: Path
) -> dict[str, LGVMatrices]:
    """Converts all matrices to time periods based on factors in `factors_path`.

    Saves all matrices to sub-folder inside `output_folder`,
    the sub-folders have the same names as the time periods
    given.

    Parameters
    ----------
    matrices : LGVMatrices
        The trip matrices to be converted.
    factors_path : Path
        Path to Excel workbook containing time period
        factors.
    output_folder : Path
        Path to the folder where outputs are saved.

    Returns
    -------
    dict[str, LGVMatrices]
        Dictionary containing all matrices (values) for
        each time period (keys), contains the same time
        periods as given in the input table.

    See Also
    --------
    read_time_factors
        Function to read time period factors from `factors_path`.
    """
    factors = read_time_factors(factors_path)
    output_folder.mkdir(exist_ok=True)
    df = pd.DataFrame.from_dict(factors, orient="index")
    df.to_csv(output_folder / "time_period_factors.csv", index_label="Time Periods")
    tp_matrices = {}
    for tp, fac in factors.items():
        folder = output_folder / tp
        folder.mkdir(exist_ok=True)
        tmp_matrices = {}
        for name, mat in matrices.asdict().items():
            if name in ("zones", "combined"):
                continue
            mat = mat * fac.get(name)
            mat.to_csv(folder / f"{tp}_{name}-trip_matrix.csv")
            tmp_matrices[name] = mat
        tp_matrices[tp] = LGVMatrices(**tmp_matrices)
        tp_matrices[tp].combined.to_csv(folder / f"{tp}_combined-trip_matrix.csv")
    return tp_matrices


def main(input_paths: LGVInputPaths, message_hook: Callable = print):
    """Runs the LGV model.

    Parameters
    ----------
    input_paths : LGVInputPaths
        Paths to all the input files for the LGV model.
    message_hook : Callable, optional
        Function for writing messages, by default print
    """
    message_hook("Getting model parameters")
    parameters = lgv_parameters(input_paths.parameters_path)

    # Create output folder
    message_hook("Creating output folder")
    output_folder = (
        input_paths.output_folder
        / f"LGV Model Outputs - {datetime.now():%Y-%m-%d %H.%M.%S}"
    )
    output_folder.mkdir(exist_ok=True, parents=True)

    message_hook("Calculating trip ends")
    trip_ends = calculate_trip_ends(
        input_paths,
        output_folder / "trip ends",
        parameters["lgv_growth"],
        parameters["year"],
        message_hook=message_hook,
    )
    message_hook("Running gravity model to get annual matrices")
    annual_matrices = run_gravity_model(
        input_paths,
        trip_ends,
        output_folder / "annual trip matrices",
        message_hook=message_hook,
    )
    message_hook("Calculating matrices by time period")
    matrix_time_periods(
        annual_matrices,
        input_paths.parameters_path,
        output_folder / "time period matrices",
    )
    message_hook("Done")


def lgv_arg_parser() -> argparse.ArgumentParser:
    """Creates `ArgumentParser` for the LGV model.

    Returns
    -------
    argparse.ArgumentParser
        ArgumentParser which accepts the path to the
        config file, a flag to create an example file
        or nothing.
    """

    def file_path(path) -> Path:
        path = Path(path)
        if not path.is_file():
            raise ValueError("file doesn't exist")
        return path

    parser = argparse.ArgumentParser(prog=__package__, description=__doc__)
    parser.add_argument(
        "-c",
        "--config_file",
        type=file_path,
        help="Path to configuration file containing all LGV model inputs",
    )
    parser.add_argument(
        "-e",
        "--example",
        action="store_true",
        help="If given will write an example config "
        "file to the current working directory",
    )
    return parser
