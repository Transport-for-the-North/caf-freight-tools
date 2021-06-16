"""
Rezones a matrix when given a lookup with splitting factors.
"""

##### IMPORTS #####
# Standard imports
import sys

# Third-party imports

# Local imports
from .utilities import Loggers, Parameters, read_csv
from .errors import IncorrectParameterError, MissingLookupValuesError


##### CLASS #####
class Rezone:
    """Class for rezoning a matrix when given a lookup with splitting factors."""

    # Class logger
    log = Loggers.childLogger(f"{__name__}.Rezone")

    @classmethod
    def read(cls, path, columns):
        """Read the lookup file.

        Parameters
        ----------
        path: str
            Path to the lookup file.
        columns: dict
            Column names in the lookup file should contain 3 keys,
            old, new, splitting_factor. If None then ignores the
            header row and uses the first 3 columns in file as old,
            new and splitting_factor respectively.

        Returns
        -------
        lookup: pandas.DataFrame
            DataFrame object with the old, new and
            splitting_factor columns read from the file.
        """
        # Check columns given
        if columns is None:
            cols = {"old": 0, "new": 1, "splitting_factor": 2}
            rename = list(cols.keys())
        else:
            cols = Parameters.checkParams(
                columns, ("old", "new", "splitting_factor"), name="INPUT_COLUMNS"
            )
            rename = {v: k for k, v in cols.items()}

        # Read file checking if there are any format errors
        try:
            df = read_csv(
                path, "Rezoning Lookup", columns=list(cols.values()), low_memory=False
            )
        except IncorrectParameterError:
            errType, errVal = sys.exc_info()[:2]
            # Log any errors and reraise
            cls.log.error("%s: %s", errType.__name__, str(errVal))
            raise

        # Set column names if rename is list or use rename method with dicts
        if isinstance(rename, (tuple, list)):
            df.columns = rename
        else:
            df.rename(columns=rename, inplace=True)
        return df

    @staticmethod
    def rezone(
        df,
        lookup,
        dfCol,
        lookupOld="old",
        lookupNew="new",
        splitCol="splitting_factor",
        rezoneCols="trips",
    ):
        """Rezones a dataframe with a lookup dataframe, using splitting factors.

        Parameters
        ----------
        df: pandas.DataFrame
            The matrix to be rezoned.
        lookup: pandas.DataFrame
            The lookup tables to do the rezoning.
        dfCol: str
            The column to be replaced with a new zone system.
        lookupOld: str, optional
            The column that contains the current zone system (present in df).
            Default 'old'
        lookupNew: str, optional
            The column that contains the new zone system.
            Default 'new'.
        splitCol: str, optional
            The column that contains the splitting factors.
            Default 'splitting_factor'.
        rezoneCols: str or list-like, optional, default "trips"
            The column(s) which should be multiplied by the `splitCol`
            during rezoning.

        Returns
        -------
        merged: DataFrame
            Rezoned input dataframe.
        missing: DataFrame
            Rows containing zones not present in the lookup dataframe
        """
        originalCols = df.columns
        # Join the dfs
        merged = df.merge(
            lookup,
            left_on=dfCol,
            right_on=lookupOld,
            how="left",
            indicator=True,
            suffixes=("", "_Lookup"),
        )
        missing = merged.loc[merged["_merge"] != "both"]
        # Set the column to the new zones
        merged[dfCol] = merged[lookupNew]
        # Convert the split columns
        if isinstance(rezoneCols, str):
            merged[rezoneCols] = merged[rezoneCols] * merged[splitCol]
        else:
            for c in rezoneCols:
                merged[c] = merged[c] * merged[splitCol]
        return merged[originalCols], missing

    @classmethod
    def rezoneOD(cls, df, lookup, dfCols=("origin", "destination"), **kwargs):
        """Rezones the matrix on both the origin and destination columns.

        Uses the `rezone` method.

        Parameters
        ----------
        df: pandas.DataFrame
            The matrix to be rezoned.
        lookup: pandas.DataFrame
            The lookup tables to do the rezoning.
        dfCols: iterable
            The columns to be replaced with a new zone system.
        kwargs: keyword arguments
            Any keyword arguments to pass to `Rezone.rezone`.

        Returns
        -------
        df: pandas.DataFrame
            The original dataframe with the columns rezoned.
        """
        # Loop through the dfCols
        for c in dfCols:
            df, missing = cls.rezone(df, lookup, c, **kwargs)
            # Check if there are any missing lookup values
            if len(missing) > 1:
                missing = missing[c].unique()
                raise MissingLookupValuesError(missing, c)

        # Group the new zones
        df = df.groupby(dfCols, as_index=False).sum()
        return df
