# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 17:13:29 2020

@author: cruella
"""

import os

import pandas as pd

_default_file_drive = 'Y:/'
_default_distribution_folder = ('Y:/NorMITs Synthesiser/Noham/iter4/' +
                               'Distribution Outputs/Compiled OD Matrices/vehicle export')

def get_target_distributions(folder = _default_distribution_folder,
                             matrix_format = 'wide',
                             required_dists = 'hb',
                             reduce_to_factors = True):

    """
    folder = target distribution folder
    
    matrix_format = 'wide' or 'long'. What format is target matrix in.
    """

    contents = os.listdir(folder)
    
    if required_dists == 'hb':
        contents = [x for x in contents if 'nhb' not in x]

    purpose_list = ['commmute', 'business', 'other']
    time_period_list = ['tp1', 'tp2', 'tp3', 'tp4']
    direction_list = ['from', 'to']

    # Placeholder for list of dicts
    export_dist = []

    for dist in contents:
        print(dist)
        for p in purpose_list:
            if p in dist:
                dist_purpose = p
        for tp in time_period_list:
            if tp in dist:
                dist_time_period = tp
        for d in direction_list:
            if d in dist:
                dist_direction = d
        # Read matrix
        dist_mat = pd.read_csv(folder + '/' + dist)
        
        # If wide, pivot long
        if matrix_format == 'wide':
            dist_mat = dist_mat.melt(id_vars = ['o_zone'],
                                     var_name = 'd_zone',
                                     value_name = 'pcu_trips')
            # Drop null rows too
            dist_mat = dist_mat[dist_mat['pcu_trips']>0]

        elif matrix_format == 'long':
            dist_mat = dist_mat.rename(columns={'dt':'pcu_trips'})

        # Reduce to factor
        if reduce_to_factors:
            total_demand = dist_mat['pcu_trips'].sum()
            dist_mat['demand_factor'] = dist_mat['pcu_trips']/total_demand
            dist_mat = dist_mat.drop('pcu_trips', axis=1)

        # Build export name
        export_dict = {'purpose':dist_purpose,
                       'time_period':dist_time_period,
                       'direction':dist_direction,
                       'data':dist_mat}        
        export_dist.append(export_dict)
        # END

    return(export_dist)
    
# TODO: Shouldn't be a main, there's too much going on

if __name__ == '__main__':
    # Define import folder
    import_folder = (_default_file_drive + 'NorMITs Freight/import/')
    
    # TODO: Build output folder, check existing exports

    # Import DfT traffic counts
    tc = pd.read_csv(import_folder + '/tra0201_dft.csv')
    # Import WSP/DfT trip purpose splits
    tps = pd.read_csv(import_folder + '/wsp_dft_van_survey_km_purpose.csv')
    # Import non freight survey factors
    s_fac = pd.read_csv(import_folder + '/non_freight_survey_factors.csv')
    # Make long format
    s_fac = s_fac.melt(id_vars = ['trip_length_bands'],
                      var_name = 'SuperReason',
                      value_name = 'trip_length_factor')
    
    # Import non freight survey mean trip lengths
    s_mtl = pd.read_csv(import_folder + '/non_freight_survey_means.csv')

    # Benchmark total traffic against 2003 (survey year) total
    wsp_total = tps['vehicle_km'].sum()
    dft_total = tc[tc['year']==2003]['lgv_yr_km'].values
    audit_perc = (wsp_total-dft_total)/dft_total
    # wsp total around 12% under - in right order of magnitude
    # Comfortable enough to use the higher figures to split for purpose.
    
    # TODO: Drop unused purposes and reuse milage
    # TODO: Factor uplifts for purpose adjustment since 2003?

    # Get 2018 total lgv miles
    lgv_2018 = dft_total = tc[tc['year']==2018]['lgv_yr_km'].values
    # Multiply by split factors
    tps['2018_vehicle_km'] = lgv_2018 * tps['trip_split_factor']
    
    # Filter to get UK Non-freight van
    non_freight = tps[tps['trip_type']=='non_freight'].copy()
    non_freight = non_freight.drop(['vehicle_km', 'trip_split_factor'],axis=1)

    ## Multiply vehicle miles by trip length band factors to get banded miles
    non_freight = non_freight.merge(s_fac,
                                    how='left',
                                    on=['SuperReason'])
    # Drop na (and unalligned milage, see above)
    non_freight = non_freight[~non_freight['trip_length_factor'].isna()]

    # Get banded miles
    non_freight['2018_vehicle_km'] = (non_freight['2018_vehicle_km']*
               non_freight['trip_length_factor'])
    # Drop factors
    non_freight = non_freight.drop('trip_length_factor', axis=1)

    # Divide bands by the mean trip length to get trips (PCU)
    non_freight = non_freight.merge(s_mtl,
                                    how='left',
                                    on=['SuperReason', 'trip_length_bands'])
    non_freight['pcu_trips'] = (non_freight['2018_vehicle_km']/
               non_freight['Distance'])
    # Drop mean distance
    non_freight = non_freight.drop('Distance', axis=1)
    
    # TODO: Reduce down from annual to daily using factors
    non_freight['pcu_trips'] = non_freight['pcu_trips']/380

    # Reduce from daily to time period using factors
    tps = [1,2,3,4]
    ph = []
    for tp in tps:
        tp_mat = non_freight.copy()
        tp_mat['pcu_trips'] = tp_mat['pcu_trips']/4
        out = {('tp'+str(tp)):tp_mat}
        ph.append(out)

    # Import compiled pcu noham distributions
    get_target_distributions(folder = _default_distribution_folder,
                             matrix_format = 'wide',
                             required_dists = 'hb',
                             reduce_to_factors = True)
    
    # TODO: Multiply out demand by dists

    # TODO: Combine OD from and OD to

    # TODO: Check trip length distribution is sensible compared to observed
    
    # TODO: Export non-freight LGV

    print('run')
