# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 17:13:29 2020

@author: cruella
"""

import os

import pandas as pd

_default_file_drive = 'Y:/'

if __name__ == '__main__':
    # Define import folder
    import_folder = (_default_file_drive + 'NorMITs Freight/import/')

    # Import DfT traffic counts
    tc = pd.read_csv(import_folder + '/tra0201_dft.csv')
    # Import WSP/DfT trip purpose splits
    tps = pd.read_csv(import_folder + '/wsp_dft_van_survey_km_purpose.csv')
    
    # Benchmark total traffic against 2003 (survey year) total
    wsp_total = tps['vehicle_km'].sum()
    dft_total = tc[tc['year']==2003]['lgv_yr_km'].values
    audit_perc = (wsp_total-dft_total)/dft_total
    # wsp total around 12% under - in right order of magnitude
    # Comfortable enough to use the higher figures to split for purpose.
    
    # TODO: Factor uplifts for purpose adjustment since 2003?

    # Get 2018 total lgv miles
    lgv_2018 = dft_total = tc[tc['year']==2018]['lgv_yr_km'].values
    # Multiply by split factors
    tps['2018_vehicle_km'] = lgv_2018 * tps['trip_split_factor']
    
    # Filter to get UK Non-freight van
    non_freight = tps[tps['trip_type']=='non_freight'].copy()
    non_freight = non_freight.drop(['vehicle_km', 'trip_split_factor'],axis=1)

    # TODO: Divide km by average trip length (by band?) to get trips.

    print('run')
