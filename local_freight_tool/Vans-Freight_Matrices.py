# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 12:07:06 2020

@author: LukeMonaghan
#Remove south-south + scot-scot trips and covert to a UFM.  
"""
import pandas as pd
import os
# Custom libs
_default_path = 'C:/Users/DataAnalytics/Documents/GitHub/NorTMS/'
os.chdir(_default_path)
import Saturn_Scripts as sat

####### Read in Tier Converter matrices ################
os.chdir(r"Y:\NorMITs Freight\Tier Converter\LM-NoHAM\3.GBFM_Annual-ModelTP\Outputs 27 July 20\LGV")
van_freight_AM= pd.read_csv('van_freightAM.csv')
van_freight_AM['Trips'].sum()    #725567.9645950339

van_freight_PM= pd.read_csv('van_freightPM.csv')
van_freight_PM['Trips'].sum()    #493040.80828289466

van_freight_IP= pd.read_csv('van_freightIP.csv')
van_freight_IP['Trips'].sum()    #670388.3343239744

van_freight_OP= pd.read_csv('van_freightOP.csv')
van_freight_OP['Trips'].sum()    #123587.92640651435



#Read in .dat file to group north/scot/south trips
zone_info=pd.read_csv("Z2S3.txt", delim_whitespace=True)


################ LGV AM #############################
van_freight_AM_int = pd.merge(van_freight_AM, zone_info, how='left', left_on='Origin', right_on='Zone') 
van_freight_AM_int = van_freight_AM_int.drop(columns = ['Zone'])
van_freight_AM_int = van_freight_AM_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
van_freight_AM_int = pd.merge(van_freight_AM_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
van_freight_AM_int = van_freight_AM_int.drop(columns = ['Zone'])
van_freight_AM_int = van_freight_AM_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})
van_freight_AM_int['Area_Code']=van_freight_AM_int['Orig_Area_Code'].astype(str)+'_'+van_freight_AM_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    van_freight_AM_int.loc[van_freight_AM_int['Area_Code'] == x, 'Trips'] = 0

van_freight_AM_int['Trips'].sum() #263845.1913047283

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
van_freight_AM_int.to_csv('van_freight_AM_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)


################ LGV PM #############################
van_freight_PM_int = pd.merge(van_freight_PM, zone_info, how='left', left_on='Origin', right_on='Zone') 
van_freight_PM_int = van_freight_PM_int.drop(columns = ['Zone'])
van_freight_PM_int = van_freight_PM_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
van_freight_PM_int = pd.merge(van_freight_PM_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
van_freight_PM_int = van_freight_PM_int.drop(columns = ['Zone'])
van_freight_PM_int = van_freight_PM_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})
van_freight_PM_int['Area_Code']=van_freight_PM_int['Orig_Area_Code'].astype(str)+'_'+van_freight_PM_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    van_freight_PM_int.loc[van_freight_PM_int['Area_Code'] == x, 'Trips'] = 0

van_freight_PM_int['Trips'].sum() #179093.87109109963

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
van_freight_PM_int.to_csv('van_freight_PM_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)


################ LGV IP #############################
van_freight_IP_int = pd.merge(van_freight_IP, zone_info, how='left', left_on='Origin', right_on='Zone') 
van_freight_IP_int = van_freight_IP_int.drop(columns = ['Zone'])
van_freight_IP_int = van_freight_IP_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
van_freight_IP_int = pd.merge(van_freight_IP_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
van_freight_IP_int = van_freight_IP_int.drop(columns = ['Zone'])
van_freight_IP_int = van_freight_IP_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})
van_freight_IP_int['Area_Code']=van_freight_IP_int['Orig_Area_Code'].astype(str)+'_'+van_freight_IP_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    van_freight_IP_int.loc[van_freight_IP_int['Area_Code'] == x, 'Trips'] = 0

van_freight_IP_int['Trips'].sum() #243645.58301614271 243689.81719527405

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
van_freight_IP_int.to_csv('van_freight_IP_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)


################ LGV OP #############################
van_freight_OP_int = pd.merge(van_freight_OP, zone_info, how='left', left_on='Origin', right_on='Zone') 
van_freight_OP_int = van_freight_OP_int.drop(columns = ['Zone'])
van_freight_OP_int = van_freight_OP_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
van_freight_OP_int = pd.merge(van_freight_OP_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
van_freight_OP_int = van_freight_OP_int.drop(columns = ['Zone'])
van_freight_OP_int = van_freight_OP_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})
van_freight_OP_int['Area_Code']=van_freight_OP_int['Orig_Area_Code'].astype(str)+'_'+van_freight_OP_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    van_freight_OP_int.loc[van_freight_OP_int['Area_Code'] == x, 'Trips'] = 0

van_freight_OP_int['Trips'].sum() #99135.47087937087 #99153.46905575016

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
van_freight_OP_int.to_csv('van_freight_OP_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)




##################Convert CSV files to UFM ####################
sat.CSV2UFM(wd = r'Y:\NorMITs Freight\Tier Converter\LM-NoHAM\3.GBFM_Annual-ModelTP\Outputs 27 July 20\LGV',
            satEXES = r'C:\Program Files (x86)\Atkins\SATURN\XEXES 11.4.07H MC N4',
            csvFile = ['van_freight_AM_int','van_freight_PM_int','van_freight_IP_int','van_freight_OP_int'])
