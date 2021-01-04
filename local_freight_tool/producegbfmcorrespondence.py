# -*- coding: utf-8 -*-
"""

Created on: Tue Mar  3 09:56:44 2020
Updated on: Wed Dec 23 15:31:50 2020

Original author: racs
Last update made by: cara

File purpose:
Produces zone_correspondence.csv which can be used within the GBFM Annual PCU
to Model Time Period PCU tool to convert the GBFM zoning system to a model
zoning system.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from utilities import  Utilities, info_window, progress_window
from text_info import ProduceGBFMCorrespondence_Text
import nest_functions as nf

# Other packages
import textwrap

class ProduceGBFMCorrespondence(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
    
        
    def initUI(self):
        self.setGeometry(600, 600, 500, 400)        
        self.setWindowTitle('Zone Correspondence Tool')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))
        
        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont('Arial', 10, QtGui.QFont.Bold))
        labelB.setText('Zone Correspondence Tool')
        labelB.setGeometry(10, 10, 700, 30)
        
        # Add file path selection fields
        self.first_zones_path = Utilities.add_file_selection(self, 70, "Select the first zone system shapefile:")
        self.second_zones_path = Utilities.add_file_selection(self, 130, "Select the second zone system shapefile:")
        
        # Folder path for the outputs
        self.path = Utilities.add_file_selection(self, 190, 'Select the output directory:', directory=True)   
        
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
        
    def run_button_clicked(self):
        if (self.first_zones_path.text() == '' or self.second_zones_path.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('Zone Correspondence Tool')
            alert.setText('Error: you must specify both shapefiles first')
            alert.show()
            
        else: 
            # Start a progress window
            self.progress = progress_window('Zone Correspondence Tool')
            self.hide()
            
            # Call the main process
            self.worker = background_thread(self)
            self.worker.start() 
  
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()    
        
    def closeEvent(self, event):
        Utilities.closeEvent(self, event)
                       
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Zone Correspondence Tool')   
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(ProduceGBFMCorrespondence_Text).strip()          
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Produce GBFM Zone Correspondence')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)

class background_thread(QThread):
    
    def __init__(self, ProduceGBFMCorrespondence):
        QThread.__init__(self)
        
        self.progress_label = ProduceGBFMCorrespondence.progress.label
        
        self.first_zones_path = ProduceGBFMCorrespondence.first_zones_path.text()
        self.second_zones_path = ProduceGBFMCorrespondence.second_zones_path.text()
        self.path = ProduceGBFMCorrespondence.path.text()
        
    def run(self):                       
        self.progress_label.setText('Applying the zone nesting process...')
        zone_correspondence = nf.ZoneNest(self.first_zones_path,
                                          self.second_zones_path,
                                          zoneName1 = 'gbfm', #NB HERE WE NEED TO LET THE USER CHANGE THESE PARAMETERS
                                          zoneName2 = 'noham',
                                          upperTolerance = .85,
                                          lowerTolerance = .10,
                                          zone1_index = 0, zone2_index = 0)
        
        self.progress_label.setText('Saving the correspondence file...')
        zone_correspondence.to_csv(self.path + '/zone_correspondence.csv', index=False)
                  
        self.progress_label.setText('Zone correspondence process complete. You may exit the program.')
