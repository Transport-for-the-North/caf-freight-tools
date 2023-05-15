#local imports
import dataclasses
import pathlib
import logging
# third party packages
import caf.toolkit
import geopandas as gpd
#local
from thirsty_vehicle_tool import input_output_constants

# constants
LOG = logging.getLogger(__name__)

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

@dataclasses.dataclass
class TonneToPCUInputs:
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
class ParsedTonneToPCUInputs:
    domestic_bulk_port: gpd.GeoDataFrame
    unitised_eu_imports: gpd.GeoDataFrame
    unitised_eu_exports: gpd.GeoDataFrame
    unitised_non_eu: gpd.GeoDataFrame
    ports: gpd.GeoDataFrame
    distance_bands: gpd.GeoDataFrame
    gbfm_distance_matrix: gpd.GeoDataFrame
    port_traffic_proportions: gpd.GeoDataFrame
    pcu_factors: gpd.GeoDataFrame

@dataclasses.dataclass
class AnalysisInputs:
    range: float
    tonne_to_pcu_inputs: TonneToPCUInputs



class ThristyTruckConfig(caf.toolkit):
    plotting_inputs: input_output_constants.PlottingInputs
    analysis_inputs: AnalysisInputs
    operational: input_output_constants.Operational

    def parse_analysis_inputs(self):
        paths_dict  = dict(zip(TONNE_TO_PCU_KEYS,[
                    self.analysis_inputs.tonne_to_pcu_inputs.domestic_bulk_port_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.unitised_eu_imports_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.unitised_eu_exports_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.unitised_non_eu_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.ports_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.distance_bands_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.gbfm_distance_matrix_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.port_traffic_proportions_path,
                    self.analysis_inputs.tonne_to_pcu_inputs.pcu_factors_path,
            ]
        ))
        
    
