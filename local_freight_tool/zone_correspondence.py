"""
Created on: Thurs Jan 28 2021

Original author: CaraLynch

File purpose:
Nest two shapefiles to produce adjustment factors from one zone to another.
"""

import geopandas as gpd

def spatial_zone_correspondence(zone_1_path, zone_2_path, outpath='', 
                                zone_1_name='gbfm', zone_2_name='noham'):
    """Finds the spatial zone corrrespondence through calculating adjustment
    factors with areas only.

    Parameters
    ----------
    zone_1_path : str
        Path to first zone system shapefile
    zone_2_path : str
        Path to second zone system shapefile
    outpath : str, optional
        Path to output directory, by default '' (working directory)
    zone_1_name : str, optional
        Name of first zone system, by default 'gbfm'
    zone_2_name : str, optional
        Name of second zone system, by default 'noham'

    Returns
    -------
    GeoDataFrame, list of GeoDataframes, list of strings
        GeoDataFrame with zone 1 and zone 2 IDs as well as spatial adjustment
        factors to convert between them, a list of zone 1 and zone 2
        GeoDataframes, and a list with the names of the zones.
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

    return spatial_correspondence, zone_list, zone_names

def find_slithers(spatial_correspondence, tolerance):
    """Finds overlap areas between zones which are very small slithers,
    filters them out of the spatial zone correspondence GeoDataFrame,
    and returns the filtered zone correspondence as well as the 
    GeoDataFrame with only the slithers.

    Parameters
    ----------
    spatial_correspondence : GeoDataFrame
        Spatial zone correspondence between zone 1 and zone 2 produced with 
        spatial_zone_correspondence.
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
    slither_filter = ((spatial_correspondence[f'{zone_names[0]}_to_{zone_names[1]}'] < (1-tolerance)) &
                    (spatial_correspondence[f'{zone_names[1]}_to_{zone_names[0]}'] < (1-tolerance)))
    slithers = spatial_correspondence[slither_filter]
    no_slithers = spatial_correspondence[~slither_filter]

    return slithers, no_slithers


def point_zone_handling(spatial_correspondence_no_slithers, point_tolerance, 
                        zone_list, zone_names, lsoa_shapefile_path, lsoa_data_path):

    # read in and combine LSOA data
    lsoa_zones = gpd.read_file(lsoa_shapefile_path)
    lsoa_data = gpd.read_file(lsoa_data_path)
    lsoa_data = lsoa_data.rename(columns={'lsoa11cd': 'LSOA11CD'})
    lsoa_data = lsoa_data[['LSOA11CD', 'var']]
    lsoa_zones_var = lsoa_zones.merge(lsoa_data, how='inner', left_on='LSOA11CD', right_on='LSOA11CD')

    # find point zones
    zone_1_point_zone_filter = ((spatial_correspondence_no_slithers[
        f'{zone_names[0]}_to_{zone_names[1]}'] > point_tolerance)
        & (spatial_correspondence_no_slithers[
        f'{zone_names[1]}_to_{zone_names[0]}'] < (1 - point_tolerance)))

    zone_2_point_zone_filter = ((spatial_correspondence_no_slithers[
        f'{zone_names[1]}_to_{zone_names[0]}'] > point_tolerance)
        & (spatial_correspondence_no_slithers[
        f'{zone_names[0]}_to_{zone_names[1]}'] < (1 - point_tolerance)))
    
    zone_1_point_zones = spatial_correspondence_no_slithers[zone_1_point_zone_filter]
        
    zone_2_point_zones = spatial_correspondence_no_slithers[zone_2_point_zone_filter]

    # find all zones in zone 2 that share an original zone 1 with a point zone
    zone_2_point_zone_sharing = spatial_correspondence_no_slithers.loc[(
        spatial_correspondence_no_slithers[f'{zone_names[0]}_zone_id'].isin(
        zone_2_point_zones[f'{zone_names[0]}_zone_id']))]


    


if __name__ == '__main__':
    gbfm_path = 'C:/WSP_projects/Freight/zone_shapefiles/GBFM/Zones.shp'
    noham_path = 'C:/WSP_projects/Freight/zone_shapefiles/NoHAM/noham_zones_freeze_2.10.shp'
    output_dir = 'C:/WSP_projects/Freight/local_freight_tool/Outputs/Zone correspondence test'
    spatial_correspondence, zone_list, zone_names = spatial_zone_correspondence(gbfm_path,
                                noham_path, outpath=output_dir)
    print(spatial_zones_adjustment)
