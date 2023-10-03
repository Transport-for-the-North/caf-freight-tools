# Introduction

This document is provided as a user guide for installing and running the Local Freight Tool.
The Local Freight Tool provides a variety of functionality for developing HGV and LGV freight
demand matrices for model integration.

The document is split into the following sections:

- [Tool Location](#tool-location): describes where the Local Freight tool can be obtained from;
- [Installation](#installation): covers the requirements for the tool and how to install them;
- [Running Local Freight Tool](#running-local-freight-tool): covers information on how to run the tool; and
- [Tool Functionality](#tool-functionality): outlines all the functionality provided by the tool
  and provides information on how to run each module, including any required inputs and the
  expected outputs.

# Tool Location

The source code for the Local Freight tool is available on the [TfN-Freight-Tools](
  https://github.com/Transport-for-the-North/TfN-Freight-Tools) GitHub repository. For just running
the tool the required version can be selected by using the dropdown menu to select a branch then
clicking on the "Code" button and downloading the zip file. In order to edit the tool the GitHub
repository should be cloned, see [GitHub guide about remote repositories](
  https://docs.github.com/en/github/getting-started-with-github/about-remote-repositories).

Once the zip file has been downloaded it should be unzipped to the local machine then the
requirements should be installed using the instructions in the [Installation section](#installation).
When all the requirements are installed the Local Freight tool can be run following the steps
outlined in the [Running section](#running-local-freight-tool).

# Installation

Installation of the Local Freight Tool requires Anaconda (or Miniconda) to be installed, which
can be downloaded from [Anaconda.org](https://www.anaconda.com/products/individual#Downloads)
(or [Miniconda's website](https://docs.conda.io/en/latest/miniconda.html)). Once Anaconda has
been installed it can be used to install the Python requirements (listed in
[Packages Required](#packages-required) section) for running the tool.

## Creating conda Environment

A batch file has been supplied with the tool which will automatically install all the
Python requirements, this is called `install_tool.bat` and is found within the local_freight_tool
folder. Run `install_tool.bat` by double-clicking on it, if this is unsuccessful the requirements
can be installed with the following steps:

- Open Anaconda Prompt, accessible from Start Menu or Windows search, and navigate to the
  local_freight_tool directory.
- Create a new conda environment with `conda env create -f environment.yml`, use `y` to proceed
  if required.

## Packages required

The Python packages required by the Local Freight Tool are as follows (detailed version
information can be found in [environment.yml](environment.yml) which is provided with the
Python files):

- PyQT;
- Pandas;
- Openpyxl;
- markdown;
- jinja2;
- packaging; and
- pyyaml.

# Running Local Freight Tool

Another batch file has been created to simplify the steps for running the tool, this file is
called `run_tool.bat` and can be found with the Python files in the local_freight_tool folder.
The tool can be launched by double clicking on `run_tool.bat`, if this is unsuccessful then it
can be launched with the following steps:

- Use Anaconda Prompt to navigate to the local_freight_tool directory;
- Activate the conda environment using `conda activate freighttool`; and
- Launch the menu using `python -m LFT`.

*Tip: start writing the file name and press tab, the command prompt will autocomplete it for you.
For more information on the command prompt see [Command Prompt cheat sheet](
  http://www.cs.columbia.edu/~sedwards/classes/2017/1102-spring/Command%20Prompt%20Cheatsheet.pdf).*

## CAF Space

Some of the modules within LFT require zone correspondence files as inputs to translate between
zoning systems. The recommended method for creating these is using TfN's
[caf.space](https://github.com/Transport-for-the-North/caf.space) Python package. CAF space is
available on PyPi and can be installed with `pip install caf.space`.

CAF Space provides functionality for generating standard weighting translations in .csv format
describing how to convert between different zoning systems. The default output format of CAF space
is the correct format for any zone correspondence files required within LFT

# Tool Functionality

This section outlines the functionality provided in the tool, this functionality is split across
a number of modules which can be accessed from the main menu. The main menu of the tool is shown
in the image below, it is split into the following three sections:

- Pre-Processing: this section contains functionality for getting time period inputs ready
  for the HGV conversion processes.
- Conversion: this sections provides the main modules for producing HGV and LGV demand matrices.
- Utilities: this section contains a variety of utility functions that can perform many matrix
  calculations, demand forecasting and cost conversion.

![Local Freight Tool main menu](doc/images/main_menu.PNG "Local Freight Tool main menu")

## Time Profile Builder

This module is used to produce the time profile selection to be used as an input in the
[HGV Annual PCU to Model Time Period PCU](#hgv-annual-pcu-to-model-time-period-pcu) conversion. It
enables the user to set up to seven different time profiles, including the name of the profile,
days to use, the time period start and end hours, and the months. The months selected are used for
all time profiles. The profile builder menu is shown below.

![Profile Builder GUI](doc/images/profile_builder_menu.PNG "Profile Builder GUI")

The user is expected to enter a name for the time period selection. The days and time periods have
default values which can be changed by selecting the relevant checkboxes and drop down menus. To
create the selected profiles, the user must click 'Save Selection'. A warning appears when the time
periods selected do not add up to 24 hours. The output is summarised in the table below.

Table: Time Profile Builder output

| Name              | Type | Columns  | Description                                                        |
| ----------------- | ---- | -------- | ------------------------------------------------------------------ |
|                   |      | name     | Name of the time profile                                           |
|                   |      | days     | Days of the week in time profile.                                  |
| Profile_Selection | CSV  | hr_start | Start hour of time profile                                         |
|                   |      | hr_end   | End hour of time profile                                           |
|                   |      | months   | Months for all time profiles (this column is the same in all rows) |

## HGV Annual Tonne to Annual PCU Conversion

The HGV Annual Tonne to Annual PCU Conversion module enables the split and conversion of GBFM HGV
annual tonnage matrices into rigid and articulated annual PCU matrices. The interface is shown below.

![Annual Tonne to Annual PCU GUI](doc/images/tonne_to_pcu_menu.PNG "Annual Tonne to Annual PCU GUI")

The conversion and splitting process is based on the specification proposed by Ian Williams in the
technical note "Separating Rigid from Artic HGVs"[^separating_rigid_artic]. The process is detailed
in the flowchart below.

[^separating_rigid_artic]: Ian Williams. 035 Separating Rigid from Artic HGVs, v1.0. February 2021.

![Annual Tonne to Annual PCU flowchart](doc/images/module_3_flowchart.png "Annual Tonne to Annual PCU flowchart")

The inputs and outputs of the process are outlined in the following tables.

Table: Inputs for HGV annual tonne to annual PCU conversion module

| Input                                          | Type | Description                                                                                                                                              | Required columns                                                                           | Required rows                                                                         |
| ---------------------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Domestic and bulk port matrix                  | CSV  | Base year domestic and bulk-port traffic                                                                                                                 | Origin, destination, trips, column names are optional but columns must be in correct order | N/A                                                                                   |
| Unitised EU imports matrix                     | CSV  | Annual imported tonnes from GB ports to inland GBFM zones for unitised (non-bulk) trade to GB from European countries (including the island of Ireland)  | Origin, destination, trips, column names are optional but columns must be in correct order | N/A                                                                                   |
| Unitised EU exports matrix                     | CSV  | Annual exported tonnes from inland GBFM zones to GB ports for unitised (non-bulk) trade from GB to European countries (including the island of Ireland); | Origin, destination, trips, column names are optional but columns must be in correct order | N/A                                                                                   |
| Unitised non-EU imports and exports matrix     | CSV  | Annual tonnes between GB ports and inland GBFM zones for unitised (non-bulk) trade between GB and non-European countries                                 | "Imp0Exp1", "GBPortctr", "GBRawZone", "Traffic"                                            | N/A                                                                                   |
| Ports lookup                                   | CSV  | Shows lookup between GBPortctr and GBFM zones                                                                                                            | "GBPortctr", "GBZone"                                                                      | All ports in the unitised non-EU imports and exports matrix                           |
| Vehicle trips per 1000 tonnes by distance band | CSV  | Artic/rigid factors to apply for each trip distance per 1000 tonnes                                                                                      | "start", "end", "rigid", "artic"                                                           | N/A                                                                                   |
| GBFM distance matrix                           | CSV  | GBFM distance skim                                                                                                                                       | Origin, destination, trips, column names are optional but columns must be in correct order | All GBFM zones in domestic and bulk port matrix                                       |
| Port traffic trips per 1000 tonnes file        | CSV  | Articulated and rigid port traffic trip factors                                                                                                          | "type", "direction", "accompanied", "artic", "rigid"                                       | Factors for bulk traffic in both directions, and unitised traffic import and exports. |
| PCU factors                                    | CSV  | Articulated and rigid tonne to PCU factors to apply                                                                                                      | "zone", "direction", "artic", "rigid"                                                      | Row with default artic and rigid values                                               |

Table: Outputs for HGV annual tonne to annual PCU conversion module

| Output                  | Type | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ----------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| artic_total_annual_pcus | CSV  | Annual articulated PCUs csv with columns "origin", "destination" and "trips"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| rigid_total_annual_pcus | CSV  | Annual rigid PCUs csv with columns "origin", "destination" and "trips"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Tonne_to_pcu_log        | XLSX | Log of the process, containing a list of inputs provided, processes completed, errors if they occurred, and a summary of matrix statistics. Contains the following sheets:<br>- `process`: indicates which processes completed and any errors that occurred;<br>- `inputs`: a list of all the input files<br>- `matrix_summaries`: summaries of the four input HGV matrices, the rigid and articulated total annual trip matrices, and the rigid and articulated total annual PCU matrices<br>- `distance_bands`: the distance bands used<br>- `port_traffic`: the port traffic factors used<br>- `pcu_factors`: the PCU factors used |

## HGV Annual PCU to Model Time Period PCU

This module converts the articulated and rigid matrices (created by [HGV Annual Tonne to
Annual PCU Conversion](#hgv-annual-tonne-to-annual-pcu-conversion) from annual PCUs to model time
period PCUs, based on the time periods defined by [Time Profile Builder](#time-profile-builder).

![Annual PCU to Model Time Period PCU Menu](doc/images/annual_to_time_period_menu.png "Annual PCU to Model Time Period PCU Menu")

![Flowchart showing the Annual PCU to Time Period methodology](doc/images/annual_to_time_period-flowchart.png "Flowchart showing the Annual PCU to Time Period methodology")

This process requires the annual PCU matrices and time period information as inputs (more details
in the inputs table below) and produces the time period articulated, rigid and combined matrices
as well as a log spreadsheet summarising the process (more details in the outputs table below). The
log spreadsheet provides a summary of the calculations and the output matrices, **these tables
should all be checked in detail before using the outputs**, in order to assist with checking the
matrix summaries have been highlighted red or green to outline where more detailed checks are needed.

***Note:** Even if the matrix summaries are all highlighted green some manual checks should still be
undertaken to make sure the outputs have been checked to an appropriate level depending on the use
case.*

Table: Inputs for the HGV annual PCU to model time period PCU module

| Input                          |      Type      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| :----------------------------- | :------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HGV Distributions              | Excel Workbook | Spreadsheet containing the DfT road traffic statistics (TRA) tables required for calculating the time period factors, should contain the following sheets:<br>- TRA3105: the HGV road type distributions with columns Road Type, Rigid, Articulated and All HGVs;<br>- TRA0305: the monthly distributions for HGV and road types with columns Road Type, Month and HGV; and<br>- WEEKLY PROFILE: weekly distributions for articulated and rigid should contain columns Road Type, Time and an articulated and rigid column for each day.<br> *This spreadsheet is available on TfN's U drive.* |
| Time Periods Profiles          |      CSV       | Time period definitions file, created by module 2, should contain the following columns:<br>- name: the name of the time period (used when labelling output matrices);<br>- days list of the selected days as numbers (0 - 6) e.g. [0, 1, 2, 3, 4] for all weekdays;<br>- hr_start: the starting hour of the time period, should be a number (0 - 23 inclusive);<br>- hr_end: the ending hour of the time period, should be a number (0 - 23 inclusive); and<br>- months: the month number (0 - 11 inclusive) as a list e.g. [0, 1, 3] to select January, February and April.                  |
| Model Year                     |    Integer     | Base year of the model, used for calculating the average number of weeks in a month during the time period conversions.                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Articulated Annual PCUs Matrix |      CSV       | Annual PCU matrix for the articulated HGVs created by module 4, should contain the following columns: origin, destination and trips, column names are optional but columns must be in correct order.                                                                                                                                                                                                                                                                                                                                                                                           |
| Rigid Annual PCUs Matrix       |      CSV       | Annual PCU matrix for the rigid HGVs created by module 4, should contain the following columns: origin, destination and trips, column names are optional but columns must be in correct order.                                                                                                                                                                                                                                                                                                                                                                                                 |
| Output Folder                  |      Text      | Path to the existing folder to save the outputs to.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |

Table: Outputs from the HGV annual PCU to model time period PCU module

| Output                                                                           |      Type      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| :------------------------------------------------------------------------------- | :------------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `time_period_conversion_log`                                                     | Excel Workbook | Spreadsheet summarising the inputs, intermediary steps and statistics for the output matrices, contains the following sheets:<br>- Notes: brief description of spreadsheet;<br>- Input Parameters: list of all the input parameters provided;<br>- Monthly Avg Profile: weighted average monthly HGV distribution;<br>- Weekly Avg Profile: weighted average weekly (and hourly) HGV distribution;<br>- Time Period Factors: summary of the input time periods and the calculated factors for each; and<br>- Matrix Summaries: summary statistics for each of the output matrices, highlighted to assist with checking. |
| `{time period}_intermediate/{time period}_HGV_artic-{original zone system name}` |      CSV       | Time period PCUs matrix for articulated HGVs **before** rezoning to new zone system, contains origin, destination and trips columns.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `{time period}_intermediate/{time period}_HGV_artic-{rezoned zone system name}`  |      CSV       | Time period PCUs matrix for articulated HGVs **after** rezoning to new zone system, contains origin, destination and trips columns.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `{time period}_intermediate/{time period}_HGV_rigid-{original zone system name}` |      CSV       | Time period PCUs matrix for rigid HGVs **before** rezoning to new zone system, contains origin, destination and trips columns.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `{time period}_intermediate/{time period}_HGV_rigid-{rezoned zone system name}`  |      CSV       | Time period PCUs matrix for rigid HGVs **after** rezoning to new zone system, contains origin, destination and trips columns.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `{time period}_HGV_combined-{rezoned zone system name}`                          |      CSV       | Time period PCUs matrix for **both vehicle types** (articulated + rigid) **after** rezoning to the new zone system, contains origin, destination and trips columns.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

## LGV Model

This module contains the functionality for running the LGV model which includes calculating trip
ends, using a gravity model to generate annual trip matrices and converting the annual matrices to
time periods. The interface is shown below. The methodology of the LGV model is based on Ian Williams'
technical note "LGVN Model Design"[^lgvn_design].

[^lgvn_design]: Ian Williams. 030 LGVN Model Design, v4.0. July 2021.

![LGV Model GUI](doc/images/lgv_model_menu.PNG "LGV Model GUI")

The following sections contain detailed information on the expected inputs and outputs, as well as
some information on the methodology for the LGV model.

### LGV Model Inputs

The LGV model has a number of input files which can be provided in the GUI, or via a configuration
file (example below). This section details all of the input files which are needed in order to run
the LGV model.

To run the LGV model with a configuration file it needs to be ran from command line. The command
for running it is **`python -m LFT.lgv_model -c "path/to/config.yml"`**, this command should be ran
from the Anaconda prompt after activating the environment (see
[Running Local Freight Tool](#running-local-freight-tool) for more information). An example of the
configuration file is shown below.

***Note:** help text for running the tool through the command line can be seen with
`python -m LFT.lgv_model -h` and an example config file can be created with the command
`python -m LFT.lgv_model -e`.*

```yaml
household_paths:
  name: LGV Households
  path: CSV of households data
  zc_path: Zone correspondence CSV
bres_path: Path to the BRES data CSV at LSOA level
warehouse_path: Path for the warehouse floorspace data CSV at LSOA level
commute_warehouse_paths:
  medium: CSV of LSOA warehouse floorspace for commute segment (medium weighting),
    required
  low: CSV of LSOA warehouse floorspace for commute segment (low weighting), optional
  high: CSV of LSOA warehouse floorspace for commute segment (high weighting), optional
parameters_path: Path to parameters spreadsheet
qs606ew_path: Path to the England & Wales Census Occupation data CSV
qs606sc_path: Path to the Scottish Census Occupation data CSV
sc_w_dwellings_path: Path to the Scottish and Welsh dwellings data CSV
e_dwellings_path: Path to the English dwellings data XLSX
ndr_floorspace_path: Path to the NDR Business Floorspace CSV.
lsoa_lookup_path: Path to the LSOA to model zone correspondence CSV
msoa_lookup_path: Path to the MSOA to model zone correspondence CSV
lad_lookup_path: Path to the Local Authority District to model zone correspondence CSV
model_study_area: Path to CSV containing lookup for zones in model study area
cost_matrix_path: Path to CSV containing cost matrix, should be square matrix with
  zone numbers as column names and indices
calibration_matrix_path: Path to CSV containing calibration matrix, should be square
  matrix with zone numbers as column names and indices
trip_distributions_path: Path to Excel Workbook containing all the trip cost distributions
output_folder: Path to folder to save outputs to
```

#### Household Projections & Zone Correspondence

UK households projections for the model year at MSOA level, data can be extracted from TEMPro. This
data should contain the number of households per MSOA for the model year. The data extracted from
TEMPro contains a number of columns only two of which are required for the model, these are
summarised in the table below, any additional columns are ignored. This data should be provided in
a comma-separated values (CSV) file.

Table: Required columns for the UK household projections data

|   Column Name    | Data Type | Description                                                |
| :--------------: | :-------: | :--------------------------------------------------------- |
| Area Description |   Text    | MSOA area code e.g. E02003616                              |
|       HHs        |   Real    | The number of households projected to be in that MSOA zone |
|       Jobs       |   Real    | The number of jobs projected to be in that MSOA zone       |

In addition to the households data the model also requires a zone correspondence file which provides
the lookup between the MSOA and the model zones, the correspondence file requires three columns which
are summarised in the table below. The zone correspondence file can be created using CAF.Space.

Table: Required columns for the UK household zone correspondence, column names are ignored the
columns just need to be in the correct order.

| Column | Data Type | Description                         |
| :----: | :-------: | :---------------------------------- |
|   1    |   Text    | MSOA area code e.g. E02003616       |
|   2    |  Integer  | Corresponding model zone ID         |
|   3    |   Real    | Splitting factor for correspondence |

#### BRES Data

The Business Register and Employment Survey (BRES) is available from [NOMIS](https://www.nomisweb.co.uk/datasets/newbres6pub)
and contains the number of employees for different industrial sectors at LSOA (Scottish data zone)
level, at time of writing the data is provided up to 2019. The LGV model requires the data to be
extracted for all LSOAs (England and Wales) and data zones (Scotland) at the model year, all broad
industrial groups and all employees should be included in the output.

The model expects the file to be saved as a comma-separated values (CSV) file with the first eight
rows used for meta data and the column names on row nine, all required columns are listed in the
table below. The BRES data is expected to be provided at LSOA level, the LSOA zone correspondence
file discussed in [Other Zone Correspondences](#other-zone-correspondences) will be used to
translate the BRES data to the model zone system.

Table: Required columns for the BRES data, column names must be exactly as listed. Any columns not
listed will be ignored.

| Column Name                                                                                                                  | Data Type | Description                                |
| :--------------------------------------------------------------------------------------------------------------------------- | :-------: | :----------------------------------------- |
| Area                                                                                                                         |   Text    | Description/name of area type              |
| mnemonic                                                                                                                     |   Text    | Data zone or LSOA area code                |
| A : Agriculture, forestry and fishing                                                                                        |   Real    | Number of employees for this industry type |
| B : Mining and quarrying                                                                                                     |   Real    | Number of employees for this industry type |
| C : Manufacturing                                                                                                            |   Real    | Number of employees for this industry type |
| D : Electricity, gas, steam and air conditioning supply                                                                      |   Real    | Number of employees for this industry type |
| E : Water supply; sewerage, waste management and remediation activities                                                      |   Real    | Number of employees for this industry type |
| F : Construction                                                                                                             |   Real    | Number of employees for this industry type |
| G : Wholesale and retail trade; repair of motor vehicles and motorcycles                                                     |   Real    | Number of employees for this industry type |
| H : Transportation and storage                                                                                               |   Real    | Number of employees for this industry type |
| I : Accommodation and food service activities                                                                                |   Real    | Number of employees for this industry type |
| J : Information and communication                                                                                            |   Real    | Number of employees for this industry type |
| K : Financial and insurance activities                                                                                       |   Real    | Number of employees for this industry type |
| L : Real estate activities                                                                                                   |   Real    | Number of employees for this industry type |
| M : Professional, scientific and technical activities                                                                        |   Real    | Number of employees for this industry type |
| N : Administrative and support service activities                                                                            |   Real    | Number of employees for this industry type |
| O : Public administration and defence; compulsory social security                                                            |   Real    | Number of employees for this industry type |
| P : Education                                                                                                                |   Real    | Number of employees for this industry type |
| Q : Human health and social work activities                                                                                  |   Real    | Number of employees for this industry type |
| R : Arts, entertainment and recreation                                                                                       |   Real    | Number of employees for this industry type |
| S : Other service activities                                                                                                 |   Real    | Number of employees for this industry type |
| T : Activities of households as employers;undifferentiated goods-and services-producing activities of households for own use |   Real    | Number of employees for this industry type |
| U : Activities of extraterritorial organisations and bodies                                                                  |   Real    | Number of employees for this industry type |

#### Warehouse Data

Warehouse floorspace area data is used for calculating trip ends for the delivery and commute
segments. The warehouse floorspace data used by Transport for the North is aggregated from
Ordnance Survey's Address Base Premium and Master map data, the methodology for which is outlined
in the Local Freight Tool - Warehouse Data technical note[^warehouse_data].

[^warehouse_data]: Local Freight Tool - Warehouse Data Technical Note (April - May 2023)

The following four warehouse floorspace input files are required (all at LSOA zoning):

- Warehouse floorspace for delivery stem productions, required
- Warehouse floorspace for attracting LGV commuting drivers
  - Medium relevance floorspace, required
  - High relevance floorspace, optional
  - Low relevance floorspace, optional

All the warehouse floorspace input files are in the same format, they should be a CSV file with
two columns, as defined in the table below.

Table: Column definitions for the warehouse floorspace input files.

| Column Name | Data Type | Description   |
| :---------- | :-------: | :------------ |
| LSOA11CD    |   Text    | LSOA zone ID. |
| area        |   Real    | Total warehouse floorspace for the LSOA ($m^2$). |

***Note: *any missing LSOAs are assumed to have zero floorspace.***

#### LGV Parameters Spreadsheet

This input should be an Excel spreadsheet containing a variety of sheets with different parameters
for the LGV model. Each of the required sheets in this input file are discussed in the following
sections.

##### Parameters

The sheet named "Parameters" should contain two columns with the headers "Parameter" and "Value".
The following table gives the names of the parameters and a description of what value should be
provided.

Table: Required parameters for the LGV model, parameters must be labelled exactly as given.

| Parameter              |  Data Type   | Description                                                                   |
| :--------------------- | :----------: | :---------------------------------------------------------------------------- |
| LGV growth             |     Real     | A factor to increase the LGV trips from the van survey year to the model year |
| Average new house size |     Real     | The average new house size in $m^2$                                           |
| Scotland SOC821/SOC82  | Real (0 - 1) | The proportion of SOC821 occupations in the SOC82 segment                     |
| Model Year             |   Integer    | The model year e.g. 2018                                                      |

##### Commute Trips by Main Usage

The sheet named "Commute trips by main usage" should contain the annual number of commute van trips
from the van survey by usage type. The following usage types should be included:

- G: Carryings goods
- S: Service / trades
- C: Commuting
- T: Carrying people
- O: Other

This sheet should have two columns with the headers in the first row, the table below lists the
columns.

Table: Required columns for the commute trips by main usage sheet.

| Column Name |   Data Type   | Description                                                  |
| :---------- | :-----------: | :----------------------------------------------------------- |
| Main usage  | Character (1) | Usage code for each of the types listed above                |
| Trips       |     Real      | The annual number of commuting LGV trips for that usage type |

##### Commute Trips by Land Use

The sheet named "Commute trips by land use" should contain the annual number of commute van trips
from the van survey by land use type. The following land uses should be included:

- Residential
- Construction
- Employment

This sheet should have two columns with the headers in the first row, the table below lists the
columns.

Table: Required columns for the commute trips by land use sheet.

| Column Name          | Data Type | Description                                                |
| :------------------- | :-------: | :--------------------------------------------------------- |
| Land use at trip end |   Text    | The name of the land use type e.g. Residential             |
| Trips                |   Real    | The annual number of commuting LGV trips for that land use |

##### Annual Service Trips

The sheet named "Annual Service Trips" should contain the annual number of LGV service trips by land
use type from the DfT van survey. The sheet should contain the following land uses:

- Residential
- Office
- All Other

This sheet should have two columns with the headers in the first row, the table below lists the
columns.

Table: Required columns for the annual service trips sheet.

| Column Name          | Data Type | Description                                              |
| :------------------- | :-------: | :------------------------------------------------------- |
| Segment              |   Text    | The name of the land use type e.g. Residential           |
| Annual Service Trips |   Real    | The annual number of LGV service trips for that land use |

##### Delivery Segment Parameters

The sheet name "Delivery Segment Parameters" contains various mandatory parameters, listed in the
table below. The sheet should have the column headers "Parameter" and "Value" on the first row.

Table: Required parameters for the delivery segment sheet, parameters should be named exactly as
written.

| Parameter                             |      Data Type       | Description                                                                                                                                                    |
| :------------------------------------ | :------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Annual Trip Productions - Parcel Stem |       Integer        | The total annual trip productions for the delivery parcel stem segment from the DfT van survey, for the **base year**.                                         |
| Annual Trips - Parcel Bush            |       Integer        | The total annual trips for the delivery parcel bush segment from the DfT van survey, for the **base year**.                                                    |
| Annual Trips - Grocery Bush           |       Integer        | The total annual trips for the delivery grocery bush segment from the DfT van survey, for the **base year**.                                                   |
| Delivery Growth Factor                |      Real (> 0)      | Growth factor to apply to the annual delivery trips to factor to forecast year.                                                                                |
| B2C vs B2B Weighting                  |     Real (0 - 1)     | The ratio of business-to-customer vs business-to-business delivery trips                                                                                       |
| Depots Infill Zones                   | Comma-separated list | List of all zones in areas that aren't covered by the warehouse dataset (e.g. Scotland), these zones will have depots allocated based on number of households. |

##### Commute Warehouse Parameters

The sheet named "Commute Warehouse Parameters" should contain all the parameters for the warehouse
input calculations, including the weighting factors and infilling parameters. The table below
describes all the required values and their use, the different weighting factors correspond to the
input files described in [Warehouse Data](#warehouse-data)).

Table: Description of the commute warehouse parameters

| Parameter          | Data Type                 | Description |
| :----------------- | :------------------------ | :---------- |
| Weighting - High   |  Number                   | Factor to apply to the high relevance warehouse floorspace input. |
| Weighting - Medium |  Number                   | Factor to apply to the medium relevance warehouse floorspace input. |
| Weighting - Low    |  Number                   | Factor to apply to the low relevance warehouse floorspace input. |
| Model Zone Infill  | Comma-separated list      | List of model zones in commute warehouse data which should be infilled. |
| Zone Infill Method | Text (from options below) | Method for infilling model zones. |

Zone infill method calculates an infill value after all the warehouse data has been factored and
combined and then infills any zones in the "Model Zone Infill" list, which don't contain non-zero
values already. The following methods can be chosen for calculating the infill value:

- min: minimum value from existing data (including zeros)
- mean: mean value from existing data
- median: median value from existing data
- non_zero_min: minimum non-zero value from existing data
- zero: infills zones with zero

##### Gravity Model Parameters

The sheet named "Gravity Model Parameters" should contains parameters for the gravity model for each
of the six LGV model segments (Service, Delivery Parcel Stem, Delivery Parcel Bush, Delivery
Grocery, Commuting Drivers and Commuting Skilled Trades). The sheet contains six columns, listed in
the table below, with the headers on the first row.

Table: Required columns for the gravity model parameters sheet.

| Column Name               |          Data Type          | Description                                                                                                                          |
| :------------------------ | :-------------------------: | :----------------------------------------------------------------------------------------------------------------------------------- |
| Segment                   |            Text             | The name of the LGV model segment e.g. Service                                                                                       |
| Furness Constraint Type   |   Text (DOUBLE or SINGLE)   | The type of furnessing to do, see [Gravity Model](#gravity-model) for more details. These can be provided in uppercase or lowercase. |
| Cost Function             | Text (tanner or log normal) | The cost function to use, see [Gravity Model](#gravity-model) for more details. These can be provided in uppercase or lowercase.     |
| Cost Function Parameter 1 |            Real             | The first variable for the cost function, $\alpha$ for tanner and $\sigma$ for log normal                                            |
| Cost Function Parameter 2 |            Real             | The second variable for the cost function, $\beta$ for tanner and $\mu$ for log normal                                               |
| Run Calibration           |      Text (Yes or No)       | Whether or not to calibrate the gravity model to the trip distribution, uses cost function parameters as starting point              |

##### Time Period Factors

The sheet named "Time Period Factors" should contain all the factors for converting from the annual
matrices to the time periods for each model segment, see Ian Williams' technical note[^lgvn_design]
for more detail on each segment. The table should contain one factor for each time period / segment
combination, a list of the required columns is given below.

The time period factors ($f_{tp}$) are multiplied by the annual matrix ($M_{annual}$) to get the
time period matrix ($M_{tp}$) using the formula below. This calculation is done for each segment
and time period separately.

$$
M_{tp} = M_{annual} \times f_{tp}
$$

***Note:** the time period factors are expected to convert from annual trips to average daily time
period, therefore each factor should be less than, approximately, 1/365.*

Table: Required columns for the time period factors sheet.

| Column Names             | Data Type | Description                                                                                                 |
| :----------------------- | :-------: | :---------------------------------------------------------------------------------------------------------- |
| Time Period              |   Text    | The name of the time period, will be used for naming the outputs                                            |
| Service                  |   Real    | The factor to multiply the annual matrix by to get the average daily time period (e.g. AM) for this segment |
| Delivery Parcel Stem     |   Real    | The factor to multiply the annual matrix by to get the average daily time period (e.g. AM) for this segment |
| Delivery Parcel Bush     |   Real    | The factor to multiply the annual matrix by to get the average daily time period (e.g. AM) for this segment |
| Delivery Grocery         |   Real    | The factor to multiply the annual matrix by to get the average daily time period (e.g. AM) for this segment |
| Commuting Drivers        |   Real    | The factor to multiply the annual matrix by to get the average daily time period (e.g. AM) for this segment |
| Commuting Skilled Trades |   Real    | The factor to multiply the annual matrix by to get the average daily time period (e.g. AM) for this segment |

#### LGV Trip Distributions Spreadsheet

The trip distributions spreadsheet should contain a sheets with distributions for the different
segments. The worksheets should be named "Commuting", "Service", "Delivery" and "Delivery Bush" and
will be used for the relevant segment. Each worksheet should have the name of the cost distribution
and it's units in cell A1, e.g. "Average Length (km)", and the column headers for the distribution
table in row two. The distribution tables require four columns which are listed in the table below.

Table: Required columns for the trip distribution tables, column headers should be on row two of
each sheet.

| Column Name | Data Type | Description                                                                                               |
| :---------: | :-------: | :-------------------------------------------------------------------------------------------------------- |
|  observed   |   Real    | The number of observed trips in this bin                                                                  |
|    start    |   Real    | The start (inclusive) of the bin in the same units as the [Cost Matrix](#cost-matrix)                     |
|     end     |   Real    | The end (exclusive) of the bin in the same units as the [Cost Matrix](#cost-matrix)                       |
|   average   |   Real    | The weighted average of the cost value for this bin, in the same units as the [Cost Matrix](#cost-matrix) |

#### Census Occupation Data

The census occupation data is provided to the tool in two separate comma-separated values (CSV)
files, both of which are available on the [NOMIS website](https://www.nomisweb.co.uk/). The census
tables required are QS606EW and QS606UK, both tables contain meta data in the first eight rows and
the column names on row nine.

The QS606EW census table contains occupation data for England and Wales at LSOA level, and more
occupation categories, a list of the expected columns is given in the table below. The table should
be provided with the units persons.

Table: Required columns for the QS606EW occupation data CSV.

| Column Name                                         | Data Type | Description                         |
| :-------------------------------------------------- | :-------: | :---------------------------------- |
| 2011 super output area - lower layer                |   Text    | LSOA name                           |
| mnemonic                                            |   Text    | LSOA area code                      |
| All categories: Occupation                          |  Integer  | Total occupation                    |
| 51. Skilled agricultural and related trades         |  Integer  | Occupation numbers for this segment |
| 52. Skilled metal, electrical and electronic trades |  Integer  | Occupation numbers for this segment |
| 53. Skilled construction and building trades        |  Integer  | Occupation numbers for this segment |
| 821. Road Transport Drivers                         |  Integer  | Occupation numbers for this segment |

The QS606UK census table should contain the occupation data extracted for Scotland only at datazone
level and should be provided with the units persons. The expected columns for this input are shown
in the table below.

Table: Required columns for the QS606UK occupation data CSV.

| Column Name                                             | Data Type | Description                         |
| :------------------------------------------------------ | :-------: | :---------------------------------- |
| 2011 scottish datazone                                  |   Text    | Datazone name                       |
| mnemonic                                                |   Text    | Datazone area code                  |
| All categories: Occupation                              |  Integer  | Total occupation                    |
| 51. Skilled agricultural and related trades             |  Integer  | Occupation numbers for this segment |
| 52. Skilled metal, electrical and electronic trades     |  Integer  | Occupation numbers for this segment |
| 53. Skilled construction and building trades            |  Integer  | Occupation numbers for this segment |
| 82. Transport and mobile machine drivers and operatives |  Integer  | Occupation numbers for this segment |

#### Dwellings Data

The dwellings data is provided to the tool in two separate files, an Excel Workbook containing the
English data and a CSV containing the Scottish and Welsh data.

The English dwellings data is provided, at Local Authority District (LAD), in Table 123 on the
[Live tables on housing supply: net additional dwellings](https://www.gov.uk/government/statistical-data-sets/live-tables-on-net-supply-of-housing)
page of the UK government website. The data is expected to be converted to an Excel workbook before
providing to the tool but no changes to the formatting should be made, the workbook should have
sheets labelled with the year of the data (e.g. 2018-19) and should contain the model year. The
worksheet is expected to have the column names on row 4, a list of the required columns is given in
the table below

Table: English dwellings data required columns, names of columns should be exactly as listed any
other columns are ignored.

| Column Name                          | Data Type | Description                                      |
| :----------------------------------- | :-------: | :----------------------------------------------- |
| Current<br>ONS code                  |   Text    | LAD area code e.g. E06000055                     |
| Lower and Single Tier Authority Data |   Text    | Name of the LAD                                  |
| Demolitions                          |  Integer  | Number of building demolitions during the year   |
| Net Additions                        |  Integer  | Net number of building additions during the year |

The Scottish and Welsh dwellings data should be input as one CSV containing the values for both
countries, both datasets can be downloaded off the internet separately. The Scottish data is
available within [National Records of Scotland Household Estimates](https://www.nrscotland.gov.uk/statistics-and-data/statistics/statistics-by-theme/households/household-estimates/2019)
dataset, table 2 contains the number of dwellings by council area for recent years. The Welsh data
is available on the [Dwelling stock estimates page](https://statswales.gov.wales/Catalogue/Housing/Dwelling-Stock-Estimates/dwellingstockestimates-by-localauthority-tenure)
of the StatsWales website and should be obtained for the model year and the model year plus one. The
data should be combined and provided to the tool as a CSV, the required columns are given in the
table below.

Table: Scottish and Welsh dwellings data required columns.

| Column Name                | Data Type | Description                                            |
| :------------------------- | :-------: | :----------------------------------------------------- |
| zone                       |   Text    | The LAD area code e.g. W06000013                       |
| lad19nm                    |   Text    | The name of the LAD e.g. Bridgend                      |
| model year (e.g. 2018)     |  Integer  | The number of dwellings in each LAD for the model year |
| model year + 1 (e.g. 2019) |  Integer  | The number of dwellings in each LAD for the next year  |

#### NDR Business Data

The non-domestic rating business floorspace data is available in the NDR Business Floorspace tables
Excel spreadsheet on [GOV.UK](https://www.gov.uk/government/statistics/non-domestic-rating-stock-of-properties-including-business-floorspace-2019)
for the whole UK. The tables provide the business floorspace by administrative area for various
years and different sectors, the tool requires the data from the various tables to be compiled into
a single CSV which contains different columns for the different sectors (Retail, Office, Industrial
and Other) and years. The table below details the columns required in the input CSV file.

Table: NDR business floorspace CSV required columns.

| Column Name                   | Data Type | Description                                                                  |
| :---------------------------- | :-------: | :--------------------------------------------------------------------------- |
| AREA_CODE                     |   Text    | Area code e.g. E92000001                                                     |
| AREA                          |   Text    | Name of area e.g. ENGLAND                                                    |
| Floorspace_2017-18_Retail     |  Integer  | Floorspace in $1000m^2$ for the retail sector ending in the model year       |
| Floorspace_2018-19_Retail     |  Integer  | Floorspace in $1000m^2$ for the retail sector starting in the model year     |
| Floorspace_2017-18_Office     |  Integer  | Floorspace in $1000m^2$ for the office sector ending in the model year       |
| Floorspace_2018-19_Office     |  Integer  | Floorspace in $1000m^2$ for the office sector starting in the model year     |
| Floorspace_2017-18_Industrial |  Integer  | Floorspace in $1000m^2$ for the industrial sector ending in the model year   |
| Floorspace_2018-19_Industrial |  Integer  | Floorspace in $1000m^2$ for the industrial sector starting in the model year |
| Floorspace_2017-18_Other      |  Integer  | Floorspace in $1000m^2$ for the other sectors ending in the model year       |
| Floorspace_2018-19_Other      |  Integer  | Floorspace in $1000m^2$ for the other sectors starting in the model year     |

**Note:** The column names should include the actual model year (and the years before and after)
instead of 2018.

#### Other Zone Correspondences

Three other more generic zone correspondence CSVs are required for converting LSOAs, MSOAs and LADs
to the model zone system. These correspondence files are used for converting the
[Census Occupation Data](#census-occupation-data), [Dwellings Data](#dwellings-data) and
[NDR Business Data](#ndr-business-data). All zone correspondence CSV files have the same format
with column names on the first row and three required columns, listed in the table below.

Table: Required columns for the zone correspondence CSVs, column names are ignored the columns just
need to be in the correct order.

| Column | Data Type | Description                         |
| :----: | :-------: | :---------------------------------- |
|   1    |   Text    | Area code e.g. E01000001            |
|   2    |  Integer  | Corresponding model zone ID         |
|   3    |   Real    | Splitting factor for correspondence |

#### Study Area Lookup

The study area lookup should be a file containing a list of all the model zones with a second column
to flag whether or not they're inside the model study area. A list of the required columns is given
in the table below.

Table: Required columns for the study area lookup CSV, column names must be exactly as listed any
other columns are ignored.

| Column Name |    Data Type     | Description                                             |
| :---------: | :--------------: | :------------------------------------------------------ |
|    zone     |     Integer      | The model zone number                                   |
|  internal   | Integer (1 or 0) | If the zone is inside (1) or outside (0) the study area |

**Note:** This should be a complete list of all zones.

#### Cost Matrix

Matrix CSV containing the cost values for all zones in the model, the units of the costs should be
the same as the units in the [LGV Trip Distributions Spreadsheet](#lgv-trip-distributions-spreadsheet).
The CSV file should be in square matrix format where the first column and row contains all the zone
numbers, an example of a three by three matrix with the same costs for all zones is shown below.

Table: Example 3x3 matrix

|       | **1** | **2** | **3** |
| :---: | :---: | :---: | :---: |
| **1** | *10*  | *10*  | *10*  |
| **2** | *10*  | *10*  | *10*  |
| **3** | *10*  | *10*  | *10*  |

#### Calibration Matrix

The calibration matrix should be a CSV in the same format as [Cost Matrix](#cost-matrix). This
matrix is used during the gravity model process to adjust the impact of trips between certain zone
pairs and should have positive values around 0 - 2. The [Gravity Model](#gravity-model) section
outlines the methodology where this input is used.

#### Output Folder

The parent directory where all the outputs will be saved. A new sub-folder will be created with the
name convention "LGV Model Outputs - {date} {time}" (e.g. "LGV Model Outputs - 2021-08-05 19.15.32")
will be created to store the outputs for a single run of the LGV model.

### LGV Model Outputs

The LGV creates a new folder for each run to store all outputs inside, this folder follows the name
convention of "LGV Model Outputs - {date} {time}" (e.g. "LGV Model Outputs - 2021-08-05 19.15.32").
The LGV model outputs are split into three sub-folders "trip ends", "annual trip matrices" and
"time period matrices", the outputs for each are discussed in the next sections.

#### Trip Ends

The trip ends folder contains six CSVs, which each contain the trip end values for each of the
following model segments (see Ian Williams' technical note[^lgvn_design] for more details):

- Service
- Delivery Grocery
- Delivery Parcel Bush
- Delivery Parcel Stem
- Commute Drivers
- Commute Skilled Trades

The output files are named after the segments e.g. `service_trip_ends.csv` and they're all saved in
the CSV format with column headers on the first row and three columns. All outputs are given as
production and attraction trip ends, except delivery grocery and delivery parcel bush which are
origin and destinations.

Table: Trip ends outputs CSV columns.

| Column Name                   | Data Type | Description                                                       |
| :---------------------------- | :-------: | :---------------------------------------------------------------- |
| Zone                          |  Integer  | The model zone number                                             |
| Productions (or Origins)      |   Real    | The number of production (or origin) trip ends for this zone      |
| Attractions (or Destinations) |   Real    | The number of attraction (or destination) trip ends for this zone |

#### Annual Trip Matrices

The annual trip matrices folder contains the following three or four files for each of the model
segments:

- Annual trip matrix in productions / attractions format (if the model segment is in that format)
- Annual trip matrix in origin / destination format
- Excel log file
- PDF trip distributions graph

The following sections discuss each of the above files in more detail.

##### Annual Trip Matrix

The annual trip matrix files (both OD and PA) are provided as CSVs in the square matrix format i.e.
the first row and column contain all the zone numbers and the remaining cells contain the values.
All LGV model segments have an OD matrix and all, except delivery grocery and delivery parcel bush,
have a PA matrix too. The naming conventions for the two matrices are as follows:

- PA: `{segment_name}-trip_matrix-PA.csv`
- OD: `{segment_name}-trip_matrix-OD.csv`

##### Excel Log File

The Excel log spreadsheet that is created contains various statistics and results from the LGV model
process. The spreadsheet is named `{segment_name}-GM_log.xlsx` and contains the following worksheets:

- Calibration Results: This sheet lists the calibration parameters used for the final run of the
  gravity model and the $R^2$ values when the matrix is compared against the trip distributions.
- Furnessing Results: This sheet provides the results of the furnessing process on the final run of
  the gravity model.
- Trip Distribution: This sheet is a table containing the observed trip distribution compared to
  the matrix distribution.
- Vehicle Kilometres: This sheet is a table of the total trips and vehicle kilometres in the annual
  OD matrix.
- Vehicle Kilometres (PA): This sheet contains the same information as above but for the PA matrix,
  if this model segment is PA.

##### Trip Distributions Graph

The PDF contains a graph of the observed trip distributions compared to the output annual trip
matrix distributions. The file is named `{segment_name}-distribution.pdf` and contains the
distributions plotted for the observed data, the calibration area of the matrix, the whole matrix
and the whole OD matrix. All the data used to produce these graphs is given in the Trip Distribution
sheet of the [Excel Log File](#excel-log-file).

#### Time Period Matrices

The time period matrices folder contains a CSV with all the input time period factors listed and
sub-folders for each time period. Each time period sub-folder contains square matrix CSVs for each
of the six model segments, all matrices have the zones in the first column and row and have the time
period name as a prefix e.g. `AM_service-trip_matrix.csv`.

### Methodology

The LGV model is split into six model segments for different types of LGV trips, these are the
following (see Ian Williams' technical note[^lgvn_design] for more details):

- Service
- Delivery Grocery
- Delivery Parcel Bush
- Delivery Parcel Stem
- Commute Drivers
- Commute Skilled Trades

The LGV model methodology is split into three sections, only the first of which varies between model
segments, these are as follows:

- Trip end generation;
- Gravity model / annual trip matrix creation; and
- Conversion to time period matrices.

The following sections will discuss each of the three parts of the methodology in turn, with
flowcharts detailing the main components of each.

#### Trip End Generation

The trip end generation varies for each of the model segments in order to account for the types of
trips that are being modelled. The trip end generation is done as productions and attractions for
each of the segments except the delivery bush trips where they instead have origin and destination
trip ends.

The trip end generation uses various inputs from the DfT van survey and census data tables, these
are all outlined in the [LGV Model Inputs](#lgv-model-inputs) section. This section will discuss
the methodologies for the three main segments (which each contain sub-segments that make up the six
total LGV model segments).

##### Service Trip Ends

The trip ends for the service segment are calculated by using employment and household projections
data to distribute the total annual service trips (from the DfT van survey) to the model zone system.
The trip ends are distributed separately for the sub-segments of Residential, Office and All Other
Employment before being combined together into a single set of service productions and attractions.
The flowchart below outlines the service trip ends methodology, more details of this methodology can
be found in section 5 of Ian Williams' technical note[^lgvn_design].

![LGV service productions and attractions trip ends methodology - flowchart](doc/images/LGV_methodology-Servicing.png "LGV service productions and attractions trip ends methodology - flowchart")

##### Delivery Trip Ends

The trip ends for the delivery segment are split into three different sub-segments, detailed below:

- Parcel stem: These are delivery trips which originate at the depots and end at the first drop-off
  location. These trips would likely be the longest single trip in a delivery round and there would
  be a corresponding return trip back to the depot to pickup more packages.
- Parcel bush: These are the delivery trips which go between various drop-off locations and would
  tend to be lots of shorter trips.
- Grocery (bush): These would encompass the trips from the supermarket to the customers but would
  likely all relatively short as the supermarkets are closer to the customers than delivery depots
  are. There will be less total grocery trips in a single round but more rounds per day as each
  delivery will be larger than parcel deliveries.

The parcel stem trips are calculated as productions and attractions, whereas both the bush types are
origin / destination trip ends. The flowchart below outlines the methodology for calculating the
trip ends for all three types of delivery trip, more details of this methodology can be found in
section 6 of Ian Williams' technical note[^lgvn_design].

***TODO** Update flowchart to show trips are factored using delivery growth factor*
![LGV delivery parcel and grocery trip ends methodology - flowchart](doc/images/LGV_methodology-Delivery.png "LGV delivery parcel and grocery trip ends methodology - flowchart")

##### Commuting Trip Ends

The trip ends for the commuting segment are split into two sub-segments, detailed below:

- Skilled trades: These are the commuting trips which represent skilled workers who commute by LGV
  due to need to carry tools and equipment. These workers may be commuting to a construction site or
  to a residential / employment building to provide some service.
- Drivers: These are the LGV commuting trips which represent resident drivers.

Both commuting segments are calculated as productions and attractions, these methodologies have been
split into two flowcharts below, one for each type of trip end. More details on the commuting
methodology is given in section 4 of Ian Williams' technical note[^lgvn_design].

***TODO** Update flowchart to show trips are factored using growth factor*
![LGV commuting attractions trip ends methodology - flowchart](doc/images/LGV_methodology-Commuting-Attractions.png "LGV commuting attractions trip ends methodology - flowchart")

![LGV commuting productions trip ends methodology - flowchart](doc/images/LGV_methodology-Commuting-Productions.png "LGV commuting productions trip ends methodology - flowchart")

#### Gravity Model

The distribution of the trip ends to create annual trip matrices is done using a bespoke gravity
model. The gravity model is built of two sections, the first contains the cost functions (tanner and
log normal) to calculate the initial matrix and then performs either 1D factoring, or 2D furnessing,
to constraint the matrix to the trip ends. The gravity model process accepts an optional calibration
matrix which allows adjustments to be applied to specific zone pairs, the flowchart for the first
section is shown below.

![LGV gravity model methodology - flowchart](doc/images/LGV_methodology-Gravity_Model.png "LGV gravity model methodology - flowchart")

The second section of the gravity model is the outer self-calibration loop, this finds the optimal
cost function parameters to fit the resulting matrix to the observed trip distribution. The
self-calibration process is detailed in the below flowchart and can be turned on or off within the
[LGV Parameters Spreadsheets](#lgv-parameters-spreadsheet).

![LGV gravity model self-calibration methodology - flowchart](doc/images/LGV_methodology-Self-Calibrating_GM.png "LGV gravity model self-calibration methodology - flowchart")

#### Time Period Conversion

The final process of the LGV model is the conversion from annual to time period specific trip
matrices. The conversion is done by factoring the annual matrices (for each model segment) by the
period factor provided for each of the given time periods. The time period factors should be
provided separately to respect the different time profiles for each of the model segments, the
factors are provided in the [LGV Parameters Spreadsheet](#lgv-parameters-spreadsheet).

## Matrix Utilities

The matrix utilities module provides functionality for a variety of different operations which can
be applied to an O-D matrix CSV file. This functionality has been developed to be extremely
flexible and as such any number of operations can be turned off or on and the inputs can be any CSV
O-D matrix containing 3 columns, see inputs table for more details. This module has not been
created to process demand matrices in a specific way, the processing stages are determined entirely
by what is selected, the other modules in this tool provide more specific processing stages for
converting GBFM data to time period specific matrices. The operations provided by this module are as
follows:

- Summary: this will provide summary statistics for the input matrix such as matrix total, average
  value, number of zeros etc.
- Rezoning: this will convert the input matrix to a new zone system when given a zone
  correspondence lookup (this can be produced by module 1).
- Matrix addition: this will add a second matrix onto the matrix from the previous step and will
  set any negative values in the output matrix to 0.
- Matrix factoring: this will multiply the matrix (from the previous step) with another matrix
  (element wise) or with a global factor; only positive factors can be applied to stop the output
  becoming negative. The factor matrix does not need to include all O-D pairs present in the input
  matrix, any which aren't given will be factored by 1 i.e. not changed from the input.
- Fill missing zones: this will add any missing zones, which are provided as input, to the matrix
  and set their value to 0.
- Remove EE trips: this will set all external-external trips to 0 when given a list of external
  zones. If a more specific subset of EE trips is needed to be removed then matrix factoring can
  be used with a CSV containing all OD pairs for removal with factors of 0.
- Convert to UFM: this will convert the matrix to a UFM file, **requires SATURN to be installed**.

***Note:** All the above operations are applied one after another in the order above, so the output
from the previous operation becomes the input matrix for the next operation. For example if
rezoning, matrix factoring and convert to UFM are selected then the input matrix will be rezoned
and then the rezoned matrix will be multiplied by the given factor to produce an output, this
output will then be converted to a UFM.*

![Matrix utilities menu](doc/images/matrix_utilities_menu.png "Matrix utilities menu")

The menu for this module is shown above (any greyed out boxes aren't required until that process is
selected) and the inputs are listed in the table below, once these have been filled in the "Run"
button can be clicked to start the process. The process runs through the matrix operations in the
order they appear in the interface and will save any outputs to the folder given, any number or
combination of operations may be selected in order to process a matrix file in whatever way is
desired. The output files produced depends upon what operations are selected but a list of all
possible outputs is outlined in the table below.

Table: Inputs for matrix utilities module

| Input              |         Type         | Optional | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------ | :------------------: | :------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Input matrix       |         CSV          |    No    | O-D matrix CSV with the following 3 columns: origin, destination and trips. Column names are optional but they must be in the correct order.                                                                                                                                                                                                                                                                                                                                              |
| Summary            |       Boolean        |   Yes    | When checked produces spreadsheet which provides summary statistics about the matrix at each stage of the process. Recommend to leave turned on as the summary is useful when checking the outputs.                                                                                                                                                                                                                                                                                       |
| Rezoning           |         CSV          |   Yes    | Zone correspondence lookup file to be used to rezone the input matrix to a new zone system, can be produced with the zone correspondence module, expected columns: zone_1_id, zone_2_id, factor (names are optional but must be in the correct order). If rezoning is turned on then the input matrix will be rezoned before any other processing stages are ran, therefore **any other inputs used further down should be in the zone system that the matrix is being converted to.**    |
| Matrix addition    |         CSV          |   Yes    | Another O-D matrix CSV, expected columns: origin, destination and value (names are optional but columns must be in the correct order). This matrix will be added to the matrix from the previous step, negative values in this matrix are allowed but any negative values in the output are set to 0.                                                                                                                                                                                     |
| Matrix factoring   |     CSV or Real      |   Yes    | Another O-D matrix CSV (or global factor), expected columns: origin, destination and value (names are optional but columns must be in the correct order). This matrix (or global factor) will be multiplied with the matrix from the previous step. Only positive factors can be applied, if a matrix is given then all cells must be positive or the process will stop. **Any O-D pairs present in the input matrix but not in the factor matrix will be factored by 1 i.e. no change.** |
| Fill missing zones | CSV or list of zones |   Yes    | CSV containing single column (or comma-separated list) of missing zones which will be added to the matrix from the previous step with a value of 0.                                                                                                                                                                                                                                                                                                                                       |
| Remove EE trips    | CSV or list of zones |   Yes    | CSV containing single column (or comma-separated list) of all zones, in the matrix from the previous step, which will have trips set to 0. If a more specific subset of EE trips is needed to be removed then matrix factoring can be used.                                                                                                                                                                                                                                               |
| Convert to UFM     |        Folder        |   Yes    | Path to the SATURN exes folder, if selected will convert the matrix (from the previous step) to a UFM file.                                                                                                                                                                                                                                                                                                                                                                               |
| Output folder      |        Folder        |    No    | Directory where all the output matrices and the summary will be saved.                                                                                                                                                                                                                                                                                                                                                                                                                    |

Table: Outputs from matrix utilities module

| File                     | File Type      | Condition                                                                                   | Description                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------ | -------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| matrix_info              | Excel Workbook | Output when summary is turned on.                                                           | List of the inputs provided for each selected operation and a summary of matrix statistics at each stage of the process, contains the following sheets:<br>- `inputs`: lists the provided inputs for each operation, information on if the operation succeeded and any error messages; and<br>- `input_summary`: statistics for the matrix being processed at each stage.                                                        |
| {input matrix}_rezoned   | CSV            | Output if rezoning is selected.                                                             | The input matrix rezoned to the new zone system, contains the following columns:<br>- `origin`: origin zone number in new zone system;<br>- `destination`: destination zone number in new zone system; and<br>- `trips`: for the OD pair.                                                                                                                                                                                        |
| {input matrix}_processed | CSV            | Output if any operations other than "Summary", "Rezoning" or "Convert to UFM" are selected. | The output matrix for any operations that have been selected, contains the following columns:<br>- `origin`: origin zone number in new zone system;<br>- `destination`: destination zone number in new zone system; and<br>- `trips`: for the OD pair.<br>This matrix is a combination of all the selected operations applied one after another and it's name contains information about the operations which have been applied. |
| {input matrix}           | UFM            | Output if "Convert to UFM" is selected.                                                     | SATURN UFM matrix created from the processed matrix.                                                                                                                                                                                                                                                                                                                                                                             |
| {input matrix}           | LPX            | Output if "Convert to UFM" is selected.                                                     | SATURN MX log file of the conversion from CSV to UFM.                                                                                                                                                                                                                                                                                                                                                                            |
| {input matrix}_VDU       | VDU            | Output if "Convert to UFM" is selected.                                                     | SATURN MX VDU file of the conversion from CSV to UFM.                                                                                                                                                                                                                                                                                                                                                                            |

## Delta Process

The Delta Process module provides the functionality for performing forecasting to calculate future
year model demand. The calculations implemented within this module follow the delta approach to
forecasting which calculates the growth in demand within the freight data and applies this growth
to the base model demand. The methodology used for this process, and the underlying formulae, is
described in the Delta Process methodology flowchart.

![Flowchart showing the Delta Process forecasting methodology](doc/images/delta_process_methodology.png "Flowchart showing the Delta Process forecasting methodology")

The user must provide the O-D matrices for the base year model assignment demand, the base year
freight demand and the forecast year freight demand; **all input matrices must be in the same zone
system and for the same time period.** In addition to the matrices the user must select from one of
two growth modes, standard or exceptional (see flowchart for information on the different modes),
and provide the weighting factors. The inputs table below provides more detailed information on
each input for this module.

The module will produce two outputs for the user, saved in the output folder, the first is a log
spreadsheet which outlines the inputs used and summarises the input and output matrices. The
second output is the forecast year demand matrix for the model, as a CSV file; the outputs table
below provides more information on all the files produced by the Delta Process.

![Delta Process GUI](doc/images/delta_process_menu.PNG "Delta Process GUI")

Table: Inputs for the Delta Process module

| Input                                    |            Type             |  Default   | Description                                                                                                                                                                                                                                                        |
| :--------------------------------------- | :-------------------------: | :--------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model Assignment Demand - Base Year      |             CSV             |     -      | O-D matrix for the assignment model base year demand. Should contain the following 3 columns: origin, destination and trips; column names are optional but they must be in the correct order.                                                                      |
| Processed Freight Demand - Base Year     |             CSV             |     -      | O-D matrix for the processed freight base year demand, **must be in the same zone system as model assignment demand**. Should contain the following 3 columns: origin, destination and trips; column names are optional but they must be in the correct order.     |
| Processed Freight Demand - Forecast Year |             CSV             |     -      | O-D matrix for the processed freight forecast year demand, **must be in the same zone system as model assignment demand**. Should contain the following 3 columns: origin, destination and trips; column names are optional but they must be in the correct order. |
| Growth Mode                              | 'Standard' or 'Exceptional' | 'Standard' | Choice between two growth modes which can be undertaken with the Delta Process, see the methodology flowchart for more information about each calculation. **'Standard' mode is recommended.**                                                                     |
| Weighting Factor - $K_1$                 |         Real (> 0)          |    1.0     | Constant used in the 'Exceptional' growth calculations, not used for the 'Standard' growth mode, see the methodology flowchart for the formulae that use this constant. **Default value of 1.0 is recommended.**                                                   |
| Weighting Factor - $K_2$                 |         Real (> 0)          |    1.0     | Constant used in the 'Exceptional' growth calculations, not used for the 'Standard' growth mode, see the methodology flowchart for the formulae that use this constant. **Default value of 1.0 is recommended.**                                                   |
| Output Folder                            |       Path to Folder        |     -      | Path to the folder where the output files will be saved.                                                                                                                                                                                                           |

Table: Outputs from the Delta Process module

| File                                  |      Type      | Description                                                                                                                                                                                                                                                                                                                         |
| :------------------------------------ | :------------: | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `forecast_log`                        | Excel Workbook | Lists all the inputs provided, summarises the outputs and provides a log of the process, contains the following sheets:<br>- `inputs`: list of all the input parameters;<br>- `matrix_summaries`: provides summary statistics for the input and output matrices; and<br>- `process`: logs any errors that occur during the process. |
| `model_forecast_demand_[growth_mode]` |      CSV       | O-D matrix for the assignment model forecast year demand, contains the following columns:<br>- `origin`: origin zone number;<br>- `destination`: destination zone number; and<br>- `trips`: forecasted trips for the OD pair.                                                                                                       |

## Cost Conversion

This module uses a the zone correspondence produced with [CAF Space](#caf-space)
to perform a demand-weighted conversion of costs in O-D format to the new zoning system. The
interface is shown below.

![Cost Conversion GUI](doc/images/cost_conversion_menu.PNG "Cost Conversion GUI")

All O-D matrices chosen must contain three columns only, with a header row that is of the form
'origin', 'destination' and 'trips' (or a cost attribute where applicable).

The user must select an O-D cost matrix file to convert, an O-D trip matrix file for the weighting,
the zone correspondence file produced in module 1, and an output directory. Once 'Run' is clicked, a
progress window displays the cost conversion process. Once completed, the cost CSV in the new zoning
system is saved to the output directory under the name 'Output_Cost_Converted'.


