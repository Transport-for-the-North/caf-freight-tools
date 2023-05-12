"""
Handles inpputs and outputs of the tool
also contains constants defined for the tool
"""
# standard packages
from __future__ import annotations
import pathlib
import dataclasses
from typing import NamedTuple, Optional
import logging
import glob
import os

# third party packages
import caf.toolkit
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
import numpy as np
from matplotlib import collections


# constants
LOG = logging.getLogger(__name__)

#   process consts
CRS = 27700
GEOSPATIAL_PRECISION = 1000
A_ROAD_LABEL = "A Road"
MOTORWAY_LABEL = "Motorway"
TO_M_FACTOR = 1000
ROADS_REQUIRED_COLUMNS = [
    "fictitious",
    "identifier",
    "class",
    "roadnumber",
    "startnode",
    "endnode",
    "geometry",
]
SERVICES_REQUIRED_COLUMNS = ["name", "geometry"]
DEMAND_MATRIX_REQUIRED_COLUMNS = ["origin", "destination", "trips"]
JUNCTION_REQUIRED_COLUMNS = ["number", "geometry"]
MAP_LABELS_REQUIRED_COLUMNS = ["name", "geometry"]

#   plotting visual const
# UPDATING COLOUR MAP WILL NOT UPDATE BOKEH COLOURBAR!!!!
COlOUR_MAP = "inferno"

SCALE_LABEL = "Thirstiness"

MOTORWAY_LINEWIDTH = 1
A_ROAD_LINEWIDTH = 0.5
ROAD_COLOUR = "gray"

JUNCTION_COLOUR = "gray"
JUNCTION_SIZE = 5
JUNCTION_SHAPE = "x"

OUTLINE_COLOUR = "deepskyblue"
OUTLINE_WIDTH = 0.3

SERVICES_SIZE = 5
SERVICES_COLOUR = "gray"
SERVICES_SHAPE = "diamond_dot"

LABEL_SHAPE = "triangle"
LABEL_TEXT_COLOUR = "white"
LABEL_SHAPE_COLOUR = "white"
LABEL_TEXT_SIZE = "8px"
LABEL_SHAPE_SIZE = 5


@dataclasses.dataclass
class AnalysisInputs:
    """Input data file paths

    Parameters
    ----------
    od_demand_matrix_path:pathlib.Path
        file path for OD trip matrix to analyse
    zone_centroids_path:pathlib.Path
        file path for zone centroids for the corresponding OD zones
    range: float
        range of vehicle
    """

    od_demand_matrix_path: pathlib.Path
    zone_centroids_path: pathlib.Path
    range: float


@dataclasses.dataclass
class PlottingInputs:
    """Paths to files used for plotting outputs

    network_path: pathlib.Path
        path to road network file/folder
    motorway_junction_path: pathlib.Path
        path to motorway junctions file/folder
    """

    network_path: pathlib.Path
    motorway_junction_path: pathlib.Path
    outlines_path: pathlib.Path
    service_stations_path: pathlib.Path
    map_labels_path: pathlib.Path


class ParsedPlottingInputs(NamedTuple):
    """for storing parsed plotting inputs

    Parameters
    ----------
    roads: gpd.GeoDataFrame
        road network for plotting
    junctions: gpd.GeoDataFrame
        motorway junctions for plotting
    """

    roads: gpd.GeoDataFrame
    junctions: gpd.GeoDataFrame
    outlines: gpd.GeoDataFrame
    service_stations: gpd.GeoDataFrame
    map_labels: gpd.GeoDataFrame


class ParsedAnalysisInputs(NamedTuple):
    """for storing the parsed inputs

    Parameters
    ----------
    demand_marix: pd.DataFrame
        OD trip matrix to analyse
    zone_centroids: gpd.GeoDataFrame
        zone centroids for the corresponding OD zones
    range: float
        vehicle range in m
    """

    demand_marix: pd.DataFrame
    zone_centroids: gpd.GeoDataFrame
    range: float


@dataclasses.dataclass
class Operational:
    """operational inputs for the tool

    Parameters
    ----------
    output_folder:pathlib.Path
        output folder path
    a_roads: bool
        whether to include A-roads on plot
    show_plots:bool
        whether to show the MatPlotLib plot
    hex_bin_width: float
        approximate width of hex bins
    """

    output_folder: pathlib.Path
    a_roads: bool
    show_plots: bool
    hex_bin_width: float


class ThirstyTruckConfig(caf.toolkit.BaseConfig):
    """manages reading the thirsty truck config file

    Parameters
    ----------
    analysis_inputs: AnalysisInputs
        file paths for inputs used for analysis
    plotting_inputs: PlottingInputs
        file paths for inputs used for plotting
    operational: Operational
        contain the operational file paths and parameters
    """

    analysis_inputs: AnalysisInputs
    plotting_inputs: PlottingInputs
    operational: Operational

    def convert_to_m(self) -> None:
        """converts any class attributes that are not in m into m"""
        self.analysis_inputs.range = self.analysis_inputs.range * TO_M_FACTOR
        self.operational.hex_bin_width = self.operational.hex_bin_width * TO_M_FACTOR

    def parse_analysis_inputs(self) -> ParsedAnalysisInputs:
        """parses inputs into a named tuple

        Returns
        -------
        ParsedAnalysisInputs
            named tuple containing all analysis input data
        """
        LOG.info("Parsing inputs")
        # read in files

        # check range is correct type
        try:
            range_ = float(self.analysis_inputs.range)
        except ValueError:
            raise ValueError(
                "The range you provided in not a number, please re-enter the value. Cheers!"
            )

        LOG.info("Parsing Centroids")
        zone_centroids = gpd.read_file(self.analysis_inputs.zone_centroids_path)
        zone_centroids = check_and_format_centroids(zone_centroids)

        LOG.info("Parsing OD demand matrix")
        demand_matrix = pd.read_csv(self.analysis_inputs.od_demand_matrix_path)
        demand_matrix = check_and_format_demand_matrix(demand_matrix)

        return ParsedAnalysisInputs(
            demand_marix=demand_matrix,
            zone_centroids=zone_centroids,
            range=range_,
        )

    def parse_plotting_inputs(self) -> ParsedPlottingInputs:
        """Parses Plotting inputs

        Returns
        -------
        ParsedPlottingInputs
            parsed plotting inputs from config file
        """
        LOG.info("Parsing road network")

        if self.plotting_inputs.network_path.is_dir():
            roads = read_in_network_folder(
                self.plotting_inputs.network_path,
                self.operational.a_roads,
                self.operational.output_folder,
            )
        else:
            roads = read_shape_file(
                self.plotting_inputs.network_path,
                required_columns=ROADS_REQUIRED_COLUMNS,
            )
            roads = format_roads(roads, self.operational.a_roads)

        if len(roads) == 0:
            LOG.warning(
                "filtering by road class yeilded no roads."
                f" Please ensure your roads file's 'class' column contains '{MOTORWAY_LABEL}' "
                f"and (if applicable) '{A_ROAD_LABEL}' values. This is the same format as the "
                "data provided on the OS datahub website."
            )

        LOG.info("Parsing motorway junctions")

        if self.plotting_inputs.motorway_junction_path.is_dir():
            junctions = read_in_junction_folder(
                self.plotting_inputs.motorway_junction_path,
                self.operational.output_folder,
            )

        else:
            junctions = read_shape_file(
                self.plotting_inputs.motorway_junction_path,
                required_columns=JUNCTION_REQUIRED_COLUMNS,
            )

        outlines = read_shape_file(
            self.plotting_inputs.outlines_path, precision=GEOSPATIAL_PRECISION
        )
        # some remove any multilinestringgs
        outlines = outlines.explode()

        services_stations = read_shape_file(
            self.plotting_inputs.service_stations_path,
            required_columns=SERVICES_REQUIRED_COLUMNS,
        )

        map_labels = read_shape_file(
            self.plotting_inputs.map_labels_path,
            required_columns=MAP_LABELS_REQUIRED_COLUMNS,
        )

        return ParsedPlottingInputs(
            roads=roads,
            junctions=junctions,
            outlines=outlines,
            service_stations=services_stations,
            map_labels=map_labels,
        )


def check_and_format_centroids(zone_centroids: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """checks and formats inputted zone centroids



    Parameters
    ----------
    zone_centroids : gpd.GeoDataFrame
        loaded in zone centroids

    Returns
    -------
    gpd.GeoDataFrame
        checked and reformatted zone centroids

    Raises
    ------
    IndexError
        Centroids must have id column called 'uniqueid' (case insensitive)
    ValueError
        zone centroids must have a Point geometry type (Multipoint is not valid)
    """
    # columns to lower case
    zone_centroids.columns = zone_centroids.columns.str.lower()
    # to easting northing
    zone_centroids.to_crs(CRS, inplace=True)
    # check centroids have "uniqueid" in columns and convert all to lowercase
    if "uniqueid" not in zone_centroids.columns:
        raise IndexError(
            "Centroids must have id column called 'uniqueid' (case insensitive)"
        )
    # check centroid geom type
    if (~(zone_centroids.geom_type == "Point")).any():
        raise ValueError(
            "zone centroids must have a Point geometry type (Multipoint is not valid)"
        )
    # remove unwanted columns from centroids
    return zone_centroids.loc[:, ["uniqueid", "geometry"]]


def check_and_format_demand_matrix(demand_matrix: pd.DataFrame) -> pd.DataFrame:
    """checks demand matrix is as expected

    Parameters
    ----------
    demand_matrix : pd.DataFrame
        inputted demand matrix

    Returns
    -------
    pd.DataFrame
        reformatted and checked demand matrix


    """
    # convert columns to lower case
    demand_matrix.columns = demand_matrix.columns.str.lower()
    # check columns are correct
    check_columns("OD matrix", demand_matrix.columns, DEMAND_MATRIX_REQUIRED_COLUMNS)
    # removed additional columns
    return demand_matrix.loc[:, DEMAND_MATRIX_REQUIRED_COLUMNS]


def read_shape_file(
    file: pathlib.Path,
    required_columns: Optional[list[str]] = None,
    precision: Optional[float] = None,
) -> gpd.GeoDataFrame:
    """read, checks and formats shape file

    if required columns is defined, will check those columns exist
    in file and remove any other columns
    if precision is defined the geometry will be simpilified to that
    precision

    Parameters
    ----------
    file : pathlib.Path
        _description_
    required_columns : Optional[list[str]], optional
        _description_, by default None
    precision : Optional[float], optional
        _description_, by default None

    Returns
    -------
    gpd.GeoDataFrame
        _description_
    """    
    read_file = gpd.read_file(file)
    read_file.to_crs(CRS)
    read_file.columns = read_file.columns.str.lower()
    if required_columns is not None:
        check_columns(file, read_file.columns, required_columns)
        read_file = read_file[required_columns]
    if precision is not None:
        read_file.simplify(precision)
    return read_file


def read_in_network_folder(
    network_folder_path: pathlib.Path,
    a_road: bool,
    output_file: pathlib.Path,
) -> gpd.GeoDataFrame:
    """Proccesses road folder containing the road links

    will read in all shape files in a folder and proccess and save them into one shape file
    with motorways and optional A-roads

    assumes data is in OS datahub format

    Parameters
    ----------
    roads_path : pathlib.Path
        path to folder containing shapefiles
    a_road : bool
        whether the user wishes to include a roads in selection
    output_file: pathlib.Path
        folder to save file to
    Returns
    -------
    gpd.GeoDataFrame
        filtered and aggregated road network

    Raises
    ------
    ValueError
        if the folder contains no .shp files
    """
    # get list of files in folder
    file_search = network_folder_path / "*.shp"
    file_list = glob.glob(str(file_search))
    if len(file_list) == 0:
        raise ValueError(
            f"The roads folder path {network_folder_path} contains"
            " no .shp files. please review this before re-runnung."
        )
    # unpack files and check format
    roads_list = []
    LOG.info("Loading road network files")
    for file in tqdm(file_list):
        roads_list.append(read_shape_file(file, ROADS_REQUIRED_COLUMNS))
    # create one df with all roads
    roads = pd.concat(roads_list, ignore_index=True)

    # filter for required roads
    roads = format_roads(roads, a_road)

    roads_file = output_file / "aggregated_filtered_road_network"
    roads_file.mkdir(exist_ok=True)
    to_shape_file(roads_file / "aggregated_filtered_road_network.shp", roads)
    return roads


def format_roads(roads: gpd.GeoDataFrame, a_road: bool) -> gpd.GeoDataFrame:
    """format and simplify road network

    simplifies the input road network
    attempts to join roads into one linestring

    Parameters
    ----------
    roads : gpd.GeoDataFrame
        road network
    a_road : bool
        whether to keep a roads

    Returns
    -------
    gpd.GeoDataFrame
        formatted and simplified roads
    """

    # filter
    LOG.info("Filtering road network")
    keep = roads["class"] == MOTORWAY_LABEL
    if a_road:
        a_road = roads["class"] == A_ROAD_LABEL
        keep = (pd.DataFrame([keep, a_road]).transpose()).any(axis=1)
    keep_roads = roads.loc[keep]

    LOG.info("Reorder road links")

    # format to gdf

    keep_roads = gpd.GeoDataFrame(keep_roads, geometry="geometry")
    keep_roads.simplify(GEOSPATIAL_PRECISION)

    return keep_roads


def read_in_junction_folder(
    junction_folder_path: pathlib.Path,
    output_file: pathlib.Path,
) -> gpd.GeoDataFrame:
    """reads in the junction folder and aggregates them into one geodataframe

    outputs the data frame to shapefile

    Parameters
    ----------
    junction_folder_path : pathlib.Path
        location of junction folder
    output_file : pathlib.Path
        location to output shapefile

    Returns
    -------
    gpd.GeoDataFrame
        aggregated junctions
    """
    file_search = junction_folder_path / "*.shp"
    file_list = glob.glob(str(file_search))
    if len(file_list) == 0:
        raise ValueError(
            f"The junctions folder path {junction_folder_path} contains"
            " no .shp files. please review this before re-runnung."
        )

    juctions_list = []
    # load in files and check columns
    LOG.info("Loading motorway junction files")
    for file in tqdm(file_list):
        juctions_list.append(read_shape_file(file, JUNCTION_REQUIRED_COLUMNS))

    junctions = pd.concat(juctions_list, ignore_index=True)

    junctions = gpd.GeoDataFrame(junctions, geometry="geometry")

    # write road shape file
    junctions_output_file = output_file / "aggregated_junctions"
    junctions_output_file.mkdir(exist_ok=True)
    to_shape_file(junctions_output_file / "aggregated_junctions.shp", junctions)

    return junctions


def check_columns(
    filename: str, file_columns: list[str], required_columns: list[str]
) -> None:
    """checks required columns are in the file column

    Parameters
    ----------
    filename : str
        name of file for error
    file_columns : list[str]
        columns in file
    required_columns : list[str]
        columns expected in file

    Raises
    ------
    IndexError
        if a required column is not in file column
    """
    for column in required_columns:
        if column not in file_columns:
            raise IndexError(
                f"{filename} does not contain {column} column."
                f" Required columns for road files are {required_columns}"
            )


def output_file_checks(output_function):
    """decorator for out put fuctions

    will deal with permission errors and warn user when overwriting file


    Parameters
    ----------
    output_function : function
        output function, the first input must be the output file path
    """

    def wrapper_func(file_path, *args, **kwargs):
        if os.path.exists(file_path):
            LOG.warning(f"overwriting {file_path}")
        while True:
            try:
                output_function(file_path, *args, **kwargs)
                break
            except PermissionError:
                input(f"Please close {file_path}, then press enter. Cheers!")
        # Do something after the function.

    return wrapper_func


@output_file_checks
def to_shape_file(file_name: pathlib.Path, data: gpd.GeoDataFrame) -> None:
    """creates shapefile from GDF utilising output file check

    Parameters
    ----------
    file_name : pathlib.Path
        file path
    data : gpd.GeoDataFrame
        data to save
    """
    data.to_file(file_name)


@dataclasses.dataclass
class HexTilling:
    """
    class to handle the hextilling parameters

    centres_x: np.ndarray
        x coords of centre of hexs
    centres_y: np.ndarray
        y coords of centre of hexs
    count: np.ndarray
        count from hex binning
    rgb: list[tuple[int]]
        rbg colour of hexes
    rel_vertices_x: Optional[np.ndarray] = None
        vertices x coords relative to centre for a single hex
    rel_vertices_y: Optional[np.ndarray] = None
        vertices y coords relative to centre for a single hex
    vertices_x: Optional[list[list[float]]] = None
        absolute x coordinates of hexes vertices (for all hexes)
    vertices_y: Optional[list[list[float]]] = None
        absolute y coordinates of hexes vertices (for all hexes)
    """

    centres_x: np.ndarray
    centres_y: np.ndarray
    count: np.ndarray
    rgb: list[tuple[int]]
    rel_vertices_x: Optional[np.ndarray] = None
    rel_vertices_y: Optional[np.ndarray] = None
    vertices_x: Optional[list[list[float]]] = None
    vertices_y: Optional[list[list[float]]] = None

    @classmethod
    def from_polycollection(cls, hexbin: collections.PolyCollection) -> HexTilling:
        """create an instance of hextilling from the hexbin polycollection output

        Parameters
        ----------
        hexbin : collections.PolyCollection
            output from matplotlib.pyplot.hexbin

        Returns
        -------
        HexTilling
            parameters unpacked from hexbin
        """
        # get attributes from hexbin
        centres_x = hexbin.get_offsets()[:, 0]
        centres_y = hexbin.get_offsets()[:, 1]
        count = hexbin.get_array()
        # apply cmap to counts
        intial_rgb = hexbin.to_rgba(count, bytes=True)
        # cut out alpha value column clarity
        intial_rgb = intial_rgb[:, 0:3]
        # relative count
        relative_count = (count / count.max()) * 100
        # calculate size of hex
        paths = hexbin.get_paths()[0]

        vertices = paths.vertices

        rel_vertices_x = vertices[:, 0]
        rel_vertices_y = vertices[:, 1]

        vertices_x = []
        vertices_y = []
        rgb = []
        for i, centre_x in enumerate(centres_x):
            vertices_x.append(rel_vertices_x + centre_x)
            vertices_y.append(rel_vertices_y + centres_y[i])
            rgb.append(tuple(intial_rgb[i]))

        return HexTilling(
            centres_x=centres_x,
            centres_y=centres_y,
            count=relative_count,
            rgb=rgb,
            vertices_x=vertices_x,
            vertices_y=vertices_y,
        )

    def create_absolute_vertex(self) -> None:
        """calculates and saves absolute vertices from relative vertices and centres"""
        vertices_x = []
        vertices_y = []
        for i, centre_x in enumerate(self.centres_x):
            vertices_x.append(self.rel_vertices_x + centre_x)
            vertices_y.append(self.rel_vertices_y + self.centres_y[i])
        self.vertices_x = vertices_x
        self.vertices_y = vertices_y
