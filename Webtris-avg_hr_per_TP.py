# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 11:24:48 2020

@author: LukeMonaghan
"""

import requests
import json
import pandas as pd
import os
import numpy as np
#Change directory to current working folder
os.chdir("C:/Users/LukeMonaghan/Documents/Python_Scripts/API_Requests_Json")


##############################################################
##############################################################
##############################################################
# All sites: 
# Inputs
api_url_base = "http://webtris.highwaysengland.co.uk/api/"
version = "v1.0"
resource = "sites"

api_url = api_url_base + "/" + version + "/" + resource
r = requests.get(api_url)

r.status_code #Ifreturns the code 200 then it works, if 404 then unsuccessful:

data = r.json()

sites = data["sites"]
sites=pd.DataFrame(sites)
sites = sites.rename(columns={'Description': 'Site Name',
                              'Name' : 'Site Information',
                               'Id' : 'Site_ID'})
sites['Site_ID']=sites['Site_ID'].astype(float)
sites.dtypes


############################################################
############################################################
############################################################

#Prepare Dataframes which collate average flows from each site: 

df_am_all = pd.DataFrame({'Site_ID' : float(),
                          '0 - 520 cm': float(),
                          '521 - 660 cm': float(),
                          '661 - 1160 cm': float(),
                          '1160+ cm': float()}, 
                           index=[1])
df_am_all.loc[:,:] = np.nan

df_am_all.dtypes

df_ip_all = pd.DataFrame({'Site_ID' : float(),
                          '0 - 520 cm': float(),
                          '521 - 660 cm': float(),
                          '661 - 1160 cm': float(),
                          '1160+ cm': float()}, 
                           index=[1])
df_ip_all.loc[:,:] = np.nan


df_pm_all = pd.DataFrame({'Site_ID' : float(),
                          '0 - 520 cm': float(),
                          '521 - 660 cm': float(),
                          '661 - 1160 cm': float(),
                          '1160+ cm': float()}, 
                           index=[1])
df_pm_all.loc[:,:] = np.nan

##############################################################
##############################################################
##############################################################
# Site Counts:
# Inputs
api_url_base = "http://webtris.highwaysengland.co.uk/api/"
version = "v1.0"
resource = "reports"
report_type = "Daily"
start_date = "01012018"
end_date = "31122018"
page_offset = "1"
page_size = "96"

site_id = list(range(1,17912)) #Site id to run between 1 and 17911
for id in site_id:
    api_url = api_url_base+"/"+version+"/"+resource+"/"+start_date+"/to/"+end_date+"/"+report_type+"?sites="+str(id)+"&page="+page_offset+"&page_size="+page_size 
    r = requests.get(api_url)
    print(r.status_code)
    if r.status_code != 200:
        df_am_all.loc[id,:] = np.nan
        df_am_all.loc[id, 'Site_ID'] = id 
        df_ip_all.loc[id,:] = np.nan
        df_ip_all.loc[id, 'Site_ID'] = id 
        df_pm_all.loc[id,:] = np.nan
        df_pm_all.loc[id, 'Site_ID'] = id         
        id = id+1
    else:
        data = r.json()
        rows = data["Rows"]
        rows = pd.DataFrame(rows)
        rows =rows.drop(["0 - 10 mph", 
                         "11 - 15 mph", 
                         "16 - 20 mph", 
                         "21 - 25 mph", 
                         "26 - 30 mph", 
                         "31 - 35 mph", 
                         "36 - 40 mph", 
                         "41 - 45 mph", 
                         "46 - 50 mph", 
                         "51 - 55 mph", 
                         "56 - 60 mph", 
                         "61 - 70 mph",
                         "71 - 80 mph",
                         "80+ mph", 
                         "Avg mph", 
                         "Report Date",
                         "Site Name",
                         "Time Interval",
                         "Time Period Ending", 
                         "Total Volume"], axis = 1)
        #Peak Periods:
        df_am=rows.loc[28:39].copy() # Copy a subset to create am peak 
        df_ip=rows.loc[40:63].copy() # Copy a subset to create ip peak 
        df_pm=rows.loc[64:75].copy() # Copy a subset to create pm peak 

#AM Peak
        df_am.reset_index(drop=True, inplace=True) # Reset index numbers 
        df_am.loc[:, 'Site_ID'] = id
        df_am['0 - 520 cm'] = pd.to_numeric(df_am['0 - 520 cm'], errors='coerce')
        df_am['521 - 660 cm'] = pd.to_numeric(df_am['521 - 660 cm'], errors='coerce')
        df_am['661 - 1160 cm'] = pd.to_numeric(df_am['661 - 1160 cm'], errors='coerce')
        df_am['1160+ cm'] = pd.to_numeric(df_am['1160+ cm'], errors='coerce')

        df_am=pd.concat([df_am['Site_ID'].astype(float),
                         df_am['0 - 520 cm'].astype(float), #Set these columns to float type
                         df_am['521 - 660 cm'].astype(float),
                         df_am['661 - 1160 cm'].astype(float),
                         df_am['1160+ cm'].astype(float)],
                         axis=1,
                         keys=['Site_ID','0 - 520 cm','521 - 660 cm','661 - 1160 cm','1160+ cm'])

        df_am.loc['Hour Avg'] = df_am.mean()*4 #Create new row giving the avg flow per hour
        df_am.loc[:, 'Site_ID'] = id #Set SiteID value again now got the averages        
        df_am=df_am.loc[['Hour Avg']] #Take final average row only

        df_am_all=df_am_all.append(df_am)
        df_am_all.reset_index(drop=True, inplace=True) # Reset index numbers     
   
#Inter-Peak    
        df_ip.reset_index(drop=True, inplace=True) # Reset index numbers 
        df_ip.loc[:, 'Site_ID'] = id
        df_ip['0 - 520 cm'] = pd.to_numeric(df_ip['0 - 520 cm'], errors='coerce')
        df_ip['521 - 660 cm'] = pd.to_numeric(df_ip['521 - 660 cm'], errors='coerce')
        df_ip['661 - 1160 cm'] = pd.to_numeric(df_ip['661 - 1160 cm'], errors='coerce')
        df_ip['1160+ cm'] = pd.to_numeric(df_ip['1160+ cm'], errors='coerce')

        df_ip=pd.concat([df_ip['Site_ID'].astype(float),
                         df_ip['0 - 520 cm'].astype(float), #Set these columns to float type
                         df_ip['521 - 660 cm'].astype(float),
                         df_ip['661 - 1160 cm'].astype(float),
                         df_ip['1160+ cm'].astype(float)],
                         axis=1,
                         keys=['Site_ID','0 - 520 cm','521 - 660 cm','661 - 1160 cm','1160+ cm'])

        df_ip.loc['Hour Avg'] = df_ip.mean()*4 #Create new row giving the avg flow per hour
        df_ip.loc[:, 'Site_ID'] = id #Set SiteID value again now got the averages
        df_ip=df_ip.loc[['Hour Avg']] #Take final average row only

        df_ip_all=df_ip_all.append(df_ip)
        df_ip_all.reset_index(drop=True, inplace=True) # Reset index numbers 

#PM Peak
        df_pm.reset_index(drop=True, inplace=True) # Reset index numbers 
        df_pm.loc[:, 'Site_ID'] = id
        df_pm['0 - 520 cm'] = pd.to_numeric(df_pm['0 - 520 cm'], errors='coerce')
        df_pm['521 - 660 cm'] = pd.to_numeric(df_pm['521 - 660 cm'], errors='coerce')
        df_pm['661 - 1160 cm'] = pd.to_numeric(df_pm['661 - 1160 cm'], errors='coerce')
        df_pm['1160+ cm'] = pd.to_numeric(df_pm['1160+ cm'], errors='coerce')

        df_pm=pd.concat([df_pm['Site_ID'].astype(float),
                         df_pm['0 - 520 cm'].astype(float), #Set these columns to float type
                         df_pm['521 - 660 cm'].astype(float),
                         df_pm['661 - 1160 cm'].astype(float),
                         df_pm['1160+ cm'].astype(float)],
                         axis=1,
                         keys=['Site_ID','0 - 520 cm','521 - 660 cm','661 - 1160 cm','1160+ cm'])

        df_pm.loc['Hour Avg'] = df_pm.mean()*4 #Create new row giving the avg flow per hour
        df_pm.loc[:, 'Site_ID'] = id #Set SiteID value again now got the averages
        df_pm=df_pm.loc[['Hour Avg']] #Take final average row only

        df_pm_all=df_pm_all.append(df_pm)
        df_pm_all.reset_index(drop=True, inplace=True) # Reset index numbers 



#Merge Site Count data above with the Site information: 
sites_am=pd.merge(sites, df_am_all, on='Site_ID', how='outer')
sites_ip=pd.merge(sites, df_ip_all, on='Site_ID', how='outer')   
sites_pm=pd.merge(sites, df_pm_all, on='Site_ID', how='outer')     

sites_am = sites_am.rename(columns={'0 - 520 cm': '0-520 cm (Motorbike/cars)',
                                    '521 - 660 cm' : '521-660cm (LGV\'s)',
                                    '661 - 1160 cm' : '661-1160cm (Rigid Lorries)',
                                    '1160+ cm' : '1160+cm (Artic Lorries)'})
sites_ip = sites_ip.rename(columns={'0 - 520 cm': '0-520 cm (Motorbike/cars)',
                                    '521 - 660 cm' : '521-660cm (LGV\'s)',
                                    '661 - 1160 cm' : '661-1160cm (Rigid Lorries)',
                                    '1160+ cm' : '1160+cm (Artic Lorries)'})
sites_pm = sites_pm.rename(columns={'0 - 520 cm': '0-520 cm (Motorbike/cars)',
                                    '521 - 660 cm' : '521-660cm (LGV\'s)',
                                    '661 - 1160 cm' : '661-1160cm (Rigid Lorries)',
                                    '1160+ cm' : '1160+cm (Artic Lorries)'})    
    
#0-520 cm - motorbike/cars, 521-660 cm - LGV's , 661-1160 cm -Rigid Lorries, 1160+ cm - Articulated Lorries


sites_am.to_excel("sites_am.xlsx")    
sites_ip.to_excel("sites_ip.xlsx")
sites_pm.to_excel("sites_pm.xlsx")
    
    
    
    
    
    
    




