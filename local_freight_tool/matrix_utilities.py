"""

Created on: Monday Feb 15 2021

Original author: CaraLynch

File purpose:
Contains all matrix utility functions required for the tool, including 
producing a summary, rezoning a matrix, adding and factoring matrices, filling
missing zones, removing external-external trips, and converting to UFM.

"""

# TODO add convert to UFM - check MX.bat exists in SATURN EXES folder, add CSV_2_UFM_KEY, update_env() and csv_to_ufm
# TODO add rezoning

##### IMPORTS #####
# Standard imports
import os
import subprocess as sp
from pathlib import Path

# User-defined imports
from rezone import Rezone

# Third party imports
import pandas as pd

##### CLASS #####
class ODMatrix:
    """O-D matrix class for creating O-D matrix objects and performing
    operations with them.
    """

    def __init__(self, dataframe, name=None, pivoted=True):
        """Intialises an O-D matrix object from a pandas dataframe, creating
        both column and pivoted matrices.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataframe of O-D trips, with 3 columns 'origin', 'destination' and
            'trips' if pivoted is false, otherwise with origins as the row
            indices, destinations as the column name and trips as the values
            if pivoted is true.
        name: str, optional
            Name of matrix, default None
        pivoted : bool, optional
            Indicates whether the input dataframe is a column matrix or
            pivoted matrix, by default True
        """
        self.name = name
        if not pivoted:
            # create pivoted version of dataframe
            self.matrix = dataframe.pivot_table(
                index="origin", columns="destination", values="trips", fill_value=0
            )
        else:
            self.matrix = dataframe

    def __str__(self):
        """Sets the column version of the OD matrix as the string output.

        Returns
        -------
        str
            string representation of column matrix with columns 'origin',
            'destination' and 'trips,
        """
        return f"{self.name}\n{self.column_matrix()}"

    def __repr__(self):
        """Sets the pivoted matrix as the representation of the OD matrix.

        Returns
        -------
        str
            string representation of pivoted O-D matrix.
        """
        return f"{self.matrix}"

    def __add__(self, other_matrix):
        """Add two ODMatrix objects, element-wise. This first aligns the
        matrices then sums them.

        Parameters
        ----------
        self : ODMatrix.Object
            First matrix instance
        other_matrix : ODMatrix.Object
            Second matrix instance

        Returns
        -------
        ODMatrix.Object
            Sum of input matrices
        """
        print("Aligning matrices")
        matrix_1_aligned, matrix_2_aligned = self.align(self, other_matrix)
        print("Adding matrices")
        sum = matrix_1_aligned + matrix_2_aligned
        "Creating name"
        name = f"{self.name}_add_{other_matrix.name}"

        return ODMatrix(sum, name=name)

    def __sub__(self, other_matrix):
        """Subract a matrix from the current matrix instance, element-wise. This first aligns the
        matrices then subtracts.

        Parameters
        ----------
        self : ODMatrix.Object
            Matrix instance to subtract from
        other_matrix : ODMatrix.Object
            Matrix to subtract

        Returns
        -------
        ODMatrix.Object
            Matrix with other_matrix subtracted
        """
        matrix_1_aligned, matrix_2_aligned = self.align(self, other_matrix)
        subtracted = matrix_1_aligned - matrix_2_aligned
        name = f"{self.name}_sub_{other_matrix.name}"

        return ODMatrix(subtracted, name=name)

    def __mul__(self, factor):
        if (type(factor) == int) | (type(factor) == float):
            print("Factoring by scalar")
            factored = self.matrix * factor
            name = f"{self.name}_by_{factor}"
        elif type(factor) == ODMatrix:
            print("Aligning matrices")
            matrix_1_aligned, matrix_2_aligned = ODMatrix.align(self, factor)
            print("Factoring matrices")
            factored = matrix_1_aligned * matrix_2_aligned
            name = f"{self.name}_by_{factor.name}"
        else:
            raise TypeError(
                "Can only multiply an O-D matrix by a scalar or another O-D matrix"
            )

        return ODMatrix(factored, name=name)

    def summary(self):
        """Calculates total number of trips, the mean, standard deviation,
        number of 0 counts and number of NaNs in the ODMatrix. Returns a
        dictionary.

        Returns
        -------
        dict
            dictionary with 'Total', 'Mean', 'Standard deviation', '0 count'
            and 'NaN count' of the O-D trip matrix.
        """
        column_matrix = self.column_matrix()
        total = column_matrix.trips.sum()
        mean = column_matrix.trips.mean()
        standard_dev = column_matrix.trips.std()
        zero_count = (column_matrix.trips == 0).sum()
        null_counts = column_matrix.trips.isna().sum()
        summary = {
            "Total": total,
            "Mean": mean,
            "Standard deviation": standard_dev,
            "0 count": zero_count,
            "NaN count": null_counts,
        }

        return summary

    def column_matrix(self, include_zeros=True):
        """Transforms the matrix of the ODMatrix instance into a 3 column
        matrix, ideal for writing the output to a file.

        Returns
        -------
        pd.DataFrame
            3-column dataframe representing an O-D matrix with columns
            'origin', 'destination' and 'trips'.
        """
        column_matrix = (
            self.matrix.melt(value_name="trips", ignore_index=False)
            .reset_index()
            .sort_values(by="origin", ignore_index=True)
        )
        if not include_zeros:
            column_matrix = column_matrix[column_matrix.trips != 0]
        return column_matrix

    def fill_missing_zones(self, missing_zones):
        """Updates OD matrix to include missing zones. Missing zone values are
        set to 0.

        Parameters
        ----------
        missing_zones : list or pd.DataFrame
            list of missing zones or 1 column DataFrame of missing zones

        Returns
        -------
        ODMatrix
            Updated ODMatrix with missing zones included
        """
        # check if zones given as list or DataFrame
        if type(missing_zones) != list:
            try:
                missing_zones = list(missing_zones[0])
            except TypeError:
                raise TypeError("Missing zones are not a list or pandas dataframe")

        # check that the zones are missing, if there are any that appear in
        # the matrix, remove them from the missing zones list
        shared_zones = self.matrix.loc[self.matrix.index.isin(missing_zones)].index
        if len(shared_zones) > 0:
            missing_zones.remove(shared_zones)

        # add 0 value columns and rows to matrix
        columns_to_add = pd.DataFrame(0, index=self.matrix.index, columns=missing_zones)
        columns_to_add.columns.name = "destination"
        self.matrix = pd.concat([self.matrix, columns_to_add], axis=1, join="outer")
        rows_to_add = pd.DataFrame(0, index=missing_zones, columns=self.matrix.columns)
        rows_to_add.index.name = "origin"
        self.matrix = pd.concat([self.matrix, rows_to_add], axis=0, join="outer")

        return self

    def remove_external_trips(self, external_zones):
        """Updates the O-D matrix. Sets external-external trips to 0.

        Parameters
        ----------
        external_zones : list or pd.DataFrane
            List or 1 column DataFrame of external zones with header ext_zones

        Returns
        -------
        ODMatrix
            ODMatrix with the external-external trips set to 0.
        """
        # check if zones given as list or DataFrame
        if type(external_zones) != list:
            try:
                external_zones = list(external_zones.ext_zones)
            except TypeError:
                raise TypeError("External zones are not a list or a pandas dataframe.")

        # only set trips to 0 for zones that are already in the matrix
        shared_zones = self.matrix.loc[self.matrix.index.isin(external_zones)].index
        external_zones = list(shared_zones)
        print(f"Shared zones: {external_zones}")

        # set external-external trip values to 0
        self.matrix.loc[external_zones, external_zones] = 0

        return self

    def rezone(self, zone_correspondence_path):
        """Rezones O-D matrix using a zone correspondence lookup. Returns a
        new rezoned O-D matrix instance and saves it to a csv.

        Parameters
        ----------
        zone_correspondence_path : str
            Path to zone correspondence lookup csv. Must have 3 columns: the
            old zoning system zone IDs, the new zoning system zone IDs, and
            the splitting factor. The column names do not matter, but they
            must be in the specified order.
        outpath : str
            Path to output folder to save the rezoned csv into.

        Returns
        -------
        rezoned_od_matrix: ODMatrix
            Rezoned ODMatrix instance.
        """
        print("Rezone started")
        try:
            whitespace, header_row = ODMatrix.check_file_header(
                zone_correspondence_path
            )
            zone_correspondence = pd.read_csv(
                zone_correspondence_path,
                delim_whitespace=whitespace,
                header=header_row,
                names=["old", "new", "splitting_factor"],
                usecols=[0, 1, 2],
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Zone correspondence file not found at {zone_correspondence_path}."
            )
        except ValueError as e:
            loc = str(e).find("columns expected")
            raise ValueError(f"Zone correspondence file, {str(e)[loc:]}") from e

        column_matrix = self.column_matrix()
        rezoned_matrix = Rezone.rezoneOD(column_matrix, zone_correspondence)
        rezoned_od_matrix = ODMatrix(rezoned_matrix, name=self.name, pivoted=False)
        print("Rezone finished")
        return rezoned_od_matrix

    def export_to_csv(self, outpath, include_zeros=True, include_headers=True):
        """Export column matrix to csv file

        Parameters
        ----------
        filepath : str
            Path to save output file to
        include_zeros : bool, optional
            Whether to include zero-value trips, by default True
        """
        column_matrix = self.column_matrix(include_zeros=include_zeros)
        column_matrix.to_csv(outpath, header=include_headers, index=False)

    def export_to_ufm(self, saturn_exes_path, outpath):
        """Export ODMatrix as UFM using TBA22UFM.

        Parameters
        ----------
        saturn_exes_path: str
            Path to SATURN EXES folder.
        outpath:
            Path to folder to save UFM to.

        Returns
        -------
        out_mat: str
            Path to output file

        Raises
        ------
        FileNotFoundError
            If the UFM file isn't created correctly.
        """
        CSV_2_UFM_KEY = (
            "    1\n"
            "{csv_file}\n"
            "    2\n"
            "    7\n"
            "    1\n"
            "    14\n"
            "    1\n"
            "{ufm_file}\n"
            "{mat_nm}\n"
            "    0\n"
            "    0\n"
            "y"
        )

        def update_env(saturn_exes_path):
            """Creates a copy of environment variables and adds SATURN path.

            Parameters
            ----------
            saturn_exes_path : str
                Path to SATURN exes folder.

            Returns
            -------
            saturn_env:
                Updated environment variables.
            """
            new_env = os.environ.copy()
            sat_paths = fr"{saturn_exes_path};{saturn_exes_path}\BATS;"
            new_env["PATH"] = sat_paths + new_env["PATH"]
            return new_env

        # turn input strings into paths
        saturn_exes_path = Path(saturn_exes_path)
        outpath = Path(outpath)
        mx_bat_path = saturn_exes_path.joinpath("MX.BAT")

        if not mx_bat_path.exists():
            raise FileNotFoundError(f"{saturn_exes_path} does not contain MX.BAT")

        # export matrix as csv in TUBA2 format
        temp_filepath = outpath.joinpath("temp_matrix.csv")
        print(f"temp csv: {temp_filepath}")
        self.export_to_csv(temp_filepath, include_headers=False)

        # if the matrix has no name, assign a name
        if not self.name:
            self.name = f"{outpath.stem}_odmatrix"

        # write SATURN MX key file
        out_mat = outpath.joinpath(f"{self.name}.UFM")
        key_path = outpath.joinpath("MX_KEY.KEY")
        vdu_path = outpath.joinpath(f"{self.name}_VDU")

        with open(key_path, "wt") as f:
            f.write(
                CSV_2_UFM_KEY.format(
                    csv_file=temp_filepath.resolve(),
                    ufm_file=out_mat.resolve(),
                    mat_nm=self.name,
                )
            )

        # Run saturn batch file to convert to ufm
        sp.run(
            ["call", "MX", "I", "KEY", str(key_path), "VDU", str(vdu_path)],
            env=update_env(saturn_exes_path),
            check=True,
            shell=True,
            stdout=sp.DEVNULL,
        )

        # check created ufm exists and remove temp csv and key file
        if not out_mat.is_file():
            raise FileNotFoundError(f"{out_mat} was not created successfully")
        temp_filepath.unlink()
        key_path.unlink()
        mx_log_path = Path('MX.LOG')
        if mx_log_path.exists():
            mx_log_path.unlink()

        # move LPX file from wd to output directory
        if not outpath.joinpath("MX.LPX").exists():
            Path("MX.LPX").rename(str(outpath.joinpath("MX.LPX")))
        else:
            # if there's already an MX.LPX file in output directory, rename it
            i = 0
            while outpath.joinpath(f"MX_{i}.LPX").exists():
                i += 1
            Path("MX.LPX").rename(str(outpath.joinpath(f"MX_{i}.LPX")))

        return out_mat

    @classmethod
    def read_OD_file(cls, filepath):
        """Creates an O-D matrix instance from a csv file.

        Parameters
        ----------
        filepath : str
            Path to csv file with three columns: origin, destination and
            trips. The file can be comma or tab-separated, and does not
            require a header.

        Returns
        -------
        ODMatrix.Object
            Instance of the ODMatrix Class
        """
        whitespace, header_row = cls.check_file_header(filepath)
        matrix_dataframe = pd.read_csv(
            filepath,
            delim_whitespace=whitespace,
            header=header_row,
            names=["origin", "destination", "trips"],
            usecols=[0, 1, 2],
        )
        name = os.path.basename(os.path.splitext(filepath)[0])
        matrix = cls(matrix_dataframe, name, pivoted=False)
        return matrix

    @staticmethod
    def align(matrix_1, matrix_2):
        """Aligns the pivot dataframes of two ODMatrix instances via an outer
        join.

        Parameters
        ----------
        matrix_1 : ODMatrix.Object
            First matrix instance
        matrix_2 : ODMatrix.Object
            Second matrix instance

        Returns
        -------
        pd.DataFrame
            Aligned version of matrix_1's pivoted DataFrame
        pd.DataFrame
            Aligned version of matrix_2's pivoted DataFrame
        """
        return matrix_1.matrix.align(matrix_2.matrix, join="outer", fill_value=0)

    @staticmethod
    def check_file_header(filepath):
        # TODO add to utilities
        """Checks whether the O-D matrix input file is delimited by commas or
        tabs, and whether there is a header row or not.
        A header row is checked for based on whether the first element can be
        converted to an integer.

        Parameters
        ----------
        filepath : str
            Path to O-D matrix csv file.

        Returns
        -------
        whitespace : bool
            If true then the file is tab-delimited, if false it is
            comma-delimited
        header_row : int
            Indicates the index of the header row of the file, None if there
            is no header.
        """
        with open(filepath, "rt") as infile:
            line = infile.readline()

        # check whether comma or tab separated
        if len(line.split(",")) > 1:
            whitespace = False
            linesplit = line.split(",")
        else:
            whitespace = True
            linesplit = line.split("\t")

        # check whether there is a header row
        try:
            int(linesplit[0])
            header_row = None
        except:
            header_row = 0

        return whitespace, header_row
