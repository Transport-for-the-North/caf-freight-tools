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

def read_non_eu_imports_exports_file(path, ports):
    """Reads in the unitised non-European imports/exports file, rezones
    the port IDs to their GBFM zone IDs, separates imports from exports, and
    creates OD Matrix instances for imports and exports.

    Parameters
    ----------
    path : str
        Path to unitised non-EU imports/exports csv, with columns 'Imp0Exp1',
        'GBPortctr', 'GBRawZone', and 'Traffic'.
    ports: pd.DataFrame
        Port lookup dataframe, with columns 'port_id' and 'zone_id'.

    Returns
    -------
    unitised_non_eu_imports: ODMatrix
        ODMatrix instance of the unitised non-eu imports
     unitised_non_eu_exports: ODMatrix
        ODMatrix instance of the unitised non-eu exports   
    """
    non_eu_imports_exports = read_csv(path, ['Imp0Exp1', 'GBPortctr', 'GBRawZone', 'Traffic'], new_headers=['Imp0Exp1', 'port_id', 'zone_id', 'trips'], numerical_columns=['trips'])
    non_eu_imports_exports = non_eu_imports_exports.merge(ports.rename(columns={'zone_id': 'port_zone_id'}), how='left', on='port_id')
    imports_dict = {
        'port_zone_id': 'origin',
        'zone_id': 'destination',
    }
    exports_dict = {
        'port_zone_id': 'destination',
        'zone_id': 'origin',
    }
    unitised_non_eu_imports = non_eu_imports_exports.loc[non_eu_imports_exports['Imp0Exp1'] == 0].rename(columns=imports_dict)
    unitised_non_eu_exports = non_eu_imports_exports.loc[non_eu_imports_exports['Imp0Exp1'] == 1].rename(columns=exports_dict)
    unitised_non_eu_imports = ODMatrix(unitised_non_eu_imports[['origin', 'destination', 'trips']], name='unitised_non_eu_imports', pivoted=False)
    unitised_non_eu_exports = ODMatrix(unitised_non_eu_exports[['origin', 'destination', 'trips']], name='unitised_non_eu_exports', pivoted=False)
    return unitised_non_eu_imports, unitised_non_eu_exports



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
        Dictionary of HGV ODMatrix instances with keys 'domestic_bulk_port', 'unitised_eu_imports',
        'unitised_eu_exports', 'unitised_non_eu_imports' and 'unitised_non_eu_exports'
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
    hgv_matrices['unitised_non_eu_imports'], hgv_matrices['unitised_non_eu_exports']= read_non_eu_imports_exports_file(inputs['unitised_non_eu'], ports)
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

def unitised_to_artic_rigid_trips(unitised_matrix, port_traffic_proportions, direction, commodity_type='unitised'):
    """Separate a unitised import or export matrix into artic and rigid
    trips using port traffic rigid and artic proportions.

    Parameters
    ----------
    unitised_matrix : ODMatrix
        Unitised matrix.
    port_traffic_proportions : pd.DataFrame
        Dataframe with columns 'type', 'direction', 'accompanied', 'artic'
        and 'rigid'
    commodity_type : str
        Whether the input matrix is 'unitised' or 'bulk', by default
        'unitised'.
    direction : str
        Whether the input matrix is 'import' or 'export'.

    Returns
    -------
    artic_matrix: ODMatrix
        The artic proportion of the unitised matrix's trips.
    rigid_matrix: ODMatrix
        The rigid proportion of the unitised matrix's trips.
    """
    factors = port_traffic_proportions.loc[(port_traffic_proportions.type == commodity_type) & (port_traffic_proportions.direction == direction)]
    artic_factor = factors.artic.mean()
    rigid_factor = factors.rigid.mean()
    artic_matrix = unitised_matrix * (artic_factor/1000)
    artic_matrix.name = f"{unitised_matrix.name}_artic"
    rigid_matrix = unitised_matrix * (rigid_factor/1000)
    rigid_matrix.name = f"{unitised_matrix.name}_rigid"

    return artic_matrix, rigid_matrix

def aggregate_unitised_trips(imports, exports, port_traffic_proportions):
    """Aggregate all unitised HGV trips.

    Parameters
    ----------
    imports : list
        List of ODMatrix instances representing unitised imports.
    exports : list
        List of ODMatrix instances representing unitised exports.
    port_traffic_proportions : pd.DataFrame
        Dataframe with columns 'type', 'direction', 'accompanied', 'artic'
        and 'rigid'

    Returns
    -------
    artic_unitised_sum: ODMatrix
        The aggregation of all articulated unitised trips.
    rigid_unitised_sum: ODMatrix
        The aggregation of all rigid unitised trips.
    """
    artic_unitised_sum = None
    rigid_unitised_sum = None
    for matrix in (imports + exports):
        if matrix in imports:
            artic, rigid = unitised_to_artic_rigid_trips(matrix, port_traffic_proportions, 'import')
        else:
            artic, rigid = unitised_to_artic_rigid_trips(matrix, port_traffic_proportions, 'export')
        if not artic_unitised_sum:
            artic_unitised_sum = artic
            artic_unitised_sum.name = 'unitised_artic'
            rigid_unitised_sum = rigid
            rigid_unitised_sum.name = 'unitised_rigid'
        else:
            artic_unitised_sum += artic
            rigid_unitised_sum += rigid
        
    return artic_unitised_sum, rigid_unitised_sum


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
        'unitised_eu_exports']
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
    unitised_imports = [hgv_matrices['unitised_eu_imports'], hgv_matrices['unitised_non_eu_imports']]
    unitised_exports = [hgv_matrices['unitised_eu_exports'], hgv_matrices['unitised_non_eu_exports']]
    unitised_artic, unitised_rigid = aggregate_unitised_trips(unitised_imports, unitised_exports, port_traffic_proportions)

    


