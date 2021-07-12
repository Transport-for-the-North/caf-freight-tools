# -*- coding: utf-8 -*-
"""
    Module containing the gravity model used in the LGV model.
"""

##### IMPORTS #####
# Standard imports
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from .. import errors


##### CLASSES #####
class FurnessConstraint(Enum):
    """Types of furnessing/factoring for the gravity model."""

    SINGLE = auto()
    DOUBLE = auto()

    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"


@dataclass
class FurnessResults:
    """Class to store result statistics from furness/factoring functions."""

    constraint: FurnessConstraint
    """The furness/factoring process that was used."""
    message: str
    """String message about results."""
    converged: bool = None
    """If the process converged, only for 2D furness."""
    loop: int = None
    """The number of loops taken, only for 2D furness."""
    difference: float = None
    """The RMS difference between matrix and row/column totals, only for 2D furness."""


##### FUNCTIONS #####
def _check_numeric(**kwargs) -> None:
    """Checks if given parameters are floats or ints.

    Raises
    ------
    ValueError
        If any of the parameters aren't floats or ints,
        includes the parameter name in the message.
    """
    for nm, val in kwargs.items():
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"{nm} should be a scalar number (float or int) not {type(val)}"
            )


def tanner(cost: np.ndarray, alpha: float, beta: float) -> np.ndarray:
    r"""Implemenation of the travel cost tanner function.

    Parameters
    ----------
    cost : np.ndarray
        Array of the travel costs.
    alpha, beta : float
        Parameter for the tanner formula, see Notes.

    Returns
    -------
    np.ndarray
        Output from the tanner equation,
        same shape as `cost`.

    Notes
    -----
    Formula used for this function is:

    .. math:: f(C_{ij}) = C_{ij}^\alpha \cdot \exp(\beta C_{ij})

    where:

    - :math:`C_{ij}`: cost from i to k.
    - :math:`\alpha, \beta`: calibration parameters.
    """
    _check_numeric(alpha=alpha, beta=beta)
    power = np.float_power(cost, alpha)
    exp = np.exp(beta * cost)
    return power * exp


def log_normal(cost: np.ndarray, sigma: float, mu: float) -> np.ndarray:
    r"""Implementation of the travel cost log normal function.

    Parameters
    ----------
    cost : np.ndarray
        Array of the travel costs.
    sigma, mu : float
        Parameter for the equation, see Notes.

    Returns
    -------
    np.ndarray
        Output from the log normal equation,
        same shape as `cost`.

    Notes
    -----
    Formula used for this function is:

    .. math::

        f(C_{ij}) = \frac{1}{C_{ij} \cdot \sigma \cdot \sqrt{2\pi}}
        \cdot \exp\left(-\frac{(\ln C_{ij}-\mu)^2}{2\sigma^2}\right)

    where:

    - :math:`C_{ij}`: cost from i to j.
    - :math:`\sigma, \mu`: calibration parameters.
    """
    _check_numeric(sigma=sigma, mu=mu)
    frac = 1 / (cost * sigma * np.sqrt(2 * np.PI))
    exp_numerator = (np.ln(cost) - mu) ** 2
    exp_denominator = 2 * sigma ** 2
    exp = np.exp(-exp_numerator / exp_denominator)
    return frac * exp


def _get_cost_function(name: str) -> tuple[Callable, list, tuple[list, list]]:
    """Returns cost function and intial parameters.

    Parameters
    ----------
    name : str
        Name of the function.

    Returns
    -------
    Callable
        Function with given `name`.
    list
        List of initial parameters to use when trying
        to fit function to data.
    tuple[list, list]
        Tuple containing the lower and upper bounds of
        parameters to try when fitting function to data.

    Raises
    ------
    KeyError
        If the `name` given isn't an allowed cost function.
    """
    FUNCTION_LOOKUP = {
        "log_normal": (log_normal, [1.0, 1.0], ([0, -np.inf], [np.inf, np.inf])),
        "tanner": (tanner, [1.0, -1.0], ([0, -np.inf], [np.inf, 0])),
    }
    try:
        func, init_params, bounds = FUNCTION_LOOKUP[name.lower().strip()]
    except KeyError as e:
        raise KeyError(
            f"unknown function {name!r}, should be "
            f"one of {list(FUNCTION_LOOKUP.keys())}"
        ) from e
    return func, init_params, bounds


def _check_gm_inputs(
    trip_ends: pd.DataFrame, costs: pd.DataFrame, calibration: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Sorts the indices and checks the input DataFrames for `gravity_model`."""
    # Copy the DataFrames so links to them outside this function aren't edited
    data = (trip_ends.copy(), costs.copy(), calibration.copy())
    names = ("trip_ends", "costs", "calibration")
    for nm, df in zip(names, data):
        df.sort_index(axis=0, inplace=True)
        if df.index.has_duplicates:
            raise ValueError(f"duplicates not allowed in `{nm}` index")
        if df.columns.has_duplicates:
            raise ValueError(f"duplicates not allowed in `{nm}` columns")
        if nm == "trip_ends":
            continue
        df.sort_index(axis=1, inplace=True)
        if not (df.index.equals(data[0].index) and df.columns.equals(data[0].index)):
            raise ValueError(
                f"`{nm}` must be a square matrix with same zones as "
                "`trip_ends` for gravity model calculations"
            )
    return data


def gravity_model(
    trip_ends: pd.DataFrame,
    costs: pd.DataFrame,
    calibration: pd.DataFrame = None,
    function: str = "tanner",
    function_args: tuple = (1.0, -1.0),
    constraint: FurnessConstraint = FurnessConstraint.DOUBLE,
    **kwargs,
) -> tuple[pd.DataFrame, FurnessResults]:
    """Gravity model of trips initialised with given `function`.

    Gravity model can be ran singly or doubly constrained to
    trip ends.

    Parameters
    ----------
    trip_ends : pd.DataFrame
        Dataframe containing columns Attractions and
        Productions, where the index is the zone number.
    costs : pd.DataFrame
        Square matrix containing the costs between all
        zones, index and columns should both be equal
        to the `trip_ends` index.
    calibration : pd.DataFrame, optional
        Matrix of calibration parameters, should be
        the same shape as costs if given.
    function : {'tanner', 'log_normal'}
        Choice of cost function to use.
    function_args : tuple, default (1.0, 1.0)
        Arguments to pass to the chose cost `function`.
    constraint : FurnessConstraint, default FurnessConstraint.DOUBLE
        Type of furnessing/factoring to use.

    Returns
    -------
    pd.DataFrame
        Trip matrix, after furnessing, with the
        same zones as given in `trip_ends`.
    FurnessResults
        Statistics and information from the
        furness/factoring process.

    Raises
    ------
    KeyError
        If a `function` is given which doesn't exist.
    ValueError
        If any of the input DataFrames have duplicates in the
        index or they don't have the same index and columns as
        the `trip_ends` index.

    See Also
    --------
    tanner, log_normal, factor_1d, furness_2d
    """
    if calibration is None:
        calibration = pd.DataFrame(1.0, index=trip_ends.index, columns=trip_ends.index)
    trip_ends, costs, calibration = _check_gm_inputs(trip_ends, costs, calibration)

    # Calculate intial trips matrix and factor with calibration parameters
    func, _, _ = _get_cost_function(function)
    init_matrix = func(costs.values, *function_args)
    init_matrix *= calibration.values

    # Furness trip matrix to trip ends
    if constraint is FurnessConstraint.SINGLE:
        matrix = factor_1d(init_matrix, trip_ends.iloc[0], axis=0)
        results = FurnessResults(constraint, "Matrix factored to trip ends on axis 0")
    elif constraint is FurnessConstraint.DOUBLE:
        # Check trip_ends has the correct names
        trip_ends.rename(columns=lambda nm: nm.strip().lower(), inplace=True)
        missing = [
            c for c in ("attractions", "productions") if c not in trip_ends.columns
        ]
        if missing:
            errors.MissingColumnsError("gravity model trip ends", missing)
        matrix, results = furness_2d(
            init_matrix,
            trip_ends.attractions.values,
            trip_ends.productions.values,
            **kwargs,
        )
    else:
        options = ", ".join(str(i) for i in FurnessConstraint)
        options = " or".join(options.rsplit(",", 1))
        raise ValueError(f"`constraint` should be {options} not {constraint!r}")
    matrix = pd.DataFrame(matrix, index=trip_ends.index, columns=trip_ends.index)
    return matrix, results


def _check_matrix(matrix: np.ndarray):
    """Check given `matrix` is square."""
    if matrix.ndim != 2:
        raise ValueError(f"matrix should have 2 dimensions not: {matrix.ndim}")
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"matrix should be a square not shape: {matrix.shape}")


def factor_1d(matrix: np.ndarray, total: np.ndarray, axis: int) -> np.ndarray:
    """Factor the given `axis` of `matrix` to match `total`.

    Parameters
    ----------
    matrix : np.ndarray
        Square matrix to be factored.
    total : np.ndarray
        The totals that the `matrix` should be
        factored to match.
    axis : int
        The axis of `matrix` which should be factored.

    Returns
    -------
    np.ndarray
        The `matrix` after it has been factored.

    Raises
    ------
    ValueError
        If `total` isn't the correct shape or
        `axis` isn't 0 or 1.
    """
    _check_matrix(matrix)
    if total.ndim != 1:
        raise ValueError(f"total should have 1 dimension not: {total.ndim}")
    if len(total) != matrix.shape[0]:
        raise ValueError("total should be the same length as matrix")
    if axis not in (0, 1):
        raise ValueError(f"axis should be 0 or 1 not: {axis}")

    curr_tot = np.sum(matrix, axis=axis)
    factor = total / curr_tot
    if axis == 0:
        # Factoring column totals so multiplying factor by each row
        new_matrix = matrix * factor
    else:
        # Factoring row totals so muliplying factor by each column
        new_matrix = matrix * factor.reshape((len(factor), 1))
    return new_matrix


def compare_totals(
    matrix: np.ndarray, col_total: np.ndarray, row_total: np.ndarray
) -> float:
    """Calculates root mean square of differences between matrix and column/row totals.

    Parameters
    ----------
    matrix : np.ndarray
        Square matrix of trips.
    col_total, row_total : np.ndarray
        Array of the expected axis totals, should be
        1D equal to length of single axis of `matrix`.

    Returns
    -------
    float
        The root mean square of the differences
        between the `matrix` axis totals and the
        given totals.
    """
    differences = []
    for i, tot in enumerate((col_total, row_total)):
        curr_tot = np.sum(matrix, axis=i)
        differences.append(np.abs(curr_tot - tot))
    differences = np.concatenate(differences)
    return np.sqrt(np.sum(differences ** 2))


def factor_2d(
    matrix: np.ndarray, col_total: np.ndarray, row_total: np.ndarray
) -> tuple[np.ndarray, float]:
    """Factor matrix columns then rows and compare result to totals.

    Parameters
    ----------
    matrix : np.ndarray
        Square matrix of trips.
    col_total, row_total : np.ndarray
        Array of the expected axis totals, should be
        1D equal to length of single axis of `matrix`.

    Returns
    -------
    np.ndarray
        Factored matrix.
    float
        Root mean square difference between the matrix
        row/column totals and those that are given.
    """
    matrix = factor_1d(matrix, col_total, 0)
    matrix = factor_1d(matrix, row_total, 1)
    diff = compare_totals(matrix, col_total, row_total)
    return matrix, diff


def factor_totals(
    col_total: np.ndarray, row_total: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Factor column/row total arrays so they have the same total."""
    trip_ends = [col_total, row_total]
    totals = np.sum(trip_ends, axis=1)
    if totals[0] == totals[1]:
        return col_total, row_total
    mean_tot = np.mean([np.sum(col_total), np.sum(row_total)])
    print(f"Factoring trip ends sum to mean total: {mean_tot}")
    new_totals = []
    for tot, arr in zip(totals, trip_ends):
        new_totals.append(arr * mean_tot / tot)
    return tuple(new_totals)


def furness_2d(
    matrix: np.ndarray,
    col_total: np.ndarray,
    row_total: np.ndarray,
    diff_cutoff: float = 0.1,
    max_loops: int = 1000,
    check_diff: int = 10,
) -> tuple[np.ndarray, FurnessResults]:
    """2D furness `matrix` to match column and row totals.

    Doubly constrained furness of `matrix` to match
    column and row totals to within a RMS difference
    of `diff_cutoff`, may stop earlier if `max_loops`
    is reached or the RMS difference stops improving.

    Parameters
    ----------
    matrix : np.ndarray
        Square matrix of trips to be furnessed.
    col_total, row_total : np.ndarray
        Expected totals to be matched to.
    diff_cutoff : float, default 0.1
        Furness process will stop as soon as the RMS
        difference between the totals is less than
        this value.
    max_loops : int, default 1000
        Furness process will stop, without converging,
        when it reaches this number of loops.
    check_diff : int, default 10
        Furness process will stop if the RMS difference
        stays the same for this number of loops.

    Returns
    -------
    np.ndarray
        The `matrix` after the furness process is finished.
    FurnessResults
        The finishing statistics of the furness processing
        giving information on convergence, number of loops,
        final RMS difference and message about results.
    """
    col_total, row_total = factor_totals(col_total, row_total)
    loop = 0
    converged = False
    diff = compare_totals(matrix, col_total, row_total)
    differences = [diff]
    while diff > diff_cutoff:
        if loop >= max_loops:
            msg = (
                f"Reached maximum number of loops ({loop}) "
                f"with RMS row/column difference: {diff:.1e}"
            )
            break
        if len(differences) >= check_diff:
            differences = differences[-check_diff:]
            if np.isclose(differences, differences[0]).all():
                # If avg_diff hasn't changed for a number of loops then exit early
                msg = (
                    f"RMS row/column difference ({diff:.1e}) has not "
                    f"improved for {check_diff} loops, ending on loop {loop}"
                )
                break
        matrix, diff = factor_2d(matrix, col_total, row_total)
        loop += 1
        # Keep last 5 differences for checking
        differences = differences[-(check_diff - 1) :] + [diff]
        if not np.all(np.isfinite(matrix)):
            msg = (
                "Matrix contains non-finite values, "
                f"stopping furnessing on loop {loop}"
            )
            break
    else:
        converged = True
        msg = (
            f"Furness converged (loop {loop}) "
            f"with RMS row/column difference: {diff:.1e}"
        )
    return matrix, FurnessResults(FurnessConstraint.DOUBLE, msg, converged, loop, diff)


def main():
    pass


def test_gm_func():
    """Runs the `gravity_model` with small 3x3 matrix."""
    rng = np.random.default_rng(1)
    zones = [1, 2, 3]
    trip_ends = pd.DataFrame(
        {"attractions": [105, 115, 125], "productions": [110, 120, 130]}, index=zones
    )
    costs = pd.DataFrame(rng.integers(1000, 2000, (3, 3)), index=zones, columns=zones)
    trips, results = gravity_model(trip_ends, costs, function="tanner", function_args=(1, -0.01))
    print(
        "Trip Ends:",
        trip_ends,
        "Costs:",
        costs,
        "Trips:",
        trips,
        "Furness Results",
        results,
        f"Total trips: {np.sum(trips.values):}",
        f"Trip ends: {np.sum(trip_ends):}",
        sep="\n",
    )


##### MAIN #####
if __name__ == "__main__":
    test_gm_func()
