# -*- coding: utf-8 -*-
"""

Created on: Tue Mar  3 10:03:21 2020
Updated on: Wed Dec 23 15:42:52 2020

Original author: racs
Last update made by: cara

File purpose:
Implements delta approach to produce forecasted model O-D trip matrix.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from utilities import Utilities, info_window, progress_window
from text_info import Delta_Process_Text

# Other packages
import os
import numpy as np
import pandas as pd
import textwrap

class DeltaProcess(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
    
        
    def initUI(self):
        self.setGeometry(500, 200, 500, 400)        
        self.setWindowTitle('Delta Process')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))        
        
        labelB = QtWidgets.QLabel(self)
        labelB.setText('Delta Process')
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setGeometry(10, 10, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info) 
        
        # Add file path selection fields
        self.base_Model = Utilities.add_file_selection(self, 70, "Choose a base O-D trip matrix file in model zoning system (from model):", directory=False)
        self.base_GBFM = Utilities.add_file_selection(self, 130, "Choose a base O-D trip matrix file in model zoning system (from GBFM):", directory=False)
        self.forcast_GBFM = Utilities.add_file_selection(self, 190, "Choose a forcast O-D trip matrix file in model zoning system (from GBFM):", directory=False)
        
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
        if (self.base_Model.text() == '' or self.base_GBFM.text() == '' or self.forcast_GBFM.text() == ''):     
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('Delta Process')
            alert.setText('Error: you must specify all file paths first')
            alert.show()   
        else:
            # Start a progress window
            self.progress = progress_window('Delta Process', self.tier_converter)
            self.hide()
            
            # Call the main rezone process
            self.worker = background_thread(self)
            self.worker.start() 
            
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()    
        
    def closeEvent(self, event):
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()
    
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Delta Process')  
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(Delta_Process_Text).strip()          
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Delta Process Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
            Utilities.closeEvent(self, event)
             
class background_thread(QThread):
    
    def __init__(self, DeltaProcess):
        QThread.__init__(self)
        
        self.progress_label = DeltaProcess.progress.label
        
        self.base_Model = DeltaProcess.base_Model
        self.base_GBFM = DeltaProcess.base_GBFM 
        self.forcast_GBFM = DeltaProcess.forcast_GBFM
        
    def run(self):                       
        base_Model = self.base_Model.text()
        base_GBFM = self.base_GBFM.text()  
        forcast_GBFM = self.forcast_GBFM.text()
        
        self.progress_label.setText('Reading in the base model matrix (From model)...')
        df = Utilities.read_csv(base_Model)
        df.columns = ['origin', 'destination', 'flow']        
        self.progress_label.setText('Reading in the base model matrix (From GBFM)...')
        df2 = Utilities.read_csv(base_GBFM)    
        df2.columns = ['origin', 'destination', 'flow']   
        self.progress_label.setText('Reading in the forcast model matrix (From GBFM)...')
        df3 = Utilities.read_csv(forcast_GBFM)            
        df3.columns = ['origin', 'destination', 'flow']   
        self.progress_label.setText('Processing...')
        df2.loc[:,'flow'] *= -1                
        result = pd.concat([df,df2,df3])
        print(result)
        df4= result.groupby(['origin','destination'])['flow'].sum()
        df4=df4.reset_index()
        df4['flow']=np.where(df4['flow']<0,0,df4['flow'])
        print(df4)
        
        # processing ----------------------------------------        
        cwd = os.getcwd()
        self.progress_label.setText('Saving the output matrix to location')
        df4.to_csv(cwd+ '/Forecasted_Model_O-D_Matrix.csv', index=False)                 
        self.progress_label.setText('Delta Processing Tool is complete. You may exit the program.')    
