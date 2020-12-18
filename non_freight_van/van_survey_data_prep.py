# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 15:57:19 2020

@author: cruella
"""

import pandas as pd

_default_file_drive = 'Y:/'
_default_file_name = '/LGV_Survey_all_years_combined.xls'
_default_van_survey_path = (_default_file_drive +
                            '/NorMITs Freight/import' +
                            '/LGV_Survey_all_years_combined' +
                            _default_file_name)
_default_export_folder = (_default_file_drive +
                          '/NorMITs Freight/import')

# Subset van survey down to non-freight only
# Derive average trip length by band from DfT survey

def get_van_survey(vs_path = _default_van_survey_path):
    
    """
    Returns sheets in van survey as a list of dicts
    """

    vs = pd.ExcelFile(vs_path)

    # Define placeholder list
    tabs = {}

    # Get sheet names
    vs_sheets = vs.sheet_names

    # Import by sheet, allocated to list of dicts
    for sheet in vs_sheets:
        print(sheet)
        frame = vs.parse(sheet)
        out_dict = {sheet:frame}
        tabs.update(out_dict)
    
    return(tabs)

def classify_trip_length(trip_length):
    """
    Simple heuristic to give a string trip length band
    """
    if trip_length > 0 and trip_length < 5:
        c_tl = '0-5'
    elif trip_length >= 5 and trip_length < 10:
        c_tl = '5-10'
    elif trip_length >= 10 and trip_length < 20:
        c_tl = '10-20'
    elif trip_length >=20 and trip_length <30:
        c_tl = '20-30'
    elif trip_length >=30 and trip_length <40:
        c_tl = '30-40'
    elif trip_length >=40 and trip_length <50:
        c_tl = '40-50'
    elif trip_length >=50 and trip_length <75:
        c_tl = '50-75'
    elif trip_length >=75:
        c_tl = '75+'
    else:
        c_tl = trip_length

    return(c_tl)

def classify_survey_data(van_survey):

    """
    Takes the data from van survey and classifies relevant variables
    """

    # Get LGV data and classification data
    for key in van_survey:            
        if key == 'LGVS':
            main_dat = van_survey[key]
        if key == 'Lookup':
            lookup_dat = van_survey[key]

    # Data handling
    lookup_dat.columns = lookup_dat.iloc[2]
    lookup_dat = lookup_dat.iloc[3:]
    lookup_dat = lookup_dat.iloc[:,0:5].reset_index(drop=True)

    return(main_dat, lookup_dat)

def build_non_freight_trip_lengths(van_survey_data,
                                   van_survey_lookups):
    """
    Builds banded non-freight trip lengths
    No weighting applied - yet
    """

    # TODO: Use residential van data to apply weighting
    # TODO: Understand the Distance vs. Kilometres params.
 
    # Filter down to non_freight
    non_freight_data = van_survey_data[
            van_survey_data['freight'] == 'Non Freight'].copy()
    
    # Get rid of 0 length and No purpose
    non_freight_data = non_freight_data[
            non_freight_data['Distance'].notnull()]
    non_freight_data = non_freight_data[
            non_freight_data['Distance'] != 0]
    non_freight_data = non_freight_data[
                        non_freight_data['SuperReason'] != 'Unknown']
    
    # Classify by trip length
    non_freight_data['trip_length_bands'] = non_freight_data['Distance'].apply(
            classify_trip_length)

    # Print sample sizes
    samples = non_freight_data.reindex(['trip_length_bands',
                                        'SuperReason'], axis=1).groupby(
    'trip_length_bands')['SuperReason'].value_counts(
            ).unstack(
                    ).fillna(
                            0).reset_index()
    samples = samples.rename(columns={'Index':'trip_length_bands'})

    # Build factors for multiplying out non_freight trips
    factors = samples.copy()
    purpose_cols = list(factors)[1:]
    for p_col in purpose_cols:
        total = factors[p_col].sum()
        factors[p_col] = (factors[p_col]/total).copy()

    means = non_freight_data.reindex(['Distance',
                                      'SuperReason',
                                      'trip_length_bands'], axis=1).groupby(
        ['SuperReason', 'trip_length_bands']).agg('mean').reset_index()

    # dict up samples means and factors for outputs
    output = {'samples':samples,
              'means':means,
              'factors':factors}

    return(output)
    
def run(write=False,
        export_folder = _default_export_folder):

    """
    Run it all
    """

    van_survey = get_van_survey()
    van_survey = classify_survey_data(van_survey)

    data = build_non_freight_trip_lengths(van_survey[0], van_survey[1])
    if write:
        for d in data:
            print(d)
            export_path = (export_folder + '/' +
                           'non_freight_survey_' + d + '.csv')
            data[d].to_csv(export_path, index=False)

    return(data)

    
    