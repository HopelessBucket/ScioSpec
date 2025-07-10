import time
from PySide6.QtWidgets import QComboBox, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout
from PySide6.QtCore import QThread, Signal
from DataManager import EISData, LoadFromDataframe
from ImpedanceAnalyser import ImpedanceAnalyser

class MeasurementWorker(QThread):
    """Worker for parallel execution of measurements while user can switch between gui tabs

    Args:
        QThread (_type_): _description_
    """
    resultReady = Signal(EISData)
    finished = Signal(bool)
    
    def __init__(self, impedanceAnalyser:ImpedanceAnalyser, timeMode:bool, measVariable:int, intervalMs:int):
        """Standard constructor with device and measurement parameters

        Args:
            impedanceAnalyser (ImpedanceAnalyser): connected device
            timeMode (bool): True if time mode selected, False if repetition mode
            measVariable (int): If time mode, duration in ms, else number of repetitions
            intervalMs (int): Waiting time before starting the next measurement
        """
        super().__init__()
        self.impedanceAnalyser = impedanceAnalyser
        self.timeMode = timeMode
        self.measVariable = measVariable
        self.intervalMs = intervalMs
    
    def run(self):
        
        try:
            if self.timeMode:
                startTimeLoop = time.time()
                measIndex = 0
                # Runs measurements until it reaches time provided by user
                while ((time.time() - startTimeLoop) * 1000 < self.measVariable):
                    measIndex += 1
                    resReal, resImag, _, _, resTime, startTime, finishTime = self.impedanceAnalyser.GetMeasurements()
                    frequencies = self.impedanceAnalyser.GetFrequencyList()
                    electrodes = self.impedanceAnalyser.GetExtensionPortChannel()
                    data = EISData( timeStamp = resTime, 
                                    frequencies = frequencies, 
                                    electrodes = electrodes, 
                                    realParts = resReal, 
                                    imagParts = resImag, 
                                    startTime=startTime, 
                                    finishTime=finishTime)
                    if data.impedances is not None:
                        self.resultReady.emit(data)
                    time.sleep(self.intervalMs / 1000)
            
            else:
                # Runs measurements until the number of repetitions provided by user is reached
                for measIndex in range(1, self.measVariable + 1):
                    resReal, resImag, _, _, resTime, startTime, finishTime = self.impedanceAnalyser.GetMeasurements()
                    frequencies = self.impedanceAnalyser.GetFrequencyList()
                    electrodes = self.impedanceAnalyser.GetExtensionPortChannel()
                    data = EISData( timeStamp = resTime, 
                                    frequencies = frequencies, 
                                    electrodes = electrodes, 
                                    realParts = resReal, 
                                    imagParts = resImag, 
                                    startTime=startTime, 
                                    finishTime=finishTime)
                    if data.impedances is not None:
                        self.resultReady.emit(data)
                    time.sleep(self.intervalMs / 1000)
        except Exception as e:
            print("Exception encountered: " + str(e))
        finally:
            self.finished.emit(True)

class RestartWorker(QThread):
    """Worker for parallel restarting of the device while user can switch between gui tabs

    Args:
        QThread (_type_): _description_
    """
    
    restartFinished = Signal(bool)
    
    def __init__(self, impedanceAnalyser:ImpedanceAnalyser):
        super().__init__()
        self.impedanceAnalyser = impedanceAnalyser
    
    def run(self):
        # Due to the problem with connection, closing and opening the serial port is required. 12 seconds should be enough for restart from my observations
        self.impedanceAnalyser.ResetSystem()
        self.impedanceAnalyser.device.close()
        time.sleep(12)
        self.impedanceAnalyser.device.open()
        self.restartFinished.emit(True)

class UnitComboBox(QComboBox):
    """Custom combobox for time unit choice

    Args:
        QComboBox (_type_): _description_
    """
    
    def __init__(self):
        
        super().__init__()
        self.addItems(["ms", "s", "min", "h"])
        self.setCurrentText("s")
    
    def GetTimeInMs(self, lineEditValue:int):
        
        match self.currentText():
            case "ms":
                durationMs = lineEditValue
            case "s":
                durationMs = 1000 * lineEditValue
            case "min":
                durationMs = 60000 * lineEditValue
            case "h":
                durationMs = 3600000 * lineEditValue
        
        return durationMs

class StartupPopup(QDialog):
    """Dialog for COM Port choice

    Args:
        QDialog (_type_): _description_
    """
    
    def __init__(self):
        
        super().__init__()
        self.setWindowTitle("COM-Port input")
        
        # Defining controls
        self.label = QLabel("Enter COM-Port used by the device:")
        self.userInput = QLineEdit(text="COM5")
        self.okButton = QPushButton("OK")
        
        # Adding all controls to layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.userInput)
        layout.addWidget(self.okButton)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(layout)
        
        # Connecting buttons
        self.okButton.clicked.connect(self.accept)
    
    def getUserComPort(self):
        return self.userInput.text()