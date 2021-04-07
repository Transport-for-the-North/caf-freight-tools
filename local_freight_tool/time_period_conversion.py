# -*- coding: utf-8 -*-
"""
    Module to convert matrices from annual PCUs into the model
    time period and zone system.

    See Also
    --------
    `time_distributions` module which contains classes used for
    the conversion calculations.
"""

##### IMPORTS #####
# Standard imports
import time
import re
import traceback
import os
from pathlib import Path
from typing import Dict, Callable, Union, Tuple

# Third party imports
import pandas as pd
import numpy as np

# Local imports
import errors
import utilities as utils
import matrix_utilities as mu
from time_distributions import TimeProfiles, HGVProfiles


##### FUNCTIONS #####
def check_parameter_paths(
    output_folder: Path,
    profile_path: Path,
    time_profile_path: Path,
    artic_matrix: Path,
    rigid_matrix: Path,
) -> Dict[str, Path]:
    """Checks that all parameters provided are existing files.

    All input files are checked to make sure they exist and are the
    correct type, the `output_folder` is created if it doesn't already exist.

    Parameters
    ----------
    output_folder : Path
        Path to the folder for saving the outputs, it will
        be created if it doesn't already exist.
    profile_path : Path
        Path to the Excel Workbook containing the HGV distribution profiles.
    time_profile_path : Path
        Path to the CSV file containing the time period information.
    artic_matrix : Path
        Path to the CSV containing the articulated HGV matrix in PCUs.
    rigid_matrix : Path
        Path to the CSV containing the rigid HGV matrix in PCUs.

    Returns
    -------
    Dict[str, Path]
        Dictionary containing all the paths (values) with readable
        names (keys) for use in output log spreadsheet.
    """
    utils.check_folder(output_folder, "Output", create=True)
    inputs = {
        "HGV Profiles": profile_path,
        "Time Profiles": time_profile_path,
        "Articulated Matrix": artic_matrix,
        "Rigid Matrix": rigid_matrix,
    }
    extensions = ((".xlsx",), (".csv", ".txt"), (".csv", ".txt"), (".csv", ".txt"))
    for (nm, p), ext in zip(inputs.items(), extensions):
        utils.check_file_path(p, nm, *ext)
    inputs["Output Folder"] = output_folder
    return inputs


def extract_zc_names(zone_correspondence_path: Path) -> Tuple[str, str]:
    """Extract the zone system names from the column headers in correspondence.

    Zone names are extracted from the 3rd column which is expected
    to be in the format "{from}_to_{to}" where from and to and the
    zone system names. If the zone system names can't be extracted
    then "original" and "rezoned" are returned.

    Parameters
    ----------
    zone_correspondence_path : Path
        Path to the zone correspondence CSV.

    Returns
    -------
    str
        Name of zone system being converted from.
    str
        Name of zone system being converted to.

    Raises
    ------
    IndexError
        If the correpondence file doesn't contain 3 columns.
    """
    tabs, header = mu.ODMatrix.check_file_header(zone_correspondence_path)
    if header is not None:
        with open(zone_correspondence_path, "rt") as f:
            line = f.readline()
        try:
            delimeter = "\t" if tabs else ","
            text = line.split(delimeter)[2]
        except IndexError as e:
            raise IndexError(
                "Zone correspondence file doesn't have 3 columns: "
                f"'{zone_correspondence_path}'"
            ) from e
        match = re.match(r"(\w+)_\w+_(\w+)", text)
    else:
        match = None
    if match is None:
        return "original", "rezoned"
    return match.groups()


def to_time_period(
    matrices: Dict[str, mu.ODMatrix],
    factors: Dict[str, float],
    output_folder: Path,
    zone_correspondence_path: Path,
    time_per: str,
    message_hook: Callable = print,
) -> Dict[str, Dict[str, Union[float, str]]]:
    """Converts matrices to given `time_per`, rezones and aggregates them together.

    Expects a rigid and artic ODMatrix to be provided which will be
    combined into a single HGV matrix for the model zone system and
    time period. Creates the following 5 output CSVs:
    - time period matrices for both vehicle types;
    - rezoned versions of the above matrices; and
    - HGV matrix containing aggregation of the rezoned matrices.

    Parameters
    ----------
    matrices : Dict[str, mu.ODMatrix]
        Dictionary containing ODMatrix instances for artic and
        rigid HGVs, in PCUs.
    factors : Dict[str, float]
        Time period factors for converting from annual PCUs to time
        period PCUs for each matrix in `matrices` (artic and rigid).
    output_folder : Path
        Path to the folder to save the outputs to, must already exist.
    zone_correspondence_path : Path
        Path to the zone correspondence lookup CSV.
    time_per : str
        Name of the time period being converted to, used for naming
        the output files.
    message_hook : Callable, optional
        Function for writing messages, by default print

    Returns
    -------
    Dict[str, Dict[str, Union[float, str]]]
        Dictionary containing summaries of the matrices
        (`ODMatrix.summary`) for each stage of the process.

    Raises
    ------
    errors.MissingDataError
        If either artic or rigid are not provided in `matrices`,
        or if time period factors aren't provided for both.
    """
    missing = [v for v in ("artic", "rigid") if v not in matrices]
    if missing:
        raise errors.MissingDataError("matrices", missing)
    # Create sub-folder for saving intermediary matrices
    output_subfolder = output_folder / f"{time_per}_intermediate"
    output_subfolder.mkdir(exist_ok=True, parents=True)
    # Extract zone system names from correpondence
    names = extract_zc_names(zone_correspondence_path)

    rezoned = {}
    summaries = {}
    for veh, mat in matrices.items():
        message_hook(f"Factoring and rezoning {veh} - {time_per}")
        f = factors.get(veh, None)
        if f is None:
            raise errors.MissingDataError(f"time period factors - {time_per}", veh)
        tp_mat = mat * f
        tp_mat.name = f"{time_per}_HGV_{veh}-{names[0]}"
        summaries[f"{veh.title()} - {time_per} - {names[0]}"] = tp_mat.summary()
        tp_mat.export_to_csv(output_subfolder / (tp_mat.name + ".csv"))

        rezoned[veh] = tp_mat.rezone(zone_correspondence_path)
        rezoned[veh].name = f"{time_per}_HGV_{veh}-{names[1]}"
        summaries[f"{veh.title()} - {time_per} - {names[1]}"] = rezoned[veh].summary()
        rezoned[veh].export_to_csv(output_subfolder / (rezoned[veh].name + ".csv"))
    del tp_mat

    message_hook(f"Combining artic and rigid matrices for {time_per}")
    combined = rezoned["artic"] + rezoned["rigid"]
    combined.name = f"{time_per}_HGV_combined-{names[1]}"
    summaries[f"Combined - {time_per}"] = combined.summary()
    combined.export_to_csv(output_folder / (combined.name + ".csv"))
    message_hook(f"Finished processing {time_per}")
    return summaries


def process_matrices(
    matrix_paths: Dict[str, Path],
    factors: Dict[str, Dict[str, float]],
    output_folder: Path,
    zone_correspondence_path: Path,
    message_hook: Callable = print,
) -> Dict[str, Dict[str, Union[str, float]]]:
    """Converts matrices to model time periods and zone system.

    Creates a combined HGV matrix for each time period which is the
    aggregation of the artic and rigid matrices after they've been
    converted to the model zone system.

    Parameters
    ----------
    matrix_paths : Dict[str, Path]
        Paths to the rigid and artic matrix CSVs in annual PCUs.
    factors : Dict[str, Dict[str, float]]
        Time period factors (values) with names (keys), where the value
        contains 2 factors one for artic and one for rigid HGVs.
    output_folder : Path
        Path to an existing folder to save the outputs to.
    zone_correspondence_path : Path
        Path to the zone correspondence lookup file to convert matrices
        to the model zone system.
    message_hook : Callable, optional
        Function for writing message, by default print

    Returns
    -------
    Dict[str, Dict[str, Union[str, float]]]
        Dictionary containing summaries of the matrices
        (`ODMatrix.summary`) for each stage of the process.

    Raises
    ------
    errors.BaseLocalFreightError
        If there is an error reading either of the input matrix CSV files.

    See Also
    --------
    `to_time_periods` which converts the rigid and artic matrices to
    a single time period and performs the aggregation.
    """
    mat_summary = {}
    matrices = {}
    for veh, path in matrix_paths.items():
        message_hook(f"Reading {veh} matrix")
        try:
            matrices[veh] = mu.ODMatrix.read_OD_file(path)
            mat_summary[f"Input {veh.title()}"] = matrices[veh].summary()
        except Exception as e:
            mat_summary[f"Input {veh.title()}"] = {
                "Comment": f"{e.__class__.__name__}: {e}"
            }
    errs = [v for v in ("artic", "rigid") if matrices.get(v, None) is None]
    if errs:
        msg = "matrix" if len(errs) == 1 else "matrices"
        raise errors.BaseLocalFreightError(
            f"Error reading input {msg}: {', '.join(errs)}"
        )

    for tp, curr_factors in factors.items():
        try:
            summaries = to_time_period(
                matrices,
                curr_factors,
                output_folder,
                zone_correspondence_path,
                tp,
                message_hook=message_hook,
            )
            mat_summary.update(summaries)
        except Exception as e:
            traceback.print_exc()
            msg = f"{e.__class__.__name__}: {e}"
            mat_summary[tp] = {"Comment": msg}
            message_hook(f"{tp} {msg}")

    return mat_summary


def _style_tp_factors(df: pd.DataFrame) -> pd.DataFrame.style:
    """Style the time period factors DataFrame.

    Formats the DataFrame to produce a more readable
    output and emphasises the time period factors.
    """
    df = df.copy()
    for c in ("hours", "days", "months"):
        df[c] = df[c].astype(str).str.replace(r"[\[\'\]]", "", regex=True)
    bold = lambda c: ["font-weight: bold"] * len(c)
    return df.style.apply(bold, axis=1, subset=["artic", "rigid"])


def _style_mat_summary(df: pd.DataFrame) -> pd.DataFrame.style:
    """Style the matrix summary DataFrame.

    Formats the numeric columns to sensible number of decimal
    places, emboldens the comined matrix rows and highlights
    the Cell Count and Total column green based on the following
    checks (red if any cells don't pass the checks):
    - Cell Count is the same for input artic and rigid matrices;
    - Cell count is the same for all matrices before rezoning;
    - Cell count is the same for all matrices after rezoning;
    - Total is the same for each matrix before/after it is rezoned;
    - Combined total is the same as the sum of artic & rigid totals.
    """

    def highlight_cell_count(col: pd.Series) -> np.ndarray:
        """Returns list of CSS background colours for highlighting Cell Count."""
        highlight = np.array([""] * len(col), dtype="U64")
        if col["Input Artic"] == col["Input Rigid"]:
            highlight[:2] = "background-color: green"
        else:
            highlight[:2] = "background-color: red"

        # Loop through rows in chunks of N_ROWS as there are that many
        # rows per time period
        N_ROWS = 5
        for n in range(1, len(col) - N_ROWS, N_ROWS):
            # Check that 1st and 3rd row for each time period have
            # same cell count as the inputs
            for check, test in (("Input Artic", 1), ("Input Rigid", 3)):
                i = n + test
                if col[check] == col.iloc[i]:
                    highlight[i] = "background-color: green"
                else:
                    highlight[i] = "background-color: red"
            # Check 2nd, 4th and 5th row have same cell count
            ind = [n + i for i in (2, 4, 5)]
            if col[ind[0]] == col[ind[2]] and col[ind[1]] == col[ind[2]]:
                highlight[ind] = "background-color: green"
            else:
                highlight[ind] = "background-color: red"
        return highlight

    def highlight_total(col: pd.Series) -> np.ndarray:
        """Returns list of CSS background colours for highlighting Total."""
        highlight = np.array([""] * len(col), dtype="U64")
        # Loop through rows in chunks of N_ROWS as there are that many
        # rows per time period
        N_ROWS = 5
        for n in range(1, len(col) - N_ROWS, N_ROWS):
            # Check that rezoning doesn't change totals
            for i, j in ((1, 2), (3, 4)):
                i += n
                j += n
                if round(col[i]) == round(col[j]):
                    highlight[[i, j]] = "background-color: green"
                else:
                    highlight[[i, j]] = "background-color: red"
            # Check combined total is sum of rezoned totals
            if round(col[n + 2] + col[n + 4]) == round(col[n + 5]):
                highlight[n + 5] = "background-color: green"
            else:
                highlight[n + 5] = "background-color: red"
        return highlight

    # Round total and max columns
    for c in ("Total", "Max"):
        df[c] = df[c].round()
    bold = lambda x: ["font-weight: bold"] * len(x)
    combined = [r for r in df.index if r.lower().startswith("combined")]
    subset = pd.IndexSlice[combined, :]
    return (
        df.style.apply(bold, axis=1, subset=subset)
        .apply(highlight_cell_count, axis=0, subset=["Cell Count"])
        .apply(highlight_total, axis=0, subset=["Total"])
    )


def to_excel_format(
    df: pd.DataFrame,
    writer: pd.ExcelWriter,
    sheet_name: str,
    col_fmt: Union[Dict[str, str], str] = None,
    **kwargs,
):
    """Write DataFrame to Excel and format given number columns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to be written to Excel.
    writer : pd.ExcelWriter
        Writer object to write to, should use openpyxl engine.
    sheet_name : str
        Name of the sheet to create.
    col_fmt : Union[Dict[str, str], str], optional
        Dictionary containing name of column in DataFrame (keys) and
        the number format to use based on Excel formats e.g. #,##0.0,
        by default None. If a string is given then all columns will be
        formatted using that single string.
    **kwargs : Keyword arguments
        Any other keyword arguments will be passed to
        `pd.DataFrame.to_excel`.
    """
    df.to_excel(writer, sheet_name=sheet_name, **kwargs)
    if col_fmt is None:
        return
    if isinstance(col_fmt, str):
        col_fmt = dict.fromkeys(df.columns.tolist(), col_fmt)
    sheet = writer.sheets[sheet_name]
    for nm, fmt in col_fmt.items():
        # Get column number openpyxl column numbers are 1 based
        col = df.columns.tolist().index(nm) + 1
        if kwargs.get("index", True):
            col += df.index.nlevels
        for (cell,) in sheet.iter_rows(min_col=col, max_col=col):
            cell.number_format = fmt


def write_log(
    path: Path,
    inputs: Dict[str, Union[str, int, Path]],
    hgv_profiles: HGVProfiles,
    factors: Dict[str, Dict[str, float]],
    matrix_summary: Dict[str, Dict[str, float]],
    message_hook: Callable = print,
):
    """Writes parameters and summaries to Excel Workbook.

    Parameters
    ----------
    path : Path
        Path to the Excel Workbook to create.
    inputs : Dict[str, Union[str, int, Path]]
        Contains all the paths (values) with readable names (keys) for
        use in output log spreadsheet, from `check_parameter_paths`.
    hgv_profiles : HGVProfiles
        Instance of `HGVProfiles` containing all the
        information on the HGV distributions.
    factors : Dict[str, Dict[str, float]]
        Dictionary containing factors for each time period with keys
        corresponding to the time period and each value a dictionary
        containing factors for both artic and rigid HGVs, from
        `HGVProfiles.time_period_factors`.
    matrix_summary : Dict[str, Dict[str, float]]
        Dictionary containing summaries of the matrices (`ODMatrix.summary`)
        for each stage of the process, from `process_matrices`.
    message_hook : Callable, optional
        Function for writing messages, by default print
    """
    message_hook(f"Writing {path}")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        msg = "Log for the time period conversion module for the Local Freight Tool"
        df = pd.DataFrame({"Notes": msg}, index=[1])
        df.to_excel(writer, sheet_name="Notes", index=False)
        if inputs:
            inputs_df = pd.DataFrame.from_dict(
                inputs, orient="index", columns=["Parameter Value"]
            )
            inputs_df.to_excel(writer, sheet_name="Input Parameters")
        if hgv_profiles:
            to_excel_format(
                hgv_profiles.monthly_avg, writer, "Monthly Avg Profile", col_fmt="0.0"
            )
            to_excel_format(
                hgv_profiles.weekly_avg.set_index(["time_str"], append=True),
                writer,
                "Weekly Avg Profile",
                col_fmt="0.0",
            )
        if factors:
            factors_df = pd.DataFrame.from_dict(factors, orient="index")
            to_excel_format(
                _style_tp_factors(factors_df),
                writer,
                "Time Period Factors",
                col_fmt=dict.fromkeys(("artic", "rigid"), "0.0E+0"),
            )
        if matrix_summary:
            mat_sum_df = pd.DataFrame.from_dict(matrix_summary, orient="index")
            to_excel_format(
                _style_mat_summary(mat_sum_df),
                writer,
                "Matrix Summaries",
                col_fmt={
                    "Total": "#,##0",
                    "Mean": "0.000",
                    "Standard deviation": "0.000",
                },
            )
    message_hook(f"Opening {path}")
    os.startfile(path.resolve())


def main(
    output_folder: Path,
    profile_path: Path,
    time_profile_path: Path,
    year: int,
    artic_matrix: Path,
    rigid_matrix: Path,
    zone_correspondence_path: Path,
    message_hook: Callable = print,
):
    """Convert annual PCU rigid and artic matrices into time periods.

    Parameters
    ----------
    output_folder : Path
        Path to a folder where all the output files will be
        saved, will be created if it doesn't already exist.
    profile_path : Path
        Path to the Excel Workbook containing the HGV distribution
        profiles tables.
    time_profile_path : Path
        Path to the CSV containing the time period information.
    year : int
        Year that the model is being ran for, only used for
        calculating the average number of weeks in a month.
    artic_matrix : Path
        Path to the articulated matrix CSV in annual PCUs.
    rigid_matrix : Path
        Path to the rigid matrix CSV in annual PCUs.
    zone_correspondence_path : Path
        Path to the zone correspondence lookup CSV.
    message_hook : Callable, optional
        Function for writing messages, by default print
    """
    start_time = time.perf_counter()
    hgv_profiles = None
    try:
        log_sheets = {}
        # Check input paramters and add to dictionary for logging
        log_sheets["inputs"] = check_parameter_paths(
            output_folder, profile_path, time_profile_path, artic_matrix, rigid_matrix
        )
        log_sheets["inputs"]["Year"] = year

        # Calculate weighted average distributions
        message_hook("Processing HGV profiles")
        hgv_profiles = HGVProfiles(profile_path, year)
        # Read time profiles data and calculate factors
        message_hook("Processing time profiles")
        time_profiles = TimeProfiles(time_profile_path)
        message_hook("Calculating time period factors")
        factors = hgv_profiles.time_period_factors(time_profiles)

        # Read matrices and apply factors
        log_sheets["matrix_summary"] = process_matrices(
            {"artic": artic_matrix, "rigid": rigid_matrix},
            factors,
            output_folder,
            zone_correspondence_path,
            message_hook=message_hook,
        )

        # Write log file
        log_sheets["factors"] = time_profiles.time_periods.copy()
        for tp, vals in log_sheets["factors"].items():
            vals.update(factors.get(tp, {}))
    except Exception as e:
        message_hook(f"{e.__class__.__name__}: {e}")
        raise
    finally:
        try:
            write_log(
                output_folder / "time_period_conversion_log.xlsx",
                log_sheets.get("inputs", None),
                hgv_profiles,
                log_sheets.get("factors", None),
                log_sheets.get("matrix_summary", None),
                message_hook=message_hook,
            )
        except Exception as e:
            message_hook(f"Error writing log spreadsheet - {e.__class__.__name__}: {e}")
            raise

    time_taken = time.perf_counter() - start_time
    if time_taken < 60:
        tt_str = f"{time_taken:.1f}s"
    else:
        mins, secs = divmod(time_taken, 60)
        tt_str = f"{mins:.0f}m {secs:.0f}s"
    message_hook(f"Time period conversion done in {tt_str}")
