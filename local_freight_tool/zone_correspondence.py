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

def read_lsoa_data(lsoa_shapefile_path, lsoa_data_path):
    """Reads in LSOA shapefile and data, renames columns, combines shapefile
    with data.

    Parameters
    ----------
    lsoa_shapefile_path : str
        Path to LSOA zones shapefile
    lsoa_data_path : str
        Path to desired LSOA data to perform point zone handling with

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with LSOA shapefile data and selected data in var column.
    """
    # read in and combine LSOA data
    lsoa_zones = gpd.read_file(lsoa_shapefile_path)
    lsoa_data = gpd.read_file(lsoa_data_path)
    lsoa_data = lsoa_data.rename(columns={'lsoa11cd': 'lsoa_zone_id'})
    lsoa_zones = lsoa_zones.rename(columns={'LSOA11CD': 'lsoa_zone_id'})
    lsoa_data = lsoa_data[['lsoa_zone_id', 'var']]
    lsoa_data['var'] = lsoa_data['var'].astype(float)
    lsoa_zones_var = lsoa_zones.merge(lsoa_data, how='inner', 
                    left_on='lsoa_zone_id', right_on='lsoa_zone_id')
    lsoa_zones_var['lsoa_area'] = lsoa_zones_var.area
    
    return lsoa_zones_var

def spatial_zone_correspondence(zone_list, zone_names):
    """Finds the spatial zone corrrespondence through calculating adjustment
    factors with areas only.

    Parameters
    ----------
    zone_list : List[GeoDataFrame, GeoDataFrame]
        List of zone 1 and zone 2 GeoDataFrames.
    zone_names : List[str, str]
        List of zone names.
    extra_cols : str, optional
        Names of extra column to include in correspondence data, by default ''.
        

    Returns
    -------
    GeoDataFrame
        GeoDataFrame with 4 columns: zone 1 IDs, zone 2 IDs, zone 1 to zone 2
        adjustment factor and zone 2 to zone 1 adjustment factor.
    """

    # create geodataframe for intersection of zones
    zone_overlay = gpd.overlay(zone_list[0], zone_list[1], how='intersection').reset_index()
    zone_overlay['intersection_area'] = zone_overlay.area
    
    # columns to include in spatial correspondence
    column_list = [f'{zone_names[0]}_zone_id', f'{zone_names[1]}_zone_id']
    # var is important data to include in lsoa case
    if 'var' in zone_overlay.columns:
        column_list.append('var')
    
    # create geodataframe with spatial adjusted factors
    spatial_correspondence = zone_overlay[column_list]
    spatial_correspondence[f'{zone_names[0]}_to_{zone_names[1]}'] = (zone_overlay['intersection_area'] /
                                                                        zone_overlay[f'{zone_names[0]}_area'])
    spatial_correspondence[f'{zone_names[1]}_to_{zone_names[0]}'] = (zone_overlay['intersection_area'] /
                                                                        zone_overlay[f'{zone_names[1]}_area'])

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

def point_zone_filter(spatial_correspondence_no_slithers, point_tolerance, 
                        zone_list, zone_names, lsoa_shapefile_path, 
                        lsoa_data_path, tolerance):
    """Finds zone system 2 point and associated zones (sharing a zone system
    1 zone), reads in LSOA data, computes intersection, filters out slithers,
    makes sure each point zone is the only one associated with that LSOA.
    Returns var data for zone 2 zones as dataframes with zone ids as indices,
    var as column.

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
    # find point zones
    zone_2_point_zone_filter = ((spatial_correspondence_no_slithers[
        f'{zone_names[1]}_to_{zone_names[0]}'] > point_tolerance)
        & (spatial_correspondence_no_slithers[
        f'{zone_names[0]}_to_{zone_names[1]}'] < (1 - point_tolerance)))
        
    zone_2_point_zones_correspondence = spatial_correspondence_no_slithers[
        zone_2_point_zone_filter]
    
    zone_2_point_zones = zone_list[1][zone_list[1][f'{zone_names[1]}_zone_id'].isin(
        zone_2_point_zones_correspondence[f'{zone_names[1]}_zone_id']) == True]

    # find all zones in zone 2 that share an original zone 1 with a point zone
    # as these are the zones that need non-spatial handling
    zone_2_point_zone_sharing_filter = (
        spatial_correspondence_no_slithers[f'{zone_names[0]}_zone_id'].isin(
        zone_2_point_zones_correspondence[f'{zone_names[0]}_zone_id']))

    zone_2_point_affected_zone_correspondence = spatial_correspondence_no_slithers.loc[
                                zone_2_point_zone_sharing_filter]
    
    zone_2_point_affected_zones = zone_list[1][zone_list[1][f'{zone_names[1]}_zone_id'
                                ].isin(zone_2_point_affected_zone_correspondence[
                                f'{zone_names[1]}_zone_id']) == True]
    
    # create dataframe to track point zone data
    point_zones_information = pd.DataFrame(columns = [f'{zone_names[1]}_zone_id', 
                                                      'zone_type', 'correspondence', 'notes'] )
    point_zones_information[f'{zone_names[1]}_zone_id'] = zone_2_point_affected_zones[
                                                        f'{zone_names[1]}_zone_id']
    point_zones_information['correspondence'] = 'LSOA'
    point_zones_information['notes'] = ''
    point_zones_information['zone_type'] = 'non-point'
    point_zones_information.at[
        point_zones_information[f'{zone_names[1]}_zone_id'].isin(
        zone_2_point_zones[f'{zone_names[1]}_zone_id']), 'zone_type'] = 'point'
    
    # read in lsoa data
    lsoa_zone_data = read_lsoa_data(lsoa_shapefile_path, 
                                    lsoa_data_path)
    

    # perform zone correspondence between LSOA zones and zone 2 point affected zones
    lsoa_zone_2_list = [lsoa_zone_data, zone_2_point_affected_zones]
    lsoa_zone_2_names = ['lsoa', zone_names[1]]
    lsoa_zone_2_correspondence = spatial_zone_correspondence(lsoa_zone_2_list, lsoa_zone_2_names)
    
    # filter out slithers from this correspondence
    lsoa_zone_2_corr_slithers, lsoa_zone_2_corr_no_slithers = find_slithers(
        lsoa_zone_2_correspondence, lsoa_zone_2_names, tolerance)
    
    # separate correspondence for point zones and non-point zones
    point_filter = lsoa_zone_2_corr_no_slithers[f'{zone_names[1]}_zone_id'].isin(
                    zone_2_point_zones[f'{zone_names[1]}_zone_id'])
    
    lsoa_zone_2_point_corr = lsoa_zone_2_corr_no_slithers.loc[point_filter]
    
    lsoa_zone_2_non_point_corr = lsoa_zone_2_corr_no_slithers.loc[~point_filter]
    
    # check for any point zones that map to more than one LSOA
    duplicated_point_mappings = lsoa_zone_2_point_corr.loc[
        lsoa_zone_2_point_corr[f'{zone_names[1]}_zone_id'].duplicated(keep=False)]
    
    # find LSOAs that receive largest proportion of duplicated point zones
    zone_2_to_lsoa_max_factors = duplicated_point_mappings[[
        f'{zone_names[1]}_zone_id', f'{zone_names[1]}_to_lsoa']].groupby(
        f'{zone_names[1]}_zone_id').max(f'{zone_names[1]}_to_lsoa')
    
    # filter out the LSOAs that receive lesser proportions of duplicated zones
    lesser_zones_cond = ((duplicated_point_mappings[f'{zone_names[1]}_zone_id'].isin(
                        zone_2_to_lsoa_max_factors.index))
                        & ~(duplicated_point_mappings[f'{zone_names[1]}_to_lsoa'].isin(
                        zone_2_to_lsoa_max_factors[f'{zone_names[1]}_to_lsoa'])))
    
    zones_to_remove = duplicated_point_mappings.loc[lesser_zones_cond]
    
    lsoa_zone_2_point_corr = lsoa_zone_2_point_corr[
                            ~lsoa_zone_2_point_corr.index.isin(
                            zones_to_remove.index)]
    
    # check that all zones mapping to LSOAs associated with a point zone map to other zones
    # if they don't, that means a large zone is in the same LSOA as a point zone
    # so the correspondence shall have to remain spatial

    # find non-point zones mapped to only one LSOA
    lsoa_non_point_single_mapping = lsoa_zone_2_non_point_corr[
        ~lsoa_zone_2_non_point_corr[f'{zone_names[1]}_zone_id'].duplicated(keep=False)]

    if not lsoa_non_point_single_mapping.empty:
        # remove zones
        zones_to_remove = lsoa_non_point_single_mapping[
            lsoa_non_point_single_mapping['lsoa_zone_id'].isin(
            lsoa_zone_2_point_corr['lsoa_zone_id'])]
        lsoa_zone_2_non_point_corr = lsoa_zone_2_non_point_corr[
            ~lsoa_zone_2_non_point_corr['lsoa_zone_id'].isin(
            zones_to_remove['lsoa_zone_id'])]
        lsoa_zone_2_point_corr = lsoa_zone_2_point_corr[
            ~lsoa_zone_2_point_corr['lsoa_zone_id'].isin(
            zones_to_remove['lsoa_zone_id'])]
        
        # add this information to point zones info dataframe
        removed_zones_filter = point_zones_information[
            f'{zone_names[1]}_zone_id'].isin(
            zones_to_remove[f'{zone_names[1]}_zone_id'])
        point_zones_information.at[removed_zones_filter, 'correspondence'] = 'spatial'
        point_zones_information.at[removed_zones_filter, 'notes'] = f'{zone_names[1]} zone and point zone share single LSOA'
    
    # filter out LSOAs mapped to point zones to avoid overcounting var data
    point_zone_lsoa_filter = ~lsoa_zone_2_non_point_corr['lsoa_zone_id'].isin(lsoa_zone_2_point_corr['lsoa_zone_id'])
    lsoa_zone_2_non_point_corr = lsoa_zone_2_non_point_corr[point_zone_lsoa_filter]
    
    # group LSOA var data per zone 2 zone
    non_point_zone_2_var = lsoa_zone_2_non_point_corr[[f'{zone_names[1]}_zone_id', 'var']].groupby(f'{zone_names[1]}_zone_id').sum()
    point_zone_2_var = lsoa_zone_2_point_corr[[f'{zone_names[1]}_zone_id', 'var']].groupby(f'{zone_names[1]}_zone_id').sum()
    
    return non_point_zone_2_var, point_zone_2_var, point_zones_information

def point_zone_handling(spatial_correspondence_no_slithers, point_tolerance,
                        zone_list, zone_names, lsoa_shapefile_path, 
                        lsoa_data_path, tolerance):
    # get zone 2 point and non-point zone data
    non_point_zone_2_var, point_zone_2_var, point_zones_info = point_zone_filter(spatial_correspondence_no_slithers, point_tolerance, 
                        zone_list, zone_names, lsoa_shapefile_path, 
                        lsoa_data_path, tolerance)
    
    # get spatial correspondence data for point zones and point-adjacent zones
    point_zone_corr_filter = (spatial_correspondence_no_slithers[
        f'{zone_names[1]}_zone_id'].isin(
        point_zone_2_var.index))
    non_point_zone_corr_filter = (spatial_correspondence_no_slithers[
        f'{zone_names[1]}_zone_id'].isin(
        non_point_zone_2_var.index))
    
    zone_1_zone_2_point_corr = spatial_correspondence_no_slithers[point_zone_corr_filter]
    zone_1_zone_2_non_point_corr = spatial_correspondence_no_slithers[non_point_zone_corr_filter]
    
    # remove the point and point_adjacent data from the spatial correspondence
    spatial_correspondence_no_slithers = spatial_correspondence_no_slithers[
                                        ~point_zone_corr_filter | ~non_point_zone_corr_filter]
    
    return zone_1_zone_2_point_corr, zone_1_zone_2_non_point_corr, non_point_zone_2_var, point_zone_2_var   

if __name__ == '__main__':
    gbfm_path = 'C:/WSP_projects/Freight/zone_shapefiles/GBFM/Zones.shp'
    noham_path = 'C:/WSP_projects/Freight/zone_shapefiles/NoHAM/noham_zones_freeze_2.10.shp'
    output_dir = 'C:/WSP_projects/Freight/local_freight_tool/Outputs/Zone correspondence test'
    print(spatial_correspondence)
