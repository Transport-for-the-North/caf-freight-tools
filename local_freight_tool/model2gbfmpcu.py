# -*- coding: utf-8 -*-
"""

Created on: Tue Mar  3 10:00:42 2020
Updated on: Wed Dec 23 15:45:11 2020

Original author: racs
Last update made by: cara

File purpose:
Converts a freight O-D trip matric from one zoning system to another by
applying a zone correspondence file.

"""
# PyQt Imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QThread

# User-defined imports
from rezone import Rezone as rz
from utilities import Utilities, progress_window, info_window
from text_info import Model2GBFMPCU_Text

# Other imports
import textwrap

class Model2GBFMPCU(QtWidgets.QWidget):
    
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
       
    def initUI(self):
        self.setGeometry(600, 600, 500, 400)        
        self.setWindowTitle('Matrix Rezoning Tool')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))      
        
        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setText('Matrix Rezoning Tool')
        labelB.setGeometry(10, 10, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(400, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info) 
        
        # Add file path selection fields
        self.matrix = Utilities.add_file_selection(self, 70, "Choose a matrix to convert:", directory=False)
        self.correspondence = Utilities.add_file_selection(self, 130, "Choose the zone correspondence file:", directory=False)
        self.out_file = Utilities.add_file_selection(self, 190, "Choose an output file name:", directory=False)
        
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
        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()  

    def run_button_clicked(self):
        # Start a progress window
        self.progress = progress_window('Matrix Rezoning Tool')
        self.hide()
        
        # Call the main rezone process
        self.worker = background_thread(self)
        self.worker.start()    
              
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Matrix Rezoning Tool')   
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(Model2GBFMPCU_Text).strip()          
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Matrix Rezoning Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
             Utilities.closeEvent(self, event)
        
    # Function which asks the user if they really want to trigger sys.exit()
    def closeEvent(self, event):
        Utilities.closeEvent(self, event)

class background_thread(QThread):
    
    def __init__(self, Model2GBFMPCU):
        QThread.__init__(self)
        
        self.progress_label = Model2GBFMPCU.progress.label
        
        self.matrix = Utilities.read_csv(Model2GBFMPCU.matrix.text()) 
        self.matrix.columns = ['Origin', 'Destination', 'Trips']
        
        self.correspondence = Utilities.read_csv(Model2GBFMPCU.correspondence.text())
        self.correspondence.columns = ['Old', 'New', 'SplittingFactor']
        
        self.out_file = Model2GBFMPCU.out_file.text()
        
    def run(self):
        self.progress_label.setText('Reading in the file.')
        out_matrix = rz.rezoneOD(self.matrix, self.correspondence)
        self.progress_label.setText('Matrix rezone complete, saving to {}...'.format(self.out_file))
        out_matrix.to_csv(self.out_file, index=None)
        self.progress_label.setText('Matrix rezone complete and saved to {}. You may exit the program.'.format(self.out_file))
        
