# -*- coding: utf-8 -*-
"""
    Module containing the functionality for matrix furnessing and factoring.

    See Also
    --------
    .gravity_model
"""

##### IMPORTS #####
# Standard imports
from dataclasses import dataclass
from enum import Enum, auto

# Third party imports
import numpy as np

# Local imports


##### CLASSES #####
class FurnessConstraint(Enum):
    """Types of furnessing/factoring for the gravity model."""

    SINGLE = auto()
    DOUBLE = auto()

    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"


@dataclass(frozen=True)
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

    def asdict(self) -> dict:
        """Return class attributes as a dictionary."""
        attrs = {}
        for nm in dir(self):
            if nm.startswith("_"):
                continue
            a = getattr(self, nm)
            if not callable(a):
                attrs[nm] = a
        return attrs


##### FUNCTIONS #####
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
    # Set factor to 0 wherever curr_tot is zero
    factor = np.divide(total, curr_tot, out=np.zeros_like(total), where=curr_tot != 0)
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
