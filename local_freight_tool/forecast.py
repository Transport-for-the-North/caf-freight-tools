"""
Class to create a forecast demand matrix.
"""

##### IMPORTS #####
# Standard imports
import os
from pathlib import Path
import traceback
from typing import List, Dict, Callable

# Third-party imports
import pandas as pd

# User-defined imports
from matrix_utilities import ODMatrix

##### CLASS #####
class ForecastDemand:
    """Class to create a model forecast demand matrix from the base year model
    assignment demand matrix, base year processed freight demand matrix and
    forecast year processed freight demand matrix.
    """

    def __init__(
        self,
        matrix_paths: Dict[str, Path],
        output_folder: Path,
        growth_mode: str = "standard",
        k1: float = 1,
        k2: float = 1,
        message_hook: Callable = print,
    ) -> None:
        """Initialises class.

        Parameters
        ----------
        matrix_paths : Dict[Path, Path, Path]
            Dictionary of paths to the O-D matrix input CSVs. The dictionary
            keys must be "model_base", "processed_base", and
            "processed_forecast".
        output_folder: Path
            Folder to save all outputs in.
        growth_mode : str, optional
            Defined whether the growth mode is standard or exceptional, by
            default 'standard'. For more information on the growth mode
            differences, see section 7: Delta Process of the User Guide or
            readme.

        Raises
        ------
        ValueError
            Raised when weighting factors k1 and k2 are not floats.
        """
        self.message_hook = message_hook
        self.message_hook("Initialising class")
        self.matrix_paths = matrix_paths
        if growth_mode.lower().strip() not in ("standard", "exceptional"):
            raise ValueError(
                f"growth_mode should be 'standard' or 'exceptional' not '{growth_mode}'"
            )
        self.growth_mode = growth_mode.lower().strip()
        inputs = {**matrix_paths, "growth_mode": growth_mode}
        self.output_folder = output_folder
        self.progress = pd.DataFrame(
            {
                "Process": [
                    "Initialise",
                    "Log inputs",
                    "Check output folder and weightings",
                    "Read in matrix csvs",
                    "Create forecast",
                    "Save forecast matrix",
                    "Save matrix summaries",
                ],
                "Completed": ["no"] * 7,
                "Error": [""] * 7,
            }
        )
        if self.growth_mode != "standard":
            self.k1 = k1
            self.k2 = k2
            inputs["k1"] = k1
            inputs["k2"] = k2

        self.inputs = pd.DataFrame.from_dict(inputs, orient="index", columns=["value"])
        self.inputs.index.name = "parameter"
        self.progress.loc[self.progress.Process == "Initialise", "Completed"] = "yes"
        print("initialisation complete")

    def _check_inputs(self):
        """If the growth mode is not standard, check that the weighting inputs
        are floats

        Raises
        ------
        FileNotFoundError
            If the output folder specified is not a directory
        ValueError
            If k1 and k2 are not numbers.
        """
        self.message_hook("Checking inputs")
        if not self.output_folder.is_dir():
            msg = f"{self.output_folder} is not a valid directory"
            self.message_hook(msg)
            raise FileNotFoundError(msg)

        if self.growth_mode != "standard":
            try:
                self.k1 = float(self.k1)
                self.k2 = float(self.k2)
            except ValueError as e:
                msg = f"Error: k1 and k2 must be floats. Values given were k1={self.k1}, k2={self.k2}"
                self.message_hook(msg)
                raise ValueError(msg) from e

        self.progress.loc[
            self.progress.Process == "Check output folder and weightings", "Completed"
        ] = "yes"

    def export_inputs(self, writer: pd.ExcelWriter):
        """Write inputs to log file.

        Parameters
        ----------
        writer: pd.ExcelWriter
            Spreadsheet to write the inputs sheet to
        """
        self.message_hook("Saving inputs to log file")
        self.inputs.to_excel(writer, sheet_name="inputs", index=True)
        self.progress.loc[self.progress.Process == "Log inputs", "Completed"] = "yes"

    def read_matrices(self):
        """Reads in input matrices."""
        self.message_hook("Reading in input matrices")
        self.matrices = {}
        for key in self.matrix_paths:
            self.matrices[key] = ODMatrix.read_OD_file(self.matrix_paths[key])
        self.progress.loc[
            self.progress.Process == "Read in matrix csvs", "Completed"
        ] = "yes"

    def forecast(self) -> None:
        """Creates the Model Forecast Demand Matrix as detailed in the Delta
        Process methodology flowchart, which can be found in the readme and
        User Guide.
        """
        self.message_hook("Creating model forecast demand matrix")
        try:
            self.matrices.values()
        except AttributeError:
            self.read_matrices()

        # align_matrices
        model_base, processed_base, processed_forecast = self._align_matrices(
            [
                self.matrices["model_base"].matrix,
                self.matrices["processed_base"].matrix,
                self.matrices["processed_forecast"].matrix,
            ]
        )

        # calculate required processed_forecast/processed_base values
        processed_forecast_div_base = (
            (processed_forecast / processed_base)
            .where(~((processed_forecast == 0) & (processed_base != 0)), other=0)
            .where(~(processed_base == 0), other=1)
        )

        # perform generalised calculation
        model_forecast = (
            model_base * processed_forecast_div_base
            + processed_forecast
            - processed_base
        )

        # assign the values which depend on the growth mode - cases 4 and 8
        mode_condition = (processed_forecast > 0) & (processed_base > 0)

        # case 4 and 8 values are identical in standard mode
        if self.growth_mode == "standard":
            growth_mode_cases = [model_base * processed_forecast_div_base]
            growth_mode_conditions = [mode_condition]
        # case 4 and 8 differ in standard mode
        else:
            growth_mode_cases = [
                processed_forecast - self.k1 * processed_base,
                model_base * self.k2 * processed_forecast_div_base
                + processed_forecast
                - self.k2 * processed_base,
            ]
            growth_mode_conditions = [
                (model_base == 0) & mode_condition,
                (model_base > 0) & mode_condition,
            ]

        # reassign the values for cases 4 and 8
        for i, condition in enumerate(growth_mode_conditions):
            model_forecast = model_forecast.where(
                ~condition, other=growth_mode_cases[i]
            )

        # set negative values to 0
        model_forecast = model_forecast.where(model_forecast > 0, 0)

        # create model forecast ODMatrix instance
        self.model_forecast = ODMatrix(model_forecast, name="model_forecast_demand")

        self.progress.loc[
            self.progress.Process == "Create forecast", "Completed"
        ] = "yes"

    def export_forecast_demand(self):
        """Saves the forecast demand matrix as model_forecast_demand.csv in
        the specified output folder. If the forecasting process has not been
        run, it will run the process before saving the forecast matrix.

        Parameters
        ----------
        output_folder : Path
            Path to output folder.

        Returns
        -------
        outpath: Path
            Forecast matrix CSV filepath.
        """
        self.message_hook("Saving forecast demand matrix")
        try:
            self.model_forecast.name
        except AttributeError:
            self.forecast()
        finally:
            outpath = self.output_folder / Path(f"{self.model_forecast.name}_{self.growth_mode}.csv")
            self.model_forecast.export_to_csv(outpath)
            self.progress.loc[
                self.progress.Process == "Save forecast matrix", "Completed"
            ] = "yes"

    def export_summary(self, writer: pd.ExcelWriter):
        """Exports input and output matrix summaries to an excel sheet.

        Parameters
        ----------
        writer : pd.ExcelWriter
            xlsx file to add the matrix summaries sheet to
        """
        self.message_hook("Saving matrix summaries to log file")
        try:
            self.model_forecast.summary()
        except AttributeError:
            self.forecast()
        finally:
            matrix_summaries = {}
            for key in self.matrices:
                matrix_summaries[key] = self.matrices[key].summary()
            matrix_summaries[self.model_forecast.name] = self.model_forecast.summary()

            summary_df = pd.DataFrame.from_dict(matrix_summaries, orient="index")
            summary_df.index.name = "Matrix"
            summary_df.to_excel(
                writer, sheet_name="matrix_summaries", float_format="%.2f"
            )
            self.progress.loc[
                self.progress.Process == "Save matrix summaries", "Completed"
            ] = "yes"

    @staticmethod
    def _align_matrices(
        matrices: List[pd.DataFrame], fill_value: float = 0
    ) -> pd.DataFrame:
        """Aligns input matrices, returns aligned matrices in the order they
        were input.

        Parameters
        ----------
        matrices: List[pd.DataFrame]
            List of matrices to align.
        fill_value : float, optional
            Value to fill empty cells with, by default 0.

        Returns
        -------
        pd.DataFrame
            Aligned matrices.
        """
        if len(matrices) == 1:
            return matrices
        if len(matrices) == 2:
            return matrices[0].align(matrices[1], join="outer", fill_value=0)
        for i in range(len(matrices)):
            matrices[i], matrices[(i + 1) % len(matrices)] = matrices[i].align(
                matrices[(i + 1) % len(matrices)], join="outer", fill_value=fill_value
            )
        return matrices

    def main(self):
        """Main forecasting process, which creates a log file with inputs,
        processes performed, errors and matrix summaries, reads in the input
        matrices, performs the forecasting process, and exports the forecasted
        demand matrix.
        """
        log_file = self.output_folder / Path("forecast_log.xlsx")
        with pd.ExcelWriter(str(log_file), engine="openpyxl") as writer:
            try:
                self.export_inputs(writer)
                self._check_inputs()
                self.read_matrices()
                self.forecast()
                self.export_forecast_demand()
                self.export_summary(writer)

            except Exception as e:
                traceback.print_exc()
                self.progress.iloc[
                    self.progress.loc[self.progress.Completed == "no"].index[0],
                    self.progress.columns.get_loc("Error"),
                ] = str(e)
                self.message_hook(f"{e.__class__.__name__}: {e}")
            finally:
                try:
                    self.message_hook("Writing progress and errors to log spreadsheet")
                    self.progress.to_excel(writer, sheet_name="process", index=False)
                except UnboundLocalError as e:
                    self.message_hook(
                        f"Error writing log spreadsheet - {e.__class__.__name__}: {e}"
                    )
                    raise

            self.message_hook("Forecasting process complete. Outputs saved to")
            self.message_hook(f"{self.output_folder}")
            self.message_hook("Check log file for details.")

        os.startfile(log_file, "open")
