"""

Created on: Monday Feb 15 2021

Original author: CaraLynch

File purpose:
Contains all matrix utility functions required for the tool, including 
producing a summary, rezoning a matrix, adding and factoring matrices, filling
missing zones, removing external-external trips, and converting to UFM.

"""

# User-defined imports
from os import stat
import zone_correspondence as zcorr

# Other packages
import geopandas as gpd
import pandas as pd

class ODMatrix:
    """O-D matrix class for creating O-D matrix objects and performing
    operations with them.
    """
    def __init__(self, dataframe, pivoted=True):
        """Intialises an O-D matrix object from a pandas dataframe, creating
        both column and pivoted matrices.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Dataframe of O-D trips, with 3 columns 'origin', 'destination' and
            'trips' if pivoted is false, otherwise with origins as the row
            indices, destinations as the column name and trips as the values
            if pivoted is true.
        pivoted : bool, optional
            Indicates whether the input dataframe is a column matrix or
            pivoted matrix, by default True
        """
        if not pivoted:
            self.matrix = dataframe
            self.make_pivot()
        else:
            self.pivoted_matrix = dataframe
            self.melt_pivot()
        
    def __str__(self):
        return f'{self.matrix}'       

    def make_pivot(self):
        """Updates self.pivoted_matrix so that it is the pivoted version of
        self.matrix such that the row indices are origins, column indices are
        destinations, and values are trips.

        Returns
        -------
        self
            The updated class instance
        """
        self.pivoted_matrix = self.matrix.pivot_table(index='origin', columns='destination', values='trips', fill_value=0)
        return self

    def melt_pivot(self):
        """Updates self.matrix from self.pivoted_matrix, where self.matrix
        has 'origin', 'destination' and 'trips' as columns.

        Returns
        -------
        self
            The updated class instance
        """
        self.matrix = self.pivoted_matrix.melt(value_name='trips', ignore_index=False).reset_index().sort_values(by='origin', ignore_index=True)
        return self

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
        matrix_dataframe = pd.read_csv(filepath, delim_whitespace=whitespace, header=header_row, names=['origin', 'destination', 'trips'], usecols=[0, 1, 2])
        matrix = cls(matrix_dataframe, pivoted=False)
        return matrix
    
    def scalar_factor(self, factor):
        """Apply a scalar factor to every element of a matrix.
        This does not update the matrix itself, but creates a new ODMatrix
        instance.

        Parameters
        ----------
        factor : float
            Factor to multiply each element of the matrix by.

        Returns
        -------
        ODMatrix.Object
            New factored instance of the ODMatrix Class
        """
        factored = self.pivoted_matrix * factor
        return self(factored)
    
    @classmethod
    def matrix_addition(cls, matrix_1, matrix_2):
        """Add two ODMatrix objects, element-wise. This first aligns the
        matrices then sums them.

        Parameters
        ----------
        matrix_1 : ODMatrix.Object
            First matrix instance
        matrix_2 : ODMatrix.Object
            Second matrix instance

        Returns
        -------
        ODMatrix.Object
            Sum of input matrices
        """
        matrix_1_aligned, matrix_2_aligned = cls.align(matrix_1, matrix_2)
        sum = matrix_1_aligned + matrix_2_aligned

        return cls(sum)
    
    @classmethod
    def matrix_factoring(cls, matrix_1, matrix_2):
        """Factor two matrices element-wise.

        Parameters
        ----------
        matrix_1 : ODMatrix.Object
            First matrix instance
        matrix_2 : ODMatrix.Object
            Second matrix instance

        Returns
        -------
        ODMatrix.Object
            Factored matrix instance
        """
        matrix_1_aligned, matrix_2_aligned = cls.align(matrix_1, matrix_2)
        factored = matrix_1_aligned*matrix_2_aligned

        return cls(factored)

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
        return matrix_1.pivoted_matrix.align(matrix_2.pivoted_matrix, join='outer', fill_value = 0)

    @staticmethod
    def check_file_header(filepath):
        """Checks whether the O-D matrix input file is delimited by commas or
        tabs, and whether there is a header row or not.

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
        with open(filepath, 'rt') as infile:
            line = infile.readline()
        
        # check whether comma or tab separated
        if len(line.split(',')) > 1:
            whitespace = False
            linesplit = line.split(',')
        else:
            whitespace = True
            linesplit = line.split('\t')
        
        # check whether there is a header row
        try:
            int(linesplit[0])
            header_row = None
        except:
            header_row = 0

        return whitespace, header_row


if __name__ == "__main__":
    od1path = 'C:/WSP_projects/Freight/matrix_utilities_files/od_matrices/od_matrix_1.csv'
    od2path = 'C:/WSP_projects/Freight/matrix_utilities_files/od_matrices/od_matrix_2.csv'
    odmatrix = ODMatrix.read_OD_file(odpath)
    print(odmatrix.matrix)
    print(odmatrix.pivoted_matrix)