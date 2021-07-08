# -*- coding: utf-8 -*-
"""
    Module containing the gravity model used in the LGV model.
"""

##### IMPORTS #####
# Standard imports

# Third party imports
import numpy as np
import pandas as pd

# Local imports
from .. import errors


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


def _check_gm_inputs(
    trip_ends: pd.DataFrame, costs: pd.DataFrame, calibration: pd.DataFrame
) -> None:
    """Sorts the indices and checks the input DataFrames for `gravity_model_equation`."""
    args = {"trip_ends": trip_ends, "costs": costs, "calibration": calibration}
    for nm, df in args.items():
        df.sort_index(axis=0, inplace=True)
        if df.index.has_duplicates:
            raise ValueError(f"duplicates not allowed in `{nm}` index")
        if df.columns.has_duplicates:
            raise ValueError(f"duplicates not allowed in `{nm}` columns")
        if nm == "trip_ends":
            continue
        df.sort_index(axis=1, inplace=True)
        same = df.index.equals(trip_ends.index) and df.columns.equals(trip_ends.index)
        if not same:
            raise ValueError(
                f"`{nm}` must be a square matrix with same zones as "
                "`trip_ends` for gravity model calculations"
            )


def gravity_model_equation(
    trip_ends: pd.DataFrame,
    costs: pd.DataFrame,
    calibration: pd.DataFrame = None,
    normalise_costs: bool = True,
    function: str = "tanner",
    **kwargs,
) -> pd.DataFrame:
    r"""Implementation of the main Gravity Model function, see Notes.

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
    normalise_costs : bool, default True
        If costs should be normalised or not.
    function : {'tanner', 'log_normal'}
        Choice of cost function to use.

    Returns
    -------
    pd.DataFrame
        DataFrame containing trips, same shape as costs.

    Raises
    ------
    KeyError
        If a `function` is given which doesn't exist.
    ValueError
        If any of the input DataFrames have duplicates in the
        index or they don't have the same index and columns as
        the `trip_ends` index.

    Notes
    -----
    Formula use for this function is:

    .. math::

        T_{ij} = T_i \frac{A_j f(C_{ij}) K_{ij}}
        {\sum^n_{j'=1} A_{j'} f(C_{ij'}) K_{ij'}}

    where:

    - :math:`T_{ij}`: trips from i to j.
    - :math:`T_i`: trips from i (productions).
    - :math:`A_j`: trips attracted to j.
    - :math:`f(C_{ij})`: travel cost friction factor (see below).
    - :math:`K_{ij}`: calibration parameter.

    See Also
    --------
    tanner, log_normal
    """
    FUNCTION_LOOKUP = {
        "log_normal": log_normal,
        "tanner": tanner,
    }
    try:
        func = FUNCTION_LOOKUP[function.lower().strip()]
    except KeyError as e:
        raise KeyError(
            f"unknown function {function!r}, should be "
            f"one of {list(FUNCTION_LOOKUP.keys())}"
        ) from e
    # Check trip_ends has the correct names
    trip_ends.rename(columns=lambda nm: nm.strip().lower(), inplace=True)
    missing = [c for c in ("attractions", "productions") if c not in trip_ends.columns]
    if missing:
        errors.MissingColumnsError("gravity model trip ends", missing)
    # Check costs and calibrations are matrices with same zones as trip_ends
    if calibration is None:
        calibration = pd.DataFrame(1.0, index=trip_ends.index, columns=trip_ends.index)
    _check_gm_inputs(trip_ends, costs, calibration)

    # Convert vectors of productions and attractions to matrices for calcs
    matrices = [
        np.tile(trip_ends.productions, (len(trip_ends.productions), 1)).T,
        np.tile(trip_ends.attractions, (len(trip_ends.attractions), 1)),
    ]
    # TODO Check if the costs should be normalised or not?
    if normalise_costs:
        costs = costs / np.sum(costs.values)
    numerator = pd.DataFrame(
        matrices[0] * matrices[1] * func(costs.values, **kwargs) * calibration.values,
        index=trip_ends.index,
        columns=trip_ends.index,
    )
    # Denominator uses the total attractions, and then the sum of
    # all the columns (j) for costs and calibration factors
    denominator = (
        np.sum(trip_ends.attractions.values)
        * func(np.sum(costs.values, axis=1), **kwargs)
        * np.sum(calibration.values, axis=1)
    )
    # Divide all the columns of the numerator by the 1D denominator array
    return numerator.divide(denominator, axis=0)


def _check_matrix(matrix: np.ndarray):
    if matrix.ndim != 2:
        raise ValueError(f"matrix should have 2 dimensions not: {matrix.ndim}")
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"matrix should be a square not shape: {matrix.shape}")


def factor_1d(matrix: np.ndarray, total: np.ndarray, axis: int):
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


def compare_totals(matrix: np.ndarray, col_total: np.ndarray, row_total: np.ndarray):
    differences = []
    for i, tot in enumerate((col_total, row_total)):
        curr_tot = np.sum(matrix, axis=i)
        differences.append(np.abs(curr_tot - tot))
    return np.mean(differences)


def factor_2d(matrix: np.ndarray, col_total: np.ndarray, row_total: np.ndarray):
    _check_matrix(matrix)
    # Factor columns then rows
    matrix = factor_1d(matrix, col_total, 0)
    matrix = factor_1d(matrix, row_total, 1)
    avg_diff = compare_totals(matrix, col_total, row_total)
    return matrix, avg_diff


def factor_totals(
    col_total: np.ndarray, row_total: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
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
):
    col_total, row_total = factor_totals(col_total, row_total)
    loop = 0
    avg_diff = compare_totals(matrix, col_total, row_total)
    differences = [avg_diff]
    while avg_diff > diff_cutoff:
        if loop >= max_loops:
            print(
                f"Reached maximum number of loops ({loop}) "
                f"with mean row/column difference: {avg_diff:.1e}"
            )
            break
        if len(differences) >= check_diff:
            differences = differences[-check_diff:]
            if np.isclose(differences, differences[0]).all():
                # If avg_diff hasn't changed for a number of loops then exit early
                print(
                    f"Mean row/column difference ({avg_diff:.1e}) has not "
                    f"improved for {check_diff} loops, ending on loop {loop}"
                )
                break
        matrix, avg_diff = factor_2d(matrix, col_total, row_total)
        loop += 1
        # Keep last 5 differences for checking
        differences = differences[-(check_diff - 1) :] + [avg_diff]
    else:
        print(
            f"Furness converged (loop {loop}) "
            f"with mean row/column difference: {avg_diff:.1e}"
        )
    return matrix, avg_diff


def main():
    pass


def test_gm_func():
    """Runs the `gravity_model_equation` with small 3x3 matrix."""
    rng = np.random.default_rng(1)
    zones = [1, 2, 3]
    trip_ends = pd.DataFrame(
        {"attractions": [105, 115, 125], "productions": [110, 120, 130]}, index=zones
    )
    costs = pd.DataFrame(rng.integers(1000, 2000, (3, 3)), index=zones, columns=zones)
    trips = gravity_model_equation(trip_ends, costs, function="tanner", alpha=1, beta=1)
    print("Trip Ends:", trip_ends, "Costs:", costs, "Trips:", trips, sep="\n")
    trips, _ = furness_2d(
        trips.values, trip_ends.attractions.values, trip_ends.productions.values
    )
    print("Furnessed:", trips, sep="\n")
    print(
        f"Total trips: {np.sum(trips):}",
        f"Trip ends: {np.sum(trip_ends):}",
        sep="\n",
    )


##### MAIN #####
if __name__ == "__main__":
    test_gm_func()
