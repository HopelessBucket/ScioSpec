#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
Startet das GUI – Timeseries, Spectra, Derived Value.
"""
from __future__ import annotations
import sys
import pathlib
import numpy as np
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Slot
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
        btn_load = QPushButton("Daten laden")
        btn_matlab = QPushButton("Run Single Measurement")
        buttonRestartDevice = QPushButton("Restart device")
        btn_load.clicked.connect(self.load_data)
        btn_matlab.clicked.connect(self.run_measurement)
        buttonRestartDevice.clicked.connect(self.restartDevice)

        hl = QHBoxLayout()
        hl.addWidget(btn_load)
        hl.addWidget(btn_matlab)
        hl.addStretch()
        hl.addWidget(buttonRestartDevice)

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
    def run_measurement(self):
        
        try:
            frequencies = self.impedanceAnalyser.GetFrequencyList()
            electrodes = self.impedanceAnalyser.GetExtensionPortChannel()
            resReal, resImag, resWarn, resRange, resTime, startTime, finishTime = self.impedanceAnalyser.GetMeasurements()  # Simulation als Default
            data = EISData(time = resTime, frequency = frequencies, electrodes = electrodes, realPart = resReal, imagPart = resImag)
            self._broadcast_data(data)
        except Exception as e:
            QMessageBox.critical(self, "Messung Fehler", str(e))

    @Slot()
    def restartDevice(self):
        
        try:
            self.impedanceAnalyser.ResetSystem()
        except Exception as e:
            QMessageBox.critical(self, "Restart failed", str(e))

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