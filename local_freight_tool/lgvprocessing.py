# -*- coding: utf-8 -*-
"""

Created on: Tue Mar  3 09:52:36 2020
Updated on: Wed Dec 23 14:12:46 2020

Original author: racs
Last update made by: cara

File purpose:
GUI to enable user to access three separate functionalities. 
The LGV Processing Tool displays the total size of two selected O-D freight
matrices.
Applying Global Factors allows up to two O-D freight matrices to be multiplied
by a global factor.
Aggregation agggregates together two O-D freight matrices.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QLineEdit

# User-defined imports
from utilities import Utilities, info_window, progress_window
from text_info import LGV_Processing_Text

# Other packages
import os
import textwrap
import pandas as pd

class LGVProcessing(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter        
        self.initUI()    
        
    def initUI(self):
        self.setGeometry(500, 200, 500, 700)        
        self.setWindowTitle('LGV Processing')
        self.setWindowIcon(QtGui.QIcon('icon.png'))        
        
        labelD = QtWidgets.QLabel(self)
        labelD.setText('LGV Processing Tool')
        labelD.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelD.setGeometry(10, 10, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)       
                
        # Add file path selection fields
        self.gbfm_LGV_Freight = Utilities.add_file_selection( self, 70, "Choose the Freight Van GBFM output file:",directory=False)
        self.gbfm_LGV_Non_Freight = Utilities.add_file_selection(self, 140, "Choose the Non-Freight Van output file:",directory=False)        
        Total_Freight=0
        Total_Non_Freight=0
        
        self.labelA = QtWidgets.QLabel(self)
        self.labelA.setText('Freight Van Total Trips: ' + str(Total_Freight))
        self.labelA.setGeometry(10, 170, 700, 30) 
        self.labelA.hide()
        
        self.labelB = QtWidgets.QLabel(self)
        self.labelB.setText('Non-Freight Van Total Trips: ' + str(Total_Non_Freight))
        self.labelB.setGeometry(10, 200, 700, 30) 
        self.labelB.hide()
        
        self.labelC = QtWidgets.QLabel(self)
        self.labelC.setText('Apply Global Factors')
        self.labelC.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.labelC.setGeometry(10, 230, 700, 30) 
        self.labelC.show()       
           
        # Add file path selection fields
        self.gbfm_LGV_Freight_App = Utilities.add_file_selection( self, 290, "Choose the Freight Van GBFM output file:",directory=False)
        self.gbfm_LGV_Non_Freight_App = Utilities.add_file_selection(self, 360,  "Choose the Non-Freight Van output file:",directory=False)    
                
        # Create textboxes
        self.textbox_Freight = QLineEdit(self)
        self.textbox_Freight.move(260, 400)
        self.textbox_Freight.resize(120,30)        
        self.textbox_NonFreight = QLineEdit(self)
        self.textbox_NonFreight.move(260, 450)
        self.textbox_NonFreight.resize(120,30)       
        
        self.labelFr = QtWidgets.QLabel(self)
        self.labelFr.setText('Enter the Freight Global Factor to apply:')
        self.labelFr.setGeometry(10, 395, 700, 30) 
        self.labelFr.show()  
        
        self.labelNFr = QtWidgets.QLabel(self)
        self.labelNFr.setText('Enter the Non-Freight Global Factor to apply:')
        self.labelNFr.setGeometry(10, 450, 700, 30) 
        self.labelNFr.show()  
        
        self.labelD = QtWidgets.QLabel(self)
        self.labelD.setText('Aggregation')
        self.labelD.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        self.labelD.setGeometry(10, 420 + 70, 700, 30) 
        self.labelD.show()       
        
        # Add file path selection fields
        self.gbfm_LGV_Freight_Agg = Utilities.add_file_selection( self, 480 + 70, "Choose the Freight Van GBFM output file:",directory=False)
        self.gbfm_LGV_Non_Freight_Agg = Utilities.add_file_selection(self, 550 + 70, "Choose the Non-Freight Van output file:",directory=False)      
            
        run_button = QtWidgets.QPushButton(self)
        run_button.setText('Run')
        run_button.setGeometry(390, 180, 100, 30)
        run_button.clicked.connect(self.run_button_clicked)      
        
        run_button_App = QtWidgets.QPushButton(self)
        run_button_App.setText('Run')
        run_button_App.setGeometry(390, 450, 100, 30)
        run_button_App.clicked.connect(self.run_button_clicked_Apply_Global_Factors)     

        run_button_Agg = QtWidgets.QPushButton(self)
        run_button_Agg.setText('Run')
        run_button_Agg.setGeometry(390, 590 + 70, 100, 30)
        run_button_Agg.clicked.connect(self.run_button_clicked_Aggregation)      
        
        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(10, 590 + 70, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)
        
        self.show()        
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()

    def closeEvent(self, event):
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()    
                
    def run_button_clicked(self):
    
        if (self.gbfm_LGV_Freight.text() == '' or self.gbfm_LGV_Non_Freight.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('LGV Comparison')
            alert.setText('Error: you must specify both file paths first')
            alert.show()
        else:
            gbfm_LGV_Freight=self.gbfm_LGV_Freight.text()
            gbfm_LGV_Non_Freight=self.gbfm_LGV_Non_Freight.text()  
    
            df = Utilities.read_csv(gbfm_LGV_Freight) 
            df2 = Utilities.read_csv(gbfm_LGV_Non_Freight)             
            Total_Freight = df.iloc[ : , 2 ].sum()
            Total_Non_Freight = df2.iloc[ : , 2 ].sum()          
    
            self.labelA.setText('Freight Van Total Trips: ' + str(Total_Freight))
            self.labelB.setText('Non-Freight Van Total Trips: ' + str(Total_Non_Freight))
            
            self.labelA.show()
            self.labelB.show()
        
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('LGV Processing')   
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(LGV_Processing_Text)        
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('LGV Processing Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)

    def run_button_clicked_Apply_Global_Factors(self):
    
        if (self.gbfm_LGV_Freight_App.text() == '' or self.gbfm_LGV_Non_Freight_App.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('LGV Apply Global Factors')
            alert.setText('Error: you must specify both file paths first')
            alert.show()
        elif (self.textbox_Freight == '' or self.textbox_NonFreight== ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('LGV Apply Global Factors')
            alert.setText('Error: you must specify both factors first')
            alert.show()
        else:
            # Start a progress window
            self.progress = progress_window('Applying Global Factors Tool', self.tier_converter)
            self.hide()
            
            # Call the main process
            self.worker = background_thread(self)
            self.worker.start()             
            
    def run_button_clicked_Aggregation(self):
    
        if (self.gbfm_LGV_Freight_Agg.text() == '' or self.gbfm_LGV_Non_Freight_Agg.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('LGV Aggregation')
            alert.setText('Error: you must specify both file paths first')
            alert.show()
            
        else:
            # Start a progress window
            self.progress = progress_window('Applying Global Factors Tool', self.tier_converter)
            self.hide()
            
            # Call the main process
            self.worker = background_thread_Aggregation(self)
            self.worker.start()             
        
class background_thread(QThread):
    
    def __init__(self, LGVProcessing):
        QThread.__init__(self)
        
        self.progress_label = LGVProcessing.progress.label        
        self.gbfm_LGV_Freight=LGVProcessing.gbfm_LGV_Freight_App.text()
        self.gbfm_LGV_Non_Freight=LGVProcessing.gbfm_LGV_Non_Freight_App.text()  
        self.textbox_Freight=LGVProcessing.textbox_Freight.text() 
        self.textbox_NonFreight=LGVProcessing.textbox_NonFreight.text() 
        
    def run(self):                       
        self.progress_label.setText('Reading in the freight matrix...')         
        df = Utilities.read_csv(self.gbfm_LGV_Freight) 
        self.progress_label.setText('Reading in the non-freight matrix...') 
        df2 = Utilities.read_csv(self.gbfm_LGV_Non_Freight)    
        df.columns = ['origin', 'destination', 'Trips']
        df2.columns = ['origin', 'destination', 'Trips']
        self.progress_label.setText('Applying the global factors to the matrices...')              
        Freight = float(self.textbox_Freight)   
        Non_Freight = float(self.textbox_NonFreight)
        df["Trips"] = Freight * df["Trips"]                
        df2["Trips"] = Non_Freight * df2["Trips"]
        print(df)
        print(df2)
        dir = os.getcwd()
        self.progress_label.setText('Saving the factored matrices to file...') 
        df.to_csv(dir + '/Output_Freight_Global_Factor_Applied.csv', index=False)    
        df2.to_csv(dir + '/Output_Non_Freight_Global_Factor_Applied.csv', index=False)    
        self.progress_label.setText('Applying Global Factors process complete. You may exit the program.')          
                
         
    def closeEvent(self, event):
        close = Utilities.closeEvent(self, event)
   
class background_thread_Aggregation(QThread):
    
    def __init__(self, LGVProcessing):
        QThread.__init__(self)        
        self.progress_label = LGVProcessing.progress.label        
        self.gbfm_LGV_Freight=LGVProcessing.gbfm_LGV_Freight_Agg.text()
        self.gbfm_LGV_Non_Freight=LGVProcessing.gbfm_LGV_Non_Freight_Agg.text()  

    def run(self):  
        
        self.progress_label.setText('Reading in the freight matrix...')  
        df = Utilities.read_csv(self.gbfm_LGV_Freight) 
        self.progress_label.setText('Reading in the non-freight matrix...') 
        df2 = Utilities.read_csv(self.gbfm_LGV_Non_Freight)  
        dir = os.getcwd()
        df.columns = ['origin', 'destination', 'Trips']
        df2.columns = ['origin', 'destination', 'Trips']       
        self.progress_label.setText('Aggregating matrices...') 
        result = pd.concat([df,df2])
        print(result)
        df3 = result.groupby(['origin','destination'])['Trips'].sum()           
        print(df3)
        self.progress_label.setText('Saving the aggregated matrix to file...') 
        df3.reset_index().to_csv(dir + '/Output_Aggregated_Matrix.csv', index=False)                     
        self.progress_label.setText('Aggregation process complete. You may exit the program.')

    def closeEvent(self, event):
        Utilities.closeEvent(self, event)
        
   