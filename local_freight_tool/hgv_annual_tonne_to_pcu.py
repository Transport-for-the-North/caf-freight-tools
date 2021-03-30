"""

File purpose:
Class to split GBFM HGV annual tonnage matrices into rigid and artic
matrices, and convert to PCUs.

Created on: Fri Mar 19 2021

Original author: CaraLynch

"""

##### IMPORTS #####
# Standard imports
from pathlib import Path

# User-defined imports
from matrix_utilities import ODMatrix

# Third-party imports
import pandas as pd
import numpy as np


class TonneToPCU:
    """Class for the HGV artic-rigid split and annual tonnage to annual PCU
    conversion.
    """

    def __init__(
        self,
        inputs,
        hgv_keys=["domestic_bulk_port", "unitised_eu_imports", "unitised_eu_exports"],
    ):
        """Initialises class by reading in all input files required for tonne
        to PCU conversion and rigid-artic split.

        Parameters
        ----------
        inputs : dict
            Dictionary of all input file paths as strings, with keys
            'domestic_bulk_port', 'unitised_eu_imports', 'unitised_eu_exports'
            and 'unitised_non_eu', 'ports', 'distance_bands',
            'gbfm_distance_matrix', 'port_traffic_proportions' and
            'pcu_factors'. All input files must be csvs with columns:
            - domestic_bulk_port, unitised_eu_imports, unitised_eu_exports,
            gbfm_distance_matrix: origin, destination and
            trips, there is no need for headers.
            - unitised_non_eu: "Imp0Exp1", "GBPortctr", "GBRawZone",
                                "Traffic".
            - ports: "GBPortctr", "GBZone".
            - distance_bands: "start", "end", "rigid", "artic".
            - port_traffic_proportions: "type", "direction", "accompanied",
                                        "artic", "rigid".
            - pcu_factors: "zone", "direction", "artic", "rigid". There must
                            also be a default row.
        hgv_keys : list, optional
            Keys in inputs dictionary corresponding to HGV matrix strings,
            except the EU non-EU import/export matrix, by default
            ['domestic_bulk_port', 'unitised_eu_imports',
            'unitised_eu_exports']
        """
        self.input_files = inputs
        self.hgv_keys = hgv_keys
        self._read_inputs()
        self.KEYS = ["artic", "rigid"]

    def _read_inputs(self):
        """Reads in all input files required for rigid-artic split and
        conversion from tonnes to PCU as ODMatrix instances or pd.DataFrames.

        Raises
        ------
        KeyError
            Raised when there are missing O-D pairs in the GBFM distance
            matrix.
        ValueError
            Raised when duplicate zone-direction values are found in the PCU
            factors file.
        ValueError
            Raised when no default value is found in the PCU factors file.
        """
        self.inputs = {}
        for key in self.hgv_keys:
            self.inputs[key] = ODMatrix.read_OD_file(self.input_files[key])
        self.inputs["ports"] = self.read_csv(
            self.input_files["ports"],
            ["GBPortctr", "GBZone"],
            new_headers=["port_id", "zone_id"],
        )
        self._read_non_eu_imports_exports_file()
        self.inputs["distance_bands"] = self.read_csv(
            self.input_files["distance_bands"],
            ["start", "end", "rigid", "artic"],
            numerical_columns=["start", "end", "rigid", "artic"],
        )

        self.inputs["gbfm_distance_matrix"] = ODMatrix.read_OD_file(
            self.input_files["gbfm_distance_matrix"]
        )

        # Check all zones in the domestic and bulk port matrix are present in
        # the GBFM distance matrix
        some_missing = (
            ~self.inputs["domestic_bulk_port"].matrix.index.isin(
                self.inputs["gbfm_distance_matrix"].matrix.index
            )
        ).any() | (
            ~self.inputs["domestic_bulk_port"].matrix.columns.isin(
                self.inputs["gbfm_distance_matrix"].matrix.columns
            )
        ).any()

        if some_missing:
            raise KeyError(
                "Error: The GBFM distance matrix does not contain"
                " all O-D pairs in the domestic and bulk port matrix"
            )

        self.inputs["port_traffic_proportions"] = self.read_csv(
            self.input_files["port_traffic_proportions"],
            ["type", "direction", "accompanied", "artic", "rigid"],
            numerical_columns=["artic", "rigid"],
        )
        self.inputs["pcu_factors"] = self.read_csv(
            self.input_files["pcu_factors"],
            ["zone", "direction", "artic", "rigid"],
            numerical_columns=["artic", "rigid"],
        )

        # check PCU factors are unique for each zone-direction pair
        if (
            (self.inputs["pcu_factors"].groupby(["zone", "direction"]).count() > 1)
            .any()
            .any()
        ):
            msg = f"Error: duplicate zone-direction values found in PCU factors file."
            raise ValueError(msg)

        # check PCU factors contains a default column
        if not (self.inputs["pcu_factors"].zone == "default").any():
            msg = f"Error: no default value found in PCU factors file."
            raise ValueError(msg)

    def _read_non_eu_imports_exports_file(self):
        """Reads in the unitised non-European imports/exports file, rezones
        the port IDs to their GBFM zone IDs, separates imports from exports, and
        creates OD Matrix instances for imports and exports.

        Raises
        ------
        KeyError:
            Raised when there are ports in the non-EU imports/exports matrix
            missing from the port lookup file.
        """
        non_eu_imports_exports = self.read_csv(
            self.input_files["unitised_non_eu"],
            ["Imp0Exp1", "GBPortctr", "GBRawZone", "Traffic"],
            new_headers=["Imp0Exp1", "port_id", "zone_id", "trips"],
            numerical_columns=["trips"],
        )

        if (
            len(
                non_eu_imports_exports[
                    ~non_eu_imports_exports.port_id.isin(self.inputs["ports"].port_id)
                ]
            )
            > 0
        ):
            missing_from_lookup = non_eu_imports_exports[
                ~non_eu_imports_exports.port_id.isin(
                    self.inputs["ports"].port_id.unique()
                )
            ].port_id.unique()
            missing_str = ""
            for index, port in enumerate(missing_from_lookup):
                missing_str += f" {port}"
                if index != len(missing_from_lookup) - 1:
                    missing_str += ","
            msg = (
                f"Error with unitised non-EU imports and exports file:"
                f" port(s){missing_str} missing from ports lookup file."
            )
            raise KeyError(msg)
        non_eu_imports_exports = non_eu_imports_exports.merge(
            self.inputs["ports"].rename(columns={"zone_id": "port_zone_id"}),
            how="left",
            on="port_id",
        )
        imports_dict = {
            "port_zone_id": "origin",
            "zone_id": "destination",
        }
        exports_dict = {
            "port_zone_id": "destination",
            "zone_id": "origin",
        }
        unitised_non_eu_imports = non_eu_imports_exports.loc[
            non_eu_imports_exports["Imp0Exp1"] == 0
        ].rename(columns=imports_dict)
        unitised_non_eu_exports = non_eu_imports_exports.loc[
            non_eu_imports_exports["Imp0Exp1"] == 1
        ].rename(columns=exports_dict)
        self.inputs["unitised_non_eu_imports"] = ODMatrix(
            unitised_non_eu_imports[["origin", "destination", "trips"]],
            name="unitised_non_eu_imports",
            pivoted=False,
        )
        self.inputs["unitised_non_eu_exports"] = ODMatrix(
            unitised_non_eu_exports[["origin", "destination", "trips"]],
            name="unitised_non_eu_exports",
            pivoted=False,
        )
        self.hgv_keys += ["unitised_non_eu_imports", "unitised_non_eu_exports"]

    def _unitised_to_artic_rigid_trips(
        self, unitised_matrix, direction, commodity_type="unitised"
    ):
        """Separate a unitised import or export matrix into artic and rigid
        trips using port traffic rigid and artic proportions.

        Parameters
        ----------
        unitised_matrix : ODMatrix
            Unitised matrix.
        commodity_type : str
            Whether the input matrix is 'unitised' or 'bulk', by default
            'unitised'.
        direction : str
            Whether the input matrix is 'import' or 'export'.

        Returns
        -------
        artic_rigid_dict: dict
            Dictionary of two ODMatrix instances representing the artic and rigid
            proportion of the unitised matrix's trips respectively, with keys
            'artic' and 'rigid'.
        """
        factors = self.inputs["port_traffic_proportions"].loc[
            (self.inputs["port_traffic_proportions"].type == commodity_type)
            & (self.inputs["port_traffic_proportions"].direction == direction)
        ]
        artic_rigid_dict = {}
        keys = ["artic", "rigid"]
        for key in keys:
            artic_rigid_dict[key] = unitised_matrix * (factors[key].mean() / 1000)
            artic_rigid_dict[key].name = f"{key}_{unitised_matrix.name}"

        return artic_rigid_dict

    def _aggregate_unitised_trips(self):
        """Aggregates all the unitised HGV trips."""
        self.unitised_trips = {}
        imports = [
            self.inputs["unitised_eu_imports"],
            self.inputs["unitised_non_eu_imports"],
        ]
        exports = [
            self.inputs["unitised_eu_exports"],
            self.inputs["unitised_non_eu_exports"],
        ]
        for matrix in imports + exports:
            if matrix in imports:
                artic_rigid_dict = self._unitised_to_artic_rigid_trips(matrix, "import")
            else:
                artic_rigid_dict = self._unitised_to_artic_rigid_trips(matrix, "export")
            for key in self.KEYS:
                if key in self.unitised_trips.keys():
                    self.unitised_trips[key] += artic_rigid_dict[key]
                else:
                    self.unitised_trips[key] = artic_rigid_dict[key]
                    self.unitised_trips[key].name = f"{key}_unitised"

    def _update_port_distance_factors(self):
        """Updates the distance factors matrices for any zone pairs involving
        ports.
        """
        for key in self.distance_factors.keys():
            # get factor to apply
            factor = (
                self.inputs["port_traffic_proportions"]
                .loc[self.inputs["port_traffic_proportions"].type == "bulk", key]
                .mean()
            )
            # apply all-directions factor to O-D trips with port as origin
            self.distance_factors[key].loc[
                self.distance_factors[key].index.isin(self.inputs["ports"].zone_id), :
            ] = factor
            # apply all-directions factor to O-D trips with port as destination
            self.distance_factors[key].loc[
                :, self.distance_factors[key].columns.isin(self.inputs["ports"].zone_id)
            ] = factor

    def _calculate_distance_factors(self):
        """Creates a dictionary of rigid and artic ODMatrices of distance
        factors associated with each GBFM zone pair, used for converting the
        bulk port matrix to artic and rigid trips.
        """
        # Make sure the distance bands include all distances in the distance matrix
        if (
            self.inputs["gbfm_distance_matrix"].max()
            > self.inputs["distance_bands"].end.max()
        ):
            self.inputs["distance_bands"].loc[
                self.inputs["distance_bands"].end.argmax(), "end"
            ] = (self.inputs["gbfm_distance_matrix"].max() + 1)
        if (
            self.inputs["gbfm_distance_matrix"].min()
            < self.inputs["distance_bands"].start.min()
        ):
            self.inputs["distance_bands"].loc[
                self.inputs["distance_bands"].start.argmin(), "start"
            ] = 0

        # create dictionary of distance factor matrices
        self.distance_factors = {}
        for key in self.KEYS:
            self.distance_factors[key] = self.inputs[
                "gbfm_distance_matrix"
            ].matrix.copy()

        # update distance factor matrices according to the factors in
        # distance_bands
        for i in self.inputs["distance_bands"].index:
            to_factor = (
                self.inputs["distance_bands"].loc[i, "start"]
                < self.inputs["gbfm_distance_matrix"].matrix
            ) & (
                self.inputs["gbfm_distance_matrix"].matrix
                < self.inputs["distance_bands"].loc[i, "end"]
            )
            for key in self.distance_factors.keys():
                self.distance_factors[key][to_factor] = self.inputs[
                    "distance_bands"
                ].loc[i, key]

        # update factors for any zone-pairs involving ports
        self._update_port_distance_factors()

        # transform distance factor matrices into ODMatrix instances
        for key in self.distance_factors.keys():
            self.distance_factors[key] = ODMatrix(
                self.distance_factors[key], name=f"{key}_distance_factors"
            )

    def _bulk_tonnes_to_artic_rigid_trips(self):
        """Converts the domestic and bulk port matrix to artic and rigid
        trip matrices.
        """

        self._calculate_distance_factors()
        self.bulk_trips = {}
        for key in self.distance_factors.keys():
            self.bulk_trips[key] = (
                self.inputs["domestic_bulk_port"]
                * self.distance_factors[key]
                * (1 / 1000)
            )
            self.bulk_trips[key].name = f"{key}_domestic_bulk"

    def _calculate_total_trips(self):
        """Aggregates the unitised and bulk total trip matrices."""
        self.total_trips = {}
        for key in self.KEYS:
            self.total_trips[key] = self.bulk_trips[key] + self.unitised_trips[key]
            self.total_trips[key].name = f"{key}_total_annual_trips"

    def _create_pcu_factors(self):
        """Creates the PCU factors matrices required for converting artic and
        rigid trip matrices to PCU matrices.
        """
        # find default PCU factors
        default_pcu_factors = {}
        for key in self.KEYS:
            default_pcu_factors[key] = (
                self.inputs["pcu_factors"]
                .loc[self.inputs["pcu_factors"].zone == "default", key]
                .mean()
            )

        # if there are only default factors, then factor the artic and rigid trip
        # matrices by the default factors
        if (
            len(
                self.inputs["pcu_factors"].loc[
                    ~(self.inputs["pcu_factors"].zone == "default")
                ]
            )
            == 0
        ):
            self.pcu_factors = default_pcu_factors
        # if there are origin and destination specific factors, need to create a
        # factors matrix
        else:
            origins = (
                self.inputs["pcu_factors"]
                .loc[self.inputs["pcu_factors"].direction == "origin"]
                .set_index("zone")
            )
            destinations = (
                self.inputs["pcu_factors"]
                .loc[self.inputs["pcu_factors"].direction == "destination"]
                .set_index("zone")
            )
            self.pcu_factors = {}
            for key in self.KEYS:
                origin_data = np.array(
                    [origins[key]] * len(self.total_trips[key].matrix.columns)
                ).transpose()
                origin_df = pd.DataFrame(
                    data=origin_data,
                    index=origins.index,
                    columns=self.total_trips[key].matrix.columns,
                )
                origin_df.index.name = "origin"
                origin_df.index = origin_df.index.astype(int)
                origin_df.columns = origin_df.columns.astype(int)

                destination_data = np.array(
                    [destinations[key]] * len(self.total_trips[key].matrix.index)
                )
                destination_df = pd.DataFrame(
                    data=destination_data,
                    index=self.total_trips[key].matrix.index,
                    columns=destinations.index,
                )
                destination_df.columns.name = "destination"
                destination_df.index = destination_df.index.astype(int)
                destination_df.columns = destination_df.columns.astype(int)

                aligned_origins, aligned_destinations = origin_df.align(
                    destination_df, join="outer"
                )
                factors = (
                    ((aligned_origins + aligned_destinations) / 2)
                    .combine_first(aligned_origins)
                    .combine_first(aligned_destinations)
                )
                factors[factors.isnull()] = default_pcu_factors[key]
                factors = ODMatrix(factors, name=f"{key}_pcu_factors")

                self.pcu_factors[key] = factors

    def _trips_to_pcu_conversion(self):
        """Converts the artic and rigid total trip matrices to PCUs."""
        self._create_pcu_factors()
        self.total_pcus = {}
        for key in self.KEYS:
            self.total_pcus[key] = self.total_trips[key] * self.pcu_factors[key]
            self.total_pcus[key].name = f"{key}_total_annual_pcus"

    def run_conversion(self):
        """Runs the process which converts all the input HGV matrices to artic
        and rigid annual PCU matrices.
        """
        # aggregate unitised trips and split to artic and rigid
        self._aggregate_unitised_trips()

        # convert domestic and bulk port matrix to artic rigid trips
        self._bulk_tonnes_to_artic_rigid_trips()

        # aggregate trip matrices
        self._calculate_total_trips()

        # convert trips to PCUS
        self._trips_to_pcu_conversion()

    def hgv_input_summary(self):
        """Creates a summary of all input HGV matrices.

        Returns
        -------
        hgv_summary: dict
            Dictionary of ODMatrix summaries for the 4 HGV inputs.
        """
        hgv_summary = {}
        for key in self.hgv_keys:
            hgv_summary[key] = self.inputs[key].summary()
        return hgv_summary

    def total_trips_summary(self):
        """Creates a summary of the total artic and rigid trip matrices.

        Returns
        -------
        trip_summary: dict
            Dictionary of summaries of the artic and rigid trip ODMatrix
            instances.
        """
        try:
            self.total_trips.keys()
        except AttributeError:
            self.run_conversion()
        finally:
            trip_summary = {}
            for key in self.total_trips.keys():
                trip_summary[f"{key}_total_annual_trips"] = self.total_trips[
                    key
                ].summary()

            return trip_summary

    def pcu_output_summary(self):
        """Creates a summary of output artic and rigid PCU matrices.

        Returns
        -------
        pcu_summary: dict
            Dictionary of ODMatrix summaries for PCU outputs.
        """
        try:
            self.total_pcus.keys()
        except AttributeError:
            self.run_conversion()
        finally:
            pcu_summary = {}
            for key in self.total_pcus.keys():
                pcu_summary[f"{key}_total_annual_pcus"] = self.total_pcus[key].summary()

            return pcu_summary

    def summary_df(self):
        """Outputs summary of all OD Matrices involved in the conversion
        process, including the input HGVs, the total calculated O-D trip
        matrices and the final PCU outputs.

        Returns
        -------
        summary_df: pd.DataFrame
            DataFrame with summaries of each ODMatrix.
        """
        hgv_summary = self.hgv_input_summary()
        trip_summary = self.total_trips_summary()
        pcu_summary = self.pcu_output_summary()

        summary_df = pd.DataFrame.from_dict(
            {**hgv_summary, **trip_summary, **pcu_summary}, orient="index"
        )
        summary_df.index.name = "Matrix"
        return summary_df

    def save_pcu_outputs(self, output_folder):
        """Saves the PCU output matrices as csvs.

        Parameters
        ----------
        output_folder : Path
            Path to output folder
        """
        try:
            self.total_pcus.keys()
        except AttributeError:
            self.run_conversion()
        finally:
            for key in self.total_pcus.keys():
                self.total_pcus[key].export_to_csv(
                    output_folder / Path(f"{self.total_pcus[key].name}.csv")
                )

    @staticmethod
    def read_csv(path, columns, new_headers=None, numerical_columns=None):
        """Reads in a csv file and converts it to a Pandas DataFrame.

        Parameters
        ----------
        path : str
            Path to csv file
        columns : list of strings or ints
            Columns in the file to be read, indicated via their headers or indices
        new_headers : list of strings, optional
            New column names to use, by default None
        numerical_columns : list of strings, optional
            Headers of numerical columns, by default None. If new_headers is not
            None, the headers must be the new headers, not the csv headers.

        Returns
        -------
        df : pd.DataFrame
            DataFrame of the csv data.

        Raises
        ------
        FileNotFoundError
            If the input file path is incorrect
        KeyError
            If the input file does not have the correct number of columns
        Exception
            For any other issues with the file
        ValueError
            If not all values in numeric columns are numeric
        """
        path = Path(path)
        filename = path.stem
        try:
            whitespace, header_row = ODMatrix.check_file_header(path)
            df = pd.read_csv(
                path,
                delim_whitespace=whitespace,
                header=header_row,
                usecols=columns,
            )
        except FileNotFoundError as e:
            msg = f"Error: {filename} not found: {e}"
            raise FileNotFoundError(msg)
        except KeyError as e:
            msg = f"Error: problem with {filename}: {e}"
            raise KeyError(msg)
        except Exception as e:
            msg = f"Error: problem with {filename}: {e}"
            raise Exception(msg)
        if new_headers:
            if len(new_headers) != len(columns):
                msg = f"Error: new column names do not match number of columns in {filename}"
                raise KeyError(msg)
            else:
                new_names = {}
                for i in range(len(new_headers)):
                    new_names[columns[i]] = new_headers[i]
                df = df.rename(columns=new_names)
        if numerical_columns:
            try:
                df[numerical_columns].apply(
                    lambda s: pd.to_numeric(s, errors="raise").notnull().all()
                )
            except ValueError as e:
                msg = f"Error: Problem with {filename}: {e}"
                raise ValueError(msg)

        return df
