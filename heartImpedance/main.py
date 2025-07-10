"""
main.py
Starts GUI, shows dialog serial port choice and opens settings tab as the default.
"""
from __future__ import annotations
import sys
import serial
import pandas as pd
from PySide6.QtWidgets import QApplication,QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QFileDialog, QMessageBox, QRadioButton, QButtonGroup,QLineEdit, QLabel, QDialog
from PySide6.QtCore import Slot
from AdditionalClasses import MeasurementWorker, UnitComboBox, RestartWorker, StartupPopup
from DataManager import EISData, LoadFromDataframe
from TabClasses import SettingsTab, BodeDiagramTab, TimeSeriesTab, DerivedValueTab
from ImpedanceAnalyser import ImpedanceAnalyser
from ImpedanceAnalyserFake import ImpedanceAnalyserFake

# ---------------------------------------------------------------------- #
#  GUI MainWindow                                                        #
# ---------------------------------------------------------------------- #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EIS‑GUI (ISX‑3)")
        
        # COM port dialog, if dialog exited by closing or no port is entered, then the ImpedanceAnalyserFake is chosen
        dialog = StartupPopup()
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
        
        # Initiates workers and data list
        self.measWorker = None
        self.restartWorker = None
        self.savedData:list[EISData] = []

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
        self.saveButton = QPushButton("Save")
        self.loadButton = QPushButton("Load")
        self.singleMeasurementButton = QPushButton("Run Single Measurement")
        self.restartDeviceButton = QPushButton("Restart device")
        self.runLoopMeasurementButton = QPushButton("Run Multiple Measurements")
        self.saveButton.clicked.connect(self.SaveData)
        self.loadButton.clicked.connect(self.load_data)
        self.singleMeasurementButton.clicked.connect(self.RunSingleMeasurement)
        self.restartDeviceButton.clicked.connect(self.RestartDevice)
        self.runLoopMeasurementButton.clicked.connect(self.RunMultipleMeasurements)
        
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
        hl.addWidget(self.saveButton)
        hl.addWidget(self.loadButton)
        hl.addWidget(self.singleMeasurementButton)
        hl.addWidget(self.runLoopMeasurementButton)
        hl.addWidget(self.repetitionMode)
        hl.addWidget(self.repetitionsLineEdit)
        hl.addWidget(self.timeMode)
        hl.addWidget(self.timeLineEdit)
        hl.addWidget(self.timeUnitComboBox)
        hl.addWidget(QLabel("Interval: "))
        hl.addWidget(self.intervalLineEdit)
        hl.addWidget(self.intervalComboBox)
        hl.addStretch()
        hl.addWidget(self.restartDeviceButton)

        lay = QVBoxLayout(self)
        lay.addLayout(hl)
        lay.addWidget(self.tabs, stretch=1)

    # ------------------------------------------------------------------ #
    @Slot()
    def SaveData(self):
        """Saves data stored in self.savedData to csv
        """
        path, _ = QFileDialog.getSaveFileName(self, "Save data", __file__.replace("main.py", "SavedMeasurements"), "Files (*.csv)")
        if not path:
            return
        
        try:
            bigDf = pd.DataFrame()
            for data in self.savedData:
                bigDf = pd.concat([bigDf, data.SaveToDataframe()])
            bigDf.to_csv(path, index=False)
        except Exception as e:
            QMessageBox.warning(self, "Error while saving data", "Saving data failed due to: " + str(e))
        
    @Slot()
    def load_data(self):
        """Loads data from csv
        """
        path, _ = QFileDialog.getOpenFileName(self, "Load data", __file__.replace("main.py", "SavedMeasurements"), "Files (*.csv)")
        if not path:
            return
        try:
            data = pd.read_csv(path)
            uniqueMeasurements = data["MeasurementIndex"].unique()
            
            self.ClearAllData()
            for index in uniqueMeasurements:
                newData = LoadFromDataframe(data[:][data["MeasurementIndex"] == index])
                self._broadcast_data(newData)
            EISData.index = max(uniqueMeasurements) + 1
        except Exception as e:
            QMessageBox.critical(self, "Error while loading data", "Loading data failed due to: " + str(e))
            return

    @Slot()
    def RunSingleMeasurement(self):
        """Runs one iteration of measurement with chosen settings
        """
        
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
        """Restarts device, takes around 12 seconds, no measurements or settings are allowed during that time
        """
        
        try:
            self.SetAllButtonsEnabled(False)
            self.restartWorker = RestartWorker(self.impedanceAnalyser)
            self.restartWorker.restartFinished.connect(self.SetAllButtonsEnabled)
            self.restartWorker.start()
        except Exception as e:
            QMessageBox.critical(self, "Restart failed", str(e))
    
    @Slot()
    def RunMultipleMeasurements(self):
        """Runs series of measurements depending on user's choice of time or repetitions
        """
        
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
        
        # Starts measurement worker, block ui until worker finishes, each measurement data is broadcasted to GUI tabs
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
        """Handler for repetition radio button
        """
        
        self.repetitionsLineEdit.setEnabled(True)
        self.timeLineEdit.setEnabled(False)
        self.timeUnitComboBox.setEnabled(False)
    
    @Slot()
    def timeModeClicked(self):
        """Handler for time radio button
        """
        
        self.repetitionsLineEdit.setEnabled(False)
        self.timeLineEdit.setEnabled(True)
        self.timeUnitComboBox.setEnabled(True)
    
    @Slot()
    def SetAllButtonsEnabled(self, setEnabled:bool):
        """Enables or disables or the measurement and settings controls

        Args:
            setEnabled (bool): True if controls should be enabled, False otherwise
        """
        
        self.saveButton.setEnabled(setEnabled)
        self.loadButton.setEnabled(setEnabled)
        self.singleMeasurementButton.setEnabled(setEnabled)
        self.runLoopMeasurementButton.setEnabled(setEnabled)
        self.restartDeviceButton.setEnabled(setEnabled)
        self.tabSettings.setEnabled(setEnabled)

    # ------------------------------------------------------------------ #
    def ClearAllData(self):
        """Clears data from all tabs
        """
        self.savedData.clear()
        self.tabBode.savedData.clear()
        self.tabBode.data = None
        self.tabTimeSeries.savedData.clear()
        self.tabTimeSeries.data = None
        self.tabDerived.savedData.clear()
        
    def _broadcast_data(self, data: EISData):
        """Sends data from measurements to all GUI tabs

        Args:
            data (EISData): measurement data
        """
        self.savedData.append(data)
        self.tabBode.update_data(data)
        self.tabTimeSeries.update_data(data)
        self.tabDerived.update_data(data)

# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(1200, 800)
    win.show()
    sys.exit(app.exec())