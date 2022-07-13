"""
Script to import large data set containing information from 2015-2020
source: PORT0400(https://www.gov.uk/government/statistical-data-sets/port-and-domestic-waterborne-freight-statistics-port)
"""

import os

import pandas as pd
from matplotlib import pyplot as plt

# TODO: Method for calculating year on year drop


class PortDataParser:

    _working_folder = r'Y:\Freight\18. Brexit impacts on freight\2. Port0400\Raw data and code'
    _port_data_sheet = 'Data from PORT0400 from 2015-2020.xlsx'

    _default_out_data_path = r'Y:\Freight\18. Brexit impacts on freight\2. Port0400\Graphs'

    _default_data_path = os.path.join(_working_folder, _port_data_sheet)


    def __init__(self,
                 in_data_path: str = _default_data_path,
                 out_data_path: str = _default_out_data_path,
                 ):
        # Pass paths to object
        self.in_data_path = in_data_path
        self.out_data_path = out_data_path

        # Pass port data to object
        self.port_data = pd.read_excel(self.in_data_path)

        self.direction_dict = {'out': 'Outwards',
                               'in': 'Inwards'}

        self.region_dict = {'eu': 'European Union traffic',
                            'non-eu': 'Non-EU Foreign traffic',
                            'uk': 'Domestic traffic'}

    def plot_graph(self,
                   direction: str,
                   region: str,
                   graph_title: str,
                   save_as: str):
        """
        direction: str
            takes 'in', 'out' - direction of traffic to plot
        region: str
            takes 'eu', 'non-eu', 'uk' - description of freight traffic origin/destination
        graph_title: str
            text to plot above the graph
         save_as: str
            text to include with saved plot, will be appended by relevant port name
        """
        # Remove all but core data
        required_headings = ['Port', 'Year', 'Region', 'Direction', 'Value (Thousands)']
        working_data = self.port_data.copy().reindex(required_headings, axis=1)

        # Get column headings from inputs
        target_direction = self.direction_dict[direction]
        target_region = self.region_dict[region]

        # Filter down data to target subset
        working_data = working_data[working_data['Direction'] == target_direction]
        working_data = working_data[working_data['Region'] == target_region]

        # Splitting the data up just into the important data  this being port year and value
        working_data = working_data[['Port', 'Year', 'Value (Thousands)']]

        # Sum the values and then finally plot the results
        # Plot ports individually so that individual trends can be seen.
        working_data = working_data.groupby('Port')

        for key, group in working_data:
            plt.figure()
            plt.title(graph_title)
            group.groupby('Year')['Value (Thousands)'].sum().plot(label=key)
            plt.legend(loc='best')
            plt.grid()
            plt.ylabel('Tonnage (Thousands)')

            figure_name = "%s_%s.png" % (save_as, key)
            target_folder = target_direction + '_' + target_region
            target_folder = target_folder.replace(' ', '_')
            
            out_path = os.path.join(self.out_data_path, target_folder, figure_name)
            
            if not os.path.exists(out_path):
                os.mkdir(out_path)

            plt.savefig(out_path)

        return 0









