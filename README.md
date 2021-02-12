
# WebTRIS Processing

Automated download, filtering and processing of WebTRIS data from Highways England. 

## Instructions

Before using this tool please review the accompanying Jupyter notebook [WebTRIS_Analysis_Example.html](WebTRIS Analysis Example.html) to ensure you understand how the WebTRIS data is being processed. The notebook steps through the filtering, cleaning and analysis steps performed by the script.

Run [get_sites.py](get_sites.py) to get All_Sites.csv to obtain the latest list of sites from the API.
Plot this in GIS and select the subset of sites you want data for. Put the values in the ID column into a text file, preferably CSV.

Run script [WebTRIS_Analysis_v1.5.py](WebTRIS_Analysis_v1.5.py) in the command prompt and pass the following four arguments:

* Start date (ddmmyyyy)
* End date (ddmmyyyy)
* Sites list file, this is the name of the file that you put the IDs in.
* Days list, days selected for the analysis, numbered 1 = Monday to 7 = Sunday. Must be typed as 1,2,3,4 i.e no spaces
		
The below example will download and process WebTRIS data for all site ids in the sites.csv, looking only at Tuesday-Thursday for the month of March 2017.

```
python WebTRIS_Analysis_v1.5.py 01032017 01042017 sites.csv 2,3,4

python WebTRIS_Analysis_v1.5.py 01022018 01072018 northern_sites.csv 2,3,4

python WebTRIS_Analysis_v1.5.py 01012018 31122018 northern_sites.csv 1,2,3,4,5,6,7

```
## Process

* Download raw data from the internet (All days, hours in sample specified)
* Filter to get WebTAG neutral weekdays and months (All neutral weekdays and months). What are these?
* If there is no data left after this filtering, analysis of the site stops there. 
* If there is data then we clean the data to removes outliers using 'Tukey's Fences' method:

$`{\big [}Q_{L}-k(Q_{U}-Q_{L}),Q_{U}+k(Q_{U}-Q_{L}){\big ]}, k \in R_{\ge 0}`$

where $`k = 1.5`$ and $`Q_{L}`$ and $`Q_{U}`$ are the lower and upper quartiles respectively.

* Cleaning is performed on hourly data (each hour is made out of 4 time 'intervals')
* For each hour, we the extract statistics such as mean, std, quartiles (Cleaned data for neutral weekdays and months)
* This final hourly data averages the cleaned data across the neutral weekdays in the sample.


## Output

* CSV file containing the raw downloaded data.
* Hourly analysed Data (just high level stats, by vehicle length); This is the average for each hour across days, following filtering and cleaning.
* Plot of cleaned vs uncleaned data.
* Boxplot for each hour to understand variability (UNCLEANED)
* Plot of mean flow per month
* Plot of mean flow per vehicle length
* Data Report which shows how the number of days in the sample (for each hour) decreases during the filtering and cleaning process.

## Current limitations

* Incompatible with data from 2014 and older.

## Prerequisites

What things you need to install the software and how to install them

```
Python 3
```

## Versioning

We use [SemVer](http://semver.org/) for versioning.

## Authors

* **Michael Addyman** - *Initial work* - *Atkins*
* **Alex Harrison** - *Further development* - *Atkins*
