# -*- coding: utf-8 -*-
"""
    Module containing the gravity model used in the LGV model.

    See Also
    --------
    .furnessing
"""

##### IMPORTS #####
# Standard imports
from typing import Callable

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from .. import errors
from .furnessing import FurnessConstraint, FurnessResults, furness_2d, factor_1d


##### CLASSES #####


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
    kwargs : Keyword arguments
        Keyword arguments passed to `furness_2d`, ignored
        if constraint is SINGLE.

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
    .furnessing.factor_1d : 1D matrix factoring, when constring is SINGLE
    .furnessing.furness_2d : 2D matrix furnessing, when constring is DOUBLE
    .furnessing.FurnessResults : Dataclass storing furnessing results
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
    trips, results = gravity_model(
        trip_ends, costs, function="tanner", function_args=(1, -0.01)
    )
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
