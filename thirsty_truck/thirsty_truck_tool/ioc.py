#local imports
import dataclasses
import pathlib
import logging
# third party packages
import caf.toolkit
import geopandas as gpd
import pandas as pd
#local
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
    "domestic_bulk_port":None,
    "unitised_eu_imports":None,
    "unitised_eu_exports":None, 
    "unitised_non_eu":["Imp0Exp1", "GBPortctr", "GBRawZone", "Traffic"],
    "ports": ["GBPortctr", "GBZone"],
    "distance_bands": ["start", "end", "rigid", "artic"],
    "gbfm_distance_matrix": None,
    "port_traffic_proportions": ["type", "direction", "accompanied", "artic", "rigid"],
    "pcu_factors": ["zone", "direction", "artic", "rigid"],
}

@dataclasses.dataclass
class TonneToPCUInputs:
    """contains the paths for the tonne to PCU process
    """    
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
    lft_inputs: dict[str, pathlib.Path]
    range: float
    zone_centroids: gpd.GeoDataFrame
@dataclasses.dataclass
class AnalysisInputs:
    """analysis inputs for the config file
    """    
    range: float
    tonne_to_pcu_inputs: TonneToPCUInputs
    zone_centroids_path: pathlib.Path

    def parse_analysis_inputs(self)->ParsedAnalysisInputs:
        """parses the analysis inputs

        Returns
        -------
        ParsedAnalysisInputs
            parsed analysis inputs
        """        
        paths_dict  = dict(zip(TONNE_TO_PCU_KEYS,[
                    self.tonne_to_pcu_inputs.domestic_bulk_port_path,
                    self.tonne_to_pcu_inputs.unitised_eu_imports_path,
                    self.tonne_to_pcu_inputs.unitised_eu_exports_path,
                    self.tonne_to_pcu_inputs.unitised_non_eu_path,
                    self.tonne_to_pcu_inputs.ports_path,
                    self.tonne_to_pcu_inputs.distance_bands_path,
                    self.tonne_to_pcu_inputs.gbfm_distance_matrix_path,
                    self.tonne_to_pcu_inputs.port_traffic_proportions_path,
                    self.tonne_to_pcu_inputs.pcu_factors_path,
            ]
        ))
        zone_centroids = gpd.read_file(self.zone_centroids_path)
        zone_centroids =input_output_constants.check_and_format_centroids(
            zone_centroids, input_output_constants.ZONE_CENTROIDS_REQUIRED_COLUMNS
        )

        return ParsedAnalysisInputs(
            lft_inputs=paths_dict,
            zone_centroids = zone_centroids,
            range= self.range,
        )        

class ThristyTruckConfig(caf.toolkit.BaseConfig):
    """config class for thirsty truck tool
    """    
    plotting_inputs: input_output_constants.PlottingInputs
    analysis_inputs: AnalysisInputs
    operational: input_output_constants.Operational

    def convert_to_m(self, to_m_factor:float)->None:
        """converts revelant variables to m


        Parameters
        ----------
        to_m_factor : float
            factor for to m conversion (e.g. 1000 if variables are in km)
        """        
        self.operational.hex_bin_width = self.operational.hex_bin_width*to_m_factor
        self.analysis_inputs.range = self.analysis_inputs.range*to_m_factor


