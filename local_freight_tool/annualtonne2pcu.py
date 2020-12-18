# -*- coding: utf-8 -*-
"""
Created on Tue Mar  3 09:58:46 2020

@author: racs
"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from utilities import Utilities, info_window, progress_window
from text_info import AnnualTonne2PCU_Text

# Other packages
import textwrap
import pandas as pd

# Inputs
gbfm_nuts = pd.read_csv('Inputs/Rigid artic split/NTMv5_NUTS1.txt', sep='\t')[['UniqueID', 'NUTS1 code']]
region_dict = gbfm_nuts.set_index('UniqueID').to_dict()['NUTS1 code']

artic_proportions = pd.read_csv('Inputs/Rigid artic split/artic_proportions.csv')
    

class AnnualTonne2PCU(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
    
        
    def initUI(self):
        self.setGeometry(600, 600, 500, 400)        
        self.setWindowTitle('Annual Tonne to Annual PCU Conversion')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))        
        
        labelB = QtWidgets.QLabel(self)
        labelB.setText('Annual Tonne to Annual PCU Conversion')
        labelB.setFont(QtGui.QFont('Arial', 10, QtGui.QFont.Bold))
        labelB.setGeometry(10, 10, 700, 30)
        
        # Add file path selection fields
        self.hgv_pcus = Utilities.add_file_selection(self, 70, "Choose the GBFM HGV (PCUs) output file:")
        self.artic_out = Utilities.add_file_selection(self, 130, "Name the artic output file:")
        self.rigid_out = Utilities.add_file_selection(self, 190, "Name the rigid output file:")
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info) 
              
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
        
    @pyqtSlot()
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()    
        
    def run_button_clicked(self):
        if (self.hgv_pcus.text() == '' or self.artic_out.text() == '' or self.rigid_out.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('Annual Tonne to Annual PCU Conversion')
            alert.setText('Error: you must specify all files first')
            alert.show()
            
        else: 
            # Start a progress window
            self.progress = progress_window('Annual Tonne to Annual PCU Conversion')
            self.hide()
            
            # Call the main process
            self.worker = background_thread(self)
            self.worker.start() 

    def closeEvent(self, event):
        Utilities.closeEvent(self, event)
       
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Annual Tonne to Annual PCU') 
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(AnnualTonne2PCU_Text).strip()         
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Annual Tonne to Annual PCU Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)
    

# Main function
def rigid_artic_split(hgv_pcus, artic_out, rigid_out, message_box):
    
    # Step 1: read in the GBFM output:
    message_box.setText('Reading in the HGV file')
    hgv_pcus = Utilities.read_csv(hgv_pcus)
    hgv_pcus.columns = ['ORawZ', 'DRawZ', 'Traffic']
    
    # Step 2: determine the origin and destination regions:
    message_box.setText('Determining the relevant artic proportions')
    hgv_pcus['Origin region'] = hgv_pcus['ORawZ'].map(region_dict)
    hgv_pcus['Destination region'] = hgv_pcus['DRawZ'].map(region_dict)
    
    # Step 3: merge on the articulated proportions:
    hgv_pcus = hgv_pcus.merge(artic_proportions, on=['Origin region', 'Destination region'])
    hgv_pcus = hgv_pcus.drop(['Origin region', 'Destination region'], axis=1)
    
    # Step 4: create columns for the rigid and artic flows separately:
    hgv_pcus['ArticPCUs'] = hgv_pcus['Traffic'] * hgv_pcus['Artic proportion']
    hgv_pcus['RigidPCUs'] = hgv_pcus['Traffic'] - hgv_pcus['ArticPCUs']
    
    # Step 5: export the rigid and artic files:
    message_box.setText('Exporting the artic file')
    hgv_pcus[['ORawZ', 'DRawZ', 'ArticPCUs']].to_csv(artic_out, index=None)
    message_box.setText('Exporting the rigid file')
    hgv_pcus[['ORawZ', 'DRawZ', 'RigidPCUs']].to_csv(rigid_out, index=None)
    
    message_box.setText('Rigid/artic split is complete. You may exit the program.')

# Create a new thread which will run the main function
class background_thread(QThread):
    
    def __init__(self, AnnualTonne2PCU):
        QThread.__init__(self)
        self.hgv_pcus = AnnualTonne2PCU.hgv_pcus.text()
        self.artic_out = AnnualTonne2PCU.artic_out.text()
        self.rigid_out = AnnualTonne2PCU.rigid_out.text()
        self.message_box = AnnualTonne2PCU.progress.label
        
    def run(self):
        rigid_artic_split(self.hgv_pcus,
                          self.artic_out,
                          self.rigid_out,
                          self.message_box)
    