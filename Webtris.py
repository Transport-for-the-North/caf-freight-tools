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
df_sites=pd.DataFrame(sites)
df_sites = df_sites.rename(columns={'Description': 'Site Name',
                                    'Name' : 'Site Information' })

df_am_all = pd.DataFrame({'Site Name': str(),
                          '0 - 520 cm': float(),
                          '521 - 660 cm': float(),
                          '661 - 1160 cm': float(),
                          '1160+ cm': float()}, 
                           index=[1])

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
start_date = "01012018"
end_date = "31122018"
page_offset = "1"
page_size = "96"

site_id = "3" #Site id to run between 1 and 17911, problems exporting site 1 but not sure why? Do a test see how many give results

api_url = api_url_base+"/"+version+"/"+resource+"/"+start_date+"/to/"+end_date+"/"+report_type+"?sites="+site_id+"&page="+page_offset+"&page_size="+page_size 
#api_url = "http://webtris.highwaysengland.co.uk/api/v1/reports/01012018/to/31122018/Daily?sites=4%2C5&page=1&page_size=10"

r = requests.get(api_url)
#If the following returns the code 200 then it works, if 404 then unsuccessful:
r.status_code

data = r.json()

header = data["Header"]
rows = data["Rows"]
df_rows = pd.DataFrame(rows)
df_rows =df_rows.drop(["0 - 10 mph", "11 - 15 mph", "16 - 20 mph", "21 - 25 mph", "26 - 30 mph", "31 - 35 mph", "36 - 40 mph", "41 - 45 mph", "46 - 50 mph", "51 - 55 mph", "56 - 60 mph", "61 - 70 mph","71 - 80 mph","80+ mph", "Avg mph", "Report Date", "Time Interval","Time Period Ending", "Total Volume"], axis = 1)
#Peak Periods:
df_am=df_rows.loc[28:39].copy() # Copy a subset to create am peak 
df_ip=df_rows.loc[40:63].copy() # Copy a subset to create ip peak 
df_pm=df_rows.loc[64:75].copy() # Copy a subset to create pm peak 


df_am.reset_index(drop=True, inplace=True) # Reset index numbers 

df_am=pd.concat([df_am['Site Name'],
                 df_am['0 - 520 cm'].astype(float), #Set these columns to float type
                 df_am['521 - 660 cm'].astype(float),
                 df_am['661 - 1160 cm'].astype(float),
                 df_am['1160+ cm'].astype(float)],
                 axis=1,
                 keys=['Site Name','0 - 520 cm','521 - 660 cm','661 - 1160 cm','1160+ cm'])


df_am.loc['Hour Avg'] = df_am.mean()*4 #Create new row giving the avg flow per hour
df_am.iat[12,0] = df_am.iat[0,0] # Set value of location within the last row
df_am.at['Hour Avg','Site Name'] = df_am.at[1,'Site Name'] # Set value of location within the last row

df_am=df_am.loc[['Hour Avg']] #Take final average row only


df_am_all=df_am_all.append(df_am)








# Below try append but on a certain column 
df_sites=pd.merge(df_sites, df_am, on='Site Name', how='outer')







###############################################
##Options to loop over:


# non_here - doesn't exist - calling it causes error
non_here = 'Hello!'

top_loop = ['a', 'b', 'c']
test = [1,2,3,4,5,6,7,8,9]

for tl in top_loop:
    print(tl)
    for t in test:
        print(t)
        if t == 4:
            break


try:
    # Note it actually does this
    print(non_here)
except:
    # If try fails, do this
    print('That variable doesn\'t exist m8')
else:
    # If try passes, do this
    print(non_here) # again
    



#Get this loop to with work sample ID's, if status code returns 200 then go for it, otherwise skip survey ID

site_id = "1" #Site id to run between 1 and 17911, problems exporting site 1 but not sure why? Do a test see how many give results






ID=[2,3,4,1,5]
for id in ID:
    api_url = api_url_base+"/"+version+"/"+resource+"/"+start_date+"/to/"+end_date+"/"+report_type+"?sites="+str(id)+"&page="+page_offset+"&page_size="+page_size 
    r = requests.get(api_url)
    print(r.status_code)
    if r.status_code != 200:
        id = id+1
else....    
   
    
    
    
    


#0-520 cm - motorbike/cars, 521-660 cm - LGV's , 661-1160 cm -Rigid Lorries, 1160+ cm - Articulated Lorries














