# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 17:13:29 2020

@author: cruella
"""

import os
import pandas as pd

_default_file_drive = 'Y:/'
_default_distribution_folder = ('Y:/NorMITs Synthesiser/Noham/iter5/' +
                               'Distribution Outputs/Compiled OD Matrices/vehicle export')
_default_pop_translation = 'Y:/NorMITs Synthesiser/Zone Translation/Export/'


def translate_distribution(other_model_dist, # other_model_dist = nfv_dists.copy()
                           model_name = 'noham',
                           other_model_name = 'gbfm',
                           other_model_target_path = _default_pop_translation,
                           matrix_type = 'od',
                           demand_col = 'dt'): # PA or OD

    """
    Translate distribution from one model zoning system to another using
    given lookups
    """

    # TODO: Check for matrix type
    if matrix_type == 'pa':
        zone_from = 'p_zone'
        zone_to = 'a_zone'
    elif matrix_type == 'od':
        zone_from = 'o_zone'
        zone_to = 'd_zone'

    # Drop segments from distribution, retain p/a & trips
    other_model_dist = other_model_dist.reindex([zone_from, zone_to, demand_col], axis=1)
    # There goes purposes

    # Get original total productions
    om_productions = other_model_dist[demand_col].sum()

    lookup_types = [(other_model_name + '_' + model_name.lower()),
                    (model_name.lower()) + '_' + other_model_name]

    # Check for lookup types, pop weighted and employment weighted
    # TODO: if there isn't one run one - or have this at the outset
    zone_translation_lookups = []
    mzl_dir = os.listdir(other_model_target_path)
    for lt in lookup_types:
        ztl = [x for x in mzl_dir if lt in x]
        if len(ztl) > 0:
            zone_translation_lookups.append(ztl)
    # flatten list of lists
    zone_translation_lookups = [x for y in zone_translation_lookups for x in y]
    # Pull out individuals
    zt_pop = [x for x in zone_translation_lookups if 'pop' in x][0]
    zt_emp = [x for x in zone_translation_lookups if 'emp' in x][0]

    zt_pop = pd.read_csv((other_model_target_path + '/' + zt_pop))
    zt_emp = pd.read_csv((other_model_target_path + '/' + zt_emp))

    # Define index cols for lookups
    li_cols = [(other_model_name + '_zone_id'),
               (model_name.lower() + '_zone_id'),
               ('overlap_' + other_model_name + '_split_factor')]

    # Model name first, other model second
    split_factor_col = ('overlap_' + other_model_name + '_split_factor')

    zt_pop = zt_pop.reindex(li_cols, axis=1)
    zt_emp = zt_emp.reindex(li_cols, axis=1)

    # Process to get cleaner matches
    original_model_col = (other_model_name + '_zone_id')
    target_model_col = (model_name.lower() + '_zone_id')

    # Round & drop 0 segments
    zt_pop[split_factor_col] = zt_pop[split_factor_col].round(3)
    zt_pop = zt_pop[zt_pop[split_factor_col]>0]

    # Correct factors back to 0
    zt_pop_tot = zt_pop.reindex([original_model_col, split_factor_col], axis=1).groupby(
            original_model_col).sum().reset_index()

    # Derive adjustment for factor
    zt_pop_tot['adj_factor'] = 1/(zt_pop_tot[split_factor_col]/1)
    zt_pop_tot = zt_pop_tot.drop(split_factor_col, axis=1)
    zt_pop = zt_pop.merge(zt_pop_tot,
                          how='left',
                          on = original_model_col)
    zt_pop[split_factor_col] = zt_pop[split_factor_col] * zt_pop['adj_factor']
    zt_pop = zt_pop.drop('adj_factor', axis=1)

    # Round & drop 0 segments
    zt_emp[split_factor_col] = zt_emp[split_factor_col].round(3)
    zt_emp = zt_emp[zt_emp[split_factor_col]>0]

    # Correct factors back to 0
    zt_emp_tot = zt_emp.reindex([original_model_col,
                                 split_factor_col],
    axis=1).groupby(
            original_model_col).sum().reset_index()
    # Derive adjustment for factor
    zt_emp_tot['adj_factor'] = 1/(zt_emp_tot[split_factor_col]/1)
    zt_emp_tot = zt_emp_tot.drop(split_factor_col, axis=1)
    zt_emp = zt_emp.merge(zt_emp_tot,
                          how='left',
                          on = original_model_col)
    zt_emp[split_factor_col] = zt_emp[split_factor_col] * zt_emp['adj_factor']
    zt_emp = zt_emp.drop('adj_factor', axis=1)
    # zone translations defined

    # Rename destination zone names to join w/o duplication
    zt_pop = zt_pop.rename(
            columns={(other_model_name + '_zone_id'):zone_from})
    zt_emp = zt_emp.rename(
            columns={(other_model_name + '_zone_id'):zone_to})

    # Transform model demand to current model zones
    # TODO: Issue is here
    # Bring in population split for productions
    other_model_dist = other_model_dist.merge(zt_pop,
                            how='left',
                            on=zone_from)
    # Multiply out
    other_model_dist[demand_col] = other_model_dist[demand_col] * other_model_dist[('overlap_' + other_model_name + '_split_factor')]
    other_model_dist = other_model_dist.drop(
            [zone_from,
             'overlap_' + other_model_name + '_split_factor'], axis=1)
    other_model_dist = other_model_dist.rename(
            columns={(model_name.lower() + '_zone_id'):zone_from})
    # Group and sum
    group_cols = [zone_from, zone_to]
    sum_cols = group_cols.copy()
    sum_cols.append(demand_col)

    other_model_dist = other_model_dist.reindex(
            sum_cols,axis=1).groupby(
                    group_cols).sum().reset_index()

    # Bring in employment split for attractions
    other_model_dist = other_model_dist.merge(zt_emp,
                            how='left',
                            on=zone_to)
    # Multiply out
    other_model_dist[demand_col] = other_model_dist[demand_col] * other_model_dist[('overlap_' + other_model_name + '_split_factor')]
    other_model_dist = other_model_dist.drop(
            [zone_to,
             'overlap_' + other_model_name + '_split_factor'], axis=1)
    other_model_dist = other_model_dist.rename(
            columns={(model_name.lower() + '_zone_id'):zone_to})
    # Group and sum
    other_model_dist = other_model_dist.reindex(
            sum_cols,axis=1).groupby(
                    group_cols).sum().reset_index()

    # Audit total
    if om_productions.round(0) == other_model_dist[demand_col].sum().round(0):
        print('Balanced well')
    else:
        print('Balance off') # TODO: Bit more

    # Reduce to zonal factors to apply new productions to
    other_model_dist_p_totals = other_model_dist.reindex([zone_from, demand_col], axis=1).groupby(zone_from).sum().reset_index()
    other_model_dist_p_totals = other_model_dist_p_totals.rename(columns={demand_col:(demand_col+'_total')})

    other_model_dist = other_model_dist.merge(other_model_dist_p_totals,
                            how='left',
                            on=zone_from)
    # Derive p/a share by p
    other_model_dist['p_a_share'] = other_model_dist[demand_col]/other_model_dist[(demand_col+'_total')]
    other_model_dist = other_model_dist.drop([demand_col, (demand_col+'_total')],axis=1)

    return(target_dist)

def get_target_distributions(folder = _default_distribution_folder,
                             matrix_format = 'wide',
                             required_dists = 'hb',
                             combine_time_periods = True,
                             combine_directions = True,
                             reduce_to_factors = True):

    """
    folder = target distribution folder

    matrix_format = 'wide' or 'long'. What format is target matrix in.
    
    required_dists = Only handles 'hb'
    """

    contents = os.listdir(folder)

    # Subset required distributions
    # TODO: Should be able to take all or NHB only, if I'd ever want that.
    if required_dists == 'hb':
        contents = [x for x in contents if 'nhb' not in x]

    purpose_list = ['commute', 'business', 'other']
    time_period_list = ['tp1', 'tp2', 'tp3', 'tp4']
    direction_list = ['from', 'to']

    # Placeholder for list of dicts
    export_dist = []

    for dist in contents:
        print(dist)

        # Handle purpose
        for p in purpose_list:
            if p in dist:
                dist_purpose = p

        # Handle time periods
        for tp in time_period_list:
            if tp in dist:
                dist_time_period = tp

        # Handle direction
        for d in direction_list:
            if d in dist:
                dist_direction = d

        # Build export name
        export_dict = {'purpose':dist_purpose,
                       'time_period':dist_time_period,
                       'direction':dist_direction,
                       'path':dist}     
        export_dist.append(export_dict)
        # END

    # Processing loop
    # Pop time periods if aggregating
    if combine_time_periods:
        for drop_dist in export_dist:
            drop_dist.pop('time_period')
    # Pop direction if aggregating
    if combine_directions:
         for drop_dist in export_dist:
             drop_dist.pop('direction')

    # Compile to dataframe
    df_ph = pd.DataFrame(export_dist)

    # iter as dataframe

    # Recompile
    solution_dist = []
    for index, row in df_ph.iterrows():
        print(row['path'])
        ph = pd.read_csv(folder + '/' + row['path'])

        # If wide, pivot long
        if matrix_format == 'wide':
            ph = ph.melt(id_vars = ['o_zone'],
                                     var_name = 'd_zone',
                                     value_name = 'pcu_trips')

            # Drop null rows too
            ph = ph[ph['pcu_trips']>0]

        elif matrix_format == 'long':
            ph = ph.rename(columns={'dt':'pcu_trips'})
        
        # Iterate over the label rows and add as classification vars
        class_cols = list(row.index)
        class_cols.remove('path')

        for col in class_cols:
            print(col)
            ph[col] = row[col]

        solution_dist.append(ph)

    # Concatenate
    solution_dist = pd.concat(solution_dist, sort=True)
    
    group_cols = ['o_zone', 'd_zone']
    for col in class_cols:
        group_cols.append(col)
    sum_cols = group_cols.copy()
    sum_cols.append('dt')
    
    solution_dist = solution_dist.groupby(
            group_cols).sum().reset_index()

    # Aggregate and reduce to factors
    unique_groups = solution_dist.reindex(
            class_cols, axis=1).drop_duplicates().reset_index(drop=True)

    # Reduce to factor
    if reduce_to_factors:
        factor_ph = []
        for g_index, g_row in unique_groups.iterrows():

            # Reduce factors by subset
            subset = solution_dist.copy()
            for col in class_cols:
                subset = subset[subset[col]==g_row[col]].reset_index(drop=True)

            total_demand = subset['pcu_trips'].sum()
            subset['demand_factor'] = subset['pcu_trips']/total_demand
            subset = subset.drop('pcu_trips', axis=1)
            factor_ph.append(subset)
        solution_dist = pd.concat(factor_ph, sort=True)

    return(solution_dist)

def build_annual_non_freight_van(target_zone_path = _default_pop_translation):
    
    """
    Returns annual demand 
    """
    
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
    print(audit_perc)
    # wsp total around 12% under
    # Comfortable enough to use the higher figures to split for purpose.

    # TODO: Factor uplifts for purpose adjustment since 2003?

    # Get 2018 total lgv miles
    lgv_2018 = dft_total = tc[tc['year']==2018]['lgv_yr_km'].values
    # Multiply by split factors
    tps['2018_vehicle_km'] = lgv_2018 * tps['trip_split_factor']
    
    # Filter to get UK Non-freight van
    non_freight = tps[tps['trip_type']=='non_freight'].copy()
    non_freight = non_freight.drop(['vehicle_km', 'trip_split_factor'],axis=1)

    # Drop unused purposes and reuse milage in other
    non_other_for_other = non_freight[non_freight['SuperReason'].isin(['Other business', 'Unknown'])].copy()
    non_other_for_other['SuperReason'] = 'Personal'
    other_for_other = non_freight[~non_freight['SuperReason'].isin(['Other business', 'Unknown'])].copy()
    # Reassemble
    non_freight = pd.concat([other_for_other, non_other_for_other], sort=True)
    non_freight = non_freight.groupby(['SuperReason', 'ntem_purpose', 'trip_type']).sum().reset_index()

    ## Multiply vehicle miles by trip length band factors to get banded miles
    non_freight = non_freight.merge(s_fac,
                                    how='left',
                                    on=['SuperReason'])
    # Drop na (and unalligned milage, see above)
    non_freight = non_freight[~non_freight['trip_length_factor'].isna()]

    # Get banded km
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

    # Import compiled pcu noham distributions
    car_dists = get_target_distributions(folder = _default_distribution_folder,
                                         matrix_format = 'wide',
                                         required_dists = 'hb',
                                         combine_time_periods = True,
                                         combine_directions = True,
                                         reduce_to_factors = True)

    # TODO: Get trip length percentages by band
    tld_bin = non_freight.copy()
    tld_bin = tld_bin.reindex(['ntem_purpose',
                               'trip_length_bands',
                               'pcu_trips'], axis=1)
    unbanded_totals =tld_bin.copy().reindex(['ntem_purpose',
                                 'pcu_trips'],
    axis=1).groupby('ntem_purpose').sum(
            ).reset_index().rename(columns={'pcu_trips':'all_trips'})
    tld_bin = tld_bin.merge(unbanded_totals, how='left', on=['ntem_purpose'])
    tld_bin['band_share'] = tld_bin['pcu_trips']/tld_bin['all_trips']
    tld_bin = tld_bin.drop(['pcu_trips', 'all_trips'], axis=1)

    # rename unbanded totals for join
    unbanded_totals = unbanded_totals.rename(columns={'ntem_purpose':'purpose'})
    
    # TODO: Multiply out demand by dists
    nfv_dists = car_dists.copy()
    nfv_dists = nfv_dists.merge(unbanded_totals, how='left', on='purpose')    
    
    # Production model
    nfv_dists['pcu_trips'] = nfv_dists['demand_factor'] * nfv_dists['all_trips']
    nfv_dists = nfv_dists.drop(['demand_factor', 'all_trips'], axis=1)

    # TODO: Check trip length distribution is sensible compared to observed
    
    # TODO: Trip length adjustment Furness to match target trip lengths
    
    # TODO: Translate to GBFM
    # TODO: Currently pop only, should be emp too but needs directionality
    translation = pd.read_csv(target_zone_path)

    # Export formatting
    nfv_dists = nfv_dists.reindex(['o_zone', 'd_zone', 'purpose', 'pcu_trips'],
                                  axis=1)
    nfv_dists['o_zone'] = pd.to_numeric(nfv_dists['o_zone'])
    nfv_dists['d_zone'] = pd.to_numeric(nfv_dists['d_zone'])

    nfv_dists = nfv_dists.sort_values(
            by=['o_zone', 'd_zone']).reset_index(drop=True)

    # TODO: Export non-freight LGV
    nfv_dists.to_csv('Y:/NorMITs Freight/export/noham_lgv_non_freight.csv',
                     index=False)

    return(nfv_dists)
