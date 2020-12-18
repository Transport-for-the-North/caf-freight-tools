# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 09:07:28 2020

@author: hill1908
"""

# PyQt imports
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread

# User-defined imports
from time import gmtime, strftime
from profile_rzLast import profiles, day_selection, append_factors, main_converter_process

# Other packages
import sys
import os

#########################################################################

# Define a function to find a name for the log file
def available_log_name():
    log_name = 'tc.log'
    i = 0
    
    while os.path.isfile(log_name):
        i += 1
        log_name = 'tc%s.log' % str(i)
        
    return log_name

# Function which asks the user if they really want to trigger sys.exit()
def closeEvent(window, event):
        reply = QMessageBox.question(window, 'Exit?',
            "Are you sure to quit?", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

#########################################################################
            
# Create a new thread which will run the main process
class background_thread(QThread):
    
    def __init__(self, tp, veh_type, road_type, gbfm_filepath, zone_mapping, log_name, message_box):
        QThread.__init__(self)
        self.tp = tp
        self.veh_type = veh_type
        self.road_type = road_type
        self.gbfm_filepath = gbfm_filepath
        self.zone_mapping = zone_mapping
        self.log_name = log_name
        self.message_box = message_box
        
    def run(self):
        main_converter_process(self.tp,
                               self.veh_type,
                               self.road_type,
                               self.gbfm_filepath,
                               self.zone_mapping,
                               self.log_name,
                               self.message_box)
        
# Window to inform the user what stage the process is at (third interface window)
class progress_window(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setGeometry(400, 400, 850, 100)
        self.setWindowTitle('Tier converter running...')
        self.setWindowIcon(QIcon('icon.jpg'))
        self.label = QLabel(self)
        self.label.setGeometry(10, 10, 830, 30)
        self.label.setText('Rezoning the GBFM output')
        self.show()
        
    def closeEvent(self, event):
        closeEvent(self, event)

# First interface window
class tier_converter(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setGeometry(400, 400, 500, 500)        
        self.setWindowTitle('Tier converter')
        self.setWindowIcon(QIcon('icon.jpg'))
        
        # Add file path selection fields
        self.gbfm_filepath = self.add_file_selection(280, "Choose the GBFM output file:")
        self.zone_mapping = self.add_file_selection(380, "Choose the zone correspondence file:")
        
        # Dropdown menu for selecting the vehicle type
        self.veh_type = self.add_dropdown(40, 'Select the vehicle type:',
                                          ['LGV', 'Rigid', 'Articulated'])
        
        # Dropdown menu for selecting the road type
        self.road_type = self.add_dropdown(110, 'Select the road type:',
                                          ['Motorway', 'A road', 'Rural A', 'Urban A'])
        
        # Create an integer box for the user to set the number of time period selections
        self.qty_selections = self.add_dropdown(180, 'Set the number of time period selections:',
                                          [str(i) for i in range(1,11)])
        
        # Create a push button to move on to the time period selections
        next_button = QPushButton(self)
        next_button.setText('Next')
        next_button.setGeometry(10, 460, 480, 30)
        next_button.clicked.connect(self.next_button_clicked)
        
        self.show()
        
    def add_file_selection(self, y_position, label_txt):
        def browse_file():
            selected_file, _ = QFileDialog(self).getOpenFileName(self, label_txt)
            file_path.setText(selected_file)
        
        # Box which will contain the file selection
        file_path = QLineEdit(self)
        file_path.setGeometry(10, y_position, 235, 30)
        
        # Button to browse for the file
        browse_button = QPushButton(self)
        browse_button.setText('Browse')
        browse_button.setGeometry(255, y_position, 235, 30)
        browse_button.clicked.connect(browse_file)
        
        # Label with instructions
        label = QLabel(self)
        label.setText(label_txt)
        label.setGeometry(10, y_position - 30, 400, 30)
        
        return file_path
        
    def add_dropdown(self, y_position, label_txt, items):
        dropdown = QComboBox(self)
        dropdown.setGeometry(10, y_position, 200, 30)
        dropdown.addItems(items)
        
        label = QLabel(self)
        label.setText(label_txt)
        label.setGeometry(10, y_position - 30, 400, 30)
        
        return dropdown
            
    def next_button_clicked(self):
        if (self.gbfm_filepath.text() == '' or self.zone_mapping.text() == ''):
            alert = QMessageBox(self)
            alert.setWindowTitle('Tier converter')
            alert.setText('Error: you must specify both file paths first')
            alert.show()
        else:
            self.selections_window = set_tp_selections(self)
            self.selections_window.show()
            self.hide()
        
    def closeEvent(self, event):
        closeEvent(self, event)
        
# Second interface window for setting the time period selections
class set_tp_selections(QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.qty = int(self.tier_converter.qty_selections.currentText())
        self.gbfm_filepath = self.tier_converter.gbfm_filepath.text()
        self.zone_mapping = self.tier_converter.zone_mapping.text()
        self.veh_type = self.tier_converter.veh_type.currentText()
        self.road_type = self.tier_converter.road_type.currentText()
        
        self.initUI()
        
    def initUI(self):
        self.setGeometry(400, 400, 850, 10 + 40*(self.qty+2))        
        self.setWindowTitle('Tier converter')
        self.setWindowIcon(QIcon('icon.jpg'))
        
        self.add_column_header( 10, 'Name:')
        self.add_column_header(220, 'Day:')
        self.add_column_header(430, 'Hour start:')
        self.add_column_header(640, 'Hour end:')
        
        # Now set up the user input fields
        self.names= []
        self.days = []
        self.hr_starts = []
        self.hr_ends = []
        
        for i in range(self.qty):
            
            self.names.append(QLineEdit(self))
            self.names[i].setGeometry(10, 50 + 40*i, 200, 30)
            
            self.days.append(QComboBox(self))
            self.days[i].setGeometry(220, 50 + 40*i, 200, 30)
            self.days[i].addItems(['Average Weekday',
                               'Average Day',
                               'Saturday',
                               'Sunday',
                               'Monday',
                               'Tuesday',
                               'Wednesday',
                               'Thursday',
                               'Friday'])
    
            self.hr_starts.append(QComboBox(self))
            self.hr_starts[i].setGeometry(430, 50 + 40*i, 200, 30)
            self.hr_starts[i].addItems([str(i) for i in range(24)])
            
            self.hr_ends.append(QComboBox(self))
            self.hr_ends[i].setGeometry(640, 50 + 40*i, 200, 30)
            self.hr_ends[i].addItems([str(i) for i in range(24)])
    
        # Create a push button to set off the tier converter process
        go_button = QPushButton(self)
        go_button.setText('Go!')
        go_button.setGeometry(430, 40*(self.qty+1)+10, 410, 30)
        go_button.clicked.connect(self.go_button_clicked)
        
        # Create a push button to move back to the set up window
        back_button = QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(10, 40*(self.qty+1)+10, 410, 30)
        back_button.clicked.connect(self.back_button_clicked)
        
        self.show()
        
    def add_column_header(self, x_position, header_txt):
        label = QLabel(self)
        label.setText(header_txt)
        label.setGeometry(x_position, 10, 200, 30)
 
    def go_button_clicked(self): # put this in the init method of an entirely new class? ----------------------------------------------------
        # Return an error if the user doesn't specify the output file names
        if '' in [name.text() for name in self.names]:
            alert = QMessageBox(self)
            alert.setWindowTitle('Tier converter')
            alert.setText('Error: you must specify all names')
            alert.show()
        
        else:
            # Start a log file
            log_name = available_log_name()
            with open(log_name, 'a') as log_file:
                log_file.write('Tier converter\n')
                log_file.write('Run at %s\n\n' % strftime('%Y-%m-%d %H:%M:%S', gmtime()))
                log_file.write('GBFM file: %s\n' % self.gbfm_filepath)
                log_file.write('Zone correspondence: %s\n' % self.zone_mapping)
                log_file.write('Vehicle type selected: %s\n' % self.veh_type)
                log_file.write('Road type selected: %s\n\n' % self.road_type)
            
            # And a window showing the step the process is at
            self.progress = progress_window()
            self.hide()
    
            # Now let's generate the tp list of lists
            tp = [] # initialise the list of lists
            
            for i in range(self.qty):
                selection = []
                selection.append(self.names[i].text())
                selection.append(self.days[i].currentText())
                selection.append(self.hr_starts[i].currentText())
                selection.append(self.hr_ends[i].currentText())
                
                tp.append(selection)
            
            # Call the main tier converter process
            self.worker = background_thread(tp, self.veh_type, self.road_type, self.gbfm_filepath, self.zone_mapping, log_name, self.progress.label)
            self.worker.start()
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()
        
    def closeEvent(self, event):
        closeEvent(self, event)

# =============================================================================
# Main
            
app = QApplication(sys.argv)
app.setStyle('Fusion')
tc = tier_converter()
sys.exit(app.exec_())

"""

Next steps:
    1) note that at the moment the file exports are just to the working directory
    2) error checking could be improved

"""