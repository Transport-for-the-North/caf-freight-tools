"""
creates OD lines between each OD pair
"""
# standard imports
import pathlib
from typing import Optional
import glob
import os
# third party imports
import geopandas as gpd
import pandas as pd
from shapely import geometry, ops
import numpy as np
from tqdm import tqdm
import networkx as nx
import concurrent.futures

# local imports
from thirsty_vehicle_tool import input_output_constants, tv_logging

# constants
LOG = tv_logging.get_logger(__name__)
CHUNK_SIZE = 4000
M_TO_KM = 1000
OD_LINE_FILE_EXT = ".h5"
ORIGIN_COLUMN = "o"
DESTINATION_COLUMN = "d"


def get_thirsty_points(
    data_inputs: input_output_constants.ParsedAnalysisInputs,
    output_folder: pathlib.Path,
    file_name: str = "thirsty_points.shp",
    logging_tag: str = "",
) -> gpd.GeoDataFrame:
    """finds the points at which the vehicle will run out of range

    this is done for each OD pair, the number of trips associated with the
    OD pair will be an attribute of the points

    Parameters
    ----------
    data_inputs : input_output_constants.ParsedAnalysisInputs
        data inputs for analysis
    output_folder : pathlib.Path
        path to folder to output thirsty points to
    file_name : str, optional
        file name of thirsty points file, by default "thirsty_points"
    logging_tag : str, optional
        tag to indetify which process the function has been called by, by default ""

    Returns
    -------
    gpd.GeoDataFrame
        thirsty points
    """
    LOG.info(f"{logging_tag}: Finding thirsty points")

    # remove intrazonal trips, these do not create od routes on the network
    od_matrix = remove_intrazonal_trips(data_inputs.demand_marix)

    # create a linestring between each OD pair, with the trips as an atribute

    od_routes_dir = output_folder / "od_routes"
    od_routes_dir.mkdir(exist_ok=True)

    #if od_lines haven't been given we need to create them
    if data_inputs.od_lines is None:
        od_pairs = od_matrix[["origin", "destination"]]
        od_lines = create_od_lines(
            od_pairs,
            logging_tag,
            data_inputs.network,
            data_inputs.network_nodes,
            od_routes_dir,
            True,
        )

    else:
        od_lines = glob.glob(str(data_inputs.od_lines / f"*{OD_LINE_FILE_EXT}"))
        if len(od_lines)==0:
            raise ValueError(f"The directory provided for OD lines: {od_lines}, does not contain any ({OD_LINE_FILE_EXT}) files")
    
    #get thirsty points
    #remove od pairs that don't contribute to demand
    filtered_od_matrix = od_matrix.loc[od_matrix["trips"]!=0]
    thirsty_points = create_thirsty_points_in_parallel(od_lines, filtered_od_matrix, data_inputs.network, data_inputs.range, logging_tag)
            

    

    thirsty_points.reset_index(drop=True, inplace=True)
    # tidy up columns and set new geometry

    thirsty_points = gpd.GeoDataFrame(thirsty_points, geometry="geometry")
    thirsty_points.crs = input_output_constants.CRS

    # write thristy points to file
    # write to csv to prevent file too big errors
    output_thirsty_points = pd.DataFrame(thirsty_points.copy())
    output_thirsty_points["easting"] = gpd.GeoSeries(
        output_thirsty_points["geometry"]
    ).x
    output_thirsty_points["northing"] = gpd.GeoSeries(
        output_thirsty_points["geometry"]
    ).y
    output_thirsty_points.drop(columns=["geometry"])

    input_output_constants.write_to_csv(
        output_folder / file_name, output_thirsty_points
    )

    return thirsty_points

def create_thirsty_points(od_lines_file: list[str], filtered_od_matrix:pd.DataFrame, network:gpd.GeoDataFrame, range_:float, logging_tag:str):
    
    try:
        
        path = pd.read_hdf(od_lines_file).reset_index()

        
        path_geo = path.merge(network, how="left", on=["a", "b"])
        path_geo = path_geo.loc[:, ["o", "d", "a", "b", "geometry"]]



        shortest_path_temp = path_geo.groupby(["o", "d"])["geometry"].apply(ops.linemerge)
        shortest_path = shortest_path_temp.to_frame().reset_index()



        demand_path = shortest_path.merge(filtered_od_matrix, left_on=["o", "d"], right_on=["origin", "destination"], how="left")

        if demand_path["trips"].isna().any():
            LOG.warning(f"{len(demand_path[demand_path["trips"].isna()])} od pairs with missing demand")

            demand_path.loc["trips"].fillna(0, inplace=True)
        

        demand_path["point_geometry"] = demand_path["geometry"].apply(drop_points, step=range_)


        demand_path.drop(columns="geometry", inplace=True)
        demand_path.rename(columns={"point_geometry": "geometry"}, inplace=True)

        return demand_path
    except Exception as e:
        LOG.warning(f"Unable to create thirsty points for file {od_lines_file}: {str(e)}")
        return None

def create_thirsty_points_in_parallel(od_lines, filtered_od_matrix, network:gpd.GeoDataFrame, range_:float, key):
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count() - 2) as executor:
        futures = []

        for i, od_lines_file in enumerate(od_lines):
            future = executor.submit(create_thirsty_points, od_lines_file, filtered_od_matrix, network, range_, f"{key}: chunk {i+1}:")
            futures.append(future)

        results = [future.result() for future in tqdm(concurrent.futures.as_completed(futures), total = len(futures), desc = f"{key} thirsty_points")]

    # Concatenate valid results, ignoring None values
    stacked_thirsty_points = [result for result in results if result is not None]
    unstacked = pd.concat(stacked_thirsty_points, ignore_index=True)

    #explode thirsty points lists, gives each item in list its own row and dupilcate other columns
    thirsty_points = unstacked.explode(column="geometry")

    return thirsty_points

def remove_intrazonal_trips(od_trip_matrix: pd.DataFrame) -> pd.DataFrame:
    """removes intrazonal trips from the matrix

    removes entries that have the same origin and destination

    Parameters
    ----------
    od_trip_matrix : pd.DataFrame
        trip matrix

    Returns
    -------
    pd.DataFrame
        matrix with intrazonal trips removed
    """
    filtered_od_trip_matrix = od_trip_matrix.loc[
        ~(od_trip_matrix["origin"] == od_trip_matrix["destination"])
    ]
    filtered_od_trip_matrix.reset_index(drop=True, inplace=True)
    return filtered_od_trip_matrix


def create_od_lines(
    od_pairs: pd.DataFrame,
    logging_tag: str,
    network: gpd.GeoDataFrame,
    network_nodes: gpd.GeoDataFrame,
    output_path: pathlib.Path,
    skip_existing_files: bool = False, 
) -> gpd.GeoDataFrame:
    """creates linestring for each OD pair

    create a straight line between each OD pair,
    other attributes are origin, destination and trips

    Parameters
    ----------
    od_trip_matrix : pd.DataFrame
        demand matrix for which to create the OD line
    centroids : gpd.GeoDataFrame
        centroids for the corresponding zone system for the OD matrix
    network : gpd.GeoDataFrame

    range_: float
        range of vehicle (used to filter out trips short than this)
    logging_tag: str
        tag to indentify which process has called function
    network: Optional[gpd.GeoDataFrame] default None
        network to snap bendy routes to. if None, straightline process will be used

    Returns
    -------
    gpd.GeoDataFrame
        OD line strings

    Raises
    ------
    ValueError
        if the original od_trip_matrix is different to od_trip_matrix after
        joining ODs to the centroid based on IDs. this implies there is an issue
        with either the IDs in the od_trip_matrix or in the centroids.
    """
    # TODO KF add nodes to docstring and add checks for nodes

    # Create OD lines, format & tidy up
    LOG.info(f"{logging_tag}: Creating OD lines")

    #create graph
    od_pairs = remove_intrazonal_trips(od_pairs)
    #deal with undefined speed limits
    network.fillna(0, inplace=True)
    network.loc[
        network["spdlimit"] == 0, "spdlimit"
    ] = input_output_constants.DEFAULT_SPEED_LIMIT

    network.loc[
        network["distance"] == 0, "distance"
    ] = network.loc[network["distance"] == 0, "geometry"].length

    network["link_time"] = network["distance"].astype(float) / network["spdlimit"].astype(float)
    
    network_graph = create_graph(network, network_nodes)

    network.set_index(["a", "b"], inplace=True)

    #od data

    link_length_lookup = network["distance"].reset_index()
    link_length_lookup.rename(columns={"distance":"link_length"}, inplace=True)


    # chunk end points
    chunked_end_points = chunk_dataframe(od_pairs, CHUNK_SIZE)
    existing_outputs = glob.glob(str(output_path / f"*{OD_LINE_FILE_EXT}"))
    existing_outputs = [pathlib.Path(path).name for path in existing_outputs]

    create_od_lines_in_parallel(
        chunked_end_points,
        existing_outputs,
        skip_existing_files,
        output_path,
        network_graph,
        link_length_lookup,
        network_nodes,
        logging_tag
    )
    
    #for chunk in chunked_end_points:
    #    od_bendy_lines(chunk, network_graph, link_length_lookup, network_nodes.set_index("n"), logging_tag)

    #returns list of intermediary files
    return glob.glob(str(output_path/ f"*{OD_LINE_FILE_EXT}"))

def create_graph(
    network: gpd.GeoDataFrame, network_nodes: gpd.GeoDataFrame
) -> nx.DiGraph:
    network_graph = nx.DiGraph()

    #filtered_network_nodes = network_nodes.loc[network_nodes["n"].drop_duplicates().index]

    #if len(filtered_network_nodes) != len(network_nodes):
    #    LOG.warning("duplicate nodes found in network")

    filtered_nodes = network_nodes.drop_duplicates("n")

    if len(filtered_nodes)!=len(network_nodes):
        LOG.warning("Duplicate nodes IDs detected, this could indicate issues with network input!")

    filtered_nodes.set_index("n", inplace=True)

    filtered_network = network.loc[network["a"]!=network["b"]]

    if len(filtered_network)!=len(network):
        LOG.warning("Links removed from analysis network as A and B node had the same ID")

    edges = [
        ((row["a"]), int(row["b"]), {"link_time": row["link_time"]})
        for _, row in filtered_network.iterrows()
    ]
    network_graph.add_edges_from(edges)

    # set node attributes

    nodes_geom = filtered_nodes["geometry"]

    nx.set_node_attributes(network_graph, nodes_geom, name="coords")

    return network_graph

def create_od_lines_in_parallel(chunked_end_points, existing_outputs, skip_existing_files, output_path, network_graph, link_length_lookup, network_nodes, logging_tag):
    try:
        network_nodes.set_index("n", inplace=True)

    except IndexError:
        LOG.debug("Node number already set as index")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count() - 2) as executor:
        futures = []

        for i, chunk in enumerate(chunked_end_points):
            output_filename = output_path / f"routes_{i+1}{OD_LINE_FILE_EXT}"
            future = executor.submit(calculate_routes, i, chunk, existing_outputs, skip_existing_files, output_filename, network_graph, link_length_lookup, network_nodes, logging_tag)
            futures.append(future)

        for i, future in tqdm(enumerate(concurrent.futures.as_completed(futures)), total = len(futures), desc = f"{logging_tag} OD bend lines"):
            result = future.result()
            if result is not None:
                LOG.info(f"Processing complete for chunk {i+1}")
                
            

def calculate_routes(i, chunk, existing_outputs, skip_existing_files, output_path, network_graph, link_length_lookup, network_nodes, logging_tag):
    

    if output_path.name in existing_outputs and skip_existing_files:
        return None

    chunk_routes = od_bendy_lines(chunk, network_graph, link_length_lookup, network_nodes.copy(), logging_tag)

    input_output_constants.overwrite_h5(output_path, chunk_routes, "routes")

    return output_path


def drop_points(line: geometry.LineString, step: float) -> list[geometry.Point]:
    """creates a set of points at steps along a line string

    creates points begginging at step from origin and continues till
    destination is reached

    Parameters
    ----------
    line : shapely.LineString
        line string to create points along
    step : float
        step at for points

    Returns
    -------
    list[shapely.Point]
        points along line at intervals of step
    """
    distances = np.arange(step, line.length, step)
    return [line.interpolate(distance) for distance in distances]


def od_lines(
    line_end_points: pd.DataFrame, logging_tag: str
) -> list[geometry.LineString]:
    """creates linestrings between the end points

    _extended_summary_

    Parameters
    ----------
    line_end_points : pd.DataFrame
        2 x n df containing start and end points of OD lines,
        must have start point in 1st column and end point in 2nd column

    logging_tag : str
        logging tag to identify the process that called the function

    Returns
    -------
    list[geometry.LineString]
        list of resultant linestrings
    """
    lines = []
    for start, end in tqdm(line_end_points.values, desc=f"{logging_tag} OD lines"):
        lines.append(geometry.LineString([start, end]))
    return lines


def od_bendy_lines(
    line_end_points: pd.DataFrame,
    network: nx.Graph,
    link_length_lookup: gpd.GeoDataFrame,
    network_nodes: gpd.GeoDataFrame,
    logging_tag: str,
) -> pd.DataFrame:

    def calc_distance(a, b) -> float:
        return network_nodes.at[a, "geometry"].distance(
            network_nodes.at[b, "geometry"]
        )

    lines = []
    failed_count = 0
    for start, end  in line_end_points.values:

        try:
            shortest_path = nx.astar_path(
                network, start, end, heuristic=calc_distance, weight="link_time"
            )

            route = pd.DataFrame([shortest_path[:-1], shortest_path[1:]], index = ["a","b"]).transpose()
            route = route.merge(link_length_lookup, how = "left", on = ["a", "b"])
            route["o"] = start
            route["d"] = end
            route.set_index(["o", "d", "a", "b"], inplace = True)
            lines.append(route)
        except Exception as e:
                LOG.warning(f"failed to create route, due to: {e}")
                failed_count +=1
    LOG.info(f"{failed_count} failed lines, {len(lines)} successfull lines")
    return pd.concat(lines)
    


def calculate_shortest_path(end_points, network, network_nodes, network_geom):
    def calc_distance(a, b) -> float:
        return network_nodes.loc[a, "geometry"].distance(
            network_nodes.loc[b, "geometry"]
        )
    shortest_path_geom = []
    for start, end in end_points.values:
        shortest_path = nx.astar_path(
            network, start, end, heuristic=calc_distance, weight="link_time"
        )
        shortest_path_links = zip(shortest_path[:-1], shortest_path[1:])
        shortest_path_geom.append(ops.linemerge(
            network_geom.loc[shortest_path_links, "geometry"].tolist()
        ))
    return shortest_path_geom


# Define a function for parallel processing
def parallel_process(args):
    end_points = args["end_points"]
    network = args["network"]
    nodes = args["nodes"]
    geom = args["geom"]
    return calculate_shortest_path(end_points, network, nodes, geom)


def weighted_avg(values: pd.Series, weights: pd.Series) -> float:
    """calculates weighted mean

    Parameters
    ----------
    values : pd.Series
        values for mean
    weights : pd.Series
        weights for mean

    Returns
    -------
    float
        weighted mean
    """
    return (values * weights).sum() / weights.sum()


def chunk_dataframe(df, chunk_size):
    """
    Chunk a DataFrame into a list of smaller DataFrames.

    Parameters:
    - df: pandas DataFrame
        The DataFrame to be chunked.
    - chunk_size: int
        The desired length of each chunk.

    Returns:
    - List of pandas DataFrames
        A list containing smaller DataFrames of length `chunk_size`.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame.")

    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("Chunk size must be a positive integer.")

    num_rows = len(df)
    num_chunks = (num_rows + chunk_size - 1) // chunk_size  # Calculate the number of chunks

    chunks = [df.iloc[i * chunk_size: (i + 1) * chunk_size] for i in range(num_chunks)]

    return chunks