"""
    Module containing custom error classes to be used in this tool.
"""

##### ERRORS #####
class MissingParameterError(Exception):
    """
        Raised when a parameter is missing from the input.
    """
    def __init__(self, missing, parameterNm, *args, **kwargs):
        # Create message
        msg = f"'{missing}' is missing from input '{parameterNm}'."
        super().__init__(msg, *args, **kwargs)

class IncorrectParameterError(Exception):
    """
        Raised when parameter given is an unaccepted value.
    """
    def __init__(self, value, parameter=None, expected=None, *args, **kwargs):
        # Create message
        msg = f"Incorrect value of {value}"
        if not parameter is None:
            msg += f" for parameter {parameter}"
        if not expected is None:
            msg += f" expected value(s) {expected}"
        super().__init__(msg, *args, **kwargs)

class MissingLookupValuesError(Exception):
    """
        Raised when there are zones missing from the lookup DataFrame.
    """
    def __init__(self, missing, column='', *args, **kwargs):
        # Create message
        msg = (f"There are {len(missing)} zones missing from "
                f"the {column} lookup: {list(missing)}")
        super().__init__(msg, *args, **kwargs)

