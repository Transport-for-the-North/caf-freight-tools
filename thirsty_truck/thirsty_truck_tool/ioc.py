"""handles parsing and validating inputs and constants for the tools
"""
# local imports
import dataclasses
import pathlib
from typing import Optional

# third party packages
import caf.toolkit
import geopandas as gpd
import pandas as pd

# local
from thirsty_vehicle_tool import input_output_constants, tv_logging

# constants
LOG = tv_logging.get_logger(__name__)

#   process constants
TONNE_TO_PCU_KEYS = [
    "domestic_bulk_port",
    "unitised_eu_imports",
    "unitised_eu_exports",
    "unitised_non_eu",
    "ports",
    "distance_bands",
    "gbfm_distance_matrix",
    "port_traffic_proportions",
    "pcu_factors",
]
TONNE_TO_PCU_COLUMNS = {
    "domestic_bulk_port": None,
    "unitised_eu_imports": None,
    "unitised_eu_exports": None,
    "unitised_non_eu": ["Imp0Exp1", "GBPortctr", "GBRawZone", "Traffic"],
    "ports": ["GBPortctr", "GBZone"],
    "distance_bands": ["start", "end", "rigid", "artic"],
    "gbfm_distance_matrix": None,
    "port_traffic_proportions": ["type", "direction", "accompanied", "artic", "rigid"],
    "pcu_factors": ["zone", "direction", "artic", "rigid"],
}

COMBINED_KEY = "Combined"

LFT_KEYS = ["artic", "rigid"]

DISAGG_KEY_SEP = "--"
@dataclasses.dataclass
class TonneToPCUInputs:
    """contains the paths for the tonne to PCU process"""

    domestic_bulk_port_path: pathlib.Path
    unitised_eu_imports_path: pathlib.Path
    unitised_eu_exports_path: pathlib.Path
    unitised_non_eu_path: pathlib.Path
    ports_path: pathlib.Path
    distance_bands_path: pathlib.Path
    gbfm_distance_matrix_path: pathlib.Path
    port_traffic_proportions_path: pathlib.Path
    pcu_factors_path: pathlib.Path


@dataclasses.dataclass
class ParsedAnalysisInputs:
    """parsed analysis inputs

    LFT inputs path are formatted into a dictionary
    but not parsed as this is handled by the LFT
    """

    ranges: dict[str, float]
    zone_centroids: gpd.GeoDataFrame
    laden_status_factors: pd.DataFrame
    lft_inputs: Optional[dict[str, pathlib.Path]] = None
    od_matrices: Optional[dict[str, pd.DataFrame]] = None
    thirsty_points: Optional[dict[str, gpd.GeoDataFrame]] = None


@dataclasses.dataclass
class AnalysisInputs:
    """analysis inputs for the config file"""

    vehicle_keys: list[str]
    vehicle_ranges: dict[str, dict[str,float]]
    zone_centroids_path: pathlib.Path
    laden_status_factors_path: pathlib.Path
    tonne_to_pcu_inputs: Optional[TonneToPCUInputs] = None
    od_matrices_inputs: Optional[input_output_constants.ODMatrixInputs] = None
    thirsty_points_inputs: Optional[input_output_constants.ThirstyPointsInputs] = None

    def parse_analysis_inputs(self) -> ParsedAnalysisInputs:
        """parses the analysis inputs

        Returns
        -------
        ParsedAnalysisInputs
            parsed analysis inputs
        """
        # format keys
        vehicle_keys = [x.lower() for x in self.vehicle_keys]

        # check that atleast 1 data input is given
        data_input_count = 0
        if self.tonne_to_pcu_inputs is not None:
            data_input_count += 1
        if self.od_matrices_inputs is not None:
            data_input_count += 1
        if self.thirsty_points_inputs is not None:
            data_input_count += 1
        if data_input_count == 0:
            raise ValueError(
                "You must provide one set of inputs from: \n- tonne_to_pcu_inputs"
                "\n- od_matrices_inputs\n- thirsty_points_inputs"
            )
        if data_input_count > 1:
            LOG.warning(
                "You have provided more than one set of inputs from: "
                "\n- tonne_to_pcu_inputs\n- od_matrices_inputs\n- thirsty_points_inputs\n"
                "the last input (according to the list abvove) will be used for analysis"
            )
        # parse and validate laden status factors

        
        laden_status_factors = pd.read_csv(self.laden_status_factors_path, index_col= 0)
        laden_status_factors.columns = laden_status_factors.columns.str.lower()
        input_output_constants.check_columns(
            self.laden_status_factors_path,
            laden_status_factors.columns,
            vehicle_keys,
        )
        laden_status_factors = laden_status_factors[vehicle_keys]

        # format ranges

        if len(vehicle_keys) != len(self.vehicle_ranges):
            raise ValueError("vehicle ranges and keys must be same length")
        ranges = {}

        for vehicle_key, input_ranges in self.vehicle_ranges.items():
            for status_key, range_ in input_ranges.items():
                if vehicle_key.lower() not in vehicle_keys:
                    raise KeyError("range vehicle key not present in inputted vehicle keys")
                if status_key.lower() not in laden_status_factors.index:
                    raise KeyError("range status key not present in inputted laden status factors index")
                ranges[vehicle_key.lower()+DISAGG_KEY_SEP+status_key.lower()] = range_
        #TODO check for missing values

        # parse centroids
        zone_centroids = gpd.read_file(self.zone_centroids_path)
        zone_centroids = input_output_constants.check_and_format_centroids(
            zone_centroids, input_output_constants.ZONE_CENTROIDS_REQUIRED_COLUMNS
        )
        # parse tonne to pcu inputs
        if (
            self.tonne_to_pcu_inputs is not None
            and self.od_matrices_inputs is None
            and self.thirsty_points_inputs is None
        ):
            LOG.info("Proceeding analysis with annual tonnage input")
            for key in LFT_KEYS:
                if key.lower() not in vehicle_keys:
                    raise IndexError(
                        f"When using LFT inputs, the vehicle keys be {' ,'.join(LFT_KEYS)}"
                    )
            paths_dict = dict(
                zip(
                    TONNE_TO_PCU_KEYS,
                    [
                        self.tonne_to_pcu_inputs.domestic_bulk_port_path,
                        self.tonne_to_pcu_inputs.unitised_eu_imports_path,
                        self.tonne_to_pcu_inputs.unitised_eu_exports_path,
                        self.tonne_to_pcu_inputs.unitised_non_eu_path,
                        self.tonne_to_pcu_inputs.ports_path,
                        self.tonne_to_pcu_inputs.distance_bands_path,
                        self.tonne_to_pcu_inputs.gbfm_distance_matrix_path,
                        self.tonne_to_pcu_inputs.port_traffic_proportions_path,
                        self.tonne_to_pcu_inputs.pcu_factors_path,
                    ],
                )
            )
            output = ParsedAnalysisInputs(
                laden_status_factors=laden_status_factors,
                lft_inputs=paths_dict,
                zone_centroids=zone_centroids,
                ranges=ranges,
            )
        elif self.od_matrices_inputs is not None and self.thirsty_points_inputs is None:
            LOG.info("Proceeding analysis with OD matrix input")

            od_matrices = self.od_matrices_inputs.parse(vehicle_keys)

            output = ParsedAnalysisInputs(
                laden_status_factors=laden_status_factors,
                od_matrices=od_matrices,
                zone_centroids=zone_centroids,
                ranges=ranges,
            )

        else:
            LOG.info("Proceeding analysis with thirsty points input")
            thirsty_points = self.thirsty_points_inputs.parse(vehicle_keys)

            output = ParsedAnalysisInputs(
                thirsty_points=thirsty_points,
                laden_status_factors=laden_status_factors,
                zone_centroids=zone_centroids,
                ranges=ranges,
            )

        self.create_output_summary()
        return output
    

    def create_output_summary(self)->None:
        range_output = "Range Inputs\n"
        for vehicle_key, ranges in self.vehicle_ranges.items():
            range_output += f"    {vehicle_key}:\n"
            for status_key, range_ in ranges.items():
                range_output += f"        {status_key} = {range_:.3e} metres\n"
        LOG.info(range_output)
        LOG.info(f"Centroids Input - {self.zone_centroids_path}\n")
        LOG.info(f"Laden Status Factors Input - {self.laden_status_factors_path}\n")

        if self.thirsty_points_inputs is not None:
            thirsty_points_output = "Thirsty Points Inputs\n"
            for i, path in enumerate(self.thirsty_points_inputs.thirsty_points_paths):
                thirsty_points_output += f"    {self.vehicle_keys[i]} - {path}\n"
            LOG.info(thirsty_points_output)
        elif self.od_matrices_inputs is not None:
            od_matrices_output = "OD Matrices Inputs\n"
            for i, path in enumerate(self.od_matrices_inputs.od_matrices_path):
                od_matrices_output += f"    {self.vehicle_keys[i]} - {path}\n"
            LOG.info(od_matrices_output)
        else:
            tonne_to_pcu_output = "Tonne to PCU Inputs\n"
            tonne_to_pcu_output += f"   domestic_bulk_port_path - {self.tonne_to_pcu_inputs.domestic_bulk_port_path}\n"
            tonne_to_pcu_output += f"   unitised_eu_imports_path - {self.tonne_to_pcu_inputs.unitised_eu_imports_path}\n"
            tonne_to_pcu_output += f"   unitised_eu_exports_path - {self.tonne_to_pcu_inputs.unitised_eu_exports_path}\n"
            tonne_to_pcu_output += f"   unitised_non_eu_path - {self.tonne_to_pcu_inputs.unitised_non_eu_path}\n"
            tonne_to_pcu_output += f"   ports_path - {self.tonne_to_pcu_inputs.ports_path}\n"
            tonne_to_pcu_output += f"   distance_bands_path - {self.tonne_to_pcu_inputs.distance_bands_path}\n"
            tonne_to_pcu_output += f"   gbfm_distance_matrix_path - {self.tonne_to_pcu_inputs.gbfm_distance_matrix_path}\n"
            tonne_to_pcu_output += f"   port_traffic_proportions_path - {self.tonne_to_pcu_inputs.port_traffic_proportions_path}\n"
            tonne_to_pcu_output += f"   pcu_factors_path - {self.tonne_to_pcu_inputs.pcu_factors_path}\n"
            LOG.info(tonne_to_pcu_output)


class ThristyTruckConfig(caf.toolkit.BaseConfig):
    """config class for thirsty truck tool"""

    plotting_inputs: input_output_constants.PlottingInputs
    analysis_inputs: AnalysisInputs
    operational: input_output_constants.Operational

    def convert_to_m(self, to_m_factor: float) -> None:
        """converts revelant variables to m


        Parameters
        ----------
        to_m_factor : float
            factor for to m conversion (e.g. 1000 if variables are in km)
        """
        self.operational.hex_bin_width = self.operational.hex_bin_width * to_m_factor
        for vehicle_key, ranges in self.analysis_inputs.vehicle_ranges.items():
            for status_key, range_ in ranges.items():
                self.analysis_inputs.vehicle_ranges[vehicle_key][status_key] = range_ * to_m_factor



def convert_lft_keys(
    input_vehicle_keys: list[str], lft_vehicle_keys: list[str]
) -> dict[str, str]:
    """checks the LFT keys match the inputted keys (case insensitive)
    returns a lookup for the LFT keys to the inputted keys to change the casing

    Parameters
    ----------
    input_vehicle_keys : list[str]
        vehicles keys inputted from the config file
    lft_vehicle_keys : list[str]
        vehicles keys outputted by the LFT

    Returns
    -------
    dict[str, str]
        Key lookup object
    """
    new_keys = {}
    lower_input_vehicle_keys = [x.lower() for x in input_vehicle_keys]
    for key in lft_vehicle_keys:
        if key.lower() in lower_input_vehicle_keys:
            new_keys[key] = input_vehicle_keys[
                lower_input_vehicle_keys.index(key.lower())
            ]
        else:
            raise IndexError(
                "inputted vehicle keys don't match those of the LFT\n"
                f"the keys must conatain {' ,'.join(lower_input_vehicle_keys)} "
                "(case and order insensetive"
            )
    return new_keys
