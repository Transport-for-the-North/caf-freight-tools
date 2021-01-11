# -*- coding: utf-8 -*-
"""

Created on: Mon Jul 27 12:07:06 2020

Original author: LukeMonaghan

File purpose:
Sum Together the Artic+Rigid HGV matrices, remove south-south + scot-scot
trips and covert to a UFM. 
 
"""
import pandas as pd
import os
# Custom libs
_default_path = 'C:/Users/DataAnalytics/Documents/GitHub/NorTMS/'
os.chdir(_default_path)
import Saturn_Scripts as sat


####### Read in Tier Converter matrices ################
os.chdir(r"Y:\NorMITs Freight\Tier Converter\LM-NoHAM\3.GBFM_Annual-ModelTP\Outputs 27 July 20\HGV")
artic_am= pd.read_csv('articAM.csv')
rigid_am= pd.read_csv('rigidAM.csv')
artic_pm= pd.read_csv('articPM.csv')
rigid_pm= pd.read_csv('rigidPM.csv')
artic_ip= pd.read_csv('articIP.csv')
rigid_ip= pd.read_csv('rigidIP.csv')
artic_op= pd.read_csv('articOP.csv')
rigid_op= pd.read_csv('rigidOP.csv')



####### Set index to be unique id #######
artic_am = artic_am.set_index(['Origin','Destination'])
rigid_am = rigid_am.set_index(['Origin','Destination'])
artic_pm = artic_pm.set_index(['Origin','Destination'])
rigid_pm = rigid_pm.set_index(['Origin','Destination'])
artic_ip = artic_ip.set_index(['Origin','Destination'])
rigid_ip = rigid_ip.set_index(['Origin','Destination'])
artic_op = artic_op.set_index(['Origin','Destination'])
rigid_op = rigid_op.set_index(['Origin','Destination'])


######Sum together arctic+rigid ########
HGV_AM = artic_am+rigid_am
HGV_AM = HGV_AM.reset_index(level=['Origin', 'Destination'])
HGV_AM.dtypes
HGV_AM.sum() #Trips                 6.179174e+05  = 617917.4

HGV_PM = artic_pm+rigid_pm
HGV_PM = HGV_PM.reset_index(level=['Origin', 'Destination'])
HGV_PM.dtypes
HGV_PM.sum() #Trips                 3.383798e+05  = 338379.8

HGV_IP = artic_ip+rigid_ip
HGV_IP = HGV_IP.reset_index(level=['Origin', 'Destination'])
HGV_IP.dtypes
HGV_IP.sum() #Trips                  6.359717e+05 = 635971.7

HGV_OP = artic_op+rigid_op
HGV_OP = HGV_OP.reset_index(level=['Origin', 'Destination'])
HGV_OP.dtypes
HGV_OP.sum() #Trips                  1.518331e+05 = 151833.1



#Read in .dat file to group north/scot/south trips
zone_info=pd.read_csv("Z2S3.txt", delim_whitespace=True)


################ HGV AM #############################
HGV_AM_int = pd.merge(HGV_AM, zone_info, how='left', left_on='Origin', right_on='Zone') 
HGV_AM_int = HGV_AM_int.drop(columns = ['Zone'])
HGV_AM_int = HGV_AM_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
HGV_AM_int = pd.merge(HGV_AM_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
HGV_AM_int = HGV_AM_int.drop(columns = ['Zone'])
HGV_AM_int = HGV_AM_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})

HGV_AM_int['Area_Code']=HGV_AM_int['Orig_Area_Code'].astype(str)+'_'+HGV_AM_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    HGV_AM_int.loc[HGV_AM_int['Area_Code'] == x, 'Trips'] = 0

HGV_AM_int['Trips'].sum() #229482.81911542622

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
HGV_AM_int.to_csv('HGV_AM_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)


################ HGV PM #############################
HGV_PM_int = pd.merge(HGV_PM, zone_info, how='left', left_on='Origin', right_on='Zone') 
HGV_PM_int = HGV_PM_int.drop(columns = ['Zone'])
HGV_PM_int = HGV_PM_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
HGV_PM_int = pd.merge(HGV_PM_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
HGV_PM_int = HGV_PM_int.drop(columns = ['Zone'])
HGV_PM_int = HGV_PM_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})

HGV_PM_int['Area_Code']=HGV_PM_int['Orig_Area_Code'].astype(str)+'_'+HGV_PM_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    HGV_PM_int.loc[HGV_PM_int['Area_Code'] == x, 'Trips'] = 0

HGV_PM_int['Trips'].sum() #128471.45680067311

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
HGV_PM_int.to_csv('HGV_PM_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)


################ HGV IP #############################
HGV_IP_int = pd.merge(HGV_IP, zone_info, how='left', left_on='Origin', right_on='Zone') 
HGV_IP_int = HGV_IP_int.drop(columns = ['Zone'])
HGV_IP_int = HGV_IP_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
HGV_IP_int = pd.merge(HGV_IP_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
HGV_IP_int = HGV_IP_int.drop(columns = ['Zone'])
HGV_IP_int = HGV_IP_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})

HGV_IP_int['Area_Code']=HGV_IP_int['Orig_Area_Code'].astype(str)+'_'+HGV_IP_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    HGV_IP_int.loc[HGV_IP_int['Area_Code'] == x, 'Trips'] = 0

HGV_IP_int['Trips'].sum() #236313.39079960983

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
HGV_IP_int.to_csv('HGV_IP_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)


################ HGV OP #############################
HGV_OP_int = pd.merge(HGV_OP, zone_info, how='left', left_on='Origin', right_on='Zone') 
HGV_OP_int = HGV_OP_int.drop(columns = ['Zone'])
HGV_OP_int = HGV_OP_int.rename(columns={'Area_Code' : 'Orig_Area_Code'})
HGV_OP_int = pd.merge(HGV_OP_int, zone_info, how='left', left_on='Destination', right_on='Zone') 
HGV_OP_int = HGV_OP_int.drop(columns = ['Zone'])
HGV_OP_int = HGV_OP_int.rename(columns={'Area_Code' : 'Dest_Area_Code'})

HGV_OP_int['Area_Code']=HGV_OP_int['Orig_Area_Code'].astype(str)+'_'+HGV_OP_int['Dest_Area_Code'].astype(str)

for x in ['2_2','3_3']:
    HGV_OP_int.loc[HGV_OP_int['Area_Code'] == x, 'Trips'] = 0

HGV_OP_int['Trips'].sum() #59063.07195921701

#Export to csv:
columns_include = ["Origin", "Destination", "Trips"]
HGV_OP_int.to_csv('HGV_OP_int.csv',sep=',', float_format='%.5f', columns = columns_include,index = False, header = False)




##################Convert CSV files to UFM ####################
sat.CSV2UFM(wd = r'Y:\NorMITs Freight\Tier Converter\LM-NoHAM\3.GBFM_Annual-ModelTP\Outputs 27 July 20\HGV',
            satEXES = r'C:\Program Files (x86)\Atkins\SATURN\XEXES 11.4.07H MC N4',
            csvFile = ['HGV_AM_int','HGV_PM_int', 'HGV_IP_int','HGV_OP_int'])






