# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 11:23:48 2020

@author: racs
"""

# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from utilities import Utilities, info_window
import textwrap
from text_info import AnnualTonne2PCU_Text

# Other packages
import sys
import os

#########################################################################

# Define a function to find a name for the log file
def available_log_name(path):
    log_name = path + '/tc.log'
    i = 0
    
    while os.path.isfile(log_name):
        i += 1
        log_name = path + '/tc%s.log' % str(i)
        
    return log_name

# Function which asks the user if they really want to trigger sys.exit()
    def closeEvent(self, event):
        Utilities.closeEvent(self, event)

#########################################################################
            

# Main interface window
class Conversion(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
    
        
    def initUI(self):
        self.setGeometry(500, 500, 500, 400)        
        self.setWindowTitle('Tier converter')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))        
        
        labelB = QtWidgets.QLabel(self)
        labelB.setText('Annual Tonne to Annual PCU Conversion')
        labelB.setFont(QtGui.QFont('Arial', 10, QtGui.QFont.Bold))
        labelB.setGeometry(10, 50, 700, 30)
                
        # Create a push button to move back to the menu
        back_button = QtWidgets.QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(390, 360, 100, 30)
        back_button.clicked.connect(self.back_button_clicked)
        
        # Create a push button to run the process
        run_button = QtWidgets.QPushButton(self)
        run_button.setText('Run')
        run_button.setGeometry(390, 360, 100, 30)
#        run_button.clicked.connect(self.run_button_clicked)
        
        self.show()
        
    @pyqtSlot()
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()  
                   
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Annual Tonne to PCU Conversion')   
         self.progress_label = self.progress.label
#         self.progress_label.setText('Information')
         dedented_text = textwrap.dedent(AnnualTonne2PCU_Text).strip()          
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)      
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)

# =============================================================================
# Main
            
app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion')
tc = Conversion()
sys.exit(app.exec_())

