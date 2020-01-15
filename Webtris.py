# -*- coding: utf-8 -*-
"""
Created on Fri Jan 10 11:24:48 2020

@author: LukeMonaghan
"""

import requests
import json
import pandas as pd
import os
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
#If the following returns the code 200 then it works, if 404 then unsuccessful:
r.status_code

data = r.json()

sites = data["sites"]
df_sites=pd.DataFrame(sites)

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
#Site id to run between 1 and 17911, problems exporting site 1 but not sure why? Do a test see how many give results:
site_id = "2"

api_url = api_url_base+"/"+version+"/"+resource+"/"+start_date+"/to/"+end_date+"/"+report_type+"?sites="+site_id+"&page="+page_offset+"&page_size="+page_size 
#api_url = "http://webtris.highwaysengland.co.uk/api/v1/reports/01012018/to/31122018/Daily?sites=4%2C5&page=1&page_size=10"

r = requests.get(api_url)
#If the following returns the code 200 then it works, if 404 then unsuccessful:
r.status_code

data = r.json()

header = data["Header"]
rows = data["Rows"]
df_rows = pd.DataFrame(rows)
df_rows =df_rows.drop(["0 - 10 mph", "11 - 15 mph", "16 - 20 mph", "21 - 25 mph", "26 - 30 mph", "31 - 35 mph", "36 - 40 mph", "41 - 45 mph", "46 - 50 mph", "51 - 55 mph", "56 - 60 mph", "61 - 70 mph","71 - 80 mph","80+ mph" ], axis = 1)
#Peak Periods:
df_rows_am=df_rows[28:40]
df_rows_ip=df_rows[40:64]
df_rows_pm=df_rows[64:76]




















