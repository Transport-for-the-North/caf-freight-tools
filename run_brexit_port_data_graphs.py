
import brexit_ports_impacts.port_data_parser
import pandas as pd

"""
Splitting up the data even more into 6 different data sets so that i can use the data  to plot graphs later
Only interested in the Data from EU and Non-EU sources as the goal is to find  how  brexit affected these
The process is the same for all 6 data sets so only the first has been commented.
"""


def main():

    """
    Run graphing process process - pull in graphing params and iterate
    """

    run_csv_path = r'Y:\Freight\18. Brexit impacts on freight\2. Port0400\graph_run_params.csv'
    verbose = True

    # Import
    iter_params = pd.read_csv(run_csv_path)

    # Instantiate model
    port_graph_model = brexit_ports_impacts.port_data_parser.PortDataParser()

    # Iterate over spreadsheet rows
    for index, row in iter_params.iterrows():
        port_graph_model.plot_graph(
            direction=row['direction'],
            region=row['region'],
            graph_title=row['graph_title'],
            save_as=row['save_as'],
            verbose=verbose
        )


if __name__ == '__main__':
    main()
