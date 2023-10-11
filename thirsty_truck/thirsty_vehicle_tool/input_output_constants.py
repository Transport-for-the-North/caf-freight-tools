"""
Handles inpputs and outputs of the tool
also contains constants defined for the tool
"""
# standard packages
from __future__ import annotations
import pathlib
import dataclasses
from typing import NamedTuple, Optional
import glob
import os

# third party packages
import caf.toolkit
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
import numpy as np
from matplotlib import collections

from thirsty_vehicle_tool import tv_logging


# constants
LOG = tv_logging.get_logger(__name__)

#   process consts
CRS = 27700
GEOSPATIAL_PRECISION = 1000
A_ROAD_LABEL = "A Road"
MOTORWAY_LABEL = "Motorway"
TO_M_FACTOR = 1000
DEFAULT_SPEED_LIMIT = 48

ROADS_REQUIRED_COLUMNS = [
    "fictitious",
    "identifier",
    "class",
    "roadnumber",
    "geometry",
]
ZONE_CENTROIDS_REQUIRED_COLUMNS = ["uniqueid", "geometry"]
SERVICES_REQUIRED_COLUMNS = ["name", "geometry"]
DEMAND_MATRIX_REQUIRED_COLUMNS = ["origin", "destination", "trips"]
JUNCTION_REQUIRED_COLUMNS = ["number", "geometry"]
MAP_LABELS_REQUIRED_COLUMNS = ["name", "geometry"]
THRISTY_POINTS_REQUIRED_COLUMNS = ["easting", "northing", "trips"]
PLOTTING_POINTS_REQUIRED_KEYS = [
    "label",
    "data_path",
    "hover_column_name",
    "colour",
    "size",
    "shape",
]

ANALYSIS_NETWORK_NODES_REQUIRED_COLUMNS = [
    "n",
    "geometry",
]

ANALYSIS_NETWORK_REQUIRED_COLUMNS = [
    "a",
    "b",
    "distance",
    "spdlimit",
    "geometry",
]

#   plotting visual const
# UPDATING COLOUR MAP WILL NOT UPDATE BOKEH COLOURBAR!!!!
COlOUR_MAP = "inferno"

SCALE_LABEL = "Thirstiness"

MOTORWAY_LINEWIDTH = 1
A_ROAD_LINEWIDTH = 0.5
ROAD_COLOUR = "gray"

JUNCTION_COLOUR = "gray"
JUNCTION_SIZE = 3
JUNCTION_SHAPE = "circle"

OUTLINE_COLOUR = "deepskyblue"
OUTLINE_WIDTH = 0.3

DEFAULT_SIZE = 7
DEFAULT_COLOURS = "blue"
DEFAULT_SHAPES = "diamond"

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
    analysis_network_path: pathlib.Path
    analysis_network_nodes_path: pathlib.Path
    od_demand_matrix_path: pathlib.Path
    zone_centroids_path: pathlib.Path
    range: float

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
            range_ = float(self.range)
        except ValueError:
            raise ValueError(
                "The range you provided in not a number, please re-enter the value. Cheers!"
            )

        LOG.info("Parsing Centroids")
        zone_centroids = gpd.read_file(self.zone_centroids_path)
        zone_centroids = check_and_format_centroids(
            zone_centroids, ZONE_CENTROIDS_REQUIRED_COLUMNS
        )

        LOG.info("Parsing network")
        network =gpd.read_file(self.analysis_network_path)
        network = check_and_format_analysis_network(network)

        network_nodes = gpd.read_file(self.analysis_network_nodes_path)
        network_nodes = check_and_format_analysis_network_nodes(network_nodes)

        LOG.info("Parsing OD demand matrix")
        demand_matrix = pd.read_csv(self.od_demand_matrix_path)
        demand_matrix = check_and_format_demand_matrix(demand_matrix)

        return ParsedAnalysisInputs(
            demand_marix=demand_matrix,
            network=network,
            network_nodes= network_nodes, 
            zone_centroids=zone_centroids,
            range=range_,
        )


@dataclasses.dataclass
class ODMatrixInputs:
    "the input class for OD matrices"
    od_matrices_path: dict[str, pathlib.Path]

    def parse(self, keys: list[str]) -> dict[str, pd.DataFrame]:
        """parses OD matrices

        Parameters
        ----------
        keys : list[str]
            keys that define the vehicle types of the inputted OD matrices

        Returns
        -------
        dict[str, pd.DataFrame]
            parsed OD matrices

        Raises
        ------
        ValueError
            if number of vehicle keys does not match the number of matrices
        """
        if len(self.od_matrices_path.keys()) != len(keys):
            raise ValueError("OD matrix paths and keys must be the same length")
        od_matrices = {}
        lower_keys = [x.lower() for x in keys]
        for key, path in self.od_matrices_path.items():
            if key.lower() not in lower_keys:
                raise KeyError("Keys for matrices do not match vehicle keys")
            key_index = lower_keys.index(key.lower())
            matrix = pd.read_csv(path)
            od_matrices[keys[key_index]] = check_and_format_demand_matrix(matrix)
        return od_matrices


@dataclasses.dataclass
class ThirstyPointsInputs:
    "input class for thirsty points"
    thirsty_points_paths: dict[str, pathlib.Path]

    def parse(self, keys: list[str]) -> dict[str, gpd.GeoDataFrame]:
        """parses thirsty points

        Parameters
        ----------
        keys : list[str]
            keys that define the vehicle types of the inputted thirsty points

        Returns
        -------
        dict[str, pd.DataFrame]
            parsed OD matrices

        Raises
        ------
        ValueError
            if number of vehicle keys does not match the number of thirsty points
        """
        if len(self.thirsty_points_paths) != len(keys):
            raise ValueError("thirsty point paths and keys must be the same length")
        thirsty_points = {}
        lower_keys = [x.lower() for x in keys]
        for key, path in self.thirsty_points_paths.items():
            if key.lower() not in lower_keys:
                raise KeyError("Keys for thirsty points do not match vehicle keys")
            key_index = lower_keys.index(key.lower())
            points = pd.read_csv(path)
            check_columns(path, points.columns, THRISTY_POINTS_REQUIRED_COLUMNS)
            thirsty_points[keys[key_index]] = gpd.GeoDataFrame(
                points,
                geometry=gpd.points_from_xy(
                    points["easting"], points["northing"], crs=CRS
                ),
            ).drop(columns=["easting", "northing"])
        return thirsty_points


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
    map_labels_path: pathlib.Path
    plotting_points: list[dict[str, str]]

    def parse_plotting_inputs(self, operational: Operational) -> ParsedPlottingInputs:
        """Parses Plotting inputs

        Returns
        -------
        ParsedPlottingInputs
            parsed plotting inputs from config file
        """
        LOG.info("Parsing road network")

        if self.network_path.is_dir():
            roads = read_in_network_folder(
                self.network_path,
                operational.output_folder,
            )
        else:
            roads = read_shape_file(
                self.network_path,
                required_columns=ROADS_REQUIRED_COLUMNS,
            )
            roads = format_roads(roads)

        if len(roads) == 0:
            LOG.warning(
                "filtering by road class yeilded no roads."
                f" Please ensure your roads file's 'class' column contains '{MOTORWAY_LABEL}' "
                f"and (if applicable) '{A_ROAD_LABEL}' values. This is the same format as the "
                "data provided on the OS datahub website."
            )

        LOG.info("Parsing motorway junctions")

        if self.motorway_junction_path.is_dir():
            junctions = read_in_junction_folder(
                self.motorway_junction_path,
                operational.output_folder,
            )

        else:
            junctions = read_shape_file(
                self.motorway_junction_path,
                required_columns=JUNCTION_REQUIRED_COLUMNS,
            )

        outlines = read_shape_file(self.outlines_path, precision=GEOSPATIAL_PRECISION)
        # some remove any multilinestringgs
        outlines = outlines.explode()

        map_labels = read_shape_file(
            self.map_labels_path,
            required_columns=MAP_LABELS_REQUIRED_COLUMNS,
        )

        # parse plotting points
        parsed_plotting_points = []
        for row in self.plotting_points:
            check_columns("plotting points", row.keys(), PLOTTING_POINTS_REQUIRED_KEYS)
            row["points"] = read_shape_file(
                row["data_path"], [row["hover_column_name"], "geometry"]
            )
            parsed_plotting_points.append(row)

        return ParsedPlottingInputs(
            roads=roads,
            junctions=junctions,
            outlines=outlines,
            map_labels=map_labels,
            plotting_points=parsed_plotting_points,
        )

    def create_input_summary(self) -> None:
        """creates an input summary for the plotting inputs
        Returns
        -------
        str
            output summary
        """
        output = "\nPlotting Inputs\n"
        output += f"Road Network Input - {self.network_path}\n"
        output += f"Motorway Junctions Input - {self.motorway_junction_path}\n"
        output += f"Outlines Input - {self.outlines_path}\n"
        output += f"Map Labels Input - {self.map_labels_path}\n"
        plotting_points_output = "Plotting Points Input\n"
        for input in self.plotting_points:
            plotting_points_output += f"    Label - {input['label']}\n"
            plotting_points_output += f"    Data - {input['data_path']}\n"
            plotting_points_output += f"    Hover data - {input['hover_column_name']}\n"
            plotting_points_output += f"    Point Size - {input['size']}\n"
            plotting_points_output += f"    Point Shape - {input['shape']}\n"
            plotting_points_output += f"    Point Colour - {input['colour']}\n"
            plotting_points_output += "\n"
        output += plotting_points_output
        return output


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
    map_labels: gpd.GeoDataFrame
    plotting_points: list[dict]


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
    network: gpd.GeoDataFrame
    network_nodes: gpd.GeoDataFrame
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
    show_plots: bool
    hex_bin_width: float

    def create_input_summary(self) -> str:
        """Creates an summary output of the operational input

        Returns
        -------
        str
            output summary
        """
        output = "\nOperational Inputs\n"
        output += f"Output Folder - {self.output_folder}\n"
        output += f"Approx Hexbin Width = {self.hex_bin_width:.3e} metres\n"
        return output


class ThirstyVehicleConfig(caf.toolkit.BaseConfig):
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


def check_and_format_centroids(
    zone_centroids: gpd.GeoDataFrame, required_columns
) -> gpd.GeoDataFrame:
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
    # check columns
    check_columns("zone_centroids", zone_centroids.columns, required_columns)
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
    return zone_centroids.loc[:, required_columns]


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

def check_and_format_analysis_network(analysis_network:gpd.GeoDataFrame)->gpd.GeoDataFrame:
    #TODO(KF) Docstring
    analysis_network.columns = analysis_network.columns.str.lower()
    check_columns("Analysis Network", analysis_network.columns,ANALYSIS_NETWORK_REQUIRED_COLUMNS)
    return analysis_network

def check_and_format_analysis_network_nodes(network_nodes: gpd.GeoDataFrame)->gpd.GeoDataFrame:
    #TODO(KF) Docstring
    network_nodes.columns = network_nodes.columns.str.lower()
    check_columns("Analysis Network", network_nodes.columns,ANALYSIS_NETWORK_NODES_REQUIRED_COLUMNS)
    return network_nodes

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
        file to read
    required_columns : Optional[list[str]], optional
        columns to check are in file if None give check is not done, by default None
    precision : Optional[float], optional
        precision to use when simplifying, if not give simply is not performed, by default None

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
    roads = format_roads(roads)

    roads_file = output_file / "aggregated_filtered_road_network"
    roads_file.mkdir(exist_ok=True)
    to_shape_file(roads_file / "aggregated_filtered_road_network.shp", roads)
    return roads


def format_roads(roads: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
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
    motorway = roads["class"] == MOTORWAY_LABEL
    a_road = roads["class"] == A_ROAD_LABEL
    keep = (pd.DataFrame([motorway, a_road]).transpose()).any(axis=1)
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


@output_file_checks
def write_to_csv(file_path: pathlib.Path, output: pd.DataFrame) -> None:
    """wirtes file to csv

    used so wrapper with logging and permission error checks can be applied

    Parameters
    ----------
    file_path : pathlib.Path
        path to write csv to
    output : pd.DataFrame
        data to write
    """
    output.to_csv(file_path)


@output_file_checks
def write_txt(file_path: pathlib.Path, output: str) -> None:
    """Writes output to a txt file

    Parameters
    ----------
    file_path : pathlib.Path
        file path
    output : str
        output txt
    """
    file = open(file_path, "w")
    file.write(output)
    file.close()


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
    relative_count: np.ndarray
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
            count=count,
            relative_count=relative_count,
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
