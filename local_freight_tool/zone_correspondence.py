"""
Created on: Thurs Jan 28 2021

Original author: CaraLynch

File purpose:
Nest two shapefiles to produce adjustment factors from one zone to another.
"""

import geopandas as gpd
import pandas as pd

def read_zone_shapefiles(zone_1_path, zone_2_path, zone_1_name, zone_2_name):
    """Reads in zone system shapefiles, sets zone id and area column names,
    sets to same crs.

    
    Parameters
    ----------
    zone_1_path : str
        Path to first zone system shapefile
    zone_2_path : str
        Path to second zone system shapefile
    zone_1_name : str
        Name of first zone system
    zone_2_name : str
        Name of second zone system

    Returns
    -------
    List[GeoDataFrame, GeoDataFrame], List[str, str]
        List of zone 1 and zone 2 GeoDataFrames and a list with the names of 
        the zones.
    """
    # zone column lookups
    gbfm_lookup = {'ID': 'zone_id'}
    noham_lookup = {
        'zone_id': 'empty',
        'unique_id': 'zone_id'
        }
    
    # create geodataframes from zone shapefiles
    zone_1 = gpd.read_file(zone_1_path)
    zone_2 = gpd.read_file(zone_2_path)

    # create lists to deal with zones and names
    zone_list = [zone_1, zone_2]
    zone_names = [zone_1_name, zone_2_name]


    # rename zone number columns, add area column, complete crs data
    for i in range(2):
        
        if 'ID' in zone_list[i].columns:
            # this uses GBFM zone ID column name
            zone_list[i] = zone_list[i].rename(columns=gbfm_lookup)
        elif 'unique_id' in zone_list[i].columns:
            # this uses NoHAM zone ID column name
            zone_list[i] = zone_list[i].rename(columns=noham_lookup)
        else:
            print('no lookup for this zone system, need to know column names')
        
        zone_list[i] = zone_list[i].rename(
            columns = {'zone_id': f'{zone_names[i]}_zone_id'}
        )
        zone_list[i][f'{zone_names[i]}_area'] = zone_list[i].area

        # set gbfm crs data to same as noham crs data (they should be the
        # same but gbfm data is incomplete)
        # TODO might change this to just set all to this crs by default
        if not zone_list[i].crs:
            zone_list[i].crs = 'EPSG:27700'
    
    return zone_list, zone_names

def spatial_zone_correspondence(zone_list, zone_names, outpath):
    """Finds the spatial zone corrrespondence through calculating adjustment
    factors with areas only.

    Parameters
    ----------
    zone_list : List[GeoDataFrame, GeoDataFrame]
        List of zone 1 and zone 2 GeoDataFrames.
    zone_names : List[str, str]
        List of zone names.
    outpath : str, optional
        Path to output directory, by default ''

    Returns
    -------
    GeoDataFrame
        GeoDataFrame with 4 columns: zone 1 IDs, zone 2 IDs, zone 1 to zone 2
        adjustment factor and zone 2 to zone 1 adjustment factor.
    """

    # create geodataframe for intersection of zones
    zone_overlay = gpd.overlay(zone_list[0], zone_list[1], how='intersection').reset_index()
    zone_overlay['intersection_area'] = zone_overlay.area

    # create geodataframe with spatial adjusted factors
    spatial_correspondence = zone_overlay[[f'{zone_names[0]}_zone_id',
                                f'{zone_names[1]}_zone_id']]
    spatial_correspondence[f'{zone_names[0]}_to_{zone_names[1]}'] = (zone_overlay['intersection_area'] /
                                                                        zone_overlay[f'{zone_names[0]}_area'])
    spatial_correspondence[f'{zone_names[1]}_to_{zone_names[0]}'] = (zone_overlay['intersection_area'] /
                                                                        zone_overlay[f'{zone_names[1]}_area'])

    spatial_correspondence.to_csv(f'{outpath}/spatial_zone_correspondence.csv', index=False)

    return spatial_correspondence

def find_slithers(spatial_correspondence, zone_names, tolerance):
    """Finds overlap areas between zones which are very small slithers,
    filters them out of the spatial zone correspondence GeoDataFrame,
    and returns the filtered zone correspondence as well as the 
    GeoDataFrame with only the slithers.

    Parameters
    ----------
    spatial_correspondence : GeoDataFrame
        Spatial zone correspondence between zone 1 and zone 2 produced with 
        spatial_zone_correspondence.
    zone_names: List[str, str]
        List of the zone names that the spatial correspondence was performed
        between.
    tolerance : float
        User-defined tolerance for filtering out slithers, must be a float
        between 0 and 1, recommended value is 0.98.

    Returns
    -------
    GeoDataFrame, GeoDataFrame
        slithers GeoDataFrame with all the small zone overlaps, and
        no_slithers the zone correspondence GeoDataFrame with these zones
        filtered out.
    """
    slither_filter = ((spatial_correspondence[
                    f'{zone_names[0]}_to_{zone_names[1]}'] < (1-tolerance)) &
                    (spatial_correspondence[
                    f'{zone_names[1]}_to_{zone_names[0]}'] < (1-tolerance)))
    slithers = spatial_correspondence[slither_filter]
    no_slithers = spatial_correspondence[~slither_filter]

    return slithers, no_slithers


def point_zone_handling(spatial_correspondence_no_slithers, point_tolerance, 
                        zone_list, zone_names, lsoa_shapefile_path, 
                        lsoa_data_path):
    """Special method for handling zone correspondence non-spatially for point
    zones. This will only be done for the zone 1 to zone 2 correspondence.

    Parameters
    ----------
    spatial_correspondence_no_slithers : GeoDataFrame
        Spatial zone correspondence between zone systems 1 and 2, produced
        with spatial_zone_correspondence with the small overlaps filtered
        out using find_slithers.
    point_tolerance : float
        Tolerance level for filtering out point zones, a number between 0
        and 1.
    zone_list : List[GeoDataFrame, GeoDataFrame]
        List containing zone 1 and zone 2 GeoDataFrames.
    zone_names : List[str, str]
        List containing zone 1 and zone 2 names.
    lsoa_shapefile_path : str
        Path to LSOA shapefile (or the shapefile associated with the data to
        be used in point zone handling). Zone ID column must be called
        LSOA11CD.
    lsoa_data_path : str
        Path to csv file containing LSOA ID column as lsoa11cd and desired
        data in var column.
    """

    # read in and combine LSOA data
    lsoa_zones = gpd.read_file(lsoa_shapefile_path)
    lsoa_data = gpd.read_file(lsoa_data_path)
    lsoa_data = lsoa_data.rename(columns={'lsoa11cd': 'LSOA11CD'})
    lsoa_data = lsoa_data[['LSOA11CD', 'var']]
    lsoa_data['var'] = lsoa_data['var'].astype(float)
    lsoa_zones_var = lsoa_zones.merge(lsoa_data, how='inner', 
                    left_on='LSOA11CD', right_on='LSOA11CD')

    # find point zones
    zone_2_point_zone_filter = ((spatial_correspondence_no_slithers[
        f'{zone_names[1]}_to_{zone_names[0]}'] > point_tolerance)
        & (spatial_correspondence_no_slithers[
        f'{zone_names[0]}_to_{zone_names[1]}'] < (1 - point_tolerance)))
        
    zone_2_point_zones = spatial_correspondence_no_slithers[zone_2_point_zone_filter]

    # find all zones in zone 2 that share an original zone 1 with a point zone
    zone_2_point_zone_sharing_filter = (
        spatial_correspondence_no_slithers[f'{zone_names[0]}_zone_id'].isin(
        zone_2_point_zones[f'{zone_names[0]}_zone_id']))

    zone_2_point_zone_sharing = spatial_correspondence_no_slithers.loc[
                                zone_2_point_zone_sharing_filter]

    

def zone_correspondence(zone_1_path, zone_2_path, outpath='', 
                        zone_1_name='gbfm', zone_2_name='noham', 
                        tolerance=0.98, point_tolerance=0.95,
                        point_zone_handling=False, lsoa_shapefile_path='',
                        lsoa_data_path='', rounding=True):
    """Perform zone correspondence from zone system 1 to zone system 2.

    Parameters
    ----------
    zone_1_path : str
    Path to first zone system shapefile
    zone_2_path : str
        Path to second zone system shapefile
    outpath : str, optional
        Path to output directory, by default ''
    zone_1_name : str
        Name of first zone system, by default 'gbfm'
    zone_2_name : str
        Name of second zone system, by default 'noham'
    tolerance : float, optional
        Tolerance for filtering out slithers, by default 0.98
    point_tolerance : float, optional
        Tolerance for finding point zones, by default 0.95
    point_zone_handling : bool, optional
        Whether to handle point zones differently or not, by default False
    lsoa_shapefile_path : str, optional
        Path to LSOA shapefile, by default ''
    lsoa_data_path : str, optional
        Path to LSOA data, by default ''
    rounding : bool, optional
        Whether rounding is on or off, by default True

    Returns
    -------
    pd.DataFrame
        DataFrame with 3 columns, zone 1 id, zone 2 id and
        zone 1 to zone 2 adjustment factor.
    """
    # read in shapefiles
    zone_list, zone_names = read_zone_shapefiles(zone_1_path, zone_2_path, 
                                                zone_1_name, zone_2_name)
    # get spatial zone correspondence
    zone_correspondence = spatial_zone_correspondence(zone_list,
                                                        zone_names, outpath)

    # filter out slithers
    zone_correspondence_slithers, zone_correspondence_no_slithers = find_slithers(
        zone_correspondence, zone_names, tolerance)

    # special non-spatial handling for point zones
    if point_zone_handling:
        zone_correspondence_no_slithers = point_zone_handling(
                                        zone_correspondence_no_slithers,
                                        point_tolerance, 
                                        zone_list, zone_names,
                                        lsoa_shapefile_path, 
                                        lsoa_data_path)
        
    
    # rounding to ensure no demand is lost
    if rounding:
        zone_correspondence = round_zone_correspondence(
            zone_correspondence_slithers, zone_correspondence_no_slithers)
    else:
        zone_correspondence = pd.concat([zone_correspondence_slithers,
                                        zone_correspondence_no_slithers]).sort_index()
    return zone_correspondence

if __name__ == '__main__':
    gbfm_path = 'C:/WSP_projects/Freight/zone_shapefiles/GBFM/Zones.shp'
    noham_path = 'C:/WSP_projects/Freight/zone_shapefiles/NoHAM/noham_zones_freeze_2.10.shp'
    output_dir = 'C:/WSP_projects/Freight/local_freight_tool/Outputs/Zone correspondence test'
    spatial_correspondence, zone_list, zone_names = spatial_zone_correspondence(gbfm_path,
                                noham_path, outpath=output_dir)
    print(spatial_correspondence)
