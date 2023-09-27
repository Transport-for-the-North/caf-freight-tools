# -*- coding: utf-8 -*-
"""
    Script for growing the LGV model inputs to a forecast year.

    This is only necessary for inputs which aren't already
    available for forecast years.
"""

##### IMPORTS #####
# Standard imports
import datetime as dt
import logging
import pathlib
import sys
from typing import Any, Callable, Iterator

# Third party imports
import caf.toolkit
from matplotlib import pyplot as plt, ticker
import numpy as np
import pandas as pd
import pydantic
from pydantic import dataclasses, types
from scipy import stats
import strictyaml


# Local imports
sys.path.extend(["local_freight_tool", "."])
# pylint: disable=wrong-import-position
from LFT import utilities
from LFT.lgv_model import commute_segment, lgv_inputs

# pylint: enable=wrong-import-position

##### CONSTANTS #####
LOG = logging.getLogger("LFT.lgv_forecast_inputs")
CONFIG_PATH = pathlib.Path("scripts/lgv_forecast_inputs.yml")
BASE_LGV_GROWTH_FACTOR = 1.51
LGV_SURVEY_YEAR = 2003


##### CLASSES #####
class ForecastInputsConfig(caf.toolkit.BaseConfig):
    base_model_config: types.FilePath
    base_year: int
    forecast_year: int
    output_folder: types.DirectoryPath
    oa_lookup_path: types.FilePath
    base_planning_path: types.FilePath
    forecast_planning_path: types.FilePath
    forecasted_vehicle_kms: types.FilePath


@dataclasses.dataclass(config={"arbitrary_types_allowed": True})
class NTEMGrowthData:
    lsoa: pd.DataFrame
    msoa: pd.DataFrame
    lad: pd.DataFrame

    pop_col: str = "population"
    households_col: str = "households"
    jobs_col: str = "jobs"
    workers_col: str = "workers"

    @pydantic.root_validator(skip_on_failure=True)
    def _check_columns(cls, values: dict[str, Any]) -> dict[str, Any]:
        # pylint: disable=no-self-argument
        col_names = ["pop_col", "households_col", "jobs_col", "workers_col"]
        columns = [values[i] for i in col_names]

        for name in ("lsoa", "msoa", "lad"):
            data: pd.DataFrame = values[name]

            missing = [i for i in columns if i not in data.columns]
            if len(missing) > 0:
                raise ValueError(f"{len(missing)} columns missing from {name}: {missing}")

            values[name] = data[columns]

        return values

    def __iter__(self) -> Iterator[tuple[str, pd.DataFrame]]:
        yield "lsoa", self.lsoa
        yield "msoa", self.msoa
        yield "lad", self.lad


class _GrowthFactorLinRegress:
    # TODO Add docstrings to class and methods
    def __init__(self, data: pd.Series) -> None:
        self._data = data
        self._results = stats.linregress(data.index, data.values)

    def line(self, x: np.ndarray) -> np.ndarray:
        return (self._results.slope * x) + self._results.intercept

    def year_value(self, x: int):
        if x in self._data.index:
            return self._data.at[x]
        else:
            return self.line(x)

    @property
    def data(self) -> pd.Series:
        return self._data.copy()

    @property
    def slope(self) -> float:
        return self._results.slope

    @property
    def intercept(self) -> float:
        return self._results.intercept

    @property
    def rvalue(self) -> float:
        return self._results.rvalue


##### FUNCTIONS #####
def _init_logger(output_folder: pathlib.Path):
    root = logging.getLogger("LFT")
    root.setLevel(logging.DEBUG)

    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    stream_format = logging.Formatter(
        "{asctime} [{levelname:^8.8}] {message}", datefmt="%H:%M:%S", style="{"
    )
    stream.setFormatter(stream_format)
    root.addHandler(stream)

    file = logging.FileHandler(output_folder / "Forecast_inputs.log")
    file.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "{asctime} [{name:30.30}] [{module:20.20}:{lineno!s:5.5}] "
        "[{levelname:^8.8}] {message}",
        style="{",
    )
    file.setFormatter(file_format)
    root.addHandler(file)


def _load_planning_data(base_path: pathlib.Path, forecast_path: pathlib.Path):
    """Calculate growth values for the TEMPro planning data for the forecast year."""
    # TODO(MB) Load NTEM data directly from the databases, functionality for this
    # exists in NorMITs-Demand
    index_col = ["Area Description", "Name"]
    rename_columns = {
        "Total": NTEMGrowthData.pop_col,
        "HHs": NTEMGrowthData.households_col,
        "Jobs": NTEMGrowthData.jobs_col,
        "Workers": NTEMGrowthData.workers_col,
    }
    columns = {**dict.fromkeys(index_col, str), **dict.fromkeys(rename_columns.keys(), float)}

    dataframes = []
    for name, path in (("base", base_path), ("forecast", forecast_path)):
        data = utilities.read_csv(
            path, f"{name} Household projections", columns=columns, index_col=index_col
        )
        data = data.rename(columns=rename_columns)
        data.columns = pd.MultiIndex.from_product([[name], data.columns.str.lower()])
        dataframes.append(data)

    return pd.concat(dataframes, axis=1)


def load_oa_lookup(path: pathlib.Path) -> pd.DataFrame:
    # TODO Docstring
    columns = ["lsoa11cd", "msoa11cd", "ladcd", "ladnm"]
    LOG.info("Reading OA lookup: %s", path.name)
    lookup = pd.read_csv(path, usecols=columns, dtype=str)
    lookup = lookup.rename(columns={"lsoa11cd": "lsoa", "msoa11cd": "msoa", "ladcd": "lad"})
    return lookup.drop_duplicates()


def _normalise_names(data: pd.Series) -> pd.Series:
    # TODO Docstring
    data = data.str.lower().str.strip()
    data = data.str.replace(r"[!\"#$%&'\()*+,-./:;<=>?@\][\\^_`{|}~]", "", regex=True)
    data = data.str.replace(r"\s+", " ", regex=True)

    return data


def _normalise_lad_names(data: pd.Series) -> pd.Series:
    # TODO Docstring
    data = _normalise_names(data)

    lad_renaming = {
        "the vale of glamorgan": "vale of glamorgan",
        "comhairle nan eilean siar": "na heileanan siar",
        "shepway": "folkestone and hythe",
    }

    return data.replace(lad_renaming)


def _merge_check(
    data: pd.DataFrame, title: str, merge_data: str, left_name: str, right_name: str
) -> None:
    # TODO Docstring
    source_lookup = {"left_only": left_name, "right_only": right_name, "both": "both"}

    total = len(data)
    uniques = np.unique(data["_merge"], return_counts=True)

    for loc, n in zip(*uniques):
        if loc == "both":
            dataset = "both datasets"
        else:
            dataset = f"{source_lookup[loc]} dataset only"

        LOG.warning(
            "%s (%s) %s found in %s, for %s",
            n,
            f"{n / total:.0%}",
            merge_data,
            dataset,
            title,
        )


def get_planning_growth(
    base_path: pathlib.Path, forecast_path: pathlib.Path, lookup: pd.DataFrame
) -> NTEMGrowthData:
    # TODO Docstring
    planning_data = _load_planning_data(base_path, forecast_path)

    lad_growth: pd.DataFrame = planning_data.loc["Authority"]
    lad_growth = lad_growth["forecast"] / lad_growth["base"]
    lad_lookup = lookup.groupby(["lad", "ladnm"], as_index=False)[["lad", "ladnm"]].first()
    lad_lookup.loc[:, "ladnm"] = _normalise_lad_names(lad_lookup["ladnm"])

    lad_growth.index = _normalise_lad_names(lad_growth.index.to_series())
    lad_growth = lad_growth.merge(
        lad_lookup,
        left_index=True,
        right_on="ladnm",
        validate="1:1",
        how="outer",
        indicator=True,
    )

    _merge_check(
        lad_growth,
        "LAD growth factors",
        "LAD names",
        left_name="planning data",
        right_name="LAD lookup",
    )
    lad_growth = (
        lad_growth.set_index("lad").drop(columns=["ladnm", "_merge"]).dropna(how="any")
    )

    planning_data.index = planning_data.index.droplevel("Name")
    msoa_mask = planning_data.index.str.match(r"[ESWN]\d+", case=False)
    msoa_growth: pd.DataFrame = (
        planning_data.loc[msoa_mask, "forecast"] / planning_data.loc[msoa_mask, "base"]
    )

    lsoa_lookup = lookup.groupby(["msoa", "lsoa"], as_index=False)[["msoa", "lsoa"]].first()
    msoa_growth = msoa_growth.merge(
        lsoa_lookup,
        left_index=True,
        right_on="msoa",
        how="outer",
        validate="1:m",
        indicator=True,
    )

    _merge_check(msoa_growth, "LSOA growth factors", "MSOAs", "planning data", "LSOA lookup")
    msoa_growth = msoa_growth.drop(columns="_merge")

    lsoa_growth = msoa_growth.drop(columns="msoa").groupby("lsoa").first().dropna(how="any")
    msoa_growth = msoa_growth.drop(columns="lsoa").groupby("msoa").first().dropna(how="any")

    return NTEMGrowthData(lsoa=lsoa_growth, msoa=msoa_growth, lad=lad_growth)


def read_base_bres(path: pathlib.Path, forecast_year: int) -> tuple[pd.DataFrame, list[str]]:
    # TODO Docstring
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

    return base_bres, meta_data


def grow_bres(
    base_path: pathlib.Path,
    output_path: pathlib.Path,
    growth: NTEMGrowthData,
    forecast_year: int,
) -> pathlib.Path:
    # TODO Docstring
    factor_col = growth.jobs_col

    base_bres, bres_meta = read_base_bres(base_path, forecast_year)
    forecast_bres = base_bres.merge(
        growth.lsoa[factor_col],
        left_on="mnemonic",
        right_index=True,
        validate="1:1",
        how="left",
        indicator=True,
    )
    _merge_check(forecast_bres, "growing BRES data", "LSOAs", "BRES base", "LSOA growth")

    missing = forecast_bres[factor_col].isna()
    scot_zones = forecast_bres["mnemonic"].str.lower().str.startswith("s")
    missing_not_scot = (missing & ~scot_zones).sum()

    msg = f"{missing_not_scot} LSOAs outside Scotland don't have LSOA growth factors"
    if missing_not_scot > 0:
        raise ValueError(msg)
    else:
        LOG.info(msg)

    if (missing & scot_zones).sum() > 0:
        scot_growth = growth.lad.loc[
            growth.lad.index.str.lower().str.startswith("s"), growth.jobs_col
        ].mean()
        LOG.warning(
            "%s Scottish LSOAs in BRES data being grown "
            "with average Scottish growth from LADs (%.2f)",
            scot_zones.sum(),
            scot_growth,
        )
        forecast_bres.loc[scot_zones & missing, factor_col] = scot_growth

    for column, type_ in lgv_inputs.BRES_HEADER.items():
        if type_ is float:
            forecast_bres.loc[:, column] = forecast_bres[column] * forecast_bres[factor_col]

    forecast_bres = forecast_bres.drop(columns=factor_col)

    with open(output_path, "wt", encoding="utf-8") as file:
        file.write("".join(bres_meta))
        forecast_bres.to_csv(file, index=False)
    LOG.info(
        "Grown BRES data to %s using %s and saved to: %s",
        forecast_year,
        factor_col,
        output_path,
    )

    return output_path


def str_replace(text: str, replace: list[tuple[str, str]]) -> str:
    # TODO Docstring
    for old, new in replace:
        text = text.replace(old, new)
    return text


def grow_ndr_floorspace(
    base_path: pathlib.Path,
    base_year: int,
    forecast_year: int,
    growth: NTEMGrowthData,
    output_path: pathlib.Path,
) -> pathlib.Path:
    # TODO Docstring
    factor_col = growth.jobs_col
    base_ndr, data_columns = commute_segment.read_ndr_floorspace(base_path, base_year, {})

    area_col = list(commute_segment.BUSINESS_FLOORSPACE_HEADER.keys())[0]
    forecast_ndr = base_ndr.merge(
        growth.lad[factor_col],
        how="left",
        left_on=area_col,
        right_index=True,
        validate="1:1",
        indicator=True,
    )
    _merge_check(
        forecast_ndr, "grown NDR floorspace", "LADs", "base NDR floorspace", "LAD factors"
    )

    before = len(forecast_ndr)
    forecast_ndr = forecast_ndr.dropna(how="any")
    dropped = before - len(forecast_ndr)
    if dropped > 0:
        LOG.warning("Dropped %s rows from grown NDR floorspace for containing Nans", dropped)
    else:
        LOG.info("No rows dropped from grown NDR floorspace for containing Nans")

    for column in data_columns:
        forecast_ndr.loc[:, column] = forecast_ndr[column] * forecast_ndr[factor_col]

    years_replace = [
        (str(base_year - 2000 + i), str(forecast_year - 2000 + i)) for i in (-1, 0, 1)
    ]
    forecast_ndr = forecast_ndr.drop(columns=[factor_col, "_merge"])
    forecast_ndr.columns = [str_replace(i, years_replace) for i in forecast_ndr.columns]

    forecast_ndr.to_csv(output_path, index=False)
    LOG.info(
        "Grown NDR floorspace from %s to %s using %s and saved to: %s",
        base_year,
        forecast_year,
        factor_col,
        output_path,
    )

    return output_path


def grow_english_dwellings_data(
    base_path: pathlib.Path,
    output_path: pathlib.Path,
    base_year: int,
    forecast_year: int,
    growth: NTEMGrowthData,
) -> pathlib.Path:
    # TODO Docstring
    factor_col = growth.households_col
    dwellings, data_columns = commute_segment.read_english_dwellings(
        base_path, base_year, {}, False
    )

    dwellings = dwellings.merge(
        growth.lad[factor_col],
        how="left",
        left_on=commute_segment.E_DWELLINGS_HEADER[0],
        right_index=True,
        validate="1:1",
        indicator=True,
    )
    _merge_check(
        dwellings, "growing English dwellings", "LADs", "base dwellings", "LAD growth"
    )

    for column in data_columns:
        dwellings.loc[:, column] = (dwellings[column] * dwellings[factor_col]).round()

    forecast_sheet = f"{forecast_year}-{forecast_year - 1999}"
    dwellings.drop(columns=[factor_col, "_merge"]).to_excel(
        output_path, sheet_name=forecast_sheet, index=False, startrow=3
    )
    LOG.info(
        "Grown English dwellings from %s to %s using %s, saved to '%s' sheet '%s'",
        base_year,
        forecast_year,
        factor_col,
        output_path.name,
        forecast_sheet,
    )

    return output_path


def grow_sc_w_dwellings_data(
    base_path: pathlib.Path,
    output_path: pathlib.Path,
    base_year: int,
    forecast_year: int,
    growth: NTEMGrowthData,
) -> pathlib.Path:
    # TODO Docstring
    factor_col = growth.households_col
    dwellings, data_columns = commute_segment.read_sc_w_dwellings(base_path, base_year)

    zone_col = [i for i in dwellings.columns if i not in data_columns]
    if len(zone_col) != 1:
        raise ValueError(f"{len(zone_col)} zone columns but expected 1: {zone_col}")
    zone_col = zone_col[0]

    dwellings = dwellings.merge(
        growth.lad[factor_col],
        how="left",
        left_on=zone_col,
        right_index=True,
        validate="1:1",
        indicator=True,
    )
    _merge_check(
        dwellings,
        "grown Scotland & Wales dwellings",
        "LADs",
        "base dwellings",
        "LAD growth factors",
    )

    missing = dwellings[factor_col].isna()
    if missing.sum() > 0:
        avg_growth = growth.lad[factor_col].mean()
        dwellings.loc[missing, factor_col] = avg_growth
        LOG.warning(
            "%s zones missing from LAD growth factors, using average growth %.2f",
            missing.sum(),
            avg_growth,
        )

    dwellings = dwellings.drop(columns=[factor_col, "_merge"])
    dwellings.rename(
        columns=dict(zip(data_columns, [str(forecast_year + i) for i in (0, 1)])), inplace=True
    )

    dwellings.to_csv(output_path, index=False)
    LOG.info(
        "Grown Scotland and Wales dwellings from %s to %s using %s and saved to: %s",
        base_year,
        forecast_year,
        factor_col,
        output_path,
    )

    return output_path


def grow_occupation_data(
    ew_path: pathlib.Path,
    sc_path: pathlib.Path,
    growth: NTEMGrowthData,
    base_year: int,
    forecast_year: int,
    output_folder: pathlib.Path,
) -> dict[str, pathlib.Path]:
    # TODO Docstring
    def filter_float(data: dict[str, type]) -> list[str]:
        return [k for k, v in data.items() if v is float]

    factor_col = growth.workers_col

    meta_rows = {}
    for key, path in (("EW", ew_path), ("SC", sc_path)):
        meta_rows[key] = ""

        with open(path, "rt", encoding="utf-8") as file:
            for _ in range(commute_segment.QS606_HEADER_FOOTER[key][0]):
                line = file.readline()
                if "Date" in line:
                    line = line[: line.rfind('"')] + f' grown to {forecast_year}"\n'

                meta_rows[key] += line

    qs_data = commute_segment.read_qs606(ew_path, sc_path, False)

    # Use LSOA growth factors for England & Wales
    qs_data["EW"] = qs_data["EW"].merge(
        growth.lsoa[factor_col],
        how="left",
        left_on=list(commute_segment.QS606_BASE_HEADERS.keys())[0],
        right_index=True,
        validate="1:1",
        indicator=True,
    )
    _merge_check(
        qs_data["EW"], "England & Wales occupation", "LSOAs", "base occupation", "LSOA growth"
    )

    data_columns: dict[str, list[str]] = {
        k: filter_float(v) for k, v in commute_segment.QS606_HEADERS.items()
    }
    key = "EW"
    for column in data_columns[key]:
        qs_data[key].loc[:, column] = qs_data[key][column] * qs_data[key][factor_col]
    LOG.info(
        "Growing England & Wales occupation from %s to %s using LSOA %s",
        base_year,
        forecast_year,
        factor_col,
    )

    # TODO Use more spatially disaggregate values for Scotland
    # Use single average growth factor for Scotland because they're datazones not LSOAs
    key = "SC"
    scot_growth_mask = growth.lad.index.str.lower().str.startswith("s")
    avg_growth = growth.lad.loc[scot_growth_mask, factor_col].mean()
    for column in data_columns[key]:
        qs_data[key].loc[:, column] = qs_data[key][column] * avg_growth
    LOG.info(
        "Growing Scotland occupation from %s to %s using average Scottish growth "
        "(%s) because Scotland data is given by datazone instead of LSOA",
        base_year,
        forecast_year,
        factor_col,
    )

    output_paths: dict[str, pathlib.Path] = {}
    for key, data in qs_data.items():
        output_paths[key] = output_folder / f"QS606{key}_grown_{forecast_year}.csv"

        with open(output_paths[key], "wt", encoding="utf-8", newline="") as file:
            file.write(meta_rows[key])
            data.drop(columns=[factor_col, "_merge"], errors="ignore").to_csv(
                file, index=False
            )

        LOG.info("Written grown occupation data to: %s", output_paths[key].name)

    return output_paths


def grow_warehouse_data(
    base_path: pathlib.Path,
    commute_paths: lgv_inputs.CommuteWarehousePaths,
    growth: NTEMGrowthData,
    base_year: int,
    forecast_year: int,
    output_folder: pathlib.Path,
) -> dict[str, pathlib.Path]:
    # TODO Docstring
    factor_col = growth.jobs_col
    zone_col = "LSOA11CD"
    data_col = "area"

    paths = [
        ("delivery", base_path),
        ("commute_high", commute_paths.high),
        ("commute_medium", commute_paths.medium),
        ("commute_low", commute_paths.low),
    ]
    output_paths: dict[str, pathlib.Path] = {}

    for name, path in paths:
        data = utilities.read_csv(path, columns={zone_col: str, data_col: float})

        data = data.merge(
            growth.lsoa[factor_col],
            how="left",
            left_on=zone_col,
            right_index=True,
            validate="1:1",
            indicator=True,
        )
        _merge_check(
            data, f"growing {name} warehouse", "LSOAs", f"{name} warehouse", "LSOA growth"
        )
        data.loc[:, data_col] = data[data_col] * data[factor_col]

        output_paths[name] = output_folder / f"{name}_grown_{forecast_year}.csv"
        data.drop(columns=[factor_col, "_merge"]).to_csv(output_paths[name], index=False)
        LOG.info(
            "Grown %s from %s to %s with %s, written to %s",
            name,
            base_year,
            forecast_year,
            factor_col,
            output_paths[name].name,
        )

    return output_paths


def _recursive_apply(data: dict[str, Any], func: Callable) -> dict[str, Any]:
    # TODO Docstring
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = _recursive_apply(value, func)
        elif isinstance(value, (list, tuple)):
            data[key] = [func(i) for i in value]
        else:
            data[key] = func(value)

    return data


def write_forecast_log(
    paths: dict[str, Any],
    output_path: pathlib.Path,
    base_year: int,
    forecast_year: int,
) -> None:
    # TODO Docstring
    yaml = strictyaml.as_document(_recursive_apply(paths, str)).as_yaml()

    with open(output_path, "wt", encoding="utf-8") as file:
        file.write(
            f"# LGV model inputs grown from {base_year} to {forecast_year}, "
            f"produced at: {dt.datetime.now():%c}\n"
        )
        file.write(yaml)

    LOG.info("Written output log to %s", output_path)


def _plot_linear_fit(
    fit: _GrowthFactorLinRegress, base_year: int, forecast_year: int, output_path: pathlib.Path
) -> None:
    # TODO Docstring
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.set_tight_layout(True)
    ax.set_ylabel("LGV Vehicle Kilometres (billions)")
    ax.set_xlabel("Year")
    ax.set_title("LGV Forecasted Vehicle Kilometres", fontsize="x-large")

    ax.scatter(fit.data.index, fit.data.values, label="RTF Data", c="C0")
    ax.plot(
        fit.data.index,
        fit.line(fit.data.index),
        c="C1",
        ls="--",
        label=f"Linear Fit: $y={fit.slope:.2f}x"
        f"{+fit.intercept:.0f}$, $R^2={fit.rvalue**2:.2f}$",
    )

    years = {"LGV Survey": LGV_SURVEY_YEAR, "Base": base_year, "Forecast": forecast_year}
    for nm, yr in years.items():
        val = fit.year_value(yr)
        ax.annotate(
            f"{nm} Year\n({yr})",
            (yr, val),
            arrowprops=dict(arrowstyle="->", color="C2"),
            xytext=(yr + 1, val - 5),
            bbox=dict(fc=(0.8, 1, 0.8, 0.5), alpha=0.5, ec="C2", boxstyle="Round"),
        )

    ax.set_ylim(0, None)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid()
    ax.grid(which="minor", ls=":")
    plt.legend()

    fig.savefig(output_path)
    plt.close()
    LOG.info("Written: %s", output_path.name)


def calculate_growth_factor(
    veh_kms_path: pathlib.Path, base_year: int, forecast_year: int, plot_path: pathlib.Path
) -> dict[str, float]:
    # TODO Docstring
    rtf_veh_kms = pd.read_excel(
        veh_kms_path,
        sheet_name="Table 1 - Traffic - Area Type",
        skiprows=3,
        usecols=range(1, 12),
        nrows=30,
    )
    index_cols = ["Region", "Area type", "Vehicle Type"]
    rtf_veh_kms.loc[:, index_cols] = rtf_veh_kms[index_cols].fillna(method="ffill")
    rtf_veh_kms.set_index(index_cols, inplace=True)
    rtf_veh_kms.columns = pd.to_numeric(rtf_veh_kms.columns, downcast="integer")

    fit = _GrowthFactorLinRegress(rtf_veh_kms.loc["England", "All", "LGV"])
    _plot_linear_fit(fit, base_year, forecast_year, plot_path)

    base_growth = fit.year_value(base_year) / fit.year_value(LGV_SURVEY_YEAR)
    forecast_growth = fit.year_value(forecast_year) / fit.year_value(LGV_SURVEY_YEAR)
    growth_adjust = BASE_LGV_GROWTH_FACTOR / base_growth
    growth_factor = growth_adjust * forecast_growth

    return {
        "RTF growth to base": base_growth,
        "RTF growth to forecast": forecast_growth,
        "LGV growth adjustment factor": growth_adjust,
        f"LGV growth factor to forecast {forecast_year}": growth_factor,
    }


def main(params: ForecastInputsConfig) -> None:
    # TODO Docstring
    output_folder = params.output_folder / f"LGV Forecast Inputs - {params.forecast_year}"
    output_folder.mkdir(exist_ok=True)

    # TODO(MB) Use LogHelper class from caf.toolkit
    _init_logger(output_folder)
    LOG.info("Outputs saved to: %s", output_folder)

    out_path = output_folder / "forecast_inputs_config.yml"
    params.save_yaml(out_path)
    LOG.info("Written: %s", out_path.name)

    base_config = lgv_inputs.LGVInputPaths.load_yaml(params.base_model_config)
    out_path = output_folder / "base_inputs_config.yml"
    base_config.save_yaml(out_path)
    LOG.info("Written: %s", out_path.name)

    oa_lookup = load_oa_lookup(params.oa_lookup_path)
    growth = get_planning_growth(
        params.base_planning_path, params.forecast_planning_path, oa_lookup
    )

    growth_folder = output_folder / "growth_factors"
    growth_folder.mkdir(exist_ok=True)
    for name, data in growth:
        out_path = growth_folder / f"planning_data_growth_factors-{name}.csv"
        data.to_csv(out_path)
        LOG.info("Written: %s", out_path.relative_to(output_folder))

    forecast_paths: dict[str, Any] = {}

    grown_inputs_folder = output_folder / "grown_inputs"
    grown_inputs_folder.mkdir(exist_ok=True)
    forecast_paths["bres_data"] = grow_bres(
        base_config.bres_path,
        grown_inputs_folder / f"grown_BRES_{params.forecast_year}.csv",
        growth,
        params.forecast_year,
    )

    forecast_paths["ndr_floorspace"] = grow_ndr_floorspace(
        base_config.ndr_floorspace_path,
        params.base_year,
        params.forecast_year,
        growth,
        grown_inputs_folder / f"grown_NDR_floorspace_{params.forecast_year}.csv",
    )

    forecast_paths["dwellings_england"] = grow_english_dwellings_data(
        base_config.e_dwellings_path,
        grown_inputs_folder / f"grown_english_dwelling_{params.forecast_year}.xlsx",
        params.base_year,
        params.forecast_year,
        growth,
    )
    forecast_paths["dwellings_scotland_wales"] = grow_sc_w_dwellings_data(
        base_config.sc_w_dwellings_path,
        grown_inputs_folder / f"grown_scotland_wales_dwelling_{params.forecast_year}.csv",
        params.base_year,
        params.forecast_year,
        growth,
    )

    forecast_paths["QS606_data"] = grow_occupation_data(
        base_config.qs606ew_path,
        base_config.qs606sc_path,
        growth,
        params.base_year,
        params.forecast_year,
        grown_inputs_folder,
    )

    forecast_paths["warehouse_data"] = grow_warehouse_data(
        base_config.warehouse_path,
        base_config.commute_warehouse_paths,
        growth,
        params.base_year,
        params.forecast_year,
        grown_inputs_folder,
    )
    forecast_paths = _recursive_apply(forecast_paths, lambda x: x.relative_to(output_folder))

    # TODO Add function to calculate growth factor using fleet projections
    growth_factors = calculate_growth_factor(
        params.forecasted_vehicle_kms,
        params.base_year,
        params.forecast_year,
        output_folder / "LGV_growth_factor_plot.pdf",
    )
    forecast_paths.update({"growth factors": growth_factors})

    write_forecast_log(
        forecast_paths,
        output_folder / "grown_data.yml",
        params.base_year,
        params.forecast_year,
    )


##### MAIN #####
if __name__ == "__main__":
    main(ForecastInputsConfig.load_yaml(CONFIG_PATH))
