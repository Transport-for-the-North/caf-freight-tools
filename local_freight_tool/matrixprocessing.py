# -*- coding: utf-8 -*-
"""

Created on: Thu Feb 27 08:27:42 2020
Updated on: Wed Dec 23 15:46:56 2020

Original author: racs
Last update made by: cara

File purpose:
Factors specific O-D trips within a freight O-D trip matrix. Different factors
can be used to apply individual scaling to O-D trips.

"""

# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from utilities import Utilities, progress_window, info_window
from text_info import Matrix_Processing_Text

# Other packages
import textwrap
import numpy as np

class MatrixProcessing(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
    
    def initUI(self):
        self.setGeometry(500, 200, 500, 400)        
        self.setWindowTitle('Matrix Factoring')
        self.setWindowIcon(QtGui.QIcon('icon.png'))              
        
        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setText('Matrix Factoring Tool')
        labelB.setGeometry(10, 10, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info) 
                
        # Add file path selection fields
        self.ODMatrix_filepath =Utilities.add_file_selection(self, 70, "Select O-D Trip Matrix file:", directory=False)
        self.Factor_Filepath = Utilities.add_file_selection(self, 130, "Select an O-D Factor file:", directory=False)
        # Folder path for the outputs
        self.path = Utilities.add_file_selection(self, 190, 'Select the output directory:', directory=True)        
                
        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(10, 360, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)
        
        # Create a push button to run the process
        run_button = QtWidgets.QPushButton(self)
        run_button.setText('Run')
        run_button.setGeometry(390, 360, 100, 30)
        run_button.clicked.connect(self.run_button_clicked)
            
        self.show()        
     
    def run_button_clicked(self):
        if (self.ODMatrix_filepath.text() == '' or self.Factor_Filepath.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('Matrix Factoring')
            alert.setText('Error: you must specify both file paths first')
            alert.show()
            
        else: 
            # Start a progress window
            self.progress = progress_window('Matrix Factoring Tool', self.tier_converter)
            self.hide()
            
            # Call the main rezone process
            self.worker = background_thread(self)
            self.worker.start() 
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()    
        
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Matrix Processing')   
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(Matrix_Processing_Text).strip()         
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Matrix Processing Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
            Utilities.closeEvent(self, event)    
        
    def closeEvent(self, event):
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()
        
class background_thread(QThread):
    
    def __init__(self, MatrixProcessing):
        QThread.__init__(self)
        
        self.progress_label = MatrixProcessing.progress.label
        
        self.ODMatrix_filepath = MatrixProcessing.ODMatrix_filepath
        self.Factor_Filepath = MatrixProcessing.Factor_Filepath
        self.path = MatrixProcessing.path
        
    def run(self):                       
        ODMatrix_filepath = self.ODMatrix_filepath.text()
        Factor_Filepath = self.Factor_Filepath.text()  
        path = self.path.text()
        
        self.progress_label.setText('Reading in the matrix...')
        df = Utilities.read_csv(ODMatrix_filepath)
        df.columns = ['origin', 'destination', 'flow']        
        self.progress_label.setText('Reading in the factors...')
        df2 = Utilities.read_csv(Factor_Filepath)    
        df2.columns = ['origin', 'destination', 'Factor']   
        df4 = df # not sure we need to keep reassigning the name of this data frame ----------------------------------------
        df4 = df4.drop('flow', axis=1)
        df4['Factored annual_pcus'] ='Null'
        
        self.progress_label.setText('Factoring the matrix...')
        df.set_index(['origin', 'destination'], inplace=True) 
        df2.set_index(['origin', 'destination'], inplace=True) 
        joined = df.join(df2)
        joined.replace(np.nan,1, inplace=True)
        joined.columns = ['flow', 'Factor'] 
        joined['Factored annual_pcus']='Null'
        joined['Factored annual_pcus']= joined['flow'] * joined['Factor']
        joined =joined.drop(['flow','Factor'], axis=1)     
        self.progress_label.setText('Saving the factored matrix to {}'.format(path))
        joined.reset_index().to_csv(path + '/Output_Factored_Matrix.csv', index=False, header='Factored')
        self.progress_label.setText('Matrix factoring process complete. You may exit the program.')

                     
            
