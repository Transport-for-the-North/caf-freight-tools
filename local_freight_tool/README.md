# Local Freight Tool
Freight tools for developing HGV and LGV freight demand matrices for model integration.

## Installation
Download [Anaconda](https://www.anaconda.com/products/individual#Downloads).  

### Create conda environment
Run `install_tool.bat` by double-clicking on it in the scripts directory. If this is unsuccessful:

- Open Anaconda Prompt, accessible from Start Menu or Windows search. Navigate to directory containing environment.yml file.  

- Create new conda environment with `conda env create -f environment.yml`. Use y to proceed if required.

### Packages required
If you wish to create your own environment for the tool, the required packages are
(detailed version information can be found in local_freight_tool/environment.yml):
- PyQT
- Pandas
- GeoPandas
- Openpyxl

## Launching the tool
Double click on `run_tool.bat`. If this is unsuccessful:

- Use Anaconda Prompt to navigate to the scripts directory.  

- Activate the conda environment using `conda activate freighttool`.  

- Launch the menu using `python tc_main_meny.py`.  

Tip: start writing the file name and press tab, the command prompt will autocomplete it for you.

## Resources

[Command Prompt Cheatsheet](http://www.cs.columbia.edu/~sedwards/classes/2017/1102-spring/Command%20Prompt%20Cheatsheet.pdf)

## Authors

* **Cara Lynch** - *WSP*
* **Matthew Buckley** - *WSP*
