# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 09:32:01 2020

@author: racs
"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot

# User-defined imports
from profile_builder import Profile_Builder
from annualtonne2pcu import AnnualTonne2PCU
from matrixprocessing import MatrixProcessing
from gbfm2modelpcu import GBFM2ModelPCU
from lgvprocessing import LGVProcessing
from producegbfmcorrespondence import ProduceGBFMCorrespondence 
from model2gbfmpcu import Model2GBFMPCU
from deltaprocess import DeltaProcess 
from utilities import Utilities, info_window
from text_info import Tier_Converter_Text
from cost_conversion import WeightedRezone

# Other packages
import sys
import textwrap
#########################################################################

# Main interface window
class tier_converter(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()    
        
    def initUI(self):
        self.setGeometry(500, 400, 500, 490)        
        self.setWindowTitle('Tier converter')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))        

        labelA = QtWidgets.QLabel(self)
        labelA.setText('Tier Converter')
        labelA.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        labelA.setGeometry(10, 10, 700, 30) 
        
        labelB = QtWidgets.QLabel(self)
        labelB.setText('Pre-Processing')
        labelB.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelB.setGeometry(10, 50, 700, 30)
        
        # Create a push button for 'info'
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('Info')
        next_button.setGeometry(400, 10, 90, 30)
        next_button.clicked.connect(self.on_click_Info)
        
        #  Create a push button for Profile Builder
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('Profile Builder')
        next_button.setGeometry(400, 50, 90, 30)
        next_button.clicked.connect(self.on_click_Profile_Builder)
        
        # Create a push buttons for menu options
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('0: Produce GBFM Zone Correspondence')
        next_button.setGeometry(10, 90, 480, 30)     
        next_button.clicked.connect(self.on_click_ProduceGBFMCorrespondence)   

        next_button = QtWidgets.QPushButton(self)
        next_button.setText('1: Annual Tonne to Annual PCU Conversion')
        next_button.setGeometry(10, 130, 480, 30)     
        next_button.clicked.connect(self.on_click_AnnualTonne2PCU)   

        next_button = QtWidgets.QPushButton(self)
        next_button.setText('2: LGV Processing')
        next_button.setGeometry(10, 170, 480, 30)
        next_button.clicked.connect(self.on_click_LGVProcessing)   
        
        labelC = QtWidgets.QLabel(self)
        labelC.setText('Conversion')
        labelC.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelC.setGeometry(10, 210, 700, 30)
         
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('3: GBFM Annual PCU to Model Time Period PCU')
        next_button.setGeometry(10, 250, 480, 30)
        next_button.clicked.connect(self.on_click_GBFM2ModelPCU)      
                 
        labelD = QtWidgets.QLabel(self)
        labelD.setText('Utilities')
        labelD.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
        labelD.setGeometry(10, 290, 700, 30)
        
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('4: Matrix Rezoning Tool')
        next_button.setGeometry(10, 330, 480, 30)
        next_button.clicked.connect(self.on_click_Model2GBFMPCU)   
         
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('5: Matrix Factoring')
        next_button.setGeometry(10, 370, 480, 30)
        next_button.clicked.connect(self.on_click_MatrixProcessing)   

        next_button = QtWidgets.QPushButton(self)
        next_button.setText('6: Delta Process')
        next_button.setGeometry(10, 410, 480, 30)
        next_button.clicked.connect(self.on_click_DeltaProcess) 
        
        next_button = QtWidgets.QPushButton(self)
        next_button.setText('7: Cost Conversion')
        next_button.setGeometry(10, 450, 480, 30)
        next_button.clicked.connect(self.on_click_CostConversion) 
   
        self.show()
            
    @pyqtSlot()
    def on_click_Profile_Builder(self):
        self.selections_window = Profile_Builder(self)
        self.selections_window.show()

    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Tier Converter Information')    
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(Tier_Converter_Text).strip()         
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Tier Converter Information') 
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()
         
         def closeEvent(self, event):
            Utilities.closeEvent(self, event)             
             
    @pyqtSlot()
    def on_click_ProduceGBFMCorrespondence(self):
        self.selections_window = ProduceGBFMCorrespondence(self)
        self.selections_window.show()
        
    @pyqtSlot()
    def on_click_AnnualTonne2PCU(self):
        self.selections_window = AnnualTonne2PCU(self)
        self.selections_window.show()
        
    @pyqtSlot()
    def on_click_LGVProcessing(self):
        self.selections_window = LGVProcessing(self)
        self.selections_window.show()

    @pyqtSlot()
    def on_click_GBFM2ModelPCU(self):
        self.selections_window = GBFM2ModelPCU(self)
        self.selections_window.show()
        
    @pyqtSlot()
    def on_click_Model2GBFMPCU(self):
        self.selections_window = Model2GBFMPCU(self)
        self.selections_window.show()
        
    @pyqtSlot()
    def on_click_MatrixProcessing(self):
        self.selections_window = MatrixProcessing(self)
        self.selections_window.show()
        
    @pyqtSlot()
    def on_click_DeltaProcess(self):
        self.selections_window = DeltaProcess(self)
        self.selections_window.show() 
        
        
    @pyqtSlot()
    def on_click_CostConversion(self):
        self.selections_window = WeightedRezone(self)
        self.selections_window.show() 
        
    # Function which asks the user if they really want to trigger sys.exit()
    def closeEvent(self, event):
        Utilities.closeEvent(self, event)
        
# =============================================================================
# Main
            
app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion')
tc = tier_converter()
sys.exit(app.exec_())
