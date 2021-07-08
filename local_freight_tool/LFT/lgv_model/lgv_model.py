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
from .lgv_inputs import lgv_parameters
from .service_segment import ServiceTripEnds
from .delivery_segment import DeliveryTripEnds
from .commute_segment import CommuteTripEnds


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
    OPTIONS = (
        "households data",
        "households zone correspondence",
        "bres data",
        "bres zone correspondence",
        "voa data",
        "voa zone correspondence",
        "lgv parameters",
        "QS606EW",
        "QS606SC",
        "SC&W dwellings",
        "E dwellings",
        "NDR floorspace",
        "LSOA lookup",
        "MSOA lookup",
        "LAD lookup",
        "output folder",
    )
    """Names of the expected options."""
    household_paths: DataPaths = None
    """Paths for the households data and zone correspondence."""
    bres_paths: DataPaths = None
    """Paths for the BRES data and zone correspondence."""
    voa_paths: DataPaths = None
    """Paths for the VOA data and zone correspondence."""
    parameters_path: Path = None
    """Path to the LGV parameters Excel workbook."""
    qs606ew_path: Path = None
    """Path to the England & Wales Census Occupation data CSV."""
    qs606sc_path: Path = None
    """Path to the Scottish Census Occupation data CSV."""
    sc_w_dwellings_path: Path = None
    """Path to the Scottish and Welsh dwellings data CSV."""
    e_dwellings_path: Path = None
    """Path to the English dwellings data XLSX."""
    ndr_floorspace_path: Path = None
    """Path to the NDR Business Floorspace CSV."""
    lsoa_lookup_path: Path = None
    """Path to the LSOA to NoHAM zone correspondence
    CSV"""
    msoa_lookup_path: Path = None
    """Path to the MSOA to NoHAM zone correspondence
    CSV"""
    lad_lookup_path: Path = None
    """Path to the Local Authority District to NoHAM zone correspondence
    CSV"""

    def __init__(self, path: Path):
        """Initialises the class by reading the given file."""
        super().__init__()
        self.read(path)
        if not self.has_section(self.SECTION):
            raise configparser.NoSectionError(
                f"LGV config ({path.name}) doesn't contain section {self.SECTION!r}"
            )
        self.household_paths = DataPaths(
            "LGV Households",
            self.getpath(self.SECTION, self.OPTIONS[0]),
            self.getpath(self.SECTION, self.OPTIONS[1]),
        )
        self.bres_paths = DataPaths(
            "LGV BRES",
            self.getpath(self.SECTION, self.OPTIONS[2]),
            self.getpath(self.SECTION, self.OPTIONS[3]),
        )
        self.voa_paths = DataPaths(
            "LGV VOA",
            self.getpath(self.SECTION, self.OPTIONS[4]),
            self.getpath(self.SECTION, self.OPTIONS[5]),
        )
        self.parameters_path = self.getpath(self.SECTION, self.OPTIONS[6])
        self.qs606ew_path = self.getpath(self.SECTION, self.OPTIONS[7])
        self.qs606sc_path = self.getpath(self.SECTION, self.OPTIONS[8])
        self.sc_w_dwellings_path = self.getpath(self.SECTION, self.OPTIONS[9])
        self.e_dwellings_path = self.getpath(self.SECTION, self.OPTIONS[10])
        self.ndr_floorspace_path = self.getpath(self.SECTION, self.OPTIONS[11])
        self.lsoa_lookup_path = self.getpath(self.SECTION, self.OPTIONS[12])
        self.msoa_lookup_path = self.getpath(self.SECTION, self.OPTIONS[13])
        self.lad_lookup_path = self.getpath(self.SECTION, self.OPTIONS[14])
        self.output_folder = self.getpath(self.SECTION, self.OPTIONS[15])

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
        return Path(self.get(section, option, **kwargs))

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
        return f"""
        {__name__}.{self.__class__.__name__}
            {self.household_paths=}
            {self.bres_paths=}
            {self.voa_paths=}
            {self.parameters_path=}
            {self.qs606ew_path=}
            {self.qs606sc_path=}
            {self.sc_w_dwellings_path=}
            {self.e_dwellings_path=}
            {self.ndr_floorspace_path=}
            {self.lsoa_lookup_path=}
            {self.msoa_lookup_path=}
            {self.lad_lookup_path=}
        """


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

    def __dir__(self) -> tuple[str]:
        return (
            "service",
            "delivery_parcel_stem",
            "delivery_parcel_bush",
            "delivery_grocery",
            "commuting_drivers",
            "commuting_skilled_trades",
        )

    def __dict__(self) -> dict[str, pd.DataFrame]:
        return {a: getattr(self, a).copy() for a in self.__dir__()}

    def __str__(self) -> str:
        msg = [f"{self.__class__.__name__}("]
        for attr in self.__dir__():
            buf = io.StringIO()
            getattr(self, attr).info(buf=buf)
            msg.append(f"{attr}=" + buf.getvalue().replace("\n", "\n\t\t").strip())
        return "\n\t".join(msg) + "\n)"

    def __repr__(self) -> str:
        return str(self)


##### FUNCTIONS #####
def calculate_trip_ends(
    config: LGVConfig, output_folder: Path, lgv_growth: float, year: int
) -> LGVTripEnds:
    """Calculates the LGV trip ends for all segments.

    Parameters
    ----------
    config : LGVConfig
        Inputs from the config file.
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
    # Calculate the service trip ends and save output
    service = ServiceTripEnds(
        config.household_paths,
        config.bres_paths,
        config.parameters_path,
        lgv_growth,
    )
    service.read()
    service.trip_ends.to_csv(output_folder / "service_trip_ends.csv")

    # Calculate the delivery trip ends and save outputs
    delivery = DeliveryTripEnds(
        config.voa_paths,
        config.bres_paths,
        config.household_paths,
        config.parameters_path,
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
            "commuting tables": config.parameters_path,
            "household projections": config.household_paths.path,
            "BRES": config.bres_paths.path,
            "QS606EW": config.qs606ew_path,
            "QS606SC": config.qs606sc_path,
            "SC&W dwellings": config.sc_w_dwellings_path,
            "E dwellings": config.e_dwellings_path,
            "NDR floorspace": config.ndr_floorspace_path,
            "VOA": config.voa_paths.path,
            "LSOA lookup": config.lsoa_lookup_path,
            "MSOA lookup": config.msoa_lookup_path,
            "LAD lookup": config.lad_lookup_path,
            "Postcodes": config.voa_paths.zc_path,
        }
    )
    commute_trips = commute.trips()
    for key in commute_trips:
        commute_trips[key].to_csv(output_folder / Path(f"commute_{key}_trip_ends.csv"))

    return LGVTripEnds(
        service=service.trip_ends,
        delivery_parcel_stem=delivery.parcel_stem_trip_ends,
        delivery_parcel_bush=delivery.parcel_bush_trip_ends,
        delivery_grocery=delivery.grocery_bush_trip_ends,
        commute_drivers=commute_trips["Drivers"],
        commuting_skilled_trades=commute_trips["Skilled trades"],
    )


def main(config_path: Path):
    config = LGVConfig(config_path)
    parameters = lgv_parameters(config.parameters_path)

    # Create output folder
    if not config.output_folder.is_dir():
        raise NotADirectoryError(
            f"output folder is not a folder, or does not exist: {config.output_folder}"
        )
    output_folder = (
        config.output_folder / f"LGV Model Outputs - {datetime.now():%Y-%m-%d %H.%M.%S}"
    )
    output_folder.mkdir(exist_ok=True)
    out_trip_ends = output_folder / "trip ends"
    out_trip_ends.mkdir(exist_ok=True)

    trip_ends = calculate_trip_ends(
        config, out_trip_ends, parameters["lgv_growth"], parameters["year"]
    )
    print(trip_ends)


# TODO Remove Test Code
if __name__ == "__main__":
    config_file = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\LGV_config.ini"
    )
    main(config_file)
