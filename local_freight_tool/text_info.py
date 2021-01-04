# -*- coding: utf-8 -*-
"""

Created on: Thu Mar  5 12:03:18 2020
Updated on: Wed Dec 23 14:12:46 2020

Original author: racs
Last update made by: cara

File purpose:
Contains information about each aspect of the tool for display with the GUI.

"""


LGV_Processing_Text = '''
        There are three separate functions within this tool. 
        
        LGV Processing Tool:
        This function displays the total size of two selected O-D freight matrices for comparison purposes. Can be used to compare the size of freight van and non-freight van matrices. 
        How to use
        •	The user must input two O-D freight matrix files, for instance, one which contains a freight van O-D trip matrix and the other which contains a non-freight O-D trip matrix, preferably in GBFM zoning. N.B. Both matrices must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press ‘Run’.
        Once ‘Run’ has been pressed, the total trips/PCUs of both matrices are summed across all O-D zone pairs and the totals are displayed on the screen for comparison.
        
        Apply Global Factors:
        This allows up to two O-D freight matrices to be multiplied by a global factor. Can be used to apply global factors to freight van and non-freight van O-D trip matrices. 
        How to use
        •	The user must input two O-D freight matrix files, for instance, one which contains a freight van O-D trip matrix and the other which contains a non-freight O-D trip matrix, preferably in GBFM zoning. N.B. Both matrices must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. 
        •	The user must then enter the global factors to be applied for both the freight and non-freight matrices respectively in number format, decimals are permitted. N.B. If only one matrix needs to be globally factored, select a second file and place a factor of 1 in the textbox corresponding to the matrix that should remain unchanged. The user must then press ‘Run’.
        
        Once ‘Run’ is pressed, a progress window will be displayed to update the user on the progress of the factoring process. Once complete, two files are outputted named; 'Output_Freight_Global_Factor_Applied.csv' and 'Output _Non_Freight_Global_Factor_Applied.csv'. These files can be found in the same folder is as the Tier Converter application.
        
        Aggregation: 
        This function will aggregate together two chosen freight O-D matrices, can be used to aggregate the chosen freight and non-freight matrices together to produce a single full LGV O-D trip matrix.
        How to use
        •	The user must input two O-D freight matrix files, for instance, one which contains a freight van O-D trip matrix and the other which contains a non-freight O-D trip matrix, preferably in GBFM zoning. N.B. Both matrices must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. The user must then press ‘Run’.
        Once ‘Run’ has been pressed, the two freight matrices selected are aggregated, and a progress window will be displayed to update the user on the progress of the aggregation process. Once complete, the aggregated matrix is outputted to a file called 'Output_ Aggregated_Matrix.csv'. This file is located in the same folder is as the Tier Converter application.  

        '''
        
Profile_Builder_Text = '''
        The Profile Builder tool is used to produce a file named ‘profile_selection.csv’ that contains all the information required to build time period specific O-D trip matrices. The user may define up to seven different time profiles. Information stored within the file includes the name of the profile, days used to create the profile, as well as the time periods hour start and hour end for each time profile defined. The output file may then be applied to an annual O-D trip matrix to produce time period specific O-D matrices using the tool named; ‘GBFM Annual PCU to Model Time Period PCU’.
        How to use
        •	The user is expected to enter a name for the time period selection such as: ‘AM’, ‘PM etc. The user must also select all the days that should be included within the time profile selection by checking the relevant checkboxes. 
        •	Finally, the user should use the drop down menus to select the hour start and hour end needed to produce the correct time profile. There are default values for each of these selections to demonstrate common choices which may be used without any change as long the name of the profile selection is provided. This process should then be repeated until of time period selections have been properly defined. 
        •	The user must then press ‘save selection’.
        Once ‘save selection’ has been pressed, the information selected is sent to a file named ‘profile_selection.csv’ which is located in the same folder is as the Tier Converter application. This file may then be used as an input within the tool ‘GBFM Annual PCU to Model Time Period PCU’.
        N.B. Once the profile builder has been instantiated and the profile selection file has been created, if changes are required to the time profiles selected, the user may choose to run the profile builder tool again or alternatively the user may decide to edit the ‘Profile_Selection.csv’ file directly but care must be taken to retain the correct format. 

        '''
        
Tier_Converter_Text = '''
        The menu of the Tier Converter application is separated into three main sections: Pre-Processing, Conversion, and Utilities. 
		The Pre-Processing section of the application includes tools that create zone correspondence files and manipulate matrix files 
		ready to be used as the input for later tools, for instance, within the ‘GBFM Annual PCU to Model Time Period PCU’ conversion 
		process. 
		Within the Conversion section of the menu there is one tool, which is the main process that converts annual GBFM PCU 
		matrices to model time period specific PCU matrices. 
		The Utilities section of the application contains tools which rezone, factor and forecast input matrices. 
		In addition, there is a button located on the top right of the menu labelled ‘Profile Builder’. 
		Importantly, the ‘Profile Builder’ tool allows the user to select the time profiles of interest for use within the other tools in the application, so it is suggested that this function is completed before other tools are used. 
		‘Info’ buttons are situated on many windows of the application to provide information on how to use the selected tool. 
        '''
        
Matrix_Processing_Text = '''
        The matrix factoring tool can be used to factor specific origin-destination trips within a larger freight O-D trip matrix. Different factors can be used to apply individual scaling to O-D trips.
        How to use
        •	The user must firstly enter an O-D trip matrix file to convert. N.B. All matrices chosen must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. 
        •	The user must then enter an O-D trip factor matrix file. N.B. This file must contain three columns only with a header row of the form; ‘origin’, ‘destination’ and ‘factor’.
        •	The user must then select the output directory to store the factored matrix file in, and press ‘Run’.
        Once ‘Run’ has been pressed, the factoring process is carried out and a progress window is displayed to update the user on the progress. Once factoring is complete, a window will display a completion message, prompting the user to exit the program. An output factor matrix is outputted to a file named ‘Output_Factored_Matrix.csv' in the file directory chosen by the user. 

        '''
        
Model2GBFMPCU_Text = '''
        The matrix rezoning tool can be used to convert a freight O-D trip matrix from one zoning system to another by applying a zone correspondence file. This tool should be implemented provided that an appropriate zone correspondence file already been produced for the flow.
        How to use
        •	The user must firstly enter an O-D trip matrix file to convert. N.B. All matrices chosen must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. 
        •	The user must also choose a zone correspondence file. N.B.  The file must contain three columns only with a header row that is usually of the form; ‘Zone1’, ‘Zone2’ and ‘Adjusted Factor’. For instance, for a rezone conversion from NoHam to GBFM, the correspondence file required would include the header columns ‘NoHam’, ‘GBFM’ and ‘Adjusted Factor’ respectively. 
        •	The user then must enter an output file name by selecting a directory and an appropriate file name.
        •	Then the user must press ‘Run’.
        Once ‘Run’ is pressed, the matrix rezoning process is carried out, and a progress window will be displayed throughout the process to update the user on the progress of the rezone. Once the rezoning is complete the rezoning matrix file is outputted in the directory chosen with the name provided. 

        '''
        
GBFM2ModelPCU_Text = '''
        The GBFM Annual PCU to Model Time Period PCU tool is used to convert annual GBFM O-D trip/PCU matrices to model time period specific O-D trip/PCU matrices. 
        N.B. This tool requires input files that are produced using other tools within the tier converter. A zone correspondence file is required which must be create either using the ‘Produce GBFM Zone Correspondence’ tool or produced externally. Moreover, a time period selection file is needed, which is produced using the ‘Profile Builder’ tool. Therefore, it is important to ensure that both the ‘Profile Builder’ and ‘Produce GBFM Zone Correspondence’ tools have been implemented, before attempting to use this tool. 
        How to use
        •	The user must choose at least one GBFM output O-D trip matrix file N.B. All matrices chosen must contain three columns only, with a header row that is of the form; ‘origin’, ‘destination’ and either ‘annual_pcus’ or ‘trips’. 
        •	The user must also choose a zone correspondence file. N.B.  The file must contain three columns only with a header row that is usually of the form; ‘Zone1’, ‘Zone2’ and ‘Adjusted Factor’. For instance, for a rezone conversion from NoHam to GBFM, the correspondence file required would include the header columns; ‘NoHam’, ‘GBFM’ and ‘Adjusted Factor’ respectively. 
        •	The user must then choose the time period selection file, which is likely named ‘profile_selection.csv’ that was created using the profile builder tool. 
        •	The user must also select the output directory for the file that is created from this process, then the user must press ‘Next’.
        •	Once, ‘Next’ is pressed, a new window will open, and the user must select the vehicle type and output file prefix for the input files that were chosen.
        •	Then the user must press ‘Run’.
        Once ‘Run’ is pressed, a progress window will be displayed throughout the process to update the user on the progress of the rezoning process and the annual to time period PCU conversion process. Once complete, the time period O-D PCU/trip matrix file is outputted in the directory chosen.  

        '''
                
AnnualTonne2PCU_Text = '''
        The Annual Tonne to Annual PCU Conversion tool takes a GBFM total HGV PCUs output (typically called Total_AtkZ_AtkZ_PCUs_GBZ.csv) and generates two separate files for the rigid and articulated PCUs separately. This uses the methodology set out in MDST’s Meta Model Training Data note, which sets proportions of HGV traffic that is articulated at the regional level.
        How to use
        •	The user should select the GBFM total HGV PCUs output file, followed by the names of the rigid and articulated output files. These will all be in the GBFM zoning system.
        •	Then the user must press ‘Run’.
        Once ‘Run’ is pressed a progress window will be displayed to update the user on the progress of generating the two output files.
        N.B. This tool should be used before passing HGV data to the GBFM Annual PCU to Model Time Period PCU tool.
        '''
                
Delta_Process_Text = '''
        This Delta Process tool can be used to implement the delta approach to produce a forecasted model O-D trip matrix. 
        How to use
        •	The user must select a base model time period O-D trip matrix file from the models output. 
        •	The user must then select a base time period O-D trip matrix file that was prepared from GBFM annual matrices and converted to the model zoning system and time period.  N.B. This file is likely to have been produced using the GBFM Annual PCU to Model Time Period PCU tool. 
        •	The user must then select a forecast time period O-D trip matrix that was prepared from GBFM annual matrices and converted to the model zoning system and time period which also undertook some factoring.  N.B. This file is likely to have been produced using the ‘Matrix Factoring’ or ‘Apply Global Factors’ tool.
        •	Then the user must press ‘Run’.
        
        Once ‘Run’ has been pressed, the delta approach process is undertaken and a forecasted O-D trip matrix in Model zoning system for the time period in question is outputted in a file which is located in the same folder is as the Tier Converter application named; ‘Forcasted_Model_O-D_Matrix.csv’
        General Warnings:
        The user must ensure that all three matrices chosen must use the same model zoning system. 
        The user must also ensure that the same time period selection is used throughout the O-D matrices as well.
        
        '''
        
ProduceGBFMCorrespondence_Text = '''
        This tool is used to produce a zone correspondence file that can be used within the tool; ‘GBFM Annual PCU to Model Time Period PCU’ to convert the GBFM zoning system to a model zoning system. This tool is a packaged and integrated version of scripts provided by TfN. 
        How to use
        •	The user should select the first zoning system shapefile, followed by the second zoning system shapefile and finally, the user should select the directory to store the output file in. 
        •	Then the user must press ‘Run’.
        Once ‘Run’ is pressed a progress window will be displayed to update the user on the progress of producing of the zone correspondence. Once complete, the zone correspondence file named; ‘zone_correspondence.csv’ is outputted, which is located in the same folder is as the Tier Converter application.
        N.B. This tool cannot be used in isolation necessarily to build a complete correspondence and it should be checked for completeness. 

        '''
        
Cost_Conversion_Text = '''
        The Cost Conversion tool uses a demand-based zone correspondence (such as that made with tool 0) to perform a demand-weighted conversion of costs in O/D format to the new zoning system.
        How to use
        •	The user must firstly enter an O-D cost matrix file to convert. N.B. All matrices chosen must contain three columns only, with a header row that is of the form ‘origin’, ‘destination’ and a cost attribute.
        •	For the weighting, the user must also enter an O-D trip matrix file. N.B. All matrices chosen must contain three columns only, with a header row that is of the form ‘origin’, ‘destination’ and ‘trips’.
        •	The user must additionally choose a zone correspondence file. N.B. The file must contain three columns only with a header row that is usually of the form; ‘Zone1’, ‘Zone2’ and ‘Adjusted Factor’. For instance, for a rezone conversion from NoHam to GBFM, the correspondence file required would include the header columns ‘NoHam’, ‘GBFM’ and ‘Adjusted Factor’ respectively. 
        •	Finally, the user must select a directory to save the output file.
        •	Then the user must press ‘Run’.
        Once ‘Run’ is pressed, the cost conversion process is carried out, and a progress window will be displayed throughout the process to update the user on the progress of reading in the inputs and rezoning. Once complete the cost file in the new zoning system is outputted in the directory chosen with the name ‘Output_Cost_Converted.csv’. 
        General Warnings:
        If a zone pair has non-zero cost but zero flow, it is excluded from the costs in the new zoning system.

        '''