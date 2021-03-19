"""

File purpose:
Contains all matrix utility functions required for the tool, including 
producing a summary, rezoning a matrix, adding and factoring matrices, filling
missing zones, removing external-external trips, and converting to UFM.

Created on: Wednesday Mar 17 2021

Original author: CaraLynch

"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# User-defined imports
from matrix_utilities import ODMatrix

# Third-party imports
import pandas as pd


##### FUNCTIONS #####
def read_csv(path, columns, new_headers=None, numerical_columns=None):
    """Reads in a csv file and converts it to a Pandas DataFrame.

    Parameters
    ----------
    path : str
        Path to csv file
    columns : list of strings or ints
        Columns in the file to be read, indicated via their headers or indices
    new_headers : list of strings, optional
        New column names to use, by default None
    numerical_columns : list of strings, optional
        Headers of numerical columns, by default None. If new_headers is not
        None, the headers must be the new headers, not the csv headers.

    Returns
    -------
    df : pd.DataFrame
        DataFrame of the csv data.

    Raises
    ------
    FileNotFoundError
        If the input file path is incorrect
    KeyError
        If the input file does not have the correct number of columns
    Exception
        For any other issues with the file
    ValueError
        If not all values in numeric columns are numeric
    """
    path = Path(path)
    filename = path.stem
    try:
        whitespace, header_row = ODMatrix.check_file_header(path)
        df = pd.read_csv(
            path,
            delim_whitespace=whitespace,
            header=header_row,
            usecols=columns,
        )
    except FileNotFoundError as e:
        msg = f"Error: {filename} not found: {e}"
        raise FileNotFoundError(msg) from e
    except KeyError as e:
        msg = f"Error: problem with {filename}: {e}"
        raise KeyError(msg) from e
    except Exception as e:
        msg = f"Error: problem with {filename}: {e}"
        raise Exception(msg) from e
    if new_headers:
        if len(new_headers) != len(columns):
            msg = f"Error: new column names do not match number of columns in {filename}"
            raise KeyError(msg)
        else:
            new_names = {}
            for i in range(len(new_headers)):
                new_names[columns[i]] = new_headers[i]
            df = df.rename(columns=new_names)
    if numerical_columns:
        try:
            df[numerical_columns].apply(
                lambda s: pd.to_numeric(s, errors="raise").notnull().all()
            )
        except ValueError as e:
            msg = f"Error: Problem with {filename}: {e}"
            raise ValueError(msg) from e

    return df


def read_inputs(inputs, hgv_keys):
    """Reads in all input files required for rigid-artic split and conversion
    from tonnes to PCU.

    Parameters
    ----------
    inputs : dict
        Dictionary of all input file paths as strings.
    hgv_keys : list
        Keys in inputs dictionary corresponding to HGV matrix strings

    Returns
    -------
    hgv_matrices: dict
        Dictionary of HGV ODMatrix instances with the keys given in hgv_keys
    ports: pd.DataFrame
        1-column dataframe GB ports with IDs in GBFM zoning and header
        'zone_id'
    distance_bands: pd.DataFrame
        DataFrame of distance bands with columns 'start', 'end', 'rigid' and
        'artic'
    gbfm_distance_matrix: ODMatrix
        O-D matrix of the distances between GBFM zones
    port_traffic_proportions: pd.DataFrame
        Dataframe with columns 'type', 'direction', 'accompanied', 'artic'
        and 'rigid'
    pcu_factors: pd.DataFrame
        Dataframe with columns 'zone', 'direction', 'artic' and 'rigid'. There
        must be a 'default' zone with no direction which assigns the default
        artic and rigid factors.


    Raises
    ------
    ValueError
        Raised when duplicate zone-direction values are found in the PCU
        factors file.
    """
    hgv_matrices = {}
    for key in hgv_keys:
        hgv_matrices[key] = ODMatrix.read_OD_file(inputs[key])
    ports = read_csv(inputs["ports"], ['GBPortctr', 'GBZone'], new_headers=["port_id", "zone_id"])
    distance_bands = read_csv(
        inputs["distance_bands"],
        ["start", "end", "rigid", "artic"],
        numerical_columns=["start", "end", "rigid", "artic"],
    )
    gbfm_distance_matrix = ODMatrix.read_OD_file(inputs["gbfm_distance_matrix"])
    port_traffic_proportions = read_csv(
        inputs["port_traffic_proportions"],
        ["type", "direction", "accompanied", "artic", "rigid"],
        numerical_columns=["artic", "rigid"],
    )
    pcu_factors = read_csv(
        inputs["pcu_factors"],
        ["zone", "direction", "artic", "rigid"],
        numerical_columns=["artic", "rigid"],
    )

    # check PCU factors are unique for each zone-direction pair
    if (pcu_factors.groupby(["zone", "direction"]).count() > 1).any().any():
        msg = f"Error: duplicate values found in PCU factors file."
        raise ValueError(msg)

    # check PCU factors contains a default column
    if not (pcu_factors.zone == "default").any():
        msg = f"Error: no default value found in PCU factors file."
        raise ValueError(msg)

    return (
        hgv_matrices,
        ports,
        distance_bands,
        gbfm_distance_matrix,
        port_traffic_proportions,
        pcu_factors,
    )

    def main(inputs):
        """Main function for converting from annual tonnes to PCUs and
        splitting to rigid and articulated HGVs.

        Parameters
        ----------
        inputs : dict
            Dictionary of filepaths for all inputs required, which include
            HGV matrices 'domestic_bulk_port', 'unitised_eu_imports',
            'unitised_eu_exports' and 'unitised_non_eu', 'ports',
            'distance_bands', 'gbfm_distance_matrix',
            'port_traffic_proportions' and 'pcu_factors'
        """
        hgv_keys = ['domestic_bulk_port', 'unitised_eu_imports',
            'unitised_eu_exports', 'unitised_non_eu']
        # read in inputs
        (
            hgv_matrices,
            ports,
            distance_bands,
            gbfm_distance_matrix,
            port_traffic_proportions,
            pcu_factors,
        ) = read_inputs(inputs, hgv_keys)

        # Unitised trade - distance bands not required as global factors used
        # based on whether the matrix is imports or exports
        unitised_keys = hgv_keys.copy().remove('domestic_bulk_port')
        

