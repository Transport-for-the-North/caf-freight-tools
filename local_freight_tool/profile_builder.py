# -*- coding: utf-8 -*-
"""

Created on: Fri Feb 28 12:25:27 2020
Updated on: Wed Dec 23 14:17:35 2020

Original author: racs
Last update made by: cara

File purpose:
Produces profile_selection.csv that contains all information required to build
time period specific O-D trip matrices.

"""
# PyQt imports
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QCheckBox
import numpy as np
import pandas as pd
from utilities import info_window
import textwrap
from text_info import Profile_Builder_Text


class Profile_Builder(QtWidgets.QWidget):
    def __init__(self, tier_converter):
        super().__init__()
        self.tier_converter = tier_converter
        self.initUI()
        
    def add_dropdown(self, y_position, label_txt, items):
        dropdown = QtWidgets.QComboBox(self)
        dropdown.setGeometry(10, y_position, 200, 30)
        dropdown.addItems(items)
        
        label = QtWidgets.QLabel(self)
        label.setText(label_txt)
        label.setGeometry(10, y_position - 30, 400, 30)
        
        return dropdown
        
    def initUI(self):
        self.setGeometry(300, 300, 870, 70+ 20*(10+14))        
        self.setWindowTitle('Profile Builder')
        self.setWindowIcon(QtGui.QIcon('icon.jpg'))
        
        labelB = QtWidgets.QLabel(self)
        labelB.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        labelB.setText('Profile Builder')
        labelB.setGeometry(10, 5, 700, 30)
        
        label = QtWidgets.QLabel(self)
        label.setText('Select options below to build time period specific profile, then press run. ')
        label.setGeometry(10, 25, 700, 30)
        
        # Create a push button for 'info'
        Info_button = QtWidgets.QPushButton(self)
        Info_button.setText('Info')
        Info_button.setGeometry(770, 10, 90, 30)
        Info_button.clicked.connect(self.on_click_Info)  
             
        self.add_column_header(10, 50, 'Name:')
        self.add_column_header(220, 50, 'Day:')
        self.add_column_header(450, 50, 'Hour start:')
        self.add_column_header(660, 50, 'Hour end:')
                
        # Now set up the user input fields
        self.names = []
        self.days = []
        self.hr_starts = []
        self.hr_ends = []
        
        for i in range(7):
            
            self.names.append(QtWidgets.QLineEdit(self))
            self.names[i].setGeometry(10, 80 + 60*i, 200, 30)  
            self.hr_starts.append(QtWidgets.QComboBox(self))
            self.hr_starts[i].setGeometry(450, 80 + 60*i, 200, 30)
            self.hr_starts[i].addItems([str(i) for i in range(24)])
            self.hr_ends.append(QtWidgets.QComboBox(self))
            self.hr_ends[i].setGeometry(660, 80 + 60*i, 200, 30)
            self.hr_ends[i].addItems([str(i) for i in range(24)])
            
            if i==0:
                self.names[i].setPlaceholderText('AM')
                self.hr_starts[i].setCurrentIndex(7)
                self.hr_ends[i].setCurrentIndex(10)
                
            if i==1:
                self.names[i].setPlaceholderText('PM')
                self.hr_starts[i].setCurrentIndex(16)
                self.hr_ends[i].setCurrentIndex(19)
            if i==2:
                self.names[i].setPlaceholderText('IP')
                self.hr_starts[i].setCurrentIndex(10)
                self.hr_ends[i].setCurrentIndex(16)
                
            if i==3:
                self.names[3].setPlaceholderText('OP')
                self.hr_starts[i].setCurrentIndex(19)
                self.hr_ends[i].setCurrentIndex(0)

        self.choices = [] 
        for i in range(7):   
            choice=[]
            for j, DayOfWeek in enumerate(['M','T','W','T','F','S','S']):
                
                day=QCheckBox(DayOfWeek,self)
                day.move(220+30*(j),75 + 60*i )
                day.resize(32, 40)
                if (j==0) or (j==1) or (j==2) or (j==3) or (j==4):
                    day.setChecked(True)                
                choice.append(day)                
            self.choices.append(choice)       

        # Create a push button to set off the tier converter process
        go_button = QtWidgets.QPushButton(self)
        go_button.setText('Save Selection')
        go_button.setGeometry(450, 20 + 20*(10+14), 410, 30)
        go_button.clicked.connect(self.go_button_clicked)
      
        # Create a push button to move back to the set up window
        back_button = QtWidgets.QPushButton(self)
        back_button.setText('Back')
        back_button.setGeometry(10, 20 + 20*(10+14), 430, 30)
        back_button.clicked.connect(self.back_button_clicked)
            
        self.show()
        
    def add_column_header(self, x_position, y_position, header_txt):
        label = QtWidgets.QLabel(self)
        label.setText(header_txt)
        label.setGeometry(x_position, y_position, 200, 30)        
        
    def go_button_clicked(self, state):
        self.FullMatrix = []
        for choice in self.choices:  
            RowMatrix=[]
            for day in choice:   
                if day.checkState() ==2:                    
                    day2 = 1
                else: 
                    day2 = 0       
                RowMatrix.append(day2)  
            self.FullMatrix.append(RowMatrix)           
        
        #    Process the FullMatrix to convert to days of the week
        self.NewFullMatrix = []
        for RowMatrix in self.FullMatrix:
            NewRowMatrix=[]
            for k in range(7):
                if RowMatrix[k]==1:
                    number = k
                else:
                    number = None
                if number != None:
                    NewRowMatrix.append(number)
                 
            self.NewFullMatrix.append(NewRowMatrix)    
        
        # Now let's generate the tp list of dictionaries
        self.tp = [] # initialise the list of lists
        
        for i in range(7):
            selection = {}
            selection['name'] = self.names[i].text()
            selection['days'] = self.NewFullMatrix[i]
            selection['hr_start'] = self.hr_starts[i].currentText()
            selection['hr_end'] = self.hr_ends[i].currentText()
            
            self.tp.append(selection)   

        df = pd.DataFrame(self.tp)   
        df['name'].replace('', np.nan, inplace=True)
        df.dropna().to_csv('Profile_Selection.csv', index=False, header=False)
        
        alert = QtWidgets.QMessageBox(self)
        alert.setWindowTitle('Profile Builder')
        alert.setGeometry(600,600,200,200)
        alert.setText('Building Selected Profiles Complete')
        alert.show()      
                        
    def back_button_clicked(self):
        self.tier_converter.show()
        self.hide()  
        
        # Function which asks the user if they really want to trigger sys.exit()
    def closeEvent(window, event):
        reply = QtWidgets.QMessageBox.question(window, 'Exit?',
            "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            
    @pyqtSlot()
    def on_click_Info(self):
         self.progress = info_window('Profile Builder Information')   
         self.progress_label = self.progress.label
         self.progress_labelA = self.progress.labelA
         dedented_text = textwrap.dedent(Profile_Builder_Text).strip()          
         line= textwrap.fill(dedented_text, width=140)
         self.progress_label.setText(line)     
         self.progress_label.move(10,40)
         self.progress_labelA.setText('Profile Builder Tool')  
         self.progress_labelA.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
         self.progress.show()