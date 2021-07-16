# -*- coding: utf-8 -*-
"""
    Module containing the high level functions for running the LGV model.
"""

##### IMPORTS #####
# Standard imports
import configparser
import io
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# Third party imports
import pandas as pd

# Local imports
from ..data_utils import DataPaths
from .lgv_inputs import lgv_parameters, LGVInputPaths, read_study_area
from .service_segment import ServiceTripEnds
from .delivery_segment import DeliveryTripEnds
from .commute_segment import CommuteTripEnds
from .gravity_model import CalibrateGravityModel
from .furnessing import FurnessConstraint


##### CONSTANTS #####
CONSTRAINTS_BY_SEGMENT = {
    "service": FurnessConstraint.DOUBLE,
    "delivery_parcel_stem": FurnessConstraint.DOUBLE,
    "delivery_parcel_bush": FurnessConstraint.SINGLE,
    "delivery_grocery": FurnessConstraint.SINGLE,
    "commuting_drivers": FurnessConstraint.DOUBLE,
    "commuting_skilled_trades": FurnessConstraint.DOUBLE,
}
"""Constraint type for each trip ends segment."""
TRIP_DISTRIBUTION_SHEETS = {
    "service": "Service",
    "delivery_parcel_stem": "Delivery",
    "delivery_parcel_bush": "Delivery Bush",
    "delivery_grocery": "Delivery Bush",
    "commuting_drivers": "Commuting",
    "commuting_skilled_trades": "Commuting",
}
"""Name of sheet in trip distributions file for each segment."""

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
    def write_example(cls, path: Path):
        """Write example of the config file, with no values.

        Parameters
        ----------
        path : Path
            Path to write the example config file too,
            will be overwritten if already exists.
        """
        config = configparser.ConfigParser()
        config[cls.SECTION] = {k: "" for k in cls.OPTIONS}
        with open(path, "wt") as f:
            config.write(f)

    def __str__(self) -> str:
        paths_str = str(self.input_paths).replace("\n", "\n\t")
        return f"{self.__class__.__name__}\n\t{self.SECTION} = {paths_str}"


@dataclass
class LGVTripEnds:
    """Dataclass to store the trip end data for all segments."""

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

    def asdict(self) -> dict[str, pd.DataFrame]:
        """Return copies of class attributes as a dictionary."""
        attrs = (
            "service",
            "delivery_parcel_stem",
            "delivery_parcel_bush",
            "delivery_grocery",
            "commuting_drivers",
            "commuting_skilled_trades",
        )
        return {a: getattr(self, a).copy() for a in attrs}

    def __str__(self) -> str:
        msg = [f"{self.__class__.__name__}("]
        for attr in self.asdict():
            buf = io.StringIO()
            getattr(self, attr).info(buf=buf)
            msg.append(f"{attr}=" + buf.getvalue().replace("\n", "\n\t\t").strip())
        return "\n\t".join(msg) + "\n)"

    def __repr__(self) -> str:
        return str(self)


##### FUNCTIONS #####
def calculate_trip_ends(
    input_paths: LGVInputPaths, output_folder: Path, lgv_growth: float, year: int
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
    print("Calculating Trip Ends")
    output_folder.mkdir(exist_ok=True)
    # Calculate the service trip ends and save output
    service = ServiceTripEnds(
        input_paths.household_paths,
        input_paths.bres_paths,
        input_paths.parameters_path,
        lgv_growth,
    )
    service.read()
    service.trip_ends.to_csv(output_folder / "service_trip_ends.csv")

    # Calculate the delivery trip ends and save outputs
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

    print("\tDone")
    return LGVTripEnds(
        service=service.trip_ends,
        delivery_parcel_stem=delivery.parcel_stem_trip_ends,
        delivery_parcel_bush=delivery.parcel_bush_trip_ends,
        delivery_grocery=delivery.grocery_bush_trip_ends,
        commuting_drivers=commute_trips["Drivers"],
        commuting_skilled_trades=commute_trips["Skilled trades"],
    )


def run_gravity_model(
    input_paths: LGVInputPaths, trip_ends: LGVTripEnds, output_folder: Path
):
    """Run the gravity model calibration for each segment.

    Parameters
    ----------
    input_paths : LGVInputPaths
        Paths to all inputs files.
    trip_ends : LGVTripEnds
        Trip ends for each segment.
    output_folder : Path
        Path to folder to save outputs.
    """
    internals = read_study_area(input_paths.model_study_area)
    for name, te in trip_ends.asdict().items():
        print(f"Running Gravity Model: {name}")
        calib_gm = CalibrateGravityModel(
            te,
            input_paths.cost_matrix_path,
            (input_paths.trip_distributions_path, TRIP_DISTRIBUTION_SHEETS[name]),
            input_paths.calibration_matrix_path,
            internal_zones=internals,
        )
        calib_gm.calibrate_gravity_model(constraint=CONSTRAINTS_BY_SEGMENT[name])
        print("\tFinished, now writing outputs")
        output_folder.mkdir(exist_ok=True)
        calib_gm.plot_distribution(output_folder / (name + "-distribution.pdf"))
        calib_gm.trip_matrix.to_csv(output_folder / (name + "-trip_matrix.csv"))
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
        print("\tFinished writing")


def main(input_paths: LGVInputPaths):
    """Runs the LGV model.

    Parameters
    ----------
    input_paths : LGVInputPaths
        Paths to all the input files for the LGV model.
    """
    parameters = lgv_parameters(input_paths.parameters_path)

    # Create output folder
    output_folder = (
        input_paths.output_folder
        / f"LGV Model Outputs - {datetime.now():%Y-%m-%d %H.%M.%S}"
    )
    output_folder.mkdir(exist_ok=True, parents=True)

    trip_ends = calculate_trip_ends(
        input_paths,
        output_folder / "trip ends",
        parameters["lgv_growth"],
        parameters["year"],
    )
    run_gravity_model(input_paths, trip_ends, output_folder / "trip matrices")


# TODO Remove Test Code
if __name__ == "__main__":
    config_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\LGV_config.ini"
    )
    config_file = LGVConfig(config_path)
    main(config_file.input_paths)
