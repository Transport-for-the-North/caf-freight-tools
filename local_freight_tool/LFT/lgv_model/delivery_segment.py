# -*- coding: utf-8 -*-
"""
    Module to calculate the delivery trips for the LGV model.
"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# Third party imports
import pandas as pd

# Local imports
from . import lgv_inputs
from .. import utilities, errors


##### CLASSES #####
class DeliveryTripEnds:
    """Functionality for generating the LGV delivery segment trip ends.

    Parameters
    ----------
    voa_paths : tuple[Path, Path]
        - Path to the CSV containing the VOA rateable values data.
        - Path to the postcode zone correspondence file to convert
          VOA data to model zone system.
    bres_paths : tuple[Path, Path]
        - Path to the CSV containing the BRES data.
        - Path to the zone correspondence CSV for converting the
          BRES data to the model zone system.
    household_paths : tuple[Path, Path]
        - Path to the CSV containing the household projections data.
        - Path to the zone correpondence file to convert household
          data to the model zone system.
    parameters_path : Path
        Path to Excel Workbook containing sheet with the delivery
        segment parameters.
    """

    BRES_AGGREGATION = {"All": lgv_inputs.letters_range(end="U")}
    VOA_SCAT_CODES = (217, 267)
    PARAMETERS_SHEET = "Delivery Segment Parameters"
    PARAMETERS_HEADER = {"Parameter": str, "Value": float}
    PARAMETERS = [
        "Annual Trip Productions - Parcel Stem",
        "Annual Trips - Parcel Bush",
        "Annual Trips - Grocery Bush",
        "B2C vs B2B Weighting",
        "Annual Trip Length - Parcel Stem (kms)",
        "Annual Trip Length - Parcel Bush (kms)",
        "Annual Trip Length - Grocery (kms)",
        "Intra-Zonal Proportions - Parcel",
        "Intra-Zonal Proportions - Grocery",
        "Bush Cut-off (kms)",
    ]

    def __init__(
        self,
        voa_paths: tuple[Path, Path],
        bres_paths: tuple[Path, Path],
        household_paths: tuple[Path, Path],
        parameters_path: Path,
    ):
        """Initialise class by checking inputs files exist and are expected type."""
        self._check_paths(voa_paths, bres_paths, household_paths, parameters_path)
        # Initialise instance variables
        self.depots = None
        self.bres = None
        self.households = None
        self.parameters = None

    def _check_paths(
        self,
        voa_paths: tuple[Path, Path],
        bres_paths: tuple[Path, Path],
        household_paths: tuple[Path, Path],
        parameters_path: Path,
    ):
        """Checks the input files exist and are the expected type."""
        self._voa_path = utilities.check_file_path(
            voa_paths[0], "VOA data", ".csv", ".txt", return_path=True
        )
        self._voa_zc = utilities.check_file_path(
            voa_paths[1], "VOA lookup", ".csv", ".txt", return_path=True
        )
        self._bres_path = utilities.check_file_path(
            bres_paths[0], "BRES data", ".csv", ".txt", return_path=True
        )
        self._bres_zc = utilities.check_file_path(
            bres_paths[1], "BRES lookup", ".csv", ".txt", return_path=True
        )
        self._household_path = utilities.check_file_path(
            household_paths[0], "Household data", ".csv", ".txt", return_path=True
        )
        self._household_zc = utilities.check_file_path(
            household_paths[1], "Household lookup", ".csv", ".txt", return_path=True
        )
        self._parameters_path = utilities.check_file_path(
            parameters_path, "Delivery Parameters", ".xlsx", return_path=True
        )

    @property
    def inputs_summary(self) -> pd.DataFrame:
        """pd.DataFrame : Summary table of class input parameters."""
        return pd.DataFrame.from_dict(
            {
                "VOA Data Path": str(self._voa_path),
                "VOA Zone Correpondence Path": str(self._voa_zc),
                "BRES Data Path": str(self._bres_path),
                "BRES Zone Correpondence Path": str(self._bres_zc),
                "Household Data Path": str(self._household_path),
                "Household Zone Correspondence Path": str(self._household_zc),
                "Delivery Parameters Path": str(self._parameters_path),
            },
            orient="index",
            columns=["Value"],
        )

    def read(self):
        """Read the input data and perform any necessary conversions.

        See Also
        --------
        read_parameters: Reads the parameters spreadsheet.
        .lgv_inputs.household_projections
            Reads and converts household input CSV.
        .lgv_inputs.filtered_bres
            Reads, filters and converts the BRES input CSV.
        """
        self.depots = lgv_inputs.voa_ratings_list(
            self._voa_path, self.VOA_SCAT_CODES, self._voa_zc
        )
        self.households = lgv_inputs.household_projections(
            self._household_path, self._household_zc
        )
        self.households.set_index("Zone", inplace=True)
        self.bres = lgv_inputs.filtered_bres(
            self._bres_path, self._bres_zc, self.BRES_AGGREGATION
        )
        self.bres.set_index("Zone", inplace=True)
        self.parameters = self.read_parameters(self._parameters_path)

    @classmethod
    def read_parameters(cls, path: Path) -> dict[str, float]:
        """Extract expected `PARAMETERS` from the given spreadsheet.

        Parameters
        ----------
        path : Path
            Path to the Excel Workbook containing a sheet with
            the delivery segment parameters.

        Returns
        -------
        dict[str, float]
            Contains keys from `PARAMETERS` list with their
            corresponding value from the input file.

        Raises
        ------
        errors.MissingDataError
            If any of `PARAMETERS` cannot be found in the input
            worksheet.

        See Also
        --------
        PARAMETERS: Lists all required parameter names.
        PARAMETERS_SHEET: Expected name of the sheet in the workbook.
        PARAMETERS_HEADER: Expected column names and types in the sheet.
        """
        df = utilities.read_multi_sheets(
            path, {cls.PARAMETERS_SHEET: cls.PARAMETERS_HEADER}
        )[cls.PARAMETERS_SHEET]
        df["Parameter"] = df["Parameter"].str.lower().str.strip()
        df.set_index("Parameter", inplace=True)
        params = {}
        missing = []
        for p in cls.PARAMETERS:
            try:
                params[p] = df.at[p.lower().strip(), "Value"]
            except KeyError:
                missing.append(p)
        if missing:
            raise errors.MissingDataError("Delivery Parameters", missing)
        return params


# TODO Remove test code
if __name__ == "__main__":
    voa_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\VOA Data\uk-englandwales-ndr-2017-listentries-compiled-epoch-0024-baseline-csv\uk-englandwales-ndr-2017-listentries-compiled-epoch-0024-baseline-csv.csv"
    )
    voa_zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Postcode to NoHAM Lookup\postcode_to_noham_zone_correspondence-with_additions.csv"
    )
    hh_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\Household Projections\UK_HH_projections_2018-MSOA.csv"
    )
    hh_zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\NTEM to NoHAM Lookup\NTEM_to_NoHAM_zone_correspondence-updated-20210617.csv"
    )
    bres_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\BRES Data\BRES_2018_sections_GB_LSOA.csv"
    )
    bres_zc_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\lsoa_datazone_to_noham_zone_correspondence_missing_zones_added.csv"
    )
    params_path = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\LGV_input_tables.xlsx"
    )
    delivery_te = DeliveryTripEnds(
        (voa_path, voa_zc_path),
        (bres_path, bres_zc_path),
        (hh_path, hh_zc_path),
        params_path,
    )
    delivery_te.read()
    print(
        delivery_te.inputs_summary,
        delivery_te.depots,
        delivery_te.bres,
        delivery_te.households,
        delivery_te.parameters,
        sep="\n",
    )
