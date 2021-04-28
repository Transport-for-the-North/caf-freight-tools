# -*- coding: utf-8 -*-
"""
Performs demand-weighted conversion of costs in O-D format to the new zoning
system, using a demand-based zone correspondence.
"""

# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from utilities import Utilities, progress_window
from info_window import InfoWindow
from rezone import Rezone as rz

# Other packages
import numpy as np


class WeightedRezone(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
    
    def initUI(self):
        self.setGeometry(500, 200, 500, 400)        
        self.setWindowTitle('Cost Conversion')
        self.setWindowIcon(QtGui.QIcon('icon.png'))              
        
        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setText('Cost Conversion Tool')
        labelB.setGeometry(10, 10, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info) 
                
        # Add file path selection fields
        self.cost = Utilities.add_file_selection(self, 70, "Select cost file:")
        self.demand = Utilities.add_file_selection(self, 130, "Select demand file:")
        self.correspondence = Utilities.add_file_selection(self, 190, "Select zone correspondence file:")
        
        # Folder path for the outputs
        self.path = Utilities.add_file_selection(self, 250, 'Select the output directory:', directory=True)        
                
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
        if (self.cost.text() == '' or self.demand.text() == '' or self.correspondence.text() == ''):        
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('Matrix Factoring')
            alert.setText('Error: you must specify all inputs first')
            alert.show()
            
        else: 
            # Start a progress window
            self.progress = progress_window('Cost Conversion Tool', self.tier_converter)
            self.hide()
            
            # Call the main rezone process
            self.worker = background_thread(self)
            self.worker.start() 
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()    
        
    @pyqtSlot()
    def on_click_Info(self):
        self.selections_window = InfoWindow(self, 'README.md')
        self.selections_window.show()
        
    def closeEvent(self, event):
        close = Utilities.closeEvent(self, event)
        if close:
            self.tier_converter.show()
        
class background_thread(QThread):
    
    def __init__(self, WeightedRezone):
        QThread.__init__(self)
        
        self.progress_label = WeightedRezone.progress.label
        
        self.cost = WeightedRezone.cost.text()
        self.demand = WeightedRezone.demand.text()
        self.correspondence = WeightedRezone.correspondence.text()
        
        self.path = WeightedRezone.path.text()
        
    def run(self):         
    
        # Read in the input files
        self.progress_label.setText('Reading in the cost matrix...')
        cost = Utilities.read_csv(self.cost)
        cost.columns = ['origin', 'destination', 'cost']
        
        self.progress_label.setText('Reading in the trips matrix...')
        demand = Utilities.read_csv(self.demand)
        demand.columns = ['origin', 'destination', 'trips']  
        
        self.progress_label.setText('Reading in the zone correspondence...')
        correspondence = Utilities.read_csv(self.correspondence)
        correspondence.columns = ['old', 'new', 'splitting_factor']

        # Merge the reference demand onto the cost (note inner merge drops cost rows where there is no demand)
        df = cost.merge(demand, how='inner', on=['origin', 'destination'])
        
        # Compute cost*trips
        df['costXtrips'] = df['cost'] * df['trips']
        
        # Apply the rezone process
        self.progress_label.setText('Applying the weighted rezone process...')
        df_trips = rz.rezoneOD(df[['origin', 'destination', 'trips']], correspondence)
        
        df_costXtrips = df[['origin', 'destination', 'costXtrips']]
        df_costXtrips.columns = ['origin', 'destination', 'trips'] #hacky fix to give rezoneOD the columns it's expecting
        df_costXtrips = rz.rezoneOD(df_costXtrips, correspondence)
        df_costXtrips.columns = ['origin', 'destination', 'costXtrips']
        
        # Merge back together
        df_final = df_costXtrips.merge(df_trips, on=['origin', 'destination'])
        
        # Compute weighted-average cost
        df_final['weighted_cost'] = np.where(df_final['trips']==0,
                0,
                df_final['costXtrips'] / df_final['trips']
                )
        
        # Cut back to the columns of interest and save to file
        self.progress_label.setText('Saving the rezoned cost matrix to {}'.format(self.path))
        df_final[['origin', 'destination', 'weighted_cost']].to_csv(self.path + '/Output_Cost_Converted.csv', index=None)
        self.progress_label.setText('Cost Conversion process complete. You may exit the program.')
        