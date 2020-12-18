# -*- coding: utf-8 -*-
"""
Spyder Editor

"""
#Script to Ensure we have all OD's in the HGV file. 
#Currently, Van Freight contains all trip OD's whereas HGV contains non-zero trips only, need HGV to contain all Trip OD's

import pandas as pd
import os

#Load in LGVs
os.chdir(r"C:\Users\LukeMonaghan\Documents\Python_Scripts\Freight_Matrices\21 May 20 - Final NTM Zone System")
vans_freight_total = pd.read_csv('freight_vans_2018_NTM_zones_v6_5.txt', delim_whitespace=True)
#Load in HGVs
HGVs = pd.read_csv('GBFMv6.2_Total_Annual_HGV_PCUs_2018_OD_Matrix_v2_NTM_zones_v6_5.txt', delim_whitespace=True)
HGVs['Trip_id']=HGVs['Origin_NTM_zone_v6_5'].astype(str)+'_'+HGVs['Destination_NTM_zone_v6_5'].astype(str)
#Create new dataframe which contains all OD's (from LGV file)
df=pd.concat([vans_freight_total['Origin_NTM_zone_v6_5'], vans_freight_total['Destination_NTM_zone_v6_5']], axis=1)
df['Trip_ID']=df['Origin_NTM_zone_v6_5'].astype(str)+'_'+df['Destination_NTM_zone_v6_5'].astype(str)

#Merge new df with HGV file 
HGV_2 = pd.merge(df,HGVs, how='left', left_on='Trip_ID', right_on='Trip_id') 
HGV_2 = HGV_2.drop(columns = ['Trip_ID','Trip_id','Origin_NTM_zone_v6_5_y','Destination_NTM_zone_v6_5_y'])
#Fill NA values with 0
HGV_2=HGV_2.fillna(0)
HGV_2=HGV_2.rename(columns={0 : 'Origin_NTM_zone_v6_5',
                            1 : 'Destination_NTM_zone_v6_5',
                            2 : 'TotalAnnualHGV_PCUs2018'})
HGV_2.to_csv("GBFMv6.2_Total_Annual_HGV_PCUs_2018_OD_Matrix_v2_NTM_zones_v6_5.csv",index=False)

HGV_2 = pd.read_csv('GBFMv6.2_Total_Annual_HGV_PCUs_2018_OD_Matrix_v2_NTM_zones_v6_5.csv', delim_whitespace=True)


