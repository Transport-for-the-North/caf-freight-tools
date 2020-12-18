# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 09:24:11 2020

@author: hill1908
"""

import pandas as pd
from rezone import Rezone as rz
from time import gmtime, strftime

# Profile selection function
profiles = pd.read_csv('all_profiles.csv')
profiles = profiles.set_index(['VehType', 'RoadType', 'DayOfWeek'])

day_selection = {'Average Weekday': range(5),
                 'Average Day': range(7),
                 'Saturday': 5,
                 'Sunday': 6,
                 'Monday': 0,
                 'Tuesday': 1,
                 'Wednesday': 2,
                 'Thursday': 3,
                 'Friday': 4}

def append_factors(tp, veh_type, road_type):
    for selection in tp:
        selected_profile = profiles.loc[(veh_type, road_type,
                                         day_selection.get(selection[1])), slice(None)]
        if type(selected_profile) != pd.Series: # the trivial case where only one day is selected is excluded
            # computing the mean creates average profile over the selected days
            selected_profile = selected_profile.mean()
            
        # cut the series down to the hours in the selection and calculate the mean
        hr_start = int(selection[2])
        hr_end = int(selection[3])
        
        # now calculate the average flow in an hour within the time period
        if hr_start < hr_end:
            flow_in_tp = selected_profile[[i for i in range(hr_start, hr_end)]].mean()
        else: # deal with the case where the time period straddles midnight
            flow_in_tp = selected_profile[[i for i in range(hr_start, 24)]
                                         +[i for i in range(0,hr_end)]].mean()
        
        # divide the total flow per year by the flow in the tp selection and append
        selection.append(2400*365/flow_in_tp)
        
    return(tp)

def main_converter_process(tp, veh_type, road_type, gbfm_filepath, zone_mapping, log_name, message_box):
    # Read in the GBFM output
    df = pd.read_csv(gbfm_filepath, sep='\t')
    df.columns = ['Origin', 'Destination', 'Trips']
    
    # Set the column names for the correspondence
    zone_mapping = pd.read_csv(zone_mapping)
    zone_mapping.columns = ['Old', 'New', 'SplittingFactor']
    
    # Perform the transformation to the model zoning system
    rezoned_df = rz.rezoneOD(df, zone_mapping)
    
    message_box.setText('GBFM matrix rezoned')

    with open(log_name, 'a') as log_file:
        log_file.write('GBFM matrix rezone completed at %s\n\n' % strftime('%Y-%m-%d %H:%M:%S', gmtime()))
    
    # Factor the rezoned matrix to convert from annual PCU to the selected time period(s)
    tp = append_factors(tp, veh_type, road_type)
    
    for selection in tp: # to turn this into a function you would need [tp, rezoned_df, log_name] as arguments ---------------------------------------------------------
        # Divide the trips by the factor determined by the user selections
        out_df = rezoned_df.copy()
        factor = selection[4]
        out_df['Trips'] /= factor
        
        # Export the factored matrix
        file_name = selection[0] + '.csv'
        message_box.setText('Exporting ' + file_name)
        out_df.to_csv(file_name, index=None)
        message_box.setText(file_name + ' has been exported')

        with open(log_name, 'a') as log_file:
            log_file.write('Time period name: %s\n' % (selection[0]))
            log_file.write('Day selection: %s\n' % (selection[1]))
            log_file.write('Hour start: %s\n' % (selection[2]))
            log_file.write('Hour end: %s\n' % (selection[3]))
            log_file.write('Factor: %s\n\n' % (str(selection[4])))
            log_file.write(file_name + ' export completed at %s\n\n\n' % strftime('%Y-%m-%d %H:%M:%S', gmtime()))
            
    message_box.setText('All time period selections complete. You may exit the program')