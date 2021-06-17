# -*- coding: utf-8 -*-
"""
    Module containing functionality for reading and pre-processing
    the LGV inputs which are used for multiple segments.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# Third party imports
import pandas as pd

# Local imports
from .. import utilities
from ..rezone import Rezone


##### CONSTANTS #####
HH_PROJECTIONS_HEADER = {"Area Description": str, "HHs": float}


##### FUNCTIONS #####
def household_projections(path: Path, zone_lookup: Path) -> pd.DataFrame:
    """Reads the household projections CSV and converts to model zone system.

    CSV should contain two columns with headers as defined in
    `HH_PROJECTIONS_HEADER`.

    Parameters
    ----------
    path : Path
        Path to the household projections CSV.
    zone_lookup : Path
        Path to the zone correspondence CSV.

    Returns
    -------
    pd.DataFrame
        Household projections in the model zone system with columns
        'Zone' and 'Households'.
    """
    households = utilities.read_csv(
        path, "Household projections", columns=HH_PROJECTIONS_HEADER
    )
    lookup = Rezone.read(zone_lookup, None)
    cols = list(HH_PROJECTIONS_HEADER.keys())
    rezoned = Rezone.rezoneOD(households, lookup, dfCols=(cols[0],), rezoneCols=cols[1])
    rezoned.columns = ["Zone", "Households"]
    return rezoned


# TODO Remove test code
if __name__ == "__main__":
    hh_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Household Projections\UK_HH_projections_2018-MSOA.csv"
    )
    zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\NTEM to NoHAM Lookup\NTEM_to_NoHAM_zone_correspondence-updated-20210617.csv"
    )
    household_projections(hh_path, zc_path)
