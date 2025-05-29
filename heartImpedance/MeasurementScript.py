import numpy as np
import time
from CalculateValidImpedanceRange import CalculateValidImpedanceRange
from ImpedanceAnalyser import ImpedanceAnalyser
from EnumClasses import CurrentRange, InjectionType, FrequencyScale, FeChannel, FeMode, TimeStamp


myComPort = "COM3"

root_folder = "_delete"
meas_name = 'EIT_Tank_2'

elComb = [[1, 2, 3, 4]]

repeatCount = 3
repetitionTime = 0.2

# For excitation type and current range use the enum classes
excitationType = InjectionType.Voltage
excitationValue = 0.5
currentRange = CurrentRange.Auto

zMin, zMax = CalculateValidImpedanceRange(excitationType, excitationValue, currentRange)

is3x = ImpedanceAnalyser(myComPort)

fmin = 1e3
fmax = 1e6
fnum = 10
fscale = FrequencyScale.Log
channel = FeChannel.BNC
mode = FeMode.mode4pt
precision = 1
timestamp = TimeStamp.ms

is3x.DoInitialSetup(fmin, fmax, fnum, fscale, channel, mode, currentRange, precision, excitationType, excitationValue, elComb, timestamp)
is3x.SetSetup()

fVec = np.logspace(fmin, fmax, fnum)

waitTime = 0.5
for repetition in range(repeatCount):
    if waitTime > 0.01:
        time.sleep(waitTime)
    
    measurementStartTime = time.time()
    resImpList, resWarnList, resRangeList, resTimeList, startTimeList, finishTimeList = is3x.GetMeasurements()
    measurementEndTime = time.time()
    
    impMagList = []
    impAngList = []
    
    admList = []
    admMagList = []
    admAngList = []
    for impedance in resImpList:
        impMagList.append(abs(impedance))
        impAngList.append(np.angle(impedance))
        
        admList.append(1 / impedance)
        admMagList.append(abs(admList[-1]))
        admAngList.append(np.angle(admList[-1]))
        