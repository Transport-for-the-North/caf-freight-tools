"""
creates OD lines between each OD pair
"""
# standard imports
import pathlib

# third party imports
import geopandas as gpd
import pandas as pd
from shapely import geometry
import numpy as np
from tqdm import tqdm

# local imports
from thirsty_vehicle_tool import input_output_constants, tv_logging

# constants
LOG = tv_logging.get_logger(__name__)


def get_thirsty_points(
    data_inputs: input_output_constants.ParsedAnalysisInputs,
    output_folder: pathlib.Path,
    file_name: str = "thirsty_points",
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
    od_lines = create_od_lines(
        od_matrix, data_inputs.zone_centroids, data_inputs.range, logging_tag
    )

    # replace od lines geometry with a list points along line in steps of given range
    LOG.info(f"{logging_tag}: Creating thirsty points")
    tqdm.pandas(desc=f"{logging_tag} thirsty points")
    od_lines["point_geometry"] = od_lines["geometry"].progress_apply(
        drop_points, step=data_inputs.range
    )

    # expand the lists, gives each item in list its own row and dupilcate other columns
    thirsty_points = od_lines.explode(column="point_geometry", index_parts=False)
    thirsty_points.reset_index(drop=True, inplace=True)

    # tidy up columns and set new geometry
    thirsty_points.drop(columns="geometry", inplace=True)
    thirsty_points.rename(columns={"point_geometry": "geometry"}, inplace=True)
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
    range_: float
        range of vehicle (used to filter out trips short than this)
    logging_tag: str
        tag to indentify which process has called function

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
    od_geom_matrix["distance"] = o_points.distance(d_points)

    #    filter and calculate some high level stats

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
        / 1000
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
    line_end_points = filtered_od_geom_matrix.loc[
        :, ["geometry_origin", "geometry_destination"]
    ]
    # Create OD lines, format & tidy up
    LOG.info(f"{logging_tag}: Creating OD lines")

    filtered_od_geom_matrix["geometry"] = od_lines(line_end_points, logging_tag)

    filtered_od_geom_matrix.drop(
        columns=["geometry_origin", "geometry_destination", "distance"], inplace=True
    )
    filtered_od_geom_matrix = gpd.GeoDataFrame(
        filtered_od_geom_matrix, geometry="geometry"
    )
    LOG.debug("OD linestrings created")

    return filtered_od_geom_matrix


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
