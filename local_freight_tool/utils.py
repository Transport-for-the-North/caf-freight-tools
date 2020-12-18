"""
    Module containing class to create the main logger from the logging module, as well as other
    utility functions.
"""

##### IMPORTS #####
import logging
import os
import json
import pandas as pd

# Script modules
from errors import *

##### CLASSES #####
class Loggers:
    """
        Class containing methods to create the main parent logger and any child loggers.
    """
    LOGGER_NAME = 'NoHAM-FPT'

    def __init__(self, path):
        """
        Creates and sets up the main logger.

        Parameters:
            path: str
                Path to a directory for where to save the log file, or
                a path including the log file name.
        """
        # Check if path is directory
        if os.path.isdir(path):
            logFile = os.path.join(path, 'NoHAM-FPT.log')
        else:
            logFile = path

        # Initiate logger
        self.logger = logging.getLogger(self.LOGGER_NAME)
        self.logger.setLevel(logging.DEBUG)

        # Create file handler
        fh = logging.FileHandler(logFile)
        fh.setLevel(logging.DEBUG)
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # Create formatter
        format = logging.Formatter("%(asctime)s [%(name)-30.30s] [%(levelname)-8.8s] %(message)s")
        fh.setFormatter(format)
        ch.setFormatter(logging.Formatter("[%(levelname)-8.8s] %(message)s"))
        # Add handlers to logger
        for i in (ch, fh): self.logger.addHandler(i)

        # Write to logger
        self.logger.debug('-'*100)
        self.logger.info('Initialised main logger.')

        return

    def __enter__(self):
        """ Called when initialising class with 'with' statement. """
        return self

    def __exit__(self, excepType, excepVal, traceback):
        """ Called when exiting with statement, writes any error to the logger and closes the file. """
        # Write exception to logfile
        if excepType != None or excepVal != None or traceback != None:
            self.logger.critical('Oh no a critical error occurred', exc_info=True)
        else:
            self.logger.info('Program completed without any fatal errors')
        # Closes logger
        self.logger.info('Closing log file')
        logging.shutdown()
        return

    @classmethod
    def childLogger(klass, loggerName):
        """
            Creates a child logger.

            Parameters:
                loggerName: str
                    The name of the child logger.
            Returns:
                logger: logger object
        """
        # Initialise logger
        logger = logging.getLogger(f'{klass.LOGGER_NAME}.{loggerName}')
        return logger

class Parameters:
    """
        Class for reading the parameters given and creating an empty parameter file for input.
    """
    # Class constants
    _INDENT = 4

    # Default parameters
    _TIME_PERIODS = {'_comment':'Time period conversion factors.',
                    'AM':None, 'IP':None, 'PM':None, 'OP':None}
    _INPUT = {'_comment':'Parameters for one run of the process',
            'TIME_PERIODS':_TIME_PERIODS, 'FILEPATH':'',
            'INPUT_FORMAT':'TSV/CSV',
            'INPUT_COLUMNS':{'_comment':'Names of the columns in the input data.',
                            'Origin':'O', 'Destination':'D',
                            'Trips':'Annual_PCU/Annual_Tonnage'}}
    _LOOKUP = {'FILEPATH':'',
                'INPUT_FORMAT':'TSV/CSV',
                'INPUT_COLUMNS':{'Old':'', 'New':'', 'SplittingFactor':''}}
    _ZONE_LOOKUP = {'_comment':'Parameters for the rezoning process, optional.',
                    **_LOOKUP}
    _SECTOR_LOOKUP = {'_comment':('Parameters for the sector OD tables to be produced,'
                                    ' for the input matrix, optional.'),
                        **_LOOKUP}
    _REZONED_SECTOR_LOOKUP = {'_comment':('Parameters for the sector OD tables to be produced,'
                                            ' for the rezoned and output matrices, optional.'),
                            **_LOOKUP}
    DEFAULT_PARAMETERS = {'_comment':('Parameter file for NoHAM-FPT, can run process'
                                    ' on multiple files at once by creating different '
                                    'input blocks. Input blocks can have any name.'),
                            'LOOKUPS':{'ZONE_LOOKUP':_ZONE_LOOKUP,
                                        'SECTOR_LOOKUP':_SECTOR_LOOKUP,
                                        'REZONED_SECTOR_LOOKUP':_REZONED_SECTOR_LOOKUP},
                            'INPUT':_INPUT}

    def __init__(self, path=None, params=None):
        """
            Initiate the parameters class by reading file if given, using parameters if given
            or with defaults.

            Parameters:
                path: str, optional
                    Path to parameters file.
                params: dict, optional
                    Dictionary containing parameters.
        """
        if not path is None:
            self.params = self.read(path)
        elif not params is None:
            self.params = dict(params)
        else:
            self.params = self.DEFAULT_PARAMETERS
        return

    @classmethod
    def read(cls, path):
        """
            Read the paramters file given, using json.

            Parameters:
                path: str
                    Path to the parameters file.
            Returns:
                params: dict
                    Dictionary containing all the parameters read.
        """
        # Read parameters
        with open(path, 'rt') as f:
            params = json.load(f)

        return params

    def __str__(self):
        """
            Creates json string.

            Parameters:
                None
            Returns:
                params: str
                    Json str dump of parameters.
        """
        return json.dumps(self.params, indent=self._INDENT)

    def write(self, path):
        """
            Write parameters to file.

            Parameters:
                path: str
                    Path to write parameter file to.
            Returns:
                None
        """
        # Write parameters to file
        with open(path, 'wt') as f:
            json.dump(self.params, f, indent=self._INDENT)
        return

    @staticmethod
    def checkParams(parameters, expected, name):
        """
            Checks if parameters contain expected.

            Parameters:
                parameters: dict
                    Dictionary containing parameters.
                expected: iterable
                    List of the expected parameters,
                    keys in the dictionary.
                name: str
                    Name of the parameter group being checked.
            Returns:
                params: dict
                    Dictionary containing only the expected parameters.
            Raises:
                MissingParameterError: If any of the expected parameters
                are not in the dictionary.
        """
        params = {}
        for i in expected:
            if i not in parameters.keys():
                raise MissingParameterError(i, name)
            else:
                # Only keep required values
                params[i] = parameters[i]

        return params

##### FUNCTIONS #####
def outputCsv(df, path, index=False, **kwargs):
    """
        Write dataframe to csv, catching any permission errors
        and waiting for user to close file.

        Parameters:
            df: pandas.DataFrame
                DataFrame for output.
            path: str
                Path to output to.
            index: bool, optional
                Whether or not to output the DataFrame index,
                default False.
            kwargs:
                Any other keyword arguments to be passed to
                pandas.DataFrame.to_csv method.
    """
    while True:
        try:
            df.to_csv(path, index=index, **kwargs)
            break
        except PermissionError as e:
            print(e)
            input('Please close the file and press enter...')

    return

def getSeparator(format, parameter=None):
    """
        Checks whether the given format is allowed for reading a text file,
        and gets the corresponding separator.

        Parameters:
            format: str
                The format of the text file should be.
            parameter: str, optional
                Name of the parameter that is being checked.
                Default None.
        Returns:
            separator: str
                The separator to be used when reading the file.
        Raises:
            IncorrecParameterError: If format is not of correct value
    """
    # Accepted formats
    forms = {'csv':',', 'tsv':'\t'}
    # Check what format has been given
    for key, val in forms.items():
        if format.lower() == key:
            return val
    else:
        # Raise error for wrong format given
        expected = list(forms.keys())
        raise IncorrectParameterError(format, parameter=parameter, expected=expected)

def createODTable(df):
    """
        Create an OD table from a given dataframe with columns O, D, Trips
        and output it to CSV or excel file.

        Parameters
            df: pandas.DataFrame
                DataFrame containing OD data in format | Origin | Destination | Trips |
        Returns:
            df: pandas.DataFrame
                DataFrame with the Origins on the rows index
                and the Destinations as the columns index.
    """
    # Create OD matrix
    cols = df.columns.tolist()
    df = df.pivot(index=cols[0], columns=cols[1], values=cols[2])
    return df

def writeOdTables(dataframes, path):
    """
        Convert the DataFrames to OD tables and output them
        to different sheets in a single spreadsheet.

        Parameters:
            dataframes: dict of dicts
                Dictionary containing all the dataframes to output,
                keys will be used for sheet names. Each value should
                be a dictionary containing a number of different sector
                OD dataframes to be output.
            path: str
                Path to write excel file to.
        Returns:
            odTables: dict
                Dictionary containing the OD tables with the
                same keys as <<dataframes>>.
    """
    # Check path
    if not path.lower().endswith('.xlsx'):
        loc = path.rfind('.')
        if loc == -1:
            path += '.xlsx'
        else:
            path = path[:loc] + '.xlsx'
    # Initiate output dict
    outputs = {}
    # Open excel file
    with pd.ExcelWriter(path) as writer:
        # Loop through the dictionary
        for key, secDict in dataframes.items():
            outputs[key] = {}
            # Loop through the dictionary within
            startrow = 0
            for indKey, val in secDict.items():
                outputs[key][indKey] = createODTable(val)
                # Write OD table to spreadsheet
                outputs[key][indKey].to_excel(writer, sheet_name=key, index_label=indKey,
                                                startrow=startrow)
                startrow += len(outputs[key][indKey]) + 2

    return outputs

