"""
    Module containing custom error classes to be used in this tool.
"""

##### IMPORTS #####
from typing import List, Union


##### ERRORS #####
class BaseLocalFreightError(Exception):
    """Base error for Local Freight Tool."""


class MissingParameterError(BaseLocalFreightError):
    """Raised when a parameter is missing from the input."""

    def __init__(self, missing, parameterNm, *args, **kwargs):
        # Create message
        msg = f"'{missing}' is missing from input '{parameterNm}'."
        super().__init__(msg, *args, **kwargs)


class IncorrectParameterError(BaseLocalFreightError):
    """Raised when parameter given is an unaccepted value."""

    def __init__(self, value, parameter=None, expected=None, *args, **kwargs):
        # Create message
        msg = f"Incorrect value of {value}"
        if not parameter is None:
            msg += f" for parameter {parameter}"
        if not expected is None:
            msg += f" expected value(s) {expected}"
        super().__init__(msg, *args, **kwargs)


class MissingLookupValuesError(BaseLocalFreightError):
    """
    Raised when there are zones missing from the lookup DataFrame.
    """

    def __init__(self, missing, column="", *args, **kwargs):
        # Create message
        msg = (
            f"There are {len(missing)} zones missing from "
            f"the {column} lookup: {list(missing)}"
        )
        super().__init__(msg, *args, **kwargs)


class MissingWorksheetError(BaseLocalFreightError):
    """Raised when worksheet is missing from input spreadsheet."""

    def __init__(self, workbook: str, worksheet: str, *args, **kwargs):
        msg = f"Worksheet '{worksheet}' missing from '{workbook}' spreadsheet"
        super().__init__(msg, *args, *kwargs)


class MissingColumnsError(BaseLocalFreightError):
    """Raised when columns are missing from input CSV or spreadsheet."""

    def __init__(self, name: str, columns: List, *args, **kwargs):
        cols = " and".join(", ".join(f"'{s}'" for s in columns).rsplit(",", 1))
        msg = f"Columns missing from {name}: {cols}"
        super().__init__(msg, *args, **kwargs)


class MissingDataError(BaseLocalFreightError):
    """Raised when data is missing from an input file."""

    def __init__(self, name: str, missing: Union[List, str], *args, **kwargs):
        if isinstance(missing, str):
            miss = missing
        else:
            miss = " and".join(", ".join(f"'{s}'" for s in missing).rsplit(",", 1))
        msg = f"Data missing from {name}: {miss}"
        super().__init__(msg, *args, **kwargs)
