"""
creates OD lines between each OD pair
"""
# standard imports
import pathlib
import logging

# third party imports
import geopandas as gpd
import pandas as pd
from shapely import geometry
import numpy as np
from tqdm import tqdm

# local imports
from thirsty_vehicle import input_output_constants

# constants
LOG = logging.getLogger(__name__)


def get_thirsty_points(
    data_inputs: input_output_constants.ParsedAnalysisInputs,
    output_folder: pathlib.Path,
) -> gpd.GeoDataFrame:
    """finds the points at which the vehicle will run out of range

    this is done for each OD pair, the number of trips associated with the
    OD pair will be an attribute of the points

    Parameters
    ----------
    thirsty_truck_inputs : inputs.ParsedInputs
        inputs parsed from the config file

    Returns
    -------
    gpd.GeoDataFrame
        thirsty points
    """
    LOG.info("Finding thirsty points")
    # remove intrazonal trips, we assume vehicle will have enough range to perform these
    od_matrix = remove_intrazonal_trips(data_inputs.demand_marix)

    # create a linestring between each OD pair, with the trips as an atribute
    od_lines = create_od_lines(od_matrix, data_inputs.zone_centroids)

    # replace od lines geometry with a list points along line in steps of given range
    LOG.info("Creating thirsty points")
    tqdm.pandas()
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
    # change name to avoid truncated name warning
    output_thirsty_points = thirsty_points.rename(columns={"destination": "destin."})
    thirsty_point_folder = output_folder / "thirsty_points"
    thirsty_point_folder.mkdir(exist_ok=True)

    input_output_constants.to_shape_file(
        thirsty_point_folder / "thirsty_points.shp", output_thirsty_points
    )

    return thirsty_points


def remove_intrazonal_trips(od_trip_matrix: pd.DataFrame) -> pd.DataFrame:
    """removes intrazonal trips from the matrix

    removes entries that have the same origin and destination

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
    od_trip_matrix: pd.DataFrame, centroids: gpd.GeoDataFrame
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

    LOG.debug("OD points created")

    # create lines
    line_end_points = od_geom_matrix.loc[:, ["geometry_origin", "geometry_destination"]]
    line_geoms = []
    LOG.info("Creating OD lines")
    for origin_geom, desitination_geom in tqdm(line_end_points.values):
        line_geoms.append(geometry.LineString([origin_geom, desitination_geom]))
    od_geom_matrix["geometry"] = line_geoms

    od_geom_matrix.drop(
        columns=["geometry_origin", "geometry_destination"], inplace=True
    )
    od_geom_matrix = gpd.GeoDataFrame(od_geom_matrix, geometry="geometry")
    LOG.debug("OD linestrings created")
    return od_geom_matrix


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
