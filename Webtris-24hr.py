# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 16:22:37 2020

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

#Filter out North sites:
north_sites=sites.loc[(sites['Latitude'] >= 52.642702) & (sites['Latitude'] <= 55.860379 )]
north_sites.reset_index(drop=True, inplace=True) # Reset index numbers 

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

##############################################################
##############################################################
##############################################################
# Site Counts:
# Inputs
api_url_base = "http://webtris.highwaysengland.co.uk/api/"
version = "v1.0"
resource = "reports"
report_type = "Daily"
start_date = "01012015"
end_date = "31122019"
page_offset = "1"
page_size = "96"


site_id = 2
api_url = api_url_base+"/"+version+"/"+resource+"/"+start_date+"/to/"+end_date+"/"+report_type+"?sites="+str(id)+"&page="+page_offset+"&page_size="+page_size 
r = requests.get(api_url)
data = r.json()
rows = data["Rows"]
rows = pd.DataFrame(rows)


s = rows
rows['Report Date'] =pd.to_datetime(s['Report Date'])
s.dtypes
rows['Weekday']=rows['Report Date'].dt.dayofweek #Produce new column with weekdays (0 Monday, 6,7 Weekend)













#######################################################

site_id = list(range(1,5)) #Site id to run between 1 and 17911
for id in site_id:
    api_url = api_url_base+"/"+version+"/"+resource+"/"+start_date+"/to/"+end_date+"/"+report_type+"?sites="+str(id)+"&page="+page_offset+"&page_size="+page_size 
    r = requests.get(api_url)
    print(r.status_code)
    if r.status_code != 200:
        df_am_all.loc[id,:] = np.nan
        df_am_all.loc[id, 'Site_ID'] = id         
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
   

#Merge Site Count data above with the Site information: 
sites_am=pd.merge(sites, df_am_all, on='Site_ID', how='outer')
  

sites_am = sites_am.rename(columns={'0 - 520 cm': '0-520 cm (Motorbike/cars)',
                                    '521 - 660 cm' : '521-660cm (LGV\'s)',
                                    '661 - 1160 cm' : '661-1160cm (Rigid Lorries)',
                                    '1160+ cm' : '1160+cm (Artic Lorries)'})
    
#0-520 cm - motorbike/cars, 521-660 cm - LGV's , 661-1160 cm -Rigid Lorries, 1160+ cm - Articulated Lorries


sites_am.to_excel("sites_am.xlsx")    

    
    
    
    
    
    










