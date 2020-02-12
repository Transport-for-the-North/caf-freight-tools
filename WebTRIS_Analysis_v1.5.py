#!/usr/bin/env python3

###############################################################################
#Script Name: WebTRIS_Analysis_v1.4.py
#Description: Analyses WebTRIS data from user-specified list of sites

#How to run script from the command line:
#python WebTRIS_Analysis_v1.4.py <start date> <end date> <sites list> <days list>
#dates should be passed as ddmmyyyy
#sites list should be passed as a text file, which sits in the same directory as this script
#days list should be written as a list e.g. 1,2,3. Here 1 == Monday and 7 == Sunday.

#Version History
#1.4 2019-08-27, Theodoros Chatziioannou, transfer to Python version 3.6
#1.3 2018-06-19, Alex Harrison, added URLError handling for sites which have no available data report
#1.2 2018-05-21, Alex Harrison, added sys.argv input for days to search for
#1.1 2018-05-18, Alex Harrison, added TypeError handling for sparse, but not empty, datasets
#1.0, 2018-04-25, Alex Harrison, promoted to v1 as is now being presented
#0.3.4, 2018-03-27, Alex Harrison, added boxplot and refined cleaning process
#0.3.3, 2018-03-26, Alex Harrison, added extra statistics to output data
#0.3.2, 2018-03-26, Alex Harrison, modified to used argv input
#0.3.1, 2018-03-23, Alex Harrison, Looping structure added, analyses developed to produce richer analysis
#0.2, 2018-03-01, Abbie Page, transfer from .ipynb to .py and reduced some of the EDA
#0.1, 2017-11-01, Michael Addyman, initial processing setup in Jupyter notebook
###############################################################################

#import modules
import os
import sys
import re
from time import gmtime, strftime
import pandas as pd
from pandas.io.common import EmptyDataError
from urllib.error import URLError
#from exceptions import TypeError, KeyError
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('seaborn')
pd.options.mode.chained_assignment = None


#matplotlib settings
smallSize = 10
mediumSize = 12
biggerSize = 18

plt.rc('font', size = mediumSize)
plt.rc('axes', titlesize=biggerSize)
plt.rc('axes', labelsize=biggerSize)
plt.rc('xtick', labelsize=smallSize)
plt.rc('ytick', labelsize=smallSize)
plt.rc('legend', fontsize=smallSize)
plt.rc('figure', titlesize=biggerSize)

def read_data(url):
    try:
        df = pd.read_csv(url)
    except (EmptyDataError, URLError):
        df = pd.DataFrame()

    return df

#check user has entered valid dates and if not, terminate script execution
while True:
  if not len(sys.argv) == 5:
    sys.exit('You have entered the incorrect amount of arguments. You should enter the start date, the end date, the file path for the list of sites, and the list of weekdays you want to consider')
  break

while True:
  startDate = sys.argv[1]
  endDate = sys.argv[2]
  pattern = '^[0-3]\d{1}[0-1]\d{1}[0-2]\d{3}$'
  startTest = re.findall(pattern, startDate)
  endTest = re.findall(pattern, endDate)
  if not startTest:
    sys.exit('You have entered an incorrect start date, please check you have entered a valid date in the ddmmyyyy format')
  if not endTest:
    sys.exit('You have entered an incorrect end date, please check you have entered a valid date in the ddmmyyyy format')
  break

runTime = strftime('%Y-%m-%d %H:%M:%S', gmtime())
mainDir = os.getcwd()

#user defines desired start and end date in the format: ddmmyyyy, and the list of sites
startDate = sys.argv[1]
endDate = sys.argv[2]
sitesFileName = sys.argv[3]
days_list = sys.argv[4]

#convert days list-string to list
days_list = map(int, days_list.split(','))
days = [x-1 for x in days_list]

#read sites text file and extract list of site ID's to analyse. We do this with a regex
sitesFile = open(sitesFileName, 'r').read()
siteIdList = re.findall('\d+', sitesFile)

#Read WebTRIS API json to get site data into a df that we may want to extract
#information from for our basic site-by-site reporting
#for each site ID we can grab the Description, Lat, Long, Status and Name
sites = pd.read_json('http://webtris.highwaysengland.co.uk/api/v1.0/sites')
sites = pd.read_json((sites['sites']).to_json()).T
sites.set_index(['Id'], inplace=True)

siteNameList = []
meanDaysList = []
scriptResultList = []

#create directory to put all analyses
if not os.path.exists('WebTRIS Data'):
  os.makedirs('WebTRIS Data')

#begin analysing each site ID and producing outputs
for siteId in siteIdList:


  #this is used to jump back to this left once the for loop completes its first iteration and any after it
  os.chdir(mainDir + '\\WebTRIS Data')
  subDir = os.getcwd()
  if not os.path.exists('Site ' + siteId):
    os.makedirs('Site ' + siteId)
  os.chdir(subDir + '\\Site ' + siteId)

  #extract site details from the sites dataframe extract from WebTRIS API
  siteDesc = sites.at[siteId, 'Description']
  siteLat = sites.at[siteId, 'Latitude']
  siteLong = sites.at[siteId, 'Longitude']
  siteName = sites.at[siteId, 'Name']
  siteNameList.append(siteName)
  reportName = 'Site %s_TRADS Data Report.txt' % siteId
  introString = 'SiteID: %s\nDescription: %s\nLatitude: %s\nLongitude: %s\nName: %s' % (siteId, siteDesc, siteLat, siteLong, siteName)
  runTimeString = '%s script was ran at %s:' % (sys.argv[0], runTime)

  try:
  #read in the raw data for the site between the startDate and endDate specified at the start of the script. Save in site directory
      url = 'http://webtris.highwaysengland.co.uk/Report/DownloadReport?From=' + startDate + '&To=' + endDate + '&EnumReportType=1&SiteId=' + siteId + '&EnumReportSubType=0'
      rawData = read_data(url)

      if rawData.empty:
    #When our dataset is empty we report back a string to alert the user of this and print in report
        scriptResult = 'Sorry site %s has no data available.' % siteId
        scriptResultList.append(scriptResult)
        meanDaysList.append(0)

        #write data report
        with open(reportName, 'w') as reportFile:
          reportFile.write(introString + '\n')
          reportFile.write('\n' + runTimeString + '\n')
          reportFile.write('\nRaw Data Information:' + '\n')
          reportFile.write('\nSorry, this dataset has no data available.')

        print('Unforunately site %s has no valid counts for WebTAG neutral weekdays and neutral months' % siteId)

      else:
          rawData.to_csv('Site %s_Raw Data.csv' % siteId)

      #We don't need the speed bin columns, so we drop them. We also assume that if there is a NaN value that data was not being collected for this time period, so we drop it
      rawData.drop(rawData.loc[:,'0 - 10 mph':'80+ mph'].columns, axis=1, inplace=True)
      rawDataFinite = rawData[np.isfinite(rawData['0 - 520 cm'])]

      #We convert our report date to a datetime, and also extract the hour start, weekday, and
      #month for each observation
      rawDataFinite.loc[:,'Report Date'] = pd.to_datetime(rawDataFinite.loc[:,'Report Date'], format='%d/%m/%Y %H:%M:%S')
      rawDataFinite.loc[:,'Hour Start'] = pd.DatetimeIndex(rawDataFinite.loc[:,'Time Period Ending']).hour
      rawDataFinite.loc[:,'Weekday'] = pd.DatetimeIndex(rawDataFinite.loc[:,'Report Date']).weekday
      rawDataFinite.loc[:,'Month'] = pd.DatetimeIndex(rawDataFinite.loc[:,'Report Date']).month

      #get num of unique days per hour start
      rawDataDays = rawDataFinite.loc[:,['Report Date', 'Hour Start']].groupby('Hour Start').nunique()['Report Date']

      #Now we filter our data to gain a dataframe with only WebTAG neutral Weekdays and Months
      #These are Tues, Weds, Thurs for the months of March, April, May, June, September, October, and November
      #For references, Pandas datetime indices for weekdays are Monday = 0 to Sunday = 6
      filteredData = rawDataFinite[rawDataFinite.Weekday.isin(days) & rawDataFinite.Month.isin([3,4,5,6,9,10,11])]
      filteredData = filteredData.groupby(['Report Date', 'Hour Start']).sum()
      filteredData.reset_index(inplace=True)
      filteredData['Month'] = pd.DatetimeIndex(filteredData.loc[:,'Report Date']).month

      #This if-else occurs to cover cases when there is no data for neutral times. This happens when the result dataframe is essentially an array of zeroes. If this is NOT the case then we go on to clean our data and produce some basic analysis. If this is not the case then we simply log the site as lacking information for the time period of interest and moving to the next site in the list.
      if filteredData['Total Volume'].sum() != 0:

        #get num of unique days per hour start
        filteredDataDays = filteredData.loc[:,['Report Date', 'Hour Start']].groupby('Hour Start').nunique()['Report Date']

        #now we begin the cleaning process by finding the interquartile range and creating an interval of 1.5*IQR above UQ and 1.5*IQR below LQ
        #anything outside of this interval is excluded from further analysis
        df1 = filteredData[['Report Date', 'Hour Start', 'Total Volume']]
        low = 0.25 #lower quartile
        high = 0.75 #upper quartile
        res = df1.groupby('Hour Start')['Total Volume'].quantile([low, high]).unstack(level=1) #Table of the upper and lower 5% percentiles for each time interval
        res['IQR'] = res.loc[:,0.75] - res.loc[:,0.25]
        res['high'] = res.loc[:,0.75] + 1.5 * res.loc[:,'IQR']
        res['low'] = res.loc[:,0.25] - 1.5 * res.loc[:,'IQR']

        #cleaned data by removing counts that exceed these bounds derived above
        cleanedData = filteredData.loc[((res.loc[filteredData['Hour Start'], 'low'] < filteredData['Total Volume'].values)
                        & (filteredData['Total Volume'].values < res.loc[filteredData['Hour Start'], 'high'])).values]

        #get num of unique days per hour start
        cleanedDataDays = cleanedData.loc[:,['Report Date', 'Hour Start']].groupby('Hour Start').nunique()['Report Date']

        #Plot to check cleaned vs uncleaned data
        fig1, axs1 = plt.subplots(2,1, sharex=True)
        filteredData.groupby(['Hour Start', 'Report Date'])['Total Volume'].sum().unstack().plot(legend=False, figsize=(14,12), ax=axs1[0], alpha=0.5, title='Uncleaned Data', xticks=range(0,25,1))
        axs1[0].titlesize = 20
        #plt.suptitle('Site %s\nCleaned vs. Uncleaned Data' % siteId)
        df3 = cleanedData[['Report Date', 'Hour Start', 'Total Volume']]
        df3.groupby(['Hour Start', 'Report Date']).sum().unstack().plot(legend=False, figsize=(14,12), ax=axs1[1], alpha=0.5, title='Cleaned Data')
        axs1[0].set_ylabel('Hourly Flow Count')
        axs1[1].set_ylabel('Hourly Flow Count')
        plt.savefig('Site %s_Cleaned vs Uncleaned Comparison.png' % siteId)
        plt.clf()
       

        #Create dataframe averaging over the days available to give counts for each hour start, also calc median and max
        cleanedDataDaily = cleanedData.drop(cleanedData.loc[:,['Report Date', 'Time Interval', 'Avg mph', 'Weekday', 'Month']].columns, axis=1)
        cleanedDataDailyGrouped = cleanedDataDaily.groupby('Hour Start')
        cleanedDataMean = cleanedDataDailyGrouped.mean()
        cleanedDataStd = cleanedDataDailyGrouped.std()
        cleanedDataQuartiles = cleanedDataDailyGrouped.quantile([0, 0.25, 0.50, 0.75, 1]).unstack()

        #Create dataframe same as above but with for each month available and find the daily averages per month for each hour start
        cleanedDataAvgDayPerMonth = cleanedData.drop(cleanedData.loc[:,['Report Date', 'Time Interval', 'Avg mph', 'Weekday']].columns, axis=1)
        cleanedDataAvgDayPerMonth = cleanedDataAvgDayPerMonth.groupby(['Month', 'Hour Start']).mean()

        #Create 3 plots, a boxplot of the filtered data by hour, a plot per month, and a plot per mode
        ax = filteredData.boxplot('Total Volume', by='Hour Start', figsize=(20,14),
                             showmeans=True)
        #plt.suptitle('Site %s\nAll Vehicle Sample Boxplot' % siteId)
        ax.set_title('')
        ax.set_ylabel('Vehicle Flow')
        ax.set_xlabel('Hour Beginning')
        plt.savefig('Site %s_All Vehicle Sample Boxplot.png' % siteId)
        plt.clf()     
		

        ax = cleanedDataAvgDayPerMonth.unstack(level=0)['Total Volume'].plot(legend=True,
                                              figsize=(20,14), colormap='Accent',
                                              xticks=range(0,24,1))
        #plt.suptitle('Site %s\nAll Vehicle Flow by Month' % siteId)
        ax.set_ylabel('Vehicle Flow')
        ax.set_xlabel('Hour Beginning')
        plt.savefig('Site %s_All Vehicle Flow by Month.png' % siteId)
        plt.clf()       

        ax = cleanedDataMean.plot(legend=True, figsize=(20,14), colormap='Accent',
                                  xticks=range(0,24,1))
        #plt.suptitle('Site %s\nVehicle Flow by Length' % siteId)
        ax.set_ylabel('Vehicle Flow')
        ax.set_xlabel('Hour Beginning')
        plt.savefig('Site %s_Vehicle Flow by Length.png' % siteId)
        plt.clf()      

        #rename col heading in each table before concatenating
        cleanedDataMean.columns = pd.MultiIndex.from_tuples([(i, 'Mean') for i in cleanedDataMean.columns])
        cleanedDataStd.columns = pd.MultiIndex.from_tuples([(i, 'Std Dev') for i in cleanedDataStd.columns])
        quartileNames = ['Min', 'Lower Quartile', 'Median', 'Upper Quartile', 'Max']
        cleanedDataQuartiles.columns.set_levels(quartileNames, level=1, inplace=True)

        #lastly create a modeshare dataframe to add into the concat
        cleanedDataModeShare = cleanedDataMean.copy(deep=True)
        cleanedDataModeShare['0 - 520 cm'] = cleanedDataModeShare['0 - 520 cm'].div(cleanedDataModeShare['Total Volume'])
        cleanedDataModeShare['521  - 660 cm'] = cleanedDataModeShare['521  - 660 cm'].div(cleanedDataModeShare['Total Volume'])
        cleanedDataModeShare['661 - 1160 cm'] = cleanedDataModeShare['661 - 1160 cm'].div(cleanedDataModeShare['Total Volume'])
        cleanedDataModeShare['1160+ cm'] = cleanedDataModeShare['1160+ cm'].div(cleanedDataModeShare['Total Volume'])
        
        del cleanedDataModeShare['Total Volume']
		
        cleanedDataModeShare.columns = pd.MultiIndex.from_tuples([(i, 'Mean Mode Share (%)') for i in
                                                                 cleanedDataModeShare.columns])

        cleanedDf = pd.concat([cleanedDataMean, cleanedDataStd, cleanedDataQuartiles,
                               cleanedDataModeShare], axis=1)
        cleanedDf = cleanedDf[['0 - 520 cm', '521  - 660 cm', '661 - 1160 cm', '1160+ cm',
                     'Total Volume']]

        #Export cleaned dataset and report to the console that the site has been analysed
        cleanedDf.to_csv('Site %s_Hourly Output Data.csv' % siteId)

        scriptResult = 'Site %s has been processed successfully!' % siteId
        print(scriptResult)
        #Calc mean days in final dataset to assess the mean number of days available per hour start to print to a CSV
        meanDays = round(cleanedDataDays.mean(), 0)
        meanDaysList.append(meanDays)
        scriptResultList.append(scriptResult)

        #write the data report
        with open(reportName, 'w') as reportFile:
          reportFile.write(introString + '\n')
          reportFile.write('\n' + runTimeString + '\n')
          reportFile.write('\nRaw Data Information:' + '\n')
          for index in rawDataDays.index:
            reportFile.write('\tSample size for hour %d is %d days. \n' % (index, rawDataDays[index]))
          reportFile.write('\nThe counts at this site have been filtered so that they comply with WebTAG guidance on sampling data only from "neutral" weekdays and months.\nA "neutral" weekday is either Tuesday, Wednesday or Thursday, and a "neutral" month is either March, April, May, June, September, October or November.' )
          reportFile.write('\nFiltered Data Information:' + '\n')
          for index in filteredDataDays.index:
            reportFile.write('\tSample size for hour %d is %d days. \n' % (index, filteredDataDays[index]))
          reportFile.write('\nTo clean up the data we identify outliers and discard them. The interval on which we accept data points is the real interval (LQ - 1.5*IQR, UQ + 1.5*IQR). \nConsequently any data point exceeding these limits is dropped from the records.')
          reportFile.write('\nCleaned Data Information:' + '\n')
          for index in cleanedDataDays.index:
            reportFile.write('\tSample size for hour %d is %d days. \n' % (index, cleanedDataDays[index]))

      else:
        #When our dataset is empty we report back a string to alert the user of this and print in report
        scriptResult = 'Sorry site %s has no data available for WebTAG neutral weekdays and neutral months. Please check the raw data to confirm that this is the case.' % siteId
        scriptResultList.append(scriptResult)
        meanDaysList.append(0)

        #write data report
        with open(reportName, 'w') as reportFile:
          reportFile.write(introString + '\n')
          reportFile.write('\n' + runTimeString + '\n')
          reportFile.write('\nRaw Data Information:' + '\n')
          for index in rawDataDays.index:
            reportFile.write('\tSample size for hour %d is %d days. \n' % (index, rawDataDays[index]))
          reportFile.write('''\nSorry, this dataset has no data available for WebTAG neutral weekdays and neutral months.\nPlease check the raw data to confirm that this is the case.''')

        print('Unforunately site %s has no valid counts for WebTAG neutral weekdays and neutral months' % siteId)

  except (TypeError, KeyError):
        print('Site %s encountered a type error, and processing has been skipped. Raw data is still downloaded' % siteId)
        scriptResult = 'We encountered a type error for site %s' % siteId
        scriptResultList.append(scriptResult)
        meanDaysList.append(0)

        with open(reportName, 'w') as reportFile:
            reportFile.write(introString + '\n')
            reportFile.write('\n' + runTimeString + '\n')
            reportFile.write('\nRaw Data Information:' + '\n')
            for index in rawDataDays.index:
                reportFile.write('\tSample size for hour %d is %d days. \n' % (index, rawDataDays[index]))
            reportFile.write('This site encountered a type error and data processing cannot be completed.')
  plt.close('all')

print('All sites have been processed!')

#write csv file that reports on results of script for each site
os.chdir(mainDir)
receiptList = ['Site ID,Site Name,Script Result,Mean Days in Sample']
for i in range(0,len(siteIdList)):
  receiptListLine = ','.join([siteIdList[i], siteNameList[i], scriptResultList[i], str(meanDaysList[i])])
  receiptList.append(receiptListLine)
receiptContents = '\n'.join([line for line in receiptList])
with open('WebTRIS Data Analysis Script Receipt.csv', 'w') as f:
  f.write(receiptContents)
