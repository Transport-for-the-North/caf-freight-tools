# -*- coding: utf-8 -*-
"""

Created on: Fri Feb 28 14:37:53 2020
Updated on: Wed Dec 23 15:42:52 2020

Original author: racs
Last update made by: cara

File purpose:
Tool used to convert annual GBFM O-D trip/PCU matrices to model time period
specific O-D trip/PCU matrices.

"""

# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from profile_ruc import main_converter_process
from utilities import Utilities, progress_window, info_window
import textwrap
from text_info import GBFM2ModelPCU_Text

# Other packages
import os
from time import gmtime, strftime

# Define a function to find a name for the log file
def available_log_name(path):
    log_name = path + '/tc.log'
    i = 0
    
    while os.path.isfile(log_name):
        i += 1
        log_name = path + '/tc%s.log' % str(i)
        
    return log_name
        
class GBFM2ModelPCU(QtWidgets.QWidget):
    
    def __init__(self,tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
        
    def initUI(self):
        self.setGeometry(500, 200, 500, 390)        
        self.setWindowTitle('GBFM Annual PCU to Model Time Period PCU')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))        
        
        labelO = QtWidgets.QLabel(self)
        labelO.setText('GBFM Annual PCU to Model Time Period PCU')
        labelO.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelO.setGeometry(10, 10, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info) 
        
        # Add file path selection fields
        self.gbfm_filepath =  Utilities.add_file_selection(self,  70, "Choose the GBFM output file(s):", multiple_files=True)
        self.zone_mapping =   Utilities.add_file_selection(self, 140, "Choose the zone correspondence file:")
        self.tp = Utilities.add_file_selection(self, 220, "Choose the time period selection file (made using profile builder):")
        
        # Folder path for the outputs
        self.path =   Utilities.add_file_selection( self, 300, 'Select the output directory:', directory=True)
        
        # Create a push button to move on to the time period selections
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('Next')
        next_button.setGeometry(390, 350, 100, 30)
        next_button.clicked.connect(self.next_button_clicked)
        
        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(10, 350, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)
        
        self.show()        
        
    def add_dropdown(self, y_position, label_txt, items):
        dropdown = QtWidgets.QComboBox(self)
        dropdown.setGeometry(10, y_position, 200, 30)
        dropdown.addItems(items)
        
        label = QtWidgets.QLabel(self)
        label.setText(label_txt)
        label.setGeometry(10, y_position - 30, 400, 30)
        
        return dropdown
    
    def next_button_clicked(self):
        if (self.gbfm_filepath.text() == '' or self.zone_mapping.text() == ''):
            alert = QtWidgets.QMessageBox(self)
            alert.setWindowTitle('Tier converter')
            alert.setText('Error: you must specify both file paths first')
            alert.show()
        else:
            self.selections_window = set_tp_selections(self)
            self.selections_window.show()
            self.hide()        
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()   
        
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('GBFM to Model PCU')   
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(GBFM2ModelPCU_Text).strip()          
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('GBFM Annual PCU to Model Time Period PCU Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)
        
# Second interface window for setting the vehicle types
class set_tp_selections(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.tp = self.tier_converter.tp.text()
        self.gbfm_filepath = self.tier_converter.gbfm_filepath.text().split(' % ')
        self.zone_mapping = self.tier_converter.zone_mapping.text()
        if self.tier_converter.path.text() == '': # this handles the case when a user doesn't set the output directory
            self.path = '.'
        else:
            self.path = self.tier_converter.path.text()
            
        self.initUI()
        
    def initUI(self):
        self.setGeometry(500, 200, 850, 10 + 40*(4+len(self.gbfm_filepath)))        
        self.setWindowTitle('GBFM Annual PCU to Model Time Period PCU')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))
        
        labelO = QtWidgets.QLabel(self)
        labelO.setText('GBFM Annual PCU to Model Time Period PCU')
        labelO.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelO.setGeometry(10, 10, 700, 30)
        
        label = QtWidgets.QLabel(self)
        label.setText('Select vehicle type and output file prefix for the following input files:')
        label.setGeometry(10, 50, 700, 30)
        y_position = 90
        self.add_column_header( 10, y_position, 'GBFM file:')
        self.add_column_header(430, y_position, 'Vehicle type:')
        self.add_column_header(640, y_position, 'Prefix:')
        
        self.veh_type = []
        self.prefixes = []
        for i, output in enumerate(self.gbfm_filepath):
            y_position = 40*(3+i)+10
            
            self.veh_type.append(QtWidgets.QComboBox(self))
            self.veh_type[i].setGeometry(430, y_position, 200, 30)
            self.veh_type[i].addItems(['LGV', 'Rigid', 'Articulated'])

            label = QtWidgets.QLabel(self)
            label.setText(output.split('/')[-1])
            label.setGeometry(10, y_position, 410, 30)
            
            self.prefixes.append(QtWidgets.QLineEdit(self))
            self.prefixes[i].setGeometry(640, y_position, 200, 30)
    
        # Create a push button to set off the tier converter process
        go_button = QtWidgets.QPushButton(self)
        go_button.setText('Run')
        go_button.setGeometry(430, 10 + 40*(3+len(self.gbfm_filepath)), 410, 30)
        go_button.clicked.connect(self.go_button_clicked)
        
        # Create a push button to move back to the set up window
        back_button = QtWidgets.QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(10, 10 + 40*(3+len(self.gbfm_filepath)), 410, 30)
        back_button.clicked.connect(self.back_button_clicked)
        
        self.show()
        
    def add_column_header(self, x_position, y_position, header_txt):
        label = QtWidgets.QLabel(self)
        label.setText(header_txt)
        label.setGeometry(x_position, y_position, 200, 30)
 
    def go_button_clicked(self):
        # Start a log file
        self.log_name = available_log_name(self.path)
        with open(self.log_name, 'a') as log_file:
            log_file.write('Tier converter\n')
            log_file.write('Run at %s\n\n' % strftime('%Y-%m-%d %H:%M:%S', gmtime()))
            log_file.write('GBFM file: %s\n' % self.gbfm_filepath)
            log_file.write('Zone correspondence: %s\n' % self.zone_mapping)
            log_file.write('Vehicle type selected: %s\n' % [x.currentText() for x in self.veh_type])

        # And a window showing the step the process is at
        self.progress = progress_window('Tier converter running...')
        self.hide()
       
        # Call the main tier converter process
        self.worker = background_thread(self)
        self.worker.start()
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()
        
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('GBFM to Model PCU')   
         self.progress_label = self.progress.label
         dedented_text = textwrap.dedent(GBFM2ModelPCU_Text).strip()          
         line = textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)      
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)
        
# Create a new thread which will run the main process
class background_thread(QThread):
    
    def __init__(self, set_tp_selections):
        QThread.__init__(self)
        self.tp = Utilities.read_tp(set_tp_selections.tp)
        self.veh_type = [x.currentText() for x in set_tp_selections.veh_type]
        self.gbfm_filepath = set_tp_selections.gbfm_filepath
        self.prefixes = set_tp_selections.prefixes
        self.zone_mapping = set_tp_selections.zone_mapping
        self.log_name = set_tp_selections.log_name
        self.message_box = set_tp_selections.progress.label
        self.path = set_tp_selections.path
        
    def run(self):
        main_converter_process(self.tp,
                               self.veh_type,
                               self.gbfm_filepath,
                               self.prefixes,
                               self.zone_mapping,
                               self.log_name,
                               self.message_box,
                               self.path)
