# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 12:03:18 2020

@author: racs
"""


LGV_Processing_Text = '''
        2: LGV Processing 
        There are three separate functionalities within the LGV Processing Window:
        LGV Processing Tool:
        This tool will display the total size of both LGV freight and non-freight matrices selected for comparison.
        The user must input two files, one which contains an LGV Freight O-D trip matrix and one that contains an LGV non-freight O-D trip matrix, preferably in GBFM zoning. Both matrices must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all O-D zone pairs will be displayed on the screen for comparison.
        Apply Global Factors:
        This tool allows LGV freight and non-freight matrices to be factored by a single global factor. 
        The user must input two files one that contains an LGV freight O-D trip matrix and one that contains an LGV non-freight O-D trip matrix, preferably in GBFM zoning. Both matrices must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both the freight and non-freight matrices respectively in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'. These files can be found in the same folder is as the Tier Converter Python files. 
        Aggregation: 
        This tool will aggregate chosen LGV freight and non-freight matrices together to produce a single full LGV O-D trip matrix.
        The user must input two files, one which contains an LGV Freight O-D trip matrix and one that contains an LGV non-freight O-D trip matrix, preferably in GBFM zoning. Both matrices must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. This file is located in the same folder is as the Tier Converter Python files. 

        '''
        
Profile_Builder_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
        
Tier_Converter_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
        
Matrix_Processing_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
        
Model2GBFMPCU_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
        
GBFM2ModelPCU_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
        
        
AnnualTonne2PCU_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
                
Delta_Process_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''
        
        
ProduceGBFMCorrespondence_Text = '''
        2: LGV Processing               
        There are three functionalities within the LGV Processing Window:
        LGV Processing Tool: 
        This will display the total size of both LGV freight and Non-Freight matrices selected for comparison.
        The user must input two files, one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the total trips of both matrices summed across all zones will be displayed on the screen to allow for the comparison
        Apply Global Factors:\n
        This allows LGV freight and Non-Freight matrices to be factored by a single global factor. 
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’.
        The user must then enter the global factors to be applied for both  freight and non-freight matrices in number format, decimals are permitted. If only one of the two matrices need to be factored place a global factor of 1 in the box corresponding to the matrix that should remain the same. The user must then press run.
        Once run has been pressed, the factoring process is carried out and two output files are produced called; 'Output_LGV_Freight_Global_Factor_Applied.csv' and 'Output_LGV_Non_Freight_Global_Factor_Applied.csv'
        Aggregation: \n
        This will aggregate the LGV freight and Non-Freight matrices together to produce a single full LGV O-D matrix.
        The user must input two files one that contains the LGV Freight O-D trip Matrix and one that contains an LGV Non-Freight O-D Trip Matrix, preferably in GBFM zoning. Both matrices must contain three columns only with a header row that is usually of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press run.
        Once run has been pressed, the two O-D matrices selected are aggregated, this aggregated matrix is outputted to a file called 'Output_LGV_Aggregated_Matrix.csv'. The file is located in the same folder as the tier converter python files. 

        '''