# -*- coding: utf-8 -*-
"""
    Module containing the gravity model used in the LGV model.

    See Also
    --------
    .furnessing
"""

##### IMPORTS #####
# Standard imports
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Third party imports
import numpy as np
import pandas as pd
from scipy import optimize

# Local imports
from .. import errors, utilities
from .furnessing import FurnessConstraint, FurnessResults, furness_2d, factor_1d


##### CLASSES #####
@dataclass(frozen=True)
class CalibrationResults:
    """Dataclass storing results from `CalibrateGravityModel`."""

    cost_function: str
    """Name of the cost function used in calibration."""
    cost_parameters: np.ndarray
    """Optimal parameters found for the cost function."""
    call_count: int
    """The number of calls to `gravity_model` before optimum
    parameters were found.
    """
    r_squared: float
    """R squared value between the observed and trip matrix
    cost distributions."""


class CalibrateGravityModel:
    """Calibrates the gravity model using least squares fit to find optimal parameters.

    Parameters
    ----------
    trip_ends_path : Path
        Path to the trip ends data for a single segment.
    cost_path : Path
        Path to a cost matrix CSV, should be a square matrix
        with zone numbers as the column names and index.
    trip_distribution_path : tuple[Path, str]
        - Path to the trip distributions Excel file.
        - Name of the sheet containing the distribution
          the distribution should have the same units as
          the cost matrix.
    calibration_path : Path, optional
        Path to a calibration matrix CSV, should be in the
        same format as the cost matrix.

    Attributes
    ----------
    trip_matrix : pd.DataFrame
        The matrix containing the trips.
    trip_distribution : pd.DataFrame
        The input trip distribution information
        with an additional column containing the
        distribution of the `trip_matrix`.
    furness_results : FurnessResults
        The results from the final furnessing
        process.
    results : CalibrationResults
        The results from the calibration process.
    """

    TRIP_DISTRIBUTION_COLS = dict.fromkeys(
        ("start", "end", "average", "observed proportions"), float
    )
    """Names and dtypes of the columns expected in the trip distributions input."""

    def __init__(
        self,
        trip_ends_path: Path,
        cost_path: Path,
        trip_distribution_path: tuple[Path, str],
        calibration_path: Path = None,
    ):
        self._read(trip_ends_path, cost_path, trip_distribution_path, calibration_path)
        # Get bin edges from trip distribution
        self._bin_edges = np.concatenate(
            [
                self.trip_distribution.start.values,
                self.trip_distribution.end.values[-1:],
            ]
        )
        self.trip_matrix = None
        self.furness_results = None
        self.results = None
        self._call_count = 0
        self._function_name = "tanner"
        self._function_kwargs = None

    def _read(
        self,
        trip_ends_path: Path,
        cost_path: Path,
        trip_distribution_path: tuple[Path, str],
        calibration_path: Path,
    ):
        """Reads and checks input files and performs some pre-processing on them."""
        # Read trip ends, with first column as index and rename
        # to attractions and productions (expected names in gravity_model)
        self.trip_ends = utilities.read_csv(
            trip_ends_path, "Trip Ends CSV", {0: int, 1: float, 2: float}, index_col=0
        )
        self.trip_ends.columns = ["attractions", "productions"]
        # Read costs and calibration and use first column as index
        self.costs = utilities.read_csv(cost_path, "Cost matrix", index_col=0)
        self.costs.columns = pd.to_numeric(self.costs.columns, downcast="integer")
        zero_cost = self.costs.values == 0
        if np.any(zero_cost):
            raise ValueError(f"costs contains {np.sum(zero_cost)} cells with 0 cost")
        if calibration_path is None:
            self.calibration = None
        else:
            self.calibration = utilities.read_csv(
                calibration_path, "Gravity model calibration matrix", index_col=0
            )
            self.calibration.columns = pd.to_numeric(
                self.calibration.columns, downcast="integer"
            )
        # Read trip distributions name from top row of Excel file
        td_info = utilities.read_excel(
            trip_distribution_path[0],
            "Gravity model trip distribution",
            sheet_name=trip_distribution_path[1],
            nrows=1,
            header=None,
        )
        self.distribution_name = td_info.at[0, 0]
        # Read the rest of the distributions sheet
        self.trip_distribution = utilities.read_excel(
            trip_distribution_path[0],
            "Gravity model trip distribution",
            columns=self.TRIP_DISTRIBUTION_COLS,
            sheet_name=trip_distribution_path[1],
            skiprows=1,
        )
        # Normalise observed proportions
        self.trip_distribution["observed proportions"] = (
            self.trip_distribution["observed proportions"]
            / self.trip_distribution["observed proportions"].sum()
        )

    @staticmethod
    def r_squared(fit_data: np.ndarray, func_data: np.ndarray) -> float:
        r"""Calculates R squared statistic for observed `fit_data`.

        Parameters
        ----------
        fit_data, func_data : np.ndarray
            The trip distributions for comparison.

        Returns
        -------
        float
            The R squared value.

        Notes
        -----
        The :math:`R^2` is calated between the `fit_data` (y)
        and the `func_data` (f) with the following formula:

        .. math:: R^2 = 1 - \frac{SS_{res}}{SS_{tot}}

        where the total sum of squares is:

        .. math:: SS_{tot} = \sum_i(y_i - \bar{y})^2

        and the residual sum of squares is:

        .. math:: SS_{res} = \sum_i(y_i - f_i)^2
        """
        ss_res = np.sum((fit_data - func_data) ** 2)
        ss_tot = np.sum((fit_data - np.mean(fit_data)) ** 2)
        return 1 - (ss_res / ss_tot)

    def _normalised_distribution(self, matrix: np.ndarray) -> np.ndarray:
        """Calculates distribution of costs normalised to sum to 1."""
        hist, _ = np.histogram(matrix, bins=self._bin_edges, weights=self.costs)
        return hist / np.sum(hist)

    def _gm_distribution(
        self,
        _,
        *args: float,
    ) -> np.ndarray:
        """Runs gravity model with given parameters and returns distribution.

        Used by the `optimize.curve_fit` function.
        """
        if self._function_kwargs is None:
            self._function_kwargs = {}
        self._call_count += 1
        self.trip_matrix, self.furness_results = gravity_model(
            self.trip_ends,
            self.costs,
            self.calibration,
            self._function_name,
            function_args=args,
            **self._function_kwargs,
        )
        return self._normalised_distribution(self.trip_matrix)

    def calibrate_gravity_model(
        self,
        function: str = "tanner",
        **kwargs,
    ) -> CalibrationResults:
        """Finds the optimal parameters for the cost function.

        Optimal parameters are found using `scipy.optimize.curve_fit`
        to fit the matrix trip distribution to the observed distribution.

        Parameters
        ----------
        function : str, default "tanner"
            The name of the cost function to use,
            passed to `gravity_model`.
        kwargs : Keyword arguments, optional
            Keyword arguments to pass to `gravity_model`.

        Returns
        -------
        CalibrationResults
            Dataclass containing results from calibration
            process.

        Raises
        ------
        ValueError
            If the generated trip matrix contains any
            non-finite values.

        See Also
        --------
        gravity_model
        """
        self._call_count = 0
        self._function_name = function
        self._function_kwargs = kwargs
        # Find optimum parameters for cost function
        _, init_params, bounds = _get_cost_function(function)
        popt, _ = optimize.curve_fit(
            self._gm_distribution,
            self.trip_distribution.average.values,
            self.trip_distribution["observed proportions"].values,
            p0=init_params,
            bounds=bounds,
            method="dogbox",
            verbose=2,
            diff_step=1,
        )
        non_finite = ~np.isfinite(self.trip_matrix.values)
        if np.any(non_finite):
            raise ValueError(
                f"Final trip matrix has {np.sum(non_finite)} non-finite values"
            )
        self.trip_distribution["matrix proportions"] = self._normalised_distribution(
            self.trip_matrix
        )
        self.results = CalibrationResults(
            function,
            popt,
            self._call_count,
            self.r_squared(
                self.trip_distribution["observed proportions"],
                self.trip_distribution["matrix proportions"],
            ),
        )
        return self.results


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
        "log_normal": (log_normal, [1.0, 1.0], ([0, -100], [100, 100])),
        "tanner": (tanner, [1.0, -1.0], ([0, -100], [100, 0])),
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
    kwargs : Keyword arguments, optional
        Keyword arguments passed to `furness_2d`, ignored
        if `constraint` is SINGLE.

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
    CalibrateGravityModel : Class for calibration gravity model to cost distribution.
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
    folder = Path(
        r"C:\WSP_Projects\TfN Local Freight Model\01 - Delivery\LGV Method\GM Test Inputs"
    )
    trip_ends_path = folder / "trip_ends.csv"
    costs_path = folder / "costs.csv"
    trip_distribution_path = (
        folder / "LGV_trip_distributions.xlsx",
        "Test Trip Distribution",
    )
    calib_gm = CalibrateGravityModel(trip_ends_path, costs_path, trip_distribution_path)
    calib_gm.calibrate_gravity_model()

    print(
        "Trip Ends:",
        calib_gm.trip_ends,
        "Costs:",
        calib_gm.costs,
        "Calibration:",
        calib_gm.calibration,
        f"Trip Distribution: {calib_gm.distribution_name}",
        calib_gm.trip_distribution,
        "Trips:",
        calib_gm.trip_matrix,
        "Furness Results",
        calib_gm.furness_results,
        "Calibration Results",
        calib_gm.results,
        f"Total trips: {np.sum(calib_gm.trip_matrix.values):}",
        f"Trip ends: {np.sum(calib_gm.trip_ends):}",
        sep="\n",
    )


##### MAIN #####
if __name__ == "__main__":
    test_gm_func()
