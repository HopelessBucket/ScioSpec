#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
Startet das GUI – Timeseries, Spectra, Derived Value.
"""
from __future__ import annotations
import sys
import pathlib
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QRadioButton,
    QButtonGroup,
    QLineEdit,
    QLabel
)
from PySide6.QtCore import Slot
from additionalClasses import MeasurementWorker, UnitComboBox
from data_manager import load_measurement, EISData
from tabClasses import SettingsTab, SpectraTab, TimeseriesTab, DerivedTab
from ImpedanceAnalyser import ImpedanceAnalyser
from ImpedanceAnalyserFake import ImpedanceAnalyserFake

# ---------------------------------------------------------------------- #
#  Hauptfenster                                                          #
# ---------------------------------------------------------------------- #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EIS‑GUI (ISX‑3)")
        self.impedanceAnalyser = ImpedanceAnalyserFake("COM3")
        self.measWorker = None

        # Tabs
        self.tabs = QTabWidget()
        self.tabSettings = SettingsTab(self.impedanceAnalyser)
        self.tab_time = TimeseriesTab()
        self.tab_spec = SpectraTab()
        self.tab_derived = DerivedTab()
        self.tabs.addTab(self.tabSettings, "Settings")
        self.tabs.addTab(self.tab_time, "Timeseries")
        self.tabs.addTab(self.tab_spec, "Current Spectra")
        self.tabs.addTab(self.tab_derived, "Derived Value")

        # Buttons
        self.btn_load = QPushButton("Daten laden")
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
            self.measWorker.finished.connect(self.SetAllButtonsEnabled)
            self.measWorker.start()
        
        except Exception as e:  
            QMessageBox.critical(self, "Measurement error", "Measurement error in single measurement mode: " + str(e))

    @Slot()
    def RestartDevice(self):
        
        try:
            self.impedanceAnalyser.ResetSystem()
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
        self.tab_time.set_data(data)
        self.tab_spec.set_data(data)
        self.tab_derived.set_data(data)

# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1200, 800)
    win.show()
    sys.exit(app.exec())