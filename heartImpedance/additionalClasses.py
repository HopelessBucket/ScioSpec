import time
from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QThread, Signal
from data_manager import EISData
from ImpedanceAnalyser import ImpedanceAnalyser

class MeasurementWorker(QThread):
    
    resultReady = Signal(EISData)
    finished = Signal(bool)
    
    def __init__(self, impedanceAnalyser:ImpedanceAnalyser, timeMode:bool, measVariable:int, intervalMs:int):
        
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
                while ((time.time() - startTimeLoop) * 1000 < self.measVariable):
                    measIndex += 1
                    resReal, resImag, _, _, resTime, startTime, finishTime = self.impedanceAnalyser.GetMeasurements()
                    frequencies = self.impedanceAnalyser.GetFrequencyList()
                    electrodes = self.impedanceAnalyser.GetExtensionPortChannel()
                    data = EISData( time = resTime, 
                                    frequency = frequencies, 
                                    electrodes = electrodes, 
                                    realPart = resReal, 
                                    imagPart = resImag, 
                                    startTime=startTime, 
                                    finishTime=finishTime)
                    self.resultReady.emit(data)
                    time.sleep(self.intervalMs / 1000)
            
            else:
                for measIndex in range(1, self.measVariable + 1):
                    
                    resReal, resImag, _, _, resTime, startTime, finishTime = self.impedanceAnalyser.GetMeasurements()
                    frequencies = self.impedanceAnalyser.GetFrequencyList()
                    electrodes = self.impedanceAnalyser.GetExtensionPortChannel()
                    data = EISData( time = resTime, 
                                    frequency = frequencies, 
                                    electrodes = electrodes, 
                                    realPart = resReal, 
                                    imagPart = resImag, 
                                    startTime=startTime, 
                                    finishTime=finishTime, 
                                    measurementIndex=measIndex)
                    self.resultReady.emit(data)
                    time.sleep(self.intervalMs / 1000)
        except Exception as e:
            print("Exception encountered: " + str(e))
        finally:
            self.finished.emit(True)

class RestartWorker(QThread):
    
    restartFinished = Signal(bool)
    
    def __init__(self, impedanceAnalyser:ImpedanceAnalyser):
        super().__init__()
        self.impedanceAnalyser = impedanceAnalyser
    
    def run(self):
        
        self.impedanceAnalyser.ResetSystem()
        self.impedanceAnalyser.device.close()
        time.sleep(12)
        self.impedanceAnalyser.device.open()
        self.restartFinished.emit(True)


class UnitComboBox(QComboBox):
    
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