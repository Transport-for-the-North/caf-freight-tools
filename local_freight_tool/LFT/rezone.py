"""
Rezones a matrix when given a lookup with splitting factors.
"""

##### IMPORTS #####
import pandas as pd
import sys

# Local imports
from .utilities import Loggers, getSeparator, Parameters
from .errors import IncorrectParameterError, MissingLookupValuesError

##### CLASS #####
class Rezone:
    """
        Class for rezoning a matrix when given a lookup with splitting factors.
    """
    # Class logger
    log = Loggers.childLogger(f'{__name__}.Rezone')

    @classmethod
    def read(cls, path, format, columns):
        """
            Read the lookup file.

            Parameters:
                path: str
                    Path to the lookup file.
                format: str
                    Format the lookup file is in,
                    either CSV or TSV.
                columns: dict
                    Column names in the lookup file should contain 3 keys,
                    old, new, splitting_factor.
            Returns:
                lookup: pandas.DataFrame
                    DataFrame object with the Old, New and
                    SplittingFactor columns read from the file.
        """
        # Check columns given
        cols = Parameters.checkParams(columns, ('old', 'new', 'splitting_factor'),
                                        name='INPUT_COLUMNS')

        # Read file checking if there are any format errors
        try:
            df = pd.read_csv(path, sep=getSeparator(format),
                            low_memory=False, usecols=list(cols.values()))
        except IncorrectParameterError:
            errType, errVal = sys.exc_info()[:2]
            # Log any errors and reraise
            cls.log.error(f'{errType.__name__}: {errVal}')
            raise

        # Flip the dict
        cols = {v: k for k, v in cols.items()}
        # Rename columns
        df = df.rename(columns=cols)

        return df

    @staticmethod
    def _rezone(df, lookup, dfCol, lookupOld='old',
                lookupNew='new', splitCol='splitting_factor'):
        """
            Rezones a dataframe with a lookup dataframe, using splitting factors.

            Parameters:
                df: pandas.DataFrame
                    The matrix to be rezoned.
                lookup: pandas.DataFrame
                    The lookup tables to do the rezoning.
                dfCol: str
                    The column to be replaced with a new zone system.
                lookupOld: str, optional
                    The column that contains the current zone system (present in df).
                    Default 'OldZone'
                lookupNew: str, optional
                    The column that contains the new zone system.
                    Default 'NewZone'.
                splitCols: str, optional
                    The column that contains the splitting factors.
                    Default 'SplittingFactor'.
            Returns:
                merged: DataFrame
                    Rezoned input dataframe.
                missing: DataFrame
                    Rows containing zones not present in the lookup dataframe
        """
        originalCols = df.columns
        # Join the dfs
        merged = df.merge(lookup, left_on=dfCol, right_on=lookupOld, how='left',
                          indicator=True, suffixes=('', '_Lookup'))
        missing = merged.loc[merged['_merge']!='both']
        # Set the column to the new zones
        merged[dfCol] = merged[lookupNew]
        # Convert the split columns
        merged['trips'] = merged['trips'] * merged['splitting_factor']

        return merged[originalCols], missing

    @classmethod
    def rezoneOD(cls, df, lookup, dfCols=['origin', 'destination'], **kwargs):
        """
            Rezones the matrix on both the origin and destination columns,
            using the _rezone method.

            Parameters:
                df: pandas.DataFrame
                    The matrix to be rezoned.
                lookup: pandas.DataFrame
                    The lookup tables to do the rezoning.
                dfCols: iterable
                    The columns to be replaced with a new zone system.
                kwargs: keyword arguments
                    Any keyword arguments to pass to Rezone._rezone.
            Returns:
                df: pandas.DataFrame
                    The original dataframe with the columns rezoned.
        """
        # Loop through the dfCols
        for c in dfCols:
            df, missing = cls._rezone(df, lookup, c, **kwargs)
            # Check if there are any missing lookup values
            if len(missing) > 1:
                missing = missing[c].unique()
                raise MissingLookupValuesError(missing, c)

        # Group the new zones
        df = df.groupby(dfCols, as_index=False).sum()

        return df


