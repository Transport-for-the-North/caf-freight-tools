"""
Created on: Thurs Jan 28 2021

Original author: CaraLynch

File purpose:
Nest two shapefiles to produce adjustment factors from one zone to another.
"""

import geopandas as gpd

def zone_correspondence(zone_1_path, zone_2_path, outpath='', zone_1_name='gbfm', 
                        zone_2_name='noham'):
    """[summary]

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
    GeoDataFrame
        GeoDataFrame with zone 1 and zone 2 IDs as well as spatial adjustment
        factors to convert between them.
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
    spatial_zone_correspondence = zone_overlay[[f'{zone_names[0]}_zone_id',
                                f'{zone_names[1]}_zone_id']]
    spatial_zone_correspondence[f'{zone_names[0]}_to_{zone_names[1]}'] = (zone_overlay['intersection_area'] /
                                                                        zone_overlay[f'{zone_names[0]}_area'])
    spatial_zone_correspondence[f'{zone_names[1]}_to_{zone_names[0]}'] = (zone_overlay['intersection_area'] /
                                                                        zone_overlay[f'{zone_names[1]}_area'])

    spatial_zone_correspondence.to_csv(f'{outpath}/spatial_zone_correspondence.csv', index=False)

    return spatial_zone_correspondence



if __name__ == '__main__':
    gbfm_path = 'C:/WSP_projects/Freight/zone_shapefiles/GBFM/Zones.shp'
    noham_path = 'C:/WSP_projects/Freight/zone_shapefiles/NoHAM/noham_zones_freeze_2.10.shp'
    output_dir = 'C:/WSP_projects/Freight/local_freight_tool/Outputs/Zone correspondence test'
    spatial_zones_adjustment = zone_correspondence(gbfm_path, noham_path, outpath=output_dir)
    print(spatial_zones_adjustment)
