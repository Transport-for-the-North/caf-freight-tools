"""
creates OD lines between each OD pair
"""
# standard imports
import pathlib
from typing import Optional
import glob

# third party imports
import geopandas as gpd
import pandas as pd
from shapely import geometry, ops
import numpy as np
from tqdm import tqdm
import networkx as nx
import multiprocessing

# local imports
from thirsty_vehicle_tool import input_output_constants, tv_logging

# constants
LOG = tv_logging.get_logger(__name__)
CHUNK_SIZE = 20000
M_TO_KM = 1000
OD_LINE_FILE_EXT = ".shp"
ORIGIN_COLUMN = "origin"
DESTINATION_COLUMN = "destinatio"


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
    # remove intrazonal trips, we assume vehicle will have enough range to perform these
    od_matrix = remove_intrazonal_trips(data_inputs.demand_marix)

    # create a linestring between each OD pair, with the trips as an atribute

    od_routes_dir = output_folder / "od_routes"
    od_routes_dir.mkdir(exist_ok=True)
    if data_inputs.od_lines is None:
        od_lines = create_od_lines(
            od_matrix,
            data_inputs.zone_centroids,
            data_inputs.range,
            logging_tag,
            data_inputs.network,
            data_inputs.network_nodes,
            od_routes_dir,
        )
    else:
        od_lines = glob.glob(str(data_inputs.od_lines / f"*{OD_LINE_FILE_EXT}"))
        if len(od_lines)==0:
            raise ValueError(f"The directory provided for OD lines: {od_lines}, does not contain any ({OD_LINE_FILE_EXT}) files")
    
    if isinstance(od_lines, gpd.GeoDataFrame):
        demand_od_lines = od_lines
        tqdm.pandas(desc=f"{logging_tag}: creating thirsty points")
        demand_od_lines["point_geometry"] = demand_od_lines["geometry"].progress_apply(
            drop_points, step=data_inputs.range
        )
        demand_od_lines.drop(columns="geometry", inplace=True)
        demand_od_lines.rename(columns={"point_geometry": "geometry"}, inplace=True)

    else:
        stacked_thirsty_points = []
        filtered_od_matrix = od_matrix.loc[od_matrix["trips"]!=0]

        for od_lines_file in tqdm(od_lines, desc = f"{logging_tag}: creating thirsty points"):
            path = gpd.read_file(od_lines_file)
            demand_path = path.merge(filtered_od_matrix, left_on = ["origin", "destinatio"], right_on=["origin", "destination"], how="left")
            if demand_path["trips"].isna().any():
                LOG.warning("missing demand")
            demand_path["point_geometry"] = demand_path["geometry"].apply(
                drop_points, step=data_inputs.range
            )
            demand_path.drop(columns="geometry", inplace=True)
            demand_path.rename(columns={"point_geometry": "geometry"}, inplace=True)
            stacked_thirsty_points.append(demand_path)
        demand_od_lines = pd.concat(stacked_thirsty_points, ignore_index=True)
            

    #create thirsty pointshe lists, gives each item in list its own row and dupilcate other columns

    thirsty_points = demand_od_lines.explode(column="geometry")

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
    od_trip_matrix: pd.DataFrame,
    centroids: gpd.GeoDataFrame,
    range_: float,
    logging_tag: str,
    network: Optional[gpd.GeoDataFrame] = None,
    network_nodes: Optional[gpd.GeoDataFrame] = None,
    output_path: Optional[pathlib.Path] = None,
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
    # create origin and destination point
    origin_points = (
        od_trip_matrix["origin"]
        .to_frame()
        .merge(centroids, left_on="origin", right_on="uniqueid", how="left")
        .drop(columns=["uniqueid"])
    )

    destination_points = (
        od_trip_matrix["destination"]
        .to_frame()
        .merge(centroids, left_on="destination", right_on="uniqueid", how="left")
        .drop(columns=["uniqueid"])
    )

    # recombine OD points and trips
    od_geom_matrix = origin_points.merge(
        destination_points,
        how="inner",
        left_index=True,
        right_index=True,
        suffixes=("_origin", "_destination"),
    )
    # check to determine if any points have been lost
    if len(od_geom_matrix) != len(od_trip_matrix):
        raise ValueError(
            "OD points have been lost when joining to "
            "centroids. This may be because centroids are "
            "missing from the zone centroids shapefile."
            "Please review both the OD trip matrix and "
            "centroid files before rerunning the tool."
        )

    od_geom_matrix = od_geom_matrix.merge(
        od_trip_matrix["trips"], left_index=True, right_index=True
    )

    LOG.info(f"{logging_tag}: OD points created")

    # create lines
    LOG.info(
        f"{logging_tag}: Removing O-D pairs with seperation < vehicle range and/or 0 trips"
    )

    # filter for < range

    #   calculate distance
    o_points = gpd.GeoDataFrame(
        od_geom_matrix["geometry_origin"], geometry="geometry_origin"
    )
    d_points = gpd.GeoDataFrame(
        od_geom_matrix["geometry_destination"], geometry="geometry_destination"
    )
    

    #    filter and calculate some high level stats
    """
    
    """
    # Create OD lines, format & tidy up
    LOG.info(f"{logging_tag}: Creating OD lines")

    if network is not None:
        #create graph
        network.loc[
            network["spdlimit"] == 0, "spdlimit"
        ] = input_output_constants.DEFAULT_SPEED_LIMIT

        network["link_time"] = network["distance"] / network["spdlimit"]
        
        network_graph = create_graph(network, network_nodes)

        network.set_index(["a", "b"], inplace=True)


        #od data 
        line_end_points_id = od_geom_matrix.loc[:, ["origin", "destination"]]
        # chunk end points
        chunked_end_points = chunk_dataframe(line_end_points_id, CHUNK_SIZE)

        for i, chunk in enumerate(chunked_end_points):
            
            LOG.info(f"{logging_tag}:- running shortest path for chunk {i+1} / {len(chunked_end_points)}")
            chunk["geometry"] = od_bendy_lines(
                chunk, network_graph, network.copy(), network_nodes.copy(), logging_tag
            )
            if output_path is not None:

                LOG.info(f"Writing OD routes chunk {i} to {output_path}")

                input_output_constants.to_shape_file(output_path / f"routes_{i+1}{OD_LINE_FILE_EXT}", chunk)
        return glob.glob(str(output_path/ f"*{OD_LINE_FILE_EXT}"))
    
    else:
        #filter demand matrix
        od_geom_matrix["distance"] = o_points.distance(d_points)
        filtered_od_geom_matrix = od_geom_matrix.loc[od_geom_matrix["distance"] > range_]
        filtered_od_geom_matrix = filtered_od_geom_matrix.loc[
            filtered_od_geom_matrix["trips"] > 0
        ]
        filtered_out = od_geom_matrix.loc[
            ~od_geom_matrix.index.isin(filtered_od_geom_matrix.index)
        ]
        filtered_out_od_pairs = len(filtered_out)
        filtered_out_trips = filtered_out["trips"].sum()
        filtered_trips = filtered_od_geom_matrix["trips"].sum()
        mean_length = (
            weighted_avg(
                filtered_od_geom_matrix["distance"], filtered_od_geom_matrix["trips"]
            )
            / M_TO_KM
        )
        #   output stats
        LOG.info(
            f"{logging_tag}: {filtered_out_od_pairs:.3e} OD pairs removed which contains "
            f"{filtered_out_trips:.3e} trips"
        )
        LOG.info(
            f"{logging_tag}: {len(filtered_od_geom_matrix):.3e} OD pairs remaining which contains "
            f"{filtered_trips:.3e} trips of average length: {mean_length:.0f}km"
        )
        line_end_points_geom = filtered_od_geom_matrix.loc[
            :, ["geometry_origin", "geometry_destination"]
        ]
        #create OD lines
        filtered_od_geom_matrix["geometry"] = od_lines(
            line_end_points_geom, logging_tag
        )

    
        filtered_od_geom_matrix.drop(
            columns=["geometry_origin", "geometry_destination", "distance"], inplace=True
        )
        filtered_od_geom_matrix = gpd.GeoDataFrame(
            filtered_od_geom_matrix, geometry="geometry"
        )
        LOG.debug("OD linestrings created")
            

        return filtered_od_geom_matrix

def create_graph(
    network: gpd.GeoDataFrame, network_nodes: gpd.GeoDataFrame
) -> nx.DiGraph:
    network_graph = nx.DiGraph()
    network_nodes.set_index("n", inplace=True)

    edges = [
        ((row["a"]), int(row["b"]), {"time": row["link_time"]})
        for _, row in network.iterrows()
    ]
    network_graph.add_edges_from(edges)

    # set node attributes

    nodes_geom = network_nodes["geometry"]

    nx.set_node_attributes(network_graph, nodes_geom, name="coords")

    return network_graph


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
    network_geom: gpd.GeoDataFrame,
    network_nodes: gpd.GeoDataFrame,
    logging_tag: str,
) -> list[geometry.LineString]:

    def calc_distance(a, b) -> float:
        return network_nodes.loc[a, "geometry"].distance(
            network_nodes.loc[b, "geometry"]
        )

    lines = []
    failed_count = 0
    for start, end in tqdm(
        line_end_points.values, desc=f"{logging_tag} OD bendy lines"
    ):
        #one_to_all_shortest_path = nx.single_source_dijkstra_path(network, start)

        #for end in line_end_points.loc[line_end_points["origin"]==start, "destination"]:
        #    try:
        #        shortest_path = one_to_all_shortest_path[end]
        #        shortest_path_links = zip(shortest_path[:-1], shortest_path[1:])
        #        
        #        shortest_path_geom = ops.linemerge(
        #            network_geom.loc[shortest_path_links, "geometry"].tolist()
        #        )
        #        lines.append(shortest_path_geom)
        #    except KeyError:
        #        LOG.warning(f"missing bendy links between {start} and {end} nodes")

        #    except Exception as e:
        #        LOG.warning(f"failed to create route, due to: {e}")

        try:
            shortest_path = nx.astar_path(
                network, start, end, heuristic=calc_distance, weight="link_time"
            )
            shortest_path_links = zip(shortest_path[:-1], shortest_path[1:])
            shortest_path_geom = ops.linemerge(
                network_geom.loc[shortest_path_links, "geometry"].tolist()
            )
            lines.append(shortest_path_geom)
        except Exception as e:
                LOG.warning(f"failed to create route, due to: {e}")
                failed_count +=1
    LOG.info(f"{failed_count} failed lines, {len(lines)} successfull lines")
    return lines


def od_bendy_lines_mp(
    line_end_points: pd.DataFrame,
    network: nx.Graph,
    network_geom: gpd.GeoDataFrame,
    network_nodes: gpd.GeoDataFrame,
    logging_tag: str,
) -> list[geometry.LineString]:
    network_geom.set_index(["a", "b"], inplace=True)

    # Split the line_end_points DataFrame into chunks for parallel processing
    num_processes = 500
    chunk_size = len(line_end_points) // num_processes
    chunks = [
        {
            "end_points": line_end_points[i : i + chunk_size],
            "network": network,
            "nodes": network_nodes,
            "geom": network_geom,
        }
        for i in range(0, len(line_end_points), chunk_size)
    ]

    # Create a multiprocessing pool
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-1)

    # Calculate shortest paths concurrently using multiprocessing
    lines = list(tqdm(pool.imap(
        parallel_process, chunks,),  desc=f"{logging_tag} OD bendy lines", total = num_processes))

    pool.close()
    pool.join()

    return lines


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