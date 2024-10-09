# -*- coding: utf-8 -*-
"""Script to perform some analysis of CSRGT datasets."""

##### IMPORTS #####

import datetime as dt
import enum
import functools
import io
import itertools
import logging
import operator
import pathlib
import re
import textwrap
from typing import Generator, Literal, Sequence
import zipfile

import caf.toolkit as ctk
import numpy as np
import pandas as pd
import pydantic
from bokeh import models, palettes, plotting
import bokeh.io

##### CONSTANTS #####

_TOOL_NAME = "csrgt"
LOG = logging.getLogger(_TOOL_NAME)
_CONFIG_FILE = pathlib.Path(__file__).with_suffix(".yml")
_ARTIC_RIGID_LOOKUP = {0: "Artic", 1: "Rigid"}
_MOVING_MEAN_N = {"1km": 10, "NoHAM": 5, "RFS0113": 3}
_MAX_DIST = 500
_RFS0113_BAND = [0, 25, 50, 100, 150, 200, 300]


##### CLASSES & FUNCTIONS #####


class Columns(enum.StrEnum):
    """Columns expected in the CSRGT CSV."""

    VEHICLE_ID = "VehicleID"
    ARTIC_RIGID = "ArticRigid"
    AXLE = "AxleConfiguration"
    BUSINESS_TYPE = "BusinessType_NACE2"
    CAPACITY = "CarryingCapacity"
    COMMODITY = "Commodity_NST2007"
    DANGEROUS_GOODS = "DangerousGoods"
    EMPTY_DISTANCE = "EmptyDistance"
    GROSSED_TONNES = "Grossed_Tonnes"
    GROSSED_VKMS = "Grossed_VehicleKMs"
    GROSS_WEIGHT = "GrossVehicleWeight"
    LOADED_DISTANCE = "LoadedDistance"
    LOAD_PLACE = "LoadPlaceNUTS3"
    MODE_APPEARANCE = "ModeAppearance"
    NO_COL_DEL = "NoOfColAndDel"
    NO_COLLECTIONS = "NoOfCollections"
    NO_DELIVERIES = "NoOfDeliveries"
    MODE = "Mode of Operation"
    TONNES = "Tonnes"
    TYPE30 = "Type30"
    UNLOAD_PLACE = "UnloadPlaceNUTS3"
    YEAR = "Year"


class _Config(ctk.BaseConfig):
    csrgt_path: pydantic.FilePath
    output_folder: pydantic.DirectoryPath
    noham_tld_zip: pydantic.FilePath


class _DataLoad:

    def __init__(self, path: pathlib.Path) -> None:
        self._data = self._load_csrgt(path)
        self._nuts_lookup = self._calculate_nuts_lookup()

    @classmethod
    def _load_csrgt(cls, path: pathlib.Path) -> pd.DataFrame:
        LOG.info("Loading CSRGT data from %s", path.resolve())
        csrgt = pd.read_csv(path, usecols=list(Columns))

        text = io.StringIO()
        csrgt.info(buf=text)
        LOG.info("CSRGT dataset:\n%s", text.getvalue())

        # Convert commodities to uppercase to avoid confusion with "EM" and "em",
        # also pad commodity numbers with 0s to make the ordering clearer.
        csrgt.loc[:, Columns.COMMODITY] = (
            csrgt.loc[:, Columns.COMMODITY].str.upper().str.pad(2, fillchar="0")
        )
        LOG.info(_unique_column_message(csrgt[Columns.COMMODITY]))

        # Convert artic rigid integers to names
        csrgt.loc[:, Columns.ARTIC_RIGID] = csrgt[Columns.ARTIC_RIGID].replace(
            _ARTIC_RIGID_LOOKUP
        )

        return csrgt

    def _calculate_nuts_lookup(
        self,
        place_columns: Sequence[Columns] = (Columns.LOAD_PLACE, Columns.UNLOAD_PLACE),
    ) -> pd.DataFrame:
        """Create lookup from NUTS3 to NUTS 2 and 1.

        Any zones outside the UK only keep the country code.
        """
        nuts3_unique = np.unique(self._data[list(place_columns)].values).astype(str)
        nuts = {}
        for nm, val in ((2, 4), (1, 3)):
            nuts[f"NUTS{nm}"] = np.where(
                np.char.startswith(nuts3_unique, "UK"),
                np.char.ljust(nuts3_unique, val),
                np.char.ljust(nuts3_unique, 2),
            )
        nuts_lookup = pd.DataFrame({"NUTS3": nuts3_unique, **nuts})

        for _, val in nuts_lookup.items():
            LOG.info(_unique_column_message(val))

        return nuts_lookup

    def save_nuts_lookup(self, path: pathlib.Path) -> None:
        self._nuts_lookup.to_csv(path, index=False)
        LOG.info("Written NUTS lookup to: %s", path)

    def iterate_nuts_zones(
        self,
        other_cols: Sequence[str],
        place_columns: Sequence[str] = (Columns.LOAD_PLACE, Columns.UNLOAD_PLACE),
    ) -> Generator[tuple[str, pd.DataFrame, list[str]], None, None]:
        original_zoning = "NUTS3"
        missing = [i for i in place_columns if original_zoning not in i]
        if len(missing):
            raise ValueError(f"found {len(missing)} place columns not in NUTS3 zoning")

        place_columns = list(place_columns)
        other_cols = list(other_cols)

        for name in self._nuts_lookup.columns:
            if name == original_zoning:
                new_zoning: pd.DataFrame = self._data[place_columns + other_cols]
                new_place_columns = place_columns
            else:
                new_zoning = self._data[place_columns + other_cols].replace(
                    self._nuts_lookup[original_zoning].values, self._nuts_lookup[name].values
                )
                new_zoning.columns = [
                    i.replace(original_zoning, name) for i in new_zoning.columns
                ]
                new_place_columns = [i.replace(original_zoning, name) for i in place_columns]

            assert isinstance(new_zoning, pd.DataFrame)

            yield name, new_zoning, new_place_columns

    @property
    def data(self) -> pd.DataFrame:
        return self._data.copy()


class _TLDData:

    def __init__(self, data: pd.DataFrame, rolling_mean_n: int) -> None:
        self._data = data[["dist_min", "dist_max", "avg_dist", "count", "percentage"]]
        self._bins = self._data["dist_min"].to_list() + [self._data["dist_max"].to_list()[-1]]

        self._data["bin_height"] = self._data["percentage"] / (
            self._data["dist_max"] - self._data["dist_min"]
        )

        self._data["rolling_count"] = _moving_mean(self._data["count"], rolling_mean_n)
        self._data["rolling_perc"] = _moving_mean(self._data["percentage"], rolling_mean_n)
        self._data["rolling_height"] = _moving_mean(self._data["bin_height"], rolling_mean_n)

        self._hist_data_source = None
        self._rolling_data_source = None

    @property
    def data(self) -> pd.DataFrame:
        return self._data.copy()

    @property
    def bins(self) -> list[int]:
        return self._bins.copy()

    def hist_data_source(self) -> models.ColumnDataSource:
        return models.ColumnDataSource(
            self._data[
                ["dist_min", "dist_max", "avg_dist", "count", "percentage", "bin_height"]
            ].to_dict("list")
        )

    def rolling_data_source(self) -> models.ColumnDataSource:
        return models.ColumnDataSource(
            self._data[
                ["avg_dist", "rolling_count", "rolling_perc", "rolling_height"]
            ].to_dict(list)
        )

    @classmethod
    def from_data(
        cls,
        distances: np.ndarray,
        bins: Sequence[int],
        weights: np.ndarray | None = None,
        rolling_mean_n: int = 10,
    ):
        counts, bin_edges = np.histogram(distances, bins=bins, weights=weights)
        percentages = (counts / np.sum(counts)) * 100
        bin_height = np.histogram(distances, bins=bins, weights=weights, density=True)[0] * 100
        avg_dist = np.mean(np.vstack((bin_edges[:-1], bin_edges[1:])), axis=0)

        data = pd.DataFrame(
            {
                "dist_min": bin_edges[:-1],
                "dist_max": bin_edges[1:],
                "avg_dist": avg_dist,
                "count": counts,
                "percentage": percentages,
                "bin_height": bin_height,
            }
        )

        return cls(data, rolling_mean_n)


def _unique_column_message(data: pd.Series, max_len: int = 15) -> str:
    name = data.name
    unique = data.unique()
    unique.sort()
    if len(unique) > max_len:
        n = max_len // 2
        msg = ", ".join(f"'{i}'" for i in unique[:n])
        msg += " ... "
        msg += ", ".join(f"'{i}'" for i in unique[-n:])
    else:
        msg = ", ".join(f"'{i}'" for i in unique)

    return f"{len(unique):,} unique '{name}': {msg}"


def _sample_size(
    df: pd.DataFrame,
    place_columns: Sequence[Columns] | None = None,
    other_cols: Sequence[Columns] = (Columns.ARTIC_RIGID, Columns.COMMODITY),
):
    """Calculates number of rows by artic/rigid and commodity type."""
    other_cols = list(other_cols)
    if place_columns is not None:
        place_columns = list(place_columns)
        full_columns = place_columns + other_cols

    sample = df.loc[:, full_columns].copy()
    sample["# Rows"] = 1
    sample = sample.groupby(full_columns).sum()

    # Pivot dataframe to have columns for artic / rigid commodities
    if place_columns is None:
        sample["index"] = "# Rows"
        sample.set_index("index", append=True, inplace=True)
    sample = sample.unstack(other_cols)
    sample = sample.droplevel(0, axis=1)
    sample.fillna(0, inplace=True)

    # Create totals columns
    # sample.loc[("Total", "Total"), :] = sample.sum(axis=0)
    # for i in (0, 1):
    #     sample.loc[:, (i, "Total")] = sample.loc[:, i].sum(axis=1)

    sample.sort_index(axis=1, inplace=True)
    return sample


def _filter_uk(
    csrgt: pd.DataFrame,
    place_cols: Sequence[Columns] = (Columns.LOAD_PLACE, Columns.UNLOAD_PLACE),
):
    """Remove any OD pairs not starting and ending in the UK."""
    conds = []
    for c in place_cols:
        conds.append(csrgt[c].str.upper().str.startswith("UK"))

    mask = functools.reduce(operator.and_, conds)
    return csrgt.loc[mask]


def _produce_sample_sizes(
    csrgt: _DataLoad,
    excel_path: pathlib.Path,
    place_cols: Sequence[Columns] = (Columns.LOAD_PLACE, Columns.UNLOAD_PLACE),
    other_cols: Sequence[Columns] = (Columns.ARTIC_RIGID, Columns.COMMODITY),
):
    """Calculate sample size (number of rows) for different groupings.

    Calculates sample size for each combination of place column and other column
    and for both place columns with each other column.
    """
    LOG.info(
        "Calculating sample sizes for %s and %s", ", ".join(place_cols), ", ".join(other_cols)
    )
    place_cols = list(place_cols)
    other_cols = list(other_cols)

    with pd.ExcelWriter(excel_path, mode="w", engine="openpyxl") as excel:
        iterator = csrgt.iterate_nuts_zones(other_cols, place_cols)
        for name, zones, zone_place_cols in iterator:
            for place in zone_place_cols:
                for type_ in other_cols:
                    sheet = f"{place} - {type_}"
                    LOG.info("Sample size for %s", sheet)
                    sample = _sample_size(zones, place_columns=(place,), other_cols=(type_,))
                    sample.to_excel(excel, sheet_name=sheet)

                sheet = f"{place} - both"
                LOG.info("Sample size for %s", sheet)
                sample = _sample_size(zones, place_columns=(place,), other_cols=other_cols)
                sample.to_excel(excel, sheet_name=sheet)

            if name == "NUTS3":
                continue

            for type_ in other_cols:
                sheet = f"Both - {type_}"
                LOG.info("Sample size for %s", sheet)
                sample = _sample_size(
                    zones, place_columns=zone_place_cols, other_cols=(type_,)
                )
                sample.reset_index().to_excel(excel, sheet_name=sheet, index=False)

    LOG.info("Written: %s", excel_path)


def _tonnage_per_trip(
    csrgt: _DataLoad,
    excel_path: pathlib.Path,
    place_columns: Sequence[Columns] = (Columns.LOAD_PLACE, Columns.UNLOAD_PLACE),
):
    """Calculates tonnage per trip for each NUTS zone."""
    iterator = csrgt.iterate_nuts_zones([Columns.TONNES], place_columns)

    with pd.ExcelWriter(excel_path, mode="w", engine="openpyxl") as excel:
        for name, zone_data, zone_columns in iterator:
            LOG.info("Calculating tonnage by %s OD trips", name)
            zone_data: pd.DataFrame = zone_data.groupby(zone_columns)[Columns.TONNES].agg(
                total_tonnes="sum", number_trips="count", mean_per_trip="mean"
            )
            zone_data.columns = [i.replace("_", " ").title() for i in zone_data.columns]
            zone_data.to_excel(excel, sheet_name=f"Tonnes {name}")

    LOG.info("Written: %s", excel_path)


def _artic_rigid_splits(csrgt: _DataLoad, excel_path: pathlib.Path):
    """Calculate split between artic and rigid vehicle types."""
    pattern = re.compile(r"(un)?load", re.I)
    LOG.info("Producing artic / rigid splits")

    with pd.ExcelWriter(excel_path, mode="w", engine="openpyxl") as excel:
        for name, zone_data, zone_columns in csrgt.iterate_nuts_zones(
            [Columns.ARTIC_RIGID, Columns.VEHICLE_ID]
        ):
            column_groups = {"Both": zone_columns}
            column_groups.update({pattern.match(i).group(0): [i] for i in zone_columns})

            for nm, cols in column_groups.items():
                sheet = f"{name} {nm}"
                LOG.info("Artic / Rigid split for %s", sheet)

                split = zone_data.groupby(cols + [Columns.ARTIC_RIGID])[
                    Columns.VEHICLE_ID
                ].count()
                split = split.unstack()
                cols = split.columns
                split["Total"] = split.sum(axis=1)

                for c in cols:
                    split[f"% {c}"] = split[c] / split["Total"]

                split.to_excel(excel, sheet_name=sheet)

    LOG.info("Written: %s", excel_path)


def _moving_mean(arr: np.ndarray, n: int):
    arr = np.pad(arr, (n // 2, n - 1 - n // 2), mode="edge")
    return np.convolve(arr, np.ones(n), "valid") / n


def _load_noham_tld(zippath: pathlib.Path, filename_fmt: str):
    LOG.info("Loading NoHAM TLD from %s", zippath)

    noham_tld_data = []

    with zipfile.ZipFile(zippath, "r") as zip_file:
        names = zip_file.namelist()
        for period in (1, 2, 3):
            name = filename_fmt.format(tp=period)
            if name not in names:
                namelist = ", ".join(f"'{i}'" for i in names)
                raise FileNotFoundError(
                    f"NoHAM TLD TS{period} ({name}) not found in TLD zipfile: {zippath}\n"
                    f"Found files: {textwrap.fill(namelist, width=150)}"
                )

            data = pd.read_csv(zip_file.open(name), usecols=["dist_bin", "Trips"])
            bins = (
                data["dist_bin"]
                .str.replace(r"[\(\]]", "", regex=True)
                .str.split(",", expand=True)
                .astype(int)
            )
            bins.columns = ["dist_min", "dist_max"]
            data = pd.concat([bins, data.drop(columns="dist_bin")], axis=1).set_index(
                ["dist_min", "dist_max"]
            )
            noham_tld_data.append(data)

    noham_tld = pd.concat(noham_tld_data, axis=1).sum(axis=1).to_frame("count").reset_index()
    noham_tld["avg_dist"] = noham_tld[["dist_min", "dist_max"]].sum(axis=1) / 2
    noham_tld["percentage"] = (noham_tld["count"] / noham_tld["count"].sum()) * 100

    return _TLDData(noham_tld, _MOVING_MEAN_N["NoHAM"])


def _plot_tld(
    distances: np.ndarray,
    title: str,
    noham_tld: _TLDData,
    weights: np.ndarray = None,
    weight_name: str = "Trips",
    plot_type: Literal["hist", "tld"] = "hist",
) -> tuple[plotting.figure, dict[str, _TLDData]]:
    LOG.info("Creating TLD - %s", title)
    if plot_type not in ("hist", "tld"):
        raise ValueError(f"invalid {plot_type = }")

    if weights is not None and np.sum(weights) <= 0:
        raise ValueError(f'Cannot create histogram with 0 total {weight_name} for "{title}"')

    if np.any(np.isnan(distances)):
        errors = np.sum(np.isnan(distances))
        raise ValueError(
            f"{errors:,} ({errors / len(distances):.0%}) NaN values for distances"
        )
    if np.any(distances < 0):
        errors = np.sum(distances < 0)
        raise ValueError(f"{errors:,} ({errors / len(distances):.0%}) distances < 0")
    if np.all(distances == 0):
        raise ValueError("all distances are 0")

    # Calculate histogram values for different bin sizes
    bins = {
        "1km": int(np.ceil(np.max(distances))),
        "NoHAM": noham_tld.bins,
        "RFS0113": _RFS0113_BAND + [np.ceil(np.max(distances))],
    }
    sources = {"NoHAM HGV": noham_tld}

    if plot_type == "hist":
        height_col = "bin_height"
    elif plot_type == "tld":
        height_col = "percentage"
    max_height = noham_tld.data[height_col].max()

    for nm, b in bins.items():
        data = _TLDData.from_data(distances, b, weights, _MOVING_MEAN_N[nm])
        sources[f"CSRGT ({nm} bins)"] = data
        max_height = max(max_height, data.data[height_col].max())

    # Create hover tools for each line
    hover_info = {
        "hist": [
            ("Distance", "@{dist_min}-@{dist_max}km"),
            (f"No. {weight_name}", "@count"),
            (f"% {weight_name}", "@{percentage}%"),
        ],
        "rolling": [
            ("Distance", "@{avg_dist}km"),
            (f"Mean No. {weight_name}", "@rolling_count"),
            (f"Mean % {weight_name}", "@{rolling_perc}%"),
        ],
        "tld": [
            ("Distance", "@{avg_dist}km"),
            (f"No. {weight_name}", "@count"),
            (f"% {weight_name}", "@{percentage}%"),
        ],
    }
    hovers = [
        models.HoverTool(name=i, visible=False, tooltips=j) for i, j in hover_info.items()
    ]

    if plot_type == "hist":
        y_label = f"% {weight_name} / Bin Width"
    elif plot_type == "tld":
        y_label = f"% {weight_name}"

    tld = plotting.figure(
        title=title,
        width=1200,
        x_range=(0, _MAX_DIST),
        x_axis_label="Distance (km)",
        y_axis_label=y_label,
        y_range=(0, np.ceil(max_height * 2) / 2),
        tools=[
            "pan",
            "wheel_zoom",
            "box_zoom",
            *hovers,
            "reset",
            "save",
        ],
    )

    _add_plots(tld, sources, plot_type)

    # Add label with total trips
    long = np.sum(distances > _MAX_DIST)
    zero = np.sum(distances == 0)
    text = (
        f"Total trips: {len(distances):,}, trips > {_MAX_DIST}km: {long}, "
        f"trips = 0km: {zero}"
    )
    label = models.Label(
        x=int(tld.width * 0.4),
        y=tld.height - 100,
        x_units="screen",
        y_units="screen",
        text=text,
        text_font_size=tld.legend.label_text_font_size,
        border_line_color=tld.legend.border_line_color,
        background_fill_color=tld.legend.background_fill_color,
        background_fill_alpha=tld.legend.background_fill_alpha,
    )
    tld.add_layout(label)
    tld.legend.click_policy = "hide"
    return tld, sources


def _add_plots(
    fig: plotting.figure, sources: dict[str, _TLDData], plot_type: Literal["hist", "tld"]
):
    if plot_type not in ("hist", "tld"):
        raise ValueError(f"invalid {plot_type = }")

    colours = itertools.cycle(palettes.Paired7)
    for nm, data in sources.items():
        visible = "RFS0113" in nm

        if plot_type == "hist":
            fig.quad(
                top="bin_height",
                bottom=0,
                left="dist_min",
                right="dist_max",
                source=data.hist_data_source(),
                legend_label=f"{nm} Trip Length Distribution",
                name="hist",
                color=next(colours),
                visible=visible,
            )
            fig.line(
                "avg_dist",
                "rolling_height",
                source=data.rolling_data_source(),
                line_width=2,
                legend_label=f"Rolling Mean {nm}",
                color=next(colours),
                name="rolling",
                visible=visible,
            )

        elif plot_type == "tld":
            fig.line(
                "avg_dist",
                "percentage",
                source=data.hist_data_source(),
                line_width=2,
                legend_label=f"{nm} Trip Length Distribution",
                color=next(colours),
                visible=visible,
                name="tld",
            )


def tld_dashboard(
    path: pathlib.Path,
    csrgt: _DataLoad,
    noham_tld: _TLDData,
    weight_columns: Sequence[Columns | None],
    plot_type: Literal["hist", "tld"],
):
    """Produce HTML dashboard of TLD plots using Bokeh."""
    LOG.info(
        "Producing TLD (%s) dashboard for %s",
        plot_type,
        ", ".join("Trips" if i is None else i.value for i in weight_columns),
    )

    bokeh.io.output_file(path, "CSRGT Trip Length Distributions")

    def create_plot(
        title: str, weight_col: Columns | None = None, mask: pd.Series | None = None
    ):
        if mask is None:
            mask = pd.Series(True, index=csrgt.data.index)

        if weight_col is None:
            weights = None
            weight_name = "Trips"
        else:
            weights = csrgt.data.loc[mask, weight_col]
            weight_name = weight_col.replace("_", " ").title()
            title += f" by {weight_name}"

        return _plot_tld(
            csrgt.data.loc[mask, Columns.LOADED_DISTANCE],
            title,
            noham_tld,
            weights=weights,
            weight_name=weight_name,
            plot_type=plot_type,
        )

    outer_tabs = []
    excel_mode = "w"
    excel_path = path.with_name(path.stem + "-data.xlsx")
    for weight in weight_columns:
        tabs = []

        # Plot TLD for all data
        fig, sources = create_plot("Trip Length Distribution for All Data", weight)
        tabs.append(models.TabPanel(child=fig, title="All"))

        if excel_mode == "w":
            LOG.info("Writing TLD data to Excel: %s", excel_path)

        with pd.ExcelWriter(
            excel_path, mode=excel_mode, engine="openpyxl", if_sheet_exists="error"
        ) as excel:
            for nm, data in sources.items():
                if weight is None:
                    sheet_name = f"{nm}"
                else:
                    sheet_name = f"{nm} - {weight.value}"
                data.data.to_excel(excel, sheet_name=sheet_name)

            excel_mode = "a"

        LOG.info(
            "Updated %s with %s new sheets for %s weighting",
            excel_path.name,
            len(sources),
            "trips" if weight is None else weight.value,
        )

        # Plot distributions for individual columns
        for column in (Columns.ARTIC_RIGID, Columns.COMMODITY):
            for val in csrgt.data[column].unique():
                mask = csrgt.data[column] == val
                title = f"Trip Length Distribution for {column.value} = {val}"
                try:
                    fig = create_plot(title, weight, mask)
                    tabs.append(models.TabPanel(child=fig, title=str(val).title()))

                except ValueError as exc:
                    LOG.error(
                        'failed creating "%s" plot\n%s: %s', title, exc.__class__.__name__, exc
                    )

        if weight is None:
            name = "Trips"
        else:
            name = weight.value.replace("_", " ").title()

        outer_tabs.append(models.TabPanel(child=models.Tabs(tabs=tabs), title=name))

    bokeh.io.show(models.Tabs(tabs=outer_tabs))
    LOG.info("Written: %s", path)


def main() -> None:
    parameters = _Config.load_yaml(_CONFIG_FILE)
    output_folder = parameters.output_folder / f"{dt.date.today():%Y%m%d}-CSRGT_Analysis"
    output_folder.mkdir(exist_ok=True)

    details = ctk.ToolDetails(_TOOL_NAME, "0.1.0")
    log_file = output_folder / f"{_TOOL_NAME}.log"

    with ctk.LogHelper(_TOOL_NAME, details, log_file=log_file):
        LOG.info("Outputs saved to: %s", output_folder)

        out_path = output_folder / f"{_TOOL_NAME}_config.yml"
        parameters.save_yaml(out_path)
        LOG.info("Written config: %s", out_path)

        csrgt = _DataLoad(parameters.csrgt_path)
        csrgt.save_nuts_lookup(output_folder / "NUTS321_lookup.csv")

        _produce_sample_sizes(csrgt, output_folder / "sample_sizes.xlsx")
        _tonnage_per_trip(csrgt, output_folder / "tonnage_per_trip.xlsx")
        _artic_rigid_splits(csrgt, output_folder / "artic_rigid_split.xlsx")

        # Create TLD plots
        noham_tld = _load_noham_tld(
            parameters.noham_tld_zip, "TLD_Braford_Base_2018_TS{tp}_UC5.csv"
        )

        for plot_type in ("hist", "tld"):
            tld_dashboard(
                output_folder / f"trip_length_distributions-{plot_type}.html",
                csrgt,
                noham_tld,
                weight_columns=[None, Columns.TONNES],
                plot_type=plot_type,
            )


##### MAIN #####
if __name__ == "__main__":
    main()
