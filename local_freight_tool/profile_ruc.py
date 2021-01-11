# -*- coding: utf-8 -*-
"""
Created on: Mon Feb 17 09:24:11 2020

Original author: hill1908

File purpose:
Converts annual GBFM O-D trip/PCU matrices to model time period
specific O-D trip/PCU matrices.
"""

import pandas as pd
from rezone import Rezone as rz
from time import gmtime, strftime
from utilities import Utilities

profiles = pd.read_csv('all_profiles.csv')
profiles = profiles.set_index(['VehType', 'RoadType', 'DayOfWeek'])

# Read in the GBFM rural/urban classification
ruc_gbfm = pd.read_csv('../../Inputs/gbfm_classed.csv')

def append_factors(tp, veh_type):
    for selection in tp:
        for road_type in ['urban', 'urban_dense', 'rural', 'combined']:
            selected_profile = profiles.loc[(veh_type, road_type,
                                             eval(selection.get('days'))), slice(None)]

            # computing the mean creates average profile over the selected days
            selected_profile = selected_profile.mean()
                
            # cut the series down to the hours in the selection and calculate the mean
            hr_start = int(selection.get('hr_start'))
            hr_end = int(selection.get('hr_end'))
            
            # now calculate the average flow in an hour within the time period
            if hr_start < hr_end:
                flow_in_tp = selected_profile[[i for i in range(hr_start, hr_end)]].mean()
            else: # deal with the case where the time period straddles midnight
                flow_in_tp = selected_profile[[i for i in range(hr_start, 24)]
                                             +[i for i in range(0, hr_end)]].mean()
            
            # divide the total flow per year by the flow in the tp selection and add to the dictionary
            selection[road_type] = 2400*365/flow_in_tp
            
            # find the period type
            if ((7 <= hr_start <= 10) & (7 <= hr_end <= 10)):
                selection['period'] = 'AM peak'
            elif ((16 <= hr_start <= 19) & (16 <= hr_end <= 19)):
                selection['period'] = 'PM peak'
            else:
                selection['period'] = 'other'
                    
    return(tp)

def main_converter_process(tp, veh_type, gbfm_filepath, prefixes, zone_mapping, log_name, message_box, output_path):
    # Set the column names for the correspondence
    print(type(veh_type))
    try:
        zone_mapping = Utilities.read_csv(zone_mapping)
        zone_mapping.columns = ['Old', 'New', 'SplittingFactor']
    except:
        with open(log_name, 'a') as log_file:
            log_file.write('\nError: zone correspondence file was invalid')
    
    # Factor the rezoned matrix to convert from annual PCU to the selected time period(s)
    tp = append_factors(tp, veh_type)
    
    for i, output in enumerate(gbfm_filepath):
        # Determine the factors to use
        tp = append_factors(tp, veh_type[i])
        
        # Read in the GBFM output
        try:
            df = Utilities.read_csv(output)
            df.columns = ['Origin', 'Destination', 'Trips']
            
        except:
            with open(log_name, 'a') as log_file:
                log_file.write('\nError: %s was invalid' % output)
        
        for selection in tp:
            # Divide the trips by the factor determined by the user selections
            out_df = df.copy()
            
            if selection.get('period') == 'AM peak': # factor on the destination classification in AM
                message_box.setText('Factoring for %s with RUC on Destinations (AM peak)' % selection.get('name'))
                out_df = out_df.merge(ruc_gbfm, how='left', left_on='Destination', right_on='UniqueID').drop('UniqueID', axis=1)
                factors = {0: selection.get('urban_dense'), 1: selection.get('urban'), 2: selection.get('rural')}
                out_df['Factors'] = out_df['Class'].map(factors)
                out_df['Trips'] /= out_df['Factors']
                out_df = out_df.drop(['Class', 'Factors'], axis=1)
            
            elif selection.get('period') == 'PM peak': # factor on the origin classification in PM
                message_box.setText('Factoring for %s with RUC on Origins (PM peak)' % selection.get('name'))
                out_df = out_df.merge(ruc_gbfm, how='left', left_on='Origin', right_on='UniqueID').drop('UniqueID', axis=1)
                factors = {0: selection.get('urban_dense'), 1: selection.get('urban'), 2: selection.get('rural')}
                out_df['Factors'] = out_df['Class'].map(factors)
                out_df['Trips'] /= out_df['Factors']
                out_df = out_df.drop(['Class', 'Factors'], axis=1)
                
            else: # outside of the peak periods
                message_box.setText('Factoring for %s without RUC (non-peak)' % selection.get('name'))
                out_df['Trips'] /= selection.get('combined') # apply the combined road type profiles
            
            # Rezone and export the factored matrix
            file_name = prefixes[i].text() + selection.get('name') + '.csv'
            message_box.setText('Rezoning ' + file_name)   
            out_df = rz.rezoneOD(out_df, zone_mapping)
            with open(log_name, 'a') as log_file:
                log_file.write('\n%s\n\n Rezoned at %s\n\n' % (file_name, strftime('%Y-%m-%d %H:%M:%S', gmtime())))
            message_box.setText('Exporting ' + file_name)  
            out_df.to_csv(output_path + '/' + file_name, index=None)
    
            with open(log_name, 'a') as log_file:
                log_file.write('Time period name: %s\n' % (selection.get('name')))
                log_file.write('Day selection: %s\n' % (selection.get('days')))
                log_file.write('Hour start: %s\n' % (selection.get('hr_start')))
                log_file.write('Hour end: %s\n' % (selection.get('hr_end')))
                log_file.write('Rural factor: %s\n' % (str(selection.get('rural'))))
                log_file.write('Urban factor: %s\n' % (str(selection.get('urban'))))
                log_file.write('Combined factor: %s\n\n' % (str(selection.get('combined'))))
                log_file.write(file_name + ' export completed at %s\n\n\n' % strftime('%Y-%m-%d %H:%M:%S', gmtime()))
            
    message_box.setText('All time period selections complete. You may exit the program')