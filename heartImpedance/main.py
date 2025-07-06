#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
Startet das GUI – Timeseries, Spectra, Derived Value.
"""
from __future__ import annotations
import sys, time
import pathlib, serial
from PySide6.QtWidgets import QApplication,QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QFileDialog, QMessageBox, QRadioButton, QButtonGroup,QLineEdit, QLabel, QDialog
from PySide6.QtCore import Slot
from AdditionalClasses import MeasurementWorker, UnitComboBox, RestartWorker, StartupPopup
from DataManager import load_measurement, EISData
from TabClasses import SettingsTab, BodeDiagramTab, TimeSeriesTab, DerivedValueTab
from ImpedanceAnalyser import ImpedanceAnalyser
from ImpedanceAnalyserFake import ImpedanceAnalyserFake

# ---------------------------------------------------------------------- #
#  Hauptfenster                                                          #
# ---------------------------------------------------------------------- #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        dialog = StartupPopup()
        self.setWindowTitle("EIS‑GUI (ISX‑3)")
        comPort = ""
        if dialog.exec() == QDialog.DialogCode.Accepted:
            comPort = dialog.getUserComPort()
        
        if comPort == "":
            self.impedanceAnalyser = ImpedanceAnalyserFake("COM5")
        else:
            try:
                self.impedanceAnalyser = ImpedanceAnalyser("COM5")
            except serial.SerialException as e:
                QMessageBox.critical(self, "Connection unsuccessful", f"The connection with port: {comPort} was unsuccessful. Error message: " + str(e))
            
        self.measWorker = None
        self.restartWorker = None

        # Tabs
        self.tabs = QTabWidget()
        self.tabSettings = SettingsTab(self.impedanceAnalyser)
        self.tabBode = BodeDiagramTab()
        self.tabTimeSeries = TimeSeriesTab()
        self.tabDerived = DerivedValueTab()
        self.tabs.addTab(self.tabSettings, "Settings")
        self.tabs.addTab(self.tabBode, "Bode")
        self.tabs.addTab(self.tabTimeSeries, "Time Series")
        self.tabs.addTab(self.tabDerived, "Derived value")

        # Buttons
        self.btn_load = QPushButton("Load data")
        self.btn_matlab = QPushButton("Run Single Measurement")
        self.buttonRestartDevice = QPushButton("Restart device")
        self.buttonRunLoopMeasurement = QPushButton("Run Multiple Measurements")
        self.btn_load.clicked.connect(self.load_data)
        self.btn_matlab.clicked.connect(self.RunSingleMeasurement)
        self.buttonRestartDevice.clicked.connect(self.RestartDevice)
        self.buttonRunLoopMeasurement.clicked.connect(self.RunMultipleMeasurements)
        
        # MeasurementParameters
        self.radioButtonGroup = QButtonGroup()
        self.repetitionMode = QRadioButton("Repetitions:")
        self.timeMode = QRadioButton("Time:")
        self.radioButtonGroup.addButton(self.repetitionMode)
        self.radioButtonGroup.addButton(self.timeMode)
        self.repetitionsLineEdit = QLineEdit(text="100")
        self.repetitionsLineEdit.setMaximumWidth(50)
        self.repetitionsLineEdit.setEnabled(False)
        self.timeLineEdit = QLineEdit(text="100")
        self.timeLineEdit.setMaximumWidth(50)
        self.timeLineEdit.setEnabled(False)
        self.timeUnitComboBox = UnitComboBox()
        self.timeUnitComboBox.setEnabled(False)
        self.intervalLineEdit = QLineEdit(text="1")
        self.intervalLineEdit.setMaximumWidth(50)
        self.intervalComboBox = UnitComboBox()
        self.repetitionMode.clicked.connect(self.repetitionModeClicked)
        self.timeMode.clicked.connect(self.timeModeClicked)
        
        
        hl = QHBoxLayout()
        hl.addWidget(self.btn_load)
        hl.addWidget(self.btn_matlab)
        hl.addWidget(self.buttonRunLoopMeasurement)
        hl.addWidget(self.repetitionMode)
        hl.addWidget(self.repetitionsLineEdit)
        hl.addWidget(self.timeMode)
        hl.addWidget(self.timeLineEdit)
        hl.addWidget(self.timeUnitComboBox)
        hl.addWidget(QLabel("Interval: "))
        hl.addWidget(self.intervalLineEdit)
        hl.addWidget(self.intervalComboBox)
        hl.addStretch()
        hl.addWidget(self.buttonRestartDevice)

        lay = QVBoxLayout(self)
        lay.addLayout(hl)
        lay.addWidget(self.tabs, stretch=1)

    # ------------------------------------------------------------------ #
    @Slot()
    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Messdatei öffnen", "", "Messdaten (*.mat *.spec)"
        )
        if not path:
            return
        try:
            data = load_measurement(pathlib.Path(path))
        except Exception as e:
            QMessageBox.critical(self, "Fehler beim Laden", str(e))
            return
        self._broadcast_data(data)

    @Slot()
    def RunSingleMeasurement(self):
        
        try:
            self.SetAllButtonsEnabled(False)
            self.measWorker = MeasurementWorker(self.impedanceAnalyser, False, 1, 0)
            self.measWorker.resultReady.connect(self._broadcast_data)
            self.measWorker.finished.connect(self.SetAllButtonsEnabled)
            self.measWorker.start()
        
        except Exception as e:  
            QMessageBox.critical(self, "Measurement error", "Measurement error in single measurement mode: " + str(e))

    @Slot()
    def RestartDevice(self):
        
        try:
            self.SetAllButtonsEnabled(False)
            self.restartWorker = RestartWorker(self.impedanceAnalyser)
            self.restartWorker.restartFinished.connect(self.SetAllButtonsEnabled)
            self.restartWorker.start()
        except Exception as e:
            QMessageBox.critical(self, "Restart failed", str(e))
    
    @Slot()
    def RunMultipleMeasurements(self):
        
        intervalMs = self.intervalComboBox.GetTimeInMs(int(self.intervalLineEdit.text()))
        
        if self.timeMode.isChecked():
            timeMode = True
            measVariable = self.timeUnitComboBox.GetTimeInMs(int(self.timeLineEdit.text()))
        
        elif self.repetitionMode.isChecked():
            timeMode = False
            measVariable = int(self.repetitionsLineEdit.text())
        
        else:
            QMessageBox.warning(self, "Measurement mode unknown", "Please choose either repetition mode or time mode for multiple measurements")
            return
        
        
        try:
            self.SetAllButtonsEnabled(False)
            self.measWorker = MeasurementWorker(self.impedanceAnalyser, timeMode, measVariable, intervalMs)
            self.measWorker.resultReady.connect(self._broadcast_data)
            self.measWorker.finished.connect(self.SetAllButtonsEnabled)
            self.measWorker.start()
        
        except Exception as e:  
            QMessageBox.critical(self, "Measurement error", "Measurement error in time mode: " + str(e))
    
    @Slot()
    def repetitionModeClicked(self):
        
        self.repetitionsLineEdit.setEnabled(True)
        self.timeLineEdit.setEnabled(False)
        self.timeUnitComboBox.setEnabled(False)
    
    @Slot()
    def timeModeClicked(self):
        
        self.repetitionsLineEdit.setEnabled(False)
        self.timeLineEdit.setEnabled(True)
        self.timeUnitComboBox.setEnabled(True)
    
    @Slot()
    def SetAllButtonsEnabled(self, setEnabled:bool):
        
        self.btn_load.setEnabled(setEnabled)
        self.btn_matlab.setEnabled(setEnabled)
        self.buttonRunLoopMeasurement.setEnabled(setEnabled)
        self.buttonRestartDevice.setEnabled(setEnabled)
        self.tabSettings.setEnabled(setEnabled)

    # ------------------------------------------------------------------ #
    def _broadcast_data(self, data: EISData):
        startTime = time.time()
        self.tabBode.update_data(data)
        self.tabTimeSeries.update_data(data)
        self.tabDerived.update_data(data)
        print(time.time() - startTime)

# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1200, 800)
    win.show()
    sys.exit(app.exec())