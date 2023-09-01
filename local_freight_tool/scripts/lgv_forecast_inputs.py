# -*- coding: utf-8 -*-
"""
    Script for growing the LGV model inputs to a forecast year.

    This is only necessary for inputs which aren't already
    available for forecast years.
"""

##### IMPORTS #####
# Standard imports
import logging
import pathlib

# Third party imports
import caf.toolkit
import pandas as pd
from pydantic import types

# Local imports
from LFT import utilities
from LFT.lgv_model import lgv_inputs

##### CONSTANTS #####
LOG = logging.getLogger("LFT.lgv_forecast_inputs")


##### CLASSES #####
class ForecastInputsConfig(caf.toolkit.BaseConfig):
    base_model_config: types.FilePath
    base_year: int
    forecast_year: int
    output_folder: types.DirectoryPath
    oa_lookup_path: types.FilePath
    forecast_households_path: types.FilePath


##### FUNCTIONS #####
def _calculate_planning_growth(base_path: pathlib.Path, forecast_path: pathlib.Path):
    """Calculate growth values for the TEMPro planning data for the forecast year."""
    index_col = "Area Description"
    data_columns = ["Total", "HHs", "Jobs", "Workers"]
    columns = {index_col: str, **dict.fromkeys(data_columns, float)}
    base = utilities.read_csv(
        base_path, "Base Household projections", columns=columns, index_col=index_col
    )
    forecast = utilities.read_csv(
        forecast_path, "Forecast Household projections", columns=columns, index_col=index_col
    )
    growth = forecast / base
    return growth


def get_planning_growth(
    base_path: pathlib.Path, forecast_path: pathlib.Path, oa_lookup_path: pathlib.Path
) -> pd.DataFrame:
    growth = _calculate_planning_growth(base_path, forecast_path)

    columns = ["lsoa11cd", "msoa11cd", "ladcd", "lsoa11nm", "msoa11nm", "ladnm"]
    LOG.info("Reading OA lookup: %s", oa_lookup_path.name)
    oa_lookup = pd.read_csv(oa_lookup_path, usecols=columns, dtype=str)

    growth = growth.merge(
        oa_lookup, left_index=True, right_on="msoa11cd", how="left", validate="1:m"
    )
    missing = growth[oa_lookup.columns].isna().any(axis=1)
    LOG.warning("%s rows without MSOA join in output area lookup", missing.sum())

    growth = growth.set_index(oa_lookup.columns)
    return growth


def read_base_bres(path: pathlib.Path, forecast_year: int):
    # Read meta data and add comment to date before reading the rest of the file
    meta_rows = 8
    meta_data = []
    with open(path, "rt") as f:
        for _ in range(meta_rows):
            line = f.readline()
            if "Date" in line:
                line = line[: line.rfind('"')] + f' grown to {forecast_year}"\n'
            meta_data.append(line)

    base_bres = pd.read_csv(
        path,
        usecols=lgv_inputs.BRES_HEADER.keys(),
        dtype=lgv_inputs.BRES_HEADER,
        skiprows=meta_rows,
    )

    # Drop any completely empty columns and any rows with missing values
    base_bres.dropna(axis=1, how="all", inplace=True)
    base_bres.dropna(axis=0, how="any", inplace=True)

    return base_bres


def main(params: ForecastInputsConfig) -> None:
    output_folder = params.output_folder / f"LGV Forecast Inputs - {params.forecast_year}"
    output_folder.mkdir(exist_ok=True)

    # TODO(MB) Use LogHelper class from caf.toolkit
    logging.basicConfig(filename=output_folder / "Forecast_inputs.log", level=logging.DEBUG)

    out_path = output_folder / "forecast_inputs_config.yml"
    params.save_yaml(out_path)
    LOG.info("Written: %s", out_path)

    base_config = lgv_inputs.LGVInputPaths.load_yaml(params.base_model_config)
    out_path = output_folder / "base_inputs_config.yml"
    base_config.save_yaml(out_path)
    LOG.info("Written: %s", out_path)

    planning_growth = get_planning_growth(
        base_config.household_paths.path,
        params.forecast_households_path,
        params.oa_lookup_path,
    )
    out_path = output_folder / "planning_data_growth_factors.csv"
    planning_growth.to_csv(out_path)
    LOG.info("Written: %s", out_path)


##### MAIN #####
if __name__ == "__main__":
    main()
