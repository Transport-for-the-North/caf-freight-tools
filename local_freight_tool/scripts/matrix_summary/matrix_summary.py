# -*- coding: utf-8 -*-
"""Produce summary outputs for set of demand matrices."""

##### IMPORTS #####

import logging
import pathlib
import typing
import warnings

import caf.toolkit as ctk
import pandas as pd
import pydantic
from plotly import express as px
from plotly import graph_objects as go
from pydantic import dataclasses

##### CONSTANTS #####

_CONFIG_FILE = pathlib.Path(__file__).with_suffix(".yml")
_NAME = _CONFIG_FILE.stem
LOG = logging.getLogger(_NAME)


##### CLASSES & FUNCTIONS #####


@dataclasses.dataclass
class SectorTranslation:
    """Path and column names for sector translation CSV."""

    path: pydantic.FilePath
    """Path to sector translation CSV."""
    from_col: str
    """Name of column containing zone ID to translate from."""
    to_col: str
    """Name of column containing zone ID to translate to."""
    factors_col: str
    """Name of column containing translation splitting factors.."""


@dataclasses.dataclass(config=dict(arbitrary_types_allowed=True))
class Translation:
    """Sector translation data and column names."""

    data: pd.DataFrame
    """Sector translation lookup."""
    from_col: str
    """Name of column containing zone ID to translate from."""
    to_col: str
    """Name of column containing zone ID to translate to."""
    factors_col: str
    """Name of column containing translation splitting factors.."""


class Config(ctk.BaseConfig):
    """Parameters for running matrix summary."""

    output_folder: pydantic.DirectoryPath
    matrix_paths: dict[str, pydantic.FilePath]
    distance_matrix: pydantic.FilePath
    tld_bins: list[int]
    sector_translation: SectorTranslation
    comparison_tlds: dict[str, pydantic.FilePath] | None = None

    @pydantic.field_validator("tld_bins", mode="before")
    def _tld_bins(cls, value: str | list) -> list:
        # validator is a classmethod pylint: disable=no-self-argument
        if isinstance(value, str):
            return value.split(",")

        return value

    @pydantic.field_validator("comparison_tlds", mode="before")
    def _check_none(cls, value: typing.Any) -> typing.Any:
        # validator is a classmethod pylint: disable=no-self-argument
        if isinstance(value, str) and value.strip() == "":
            return None

        return value


def _load_sector_translation(input_: SectorTranslation) -> Translation:
    """Read sector translation from CSV."""
    LOG.info("Reading sector translation from %s", input_.path)
    data = ctk.io.read_csv(
        input_.path,
        name="sector translation",
        usecols=[input_.from_col, input_.to_col, input_.factors_col],
    )

    return Translation(data, input_.from_col, input_.to_col, input_.factors_col)


def main(
    output_folder: pathlib.Path,
    matrix_paths: dict[str, pathlib.Path],
    distance_matrix: pathlib.Path,
    tld_bins: list[int],
    sector_translation: SectorTranslation,
    comparison_tlds: dict[str, pathlib.Path] | None = None,
) -> typing.NoReturn:
    LOG.info("Reading distances matrix from %s", distance_matrix)
    distances = ctk.io.read_csv_matrix(distance_matrix)

    sector_lookup = _load_sector_translation(sector_translation)

    trip_kms = {}
    matrix_tlds = {}

    for name, path in matrix_paths.items():
        LOG.info("Reading %s matrix from %s", name, path)
        matrix = ctk.io.read_csv_matrix(path)

        _produce_sector_matrix(
            matrix, sector_lookup, output_folder / f"{name}-sector_matrix.csv"
        )

        trip_distances, tld = _matrix_distance_summary(matrix, distances, tld_bins, name)
        trip_kms[name] = {
            "Trips Distances": trip_distances,
            "Trips": matrix.to_numpy().sum(),
        }
        matrix_tlds[name] = tld

    out_path = output_folder / "trip_kms.csv"
    LOG.info("Writing PCU km summary to %s", out_path)
    trip_kms = pd.DataFrame.from_dict(trip_kms, orient="index")
    trip_kms.to_csv(out_path)

    # Read observed TLDs and include in plot
    for name, path in comparison_tlds.items():
        LOG.info("Reading %s TLD from %s", name, path)
        matrix_tlds[name] = ctk.cost_utils.CostDistribution.from_file(
            path,
            min_col="dist_min",
            max_col="dist_max",
            avg_col="avg_dist",
            trips_col="bin_height",
        )

    _plot_tlds(matrix_tlds, output_folder / "trip_length_distributions.html")


def _matrix_distance_summary(
    matrix: pd.DataFrame, distances: pd.DataFrame, tld_bins: list[int], name: str
) -> tuple[float, ctk.cost_utils.CostDistribution]:
    """Calculate trip distance matrix and trip length distribution."""
    LOG.info("Calculating trip kms for %s", name)
    if not distances.index.equals(matrix.index):
        raise ValueError(
            "cannot calculate trip kms because distance"
            " and trip matrix don't have the same index"
        )
    trip_distances = matrix * distances
    trip_distances = trip_distances.to_numpy().sum()

    LOG.info("Calculating TLD for %s", name)
    tld = ctk.cost_utils.CostDistribution.from_data(matrix, distances, bin_edges=tld_bins)

    return trip_distances, tld


def _produce_sector_matrix(
    matrix: pd.DataFrame, sector_lookup: Translation, out_path: pathlib.Path
) -> None:
    """Translate `matrix` to sectors and write to CSV.

    Warns
    -----
    UserWarning
        If the matrix total changes after the translation.
    """
    sector_matrix = ctk.translation.pandas_matrix_zone_translation(
        matrix,
        sector_lookup.data,
        translation_from_col=sector_lookup.from_col,
        translation_to_col=sector_lookup.to_col,
        translation_factors_col=sector_lookup.factors_col,
    )

    matrix_total = matrix.to_numpy().sum()
    sector_total = sector_matrix.to_numpy().sum()
    if sector_total != matrix_total:
        warnings.warn(
            f"matrix total changed from {matrix_total:.1e} to"
            f" {sector_total:.1e} after translating to sectors, difference of"
            f" {sector_total - matrix_total:.1e} ({sector_total / matrix_total - 1:.1%})"
        )

    LOG.info("Writing sector matrix to %s", out_path)
    sector_matrix.to_csv(out_path)


def _plot_tlds(tlds: dict[str, ctk.cost_utils.CostDistribution], output_path: pathlib.Path):
    LOG.info("Producing plot with %s TLDs", len(tlds))
    tld_data = []
    for name, tld in tlds.items():
        data = pd.DataFrame(
            {
                "Name": name,
                "Distance (km)": tld.avg_vals,
                "Trip Proportion": tld.band_share_vals,
                "Trips": tld.trip_vals,
                "Bin Range (km)": [f"{i} - {j}" for i, j in zip(tld.min_vals, tld.max_vals)],
            }
        )
        tld_data.append(data)

    tld = pd.concat(tld_data)

    fig = px.line(
        tld,
        x="Distance (km)",
        y="Trip Proportion",
        color="Name",
        title="Trip Length Distributions for HGV\nCompared to CSRGT Data",
        hover_name="Name",
        hover_data={
            "Name": False,
            "Bin Range (km)": True,
            "Distance (km)": ":,.0f",
            "Trip Proportion": ":.1%",
            "Trips": ":,.0f",
        },
        markers=True,
    )
    fig.update_layout(yaxis=go.layout.YAxis(tickformat=".0%"))

    fig.write_html(output_path, include_plotlyjs="cdn")
    LOG.info("Written TLD plots to %s", output_path)


def _run() -> None:
    """Load config, setup logging and run :func:`main`."""
    parameters = Config.load_yaml(_CONFIG_FILE)

    log_file = parameters.output_folder / f"{_NAME}.log"
    details = ctk.ToolDetails(_NAME, "0.1.0")

    with ctk.LogHelper(_NAME, details, log_file=log_file):
        LOG.info("Writing config to output folder")
        parameters.save_yaml(parameters.output_folder / _CONFIG_FILE.name)

        main(
            output_folder=parameters.output_folder,
            matrix_paths=parameters.matrix_paths,
            distance_matrix=parameters.distance_matrix,
            tld_bins=parameters.tld_bins,
            sector_translation=parameters.sector_translation,
            comparison_tlds=parameters.comparison_tlds,
        )


##### MAIN #####
if __name__ == "__main__":
    _run()
