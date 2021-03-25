"""

File purpose:
Functions to split GBFM HGV annual tonnage matrices into rigid and artic
matrices, and convert to PCUs.

Created on: Fri Mar 19 2021

Original author: CaraLynch

"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

from numpy.matrixlib.defmatrix import matrix

# User-defined imports
from matrix_utilities import ODMatrix

# Third-party imports
import pandas as pd
import numpy as np


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
        Keys in inputs dictionary corresponding to HGV matrix strings, except
        the EU non-EU import/export matrix

    Returns
    -------
    input_dfs: dict
        Dictionary of all inputs as dataframes, with the same keys as the
        inputs dictionary except the 'unitised_non_eu' file has been separated
        into imports and exports.

    Raises
    ------
    ValueError
        Raised when duplicate zone-direction values are found in the PCU
        factors file, or no default value is found in the PCU factors file.
    """
    input_dfs = {}
    for key in hgv_keys:
        input_dfs[key] = ODMatrix.read_OD_file(inputs[key])
    input_dfs['ports'] = read_csv(inputs["ports"], ['GBPortctr', 'GBZone'], new_headers=["port_id", "zone_id"])
    input_dfs['unitised_non_eu_imports'], input_dfs['unitised_non_eu_exports']= read_non_eu_imports_exports_file(inputs['unitised_non_eu'], input_dfs['ports'])
    input_dfs['distance_bands'] = read_csv(
        inputs["distance_bands"],
        ["start", "end", "rigid", "artic"],
        numerical_columns=["start", "end", "rigid", "artic"],
    )
    input_dfs['gbfm_distance_matrix'] = ODMatrix.read_OD_file(inputs["gbfm_distance_matrix"])
    input_dfs['port_traffic_proportions'] = read_csv(
        inputs["port_traffic_proportions"],
        ["type", "direction", "accompanied", "artic", "rigid"],
        numerical_columns=["artic", "rigid"],
    )
    input_dfs['pcu_factors'] = read_csv(
        inputs["pcu_factors"],
        ["zone", "direction", "artic", "rigid"],
        numerical_columns=["artic", "rigid"],
    )

    # check PCU factors are unique for each zone-direction pair
    if (input_dfs['pcu_factors'].groupby(["zone", "direction"]).count() > 1).any().any():
        msg = f"Error: duplicate values found in PCU factors file."
        raise ValueError(msg)

    # check PCU factors contains a default column
    if not (input_dfs['pcu_factors'].zone == "default").any():
        msg = f"Error: no default value found in PCU factors file."
        raise ValueError(msg)

    return input_dfs

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
    artic_rigid_dict: dict
        Dictionary of two ODMatrix instances representing the artic and rigid
        proportion of the unitised matrix's trips respectively, with keys
        'artic' and 'rigid'.
    """
    factors = port_traffic_proportions.loc[(port_traffic_proportions.type == commodity_type) & (port_traffic_proportions.direction == direction)]
    artic_rigid_dict = {}
    keys = ['artic', 'rigid']
    for key in keys:
        artic_rigid_dict[key] = unitised_matrix * (factors[key].mean()/1000)
        artic_rigid_dict[key].name = f"{key}_{unitised_matrix.name}"
    
    return artic_rigid_dict

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
    unitised_sums = {}
    keys = ['artic', 'rigid']
    for matrix in (imports + exports):
        if matrix in imports:
            artic_rigid_dict = unitised_to_artic_rigid_trips(matrix, port_traffic_proportions, 'import')
        else:
            artic_rigid_dict = unitised_to_artic_rigid_trips(matrix, port_traffic_proportions, 'export')
        for key in keys:
            if key in unitised_sums.keys():
                unitised_sums[key] += artic_rigid_dict[key]
            else:
                unitised_sums[key] = artic_rigid_dict[key]
                unitised_sums[key].name = f'{key}_unitised'

    return unitised_sums

def update_port_distance_factors(distance_factors, ports, port_traffic_proportions):
    """Updates distance factors for any zone pairs involving ports.

    Parameters
    ----------
    distance_factors : dict
        Dictionary of two matrices of rigid and artic distance factors
        respectively with rows as origins, columns as destinations.
    ports : pd.DataFrame
        Dataframe with list of port zones in zone_id column.
    port_traffic_proportions : pd.DataFrame
        Dataframe with the port traffic trips per 1000 tonnes, must contain a
        row with the type 'bulk', the direction is assumed to be both import
        and export.

    Returns
    -------
    distance_factors: dict
        Dictionary of two matrices of rigid and artic distance factors
        respectively with rows as origins, columns as destinations.
    """
    for key in distance_factors.keys():
        # get factor to apply
        factor = port_traffic_proportions.loc[port_traffic_proportions.type == 'bulk', key].mean()
        # apply all-directions factor to O-D trips with port as origin
        distance_factors[key].loc[distance_factors[key].index.isin(ports.zone_id), :] = factor
        # apply all-directions factor to O-D trips with port as destination
        distance_factors[key].loc[:, distance_factors[key].columns.isin(ports.zone_id)] = factor

        return distance_factors

def calculate_distance_factors(distance_matrix, distance_bands, ports, port_traffic_proportions):
    """Creates a dictionary of rigid and artic ODMatrices of the distance
    factor associated with each GBFM zone pair.

    Parameters
    ----------
    distance_matrix : ODMatrix
        O-D matrix of distances between GBFM zone pairs.
    distance_bands : pd.DataFrame
        Dataframe of distance factors with columns 'start', 'end', 'artic' and
        'rigid'.
    ports : pd.DataFrame
        Dataframe with list of port zones in zone_id column.
    port_traffic_proportions : pd.DataFrame
        Dataframe with the port traffic trips per 1000 tonnes, must contain a
        row with the type 'bulk', the direction is assumed to be both import
        and export.

    Returns
    -------
    distance_factors: dict
        Dictionary of two ODMatrix instances representing the distance factors
        to apply to each OD pair, with keys 'artic' and 'rigid'.
    """
    # Make sure the distance bands include all distances in the distance matrix
    if distance_matrix.max() > distance_bands.end.max():
        distance_bands.loc[distance_bands.end.argmax(), 'end'] = distance_matrix.max() + 1
    if distance_matrix.min() < distance_bands.start.min():
        distance_bands.loc[distance_bands.start.argmin(), 'start'] = 0
    
    # create dictionary of distance factor matrices
    distance_factors = {
        'artic': distance_matrix.matrix.copy(),
        'rigid': distance_matrix.matrix.copy()
    }

    # update distance factor matrices according to the factors in
    # distance_bands
    for i in distance_bands.index:
        to_factor = (distance_bands.loc[i, 'start'] < distance_matrix.matrix) & (distance_matrix.matrix < distance_bands.loc[i, 'end'])
        for key in distance_factors.keys():
            distance_factors[key][to_factor] = distance_bands.loc[i, key]
    
    # update factors for any zone-pairs involving ports
    distance_factors = update_port_distance_factors(distance_factors, ports, port_traffic_proportions)

    # transform distance factor matrices into ODMatrix instances
    for key in distance_factors.keys():
        distance_factors[key] = ODMatrix(distance_factors[key], name=f"{key}_distance_factors")
    
    return distance_factors

def bulk_to_artic_rigid_trips(domestic_bulk_port_matrix, distance_matrix, distance_bands, ports, port_traffic_proportions):
    """Convert domestic and bulk port matrix to artic and rigid trips

    Parameters
    ----------
    domestic_bulk_port_matrix : ODMatrix
        Domestic and bulk port annual tonnage matrix.
    distance_matrix : ODMatrix
        O-D matrix of distances between GBFM zone pairs.
    distance_bands : pd.DataFrame
        Dataframe of distance factors with columns 'start', 'end', 'artic' and
        'rigid'.
    ports : pd.DataFrame
        Dataframe with list of port zones in zone_id column.
    port_traffic_proportions : pd.DataFrame
        Dataframe with the port traffic trips per 1000 tonnes, must contain a
        row with the type 'bulk', the direction is assumed to be both import
        and export.

    Returns
    -------
    bulk_artic_rigid: dict
        DDictionary of two ODMatrix instances representing the artic and rigid
        annual domestic and bulk port vehicle traffic, with keys 'artic' and
        'rigid'.
    """
    distance_factors = calculate_distance_factors(distance_matrix, distance_bands, ports, port_traffic_proportions)
    bulk_artic_rigid = {}
    for key in distance_factors.keys():
        bulk_artic_rigid[key] = domestic_bulk_port_matrix * distance_factors[key] * (1/1000)
        bulk_artic_rigid[key].name = f"{key}_domestic_bulk"
    
    return bulk_artic_rigid

def convert_to_pcus(artic_rigid_trips, pcu_factors):
    """Converts artic and rigid total annual vehicles to annual PCUs.

    Parameters
    ----------
    artic_rigid_trips : dict
        Dictionary of two ODMatrices of total annual vehicles for rigid and
        artic HGVs, with keys 'artic' and 'rigid.
    pcu_factors : pd.DataFrame
        Dataframe with 4 columns: zone, direction, artic and rigid, and one
        'default' row with values ('default', NaN, default_artic_pcu_factor,
        default_rigid_pcu_factor).

    Returns
    -------
    artic_rigid_pcus: dict
        Dictionary of two ODMatrices of total annual PCUs for rigid and
        artic HGVs, with keys 'artic' and 'rigid.
    """
    default_factors = {}
    artic_rigid_pcus = {}
    # get default factors
    for key in artic_rigid_trips.keys():
        default_factors[key] = pcu_factors.loc[pcu_factors.zone == 'default', key].mean()
    
    # if there are only default factors, then factor the artic and rigid trip
    # matrices by the default factors
    if len(pcu_factors.loc[~(pcu_factors.zone == 'default')]) == 0:
        for key in artic_rigid_trips.keys():
            artic_rigid_pcus[key]  = artic_rigid_trips[key] * default_factors[key]
    # if there are origin and destination specific factors, need to create a
    # factors matrix
    else:
        origins = pcu_factors.loc[pcu_factors.direction == 'origin'].set_index('zone')
        destinations = pcu_factors.loc[pcu_factors.direction == 'destination'].set_index('zone')

        for key in artic_rigid_trips.keys():
            origin_data = np.array([origins[key]]*len(artic_rigid_trips[key].matrix.columns)).transpose()
            origin_df = pd.DataFrame(data=origin_data, index=origins.index, columns=artic_rigid_trips[key].matrix.columns)
            origin_df.index.name = 'origin'
            origin_df.index = origin_df.index.astype(int)
            origin_df.columns = origin_df.columns.astype(int)

            destination_data = np.array([destinations[key]]*len(artic_rigid_trips[key].matrix.index))
            destination_df = pd.DataFrame(data=destination_data, index=artic_rigid_trips[key].matrix.index, columns=destinations.index)
            destination_df.columns.name='destination'
            destination_df.index = destination_df.index.astype(int)
            destination_df.columns = destination_df.columns.astype(int)

            aligned_origins, aligned_destinations = origin_df.align(destination_df, join='outer')
            factors = ((aligned_origins + aligned_destinations)/2).combine_first(aligned_origins).combine_first(aligned_destinations)
            factors[factors.isnull()] = default_factors[key]
            factors = ODMatrix(factors, name='pcu_factors')
            artic_rigid_pcus[key] = artic_rigid_trips[key] * factors
    
    return artic_rigid_pcus

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

    Returns
    ----------
    artic_rigid_pcus: dict
        Dictionary of two ODMatrices of total annual PCUs for rigid and
        artic HGVs, with keys 'artic' and 'rigid.
    """
    hgv_keys = ['domestic_bulk_port', 'unitised_eu_imports',
        'unitised_eu_exports']
    
    # read in inputs
    input_df = read_inputs(inputs, hgv_keys)

    # Unitised trade - distance bands not required as global factors used
    # based on whether the matrix is imports or exports
    unitised_imports = [input_df['unitised_eu_imports'], input_df['unitised_non_eu_imports']]
    unitised_exports = [input_df['unitised_eu_exports'], input_df['unitised_non_eu_exports']]
    all_unitised_artic_rigid = aggregate_unitised_trips(unitised_imports, unitised_exports, input_df['port_traffic_proportions'])

    # Convert domestic and bulk port matrix to artic and rigid trips
    bulk_artic_rigid = bulk_to_artic_rigid_trips(input_df['domestic_bulk_port'], input_df['gbfm_distance_matrix'], input_df['distance_bands'], input_df['ports'], input_df['port_traffic_proportions'])

    # aggregate matrices
    all_artic_rigid = {}
    for key in all_unitised_artic_rigid.keys():
        all_artic_rigid[key] = all_unitised_artic_rigid[key] + bulk_artic_rigid[key]
        all_artic_rigid[key].name = f"total_{key}_trips"
    
    # convert number of trips to PCUs
    artic_rigid_pcus = convert_to_pcus(all_artic_rigid, input_df['pcu_factors'])

    return artic_rigid_pcus



    


