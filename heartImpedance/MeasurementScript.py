import numpy as np
import time
from CalculateValidImpedanceRange import CalculateValidImpedanceRange
from ImpedanceAnalyser import ImpedanceAnalyser
from ImpedanceAnalyserFake import ImpedanceAnalyserFake
from EnumClasses import CurrentRange, InjectionType, FrequencyScale, FeChannel, FeMode, TimeStamp


myComPort = "COM3"

root_folder = "_delete"
meas_name = 'EIT_Tank_2'

elComb = [[1, 2, 3, 4]]

repeatCount = 3
repetitionTime = 0.2

# For excitation type and current range use the enum classes
excitationType = InjectionType.voltage
excitationValue = 0.5
currentRange = CurrentRange.rangeAuto

zMin, zMax = CalculateValidImpedanceRange(excitationType, excitationValue, currentRange)

is3x = ImpedanceAnalyserFake(myComPort)

fmin = 1e3
fmax = 1e6
fnum = 10
fscale = FrequencyScale.logarithmic
channel = FeChannel.BNC
mode = FeMode.mode4pt
precision = 1
timestamp = TimeStamp.off
is3x.DoInitialSetup(fmin, fmax, fnum, fscale, channel, mode, currentRange, precision, excitationType, excitationValue, timestamp)
is3x.SetSetup()
is3x.GetFrequencyList()

fVec = np.logspace(fmin, fmax, fnum)

waitTime = 0.5
for repetition in range(repeatCount):
    if waitTime > 0.01:
        time.sleep(waitTime)
    
    measurementStartTime = time.time()
    resRealList, resImagList, resWarnList, resRangeList, resTimeList, startTimeList, finishTimeList = is3x.GetMeasurements()
    measurementEndTime = time.time()
    
    impMagList = []
    impAngList = []
    
    admList = []
    admMagList = []
    admAngList = []
    for index, _ in enumerate(resWarnList):
        impedanceComplex = complex(resRealList[index][0], resImagList[index][0])
        impMagList.append(abs(impedanceComplex))
        impAngList.append(np.angle(impedanceComplex))
        
        admList.append(1 / impedanceComplex)
        admMagList.append(abs(admList[-1]))
        admAngList.append(np.angle(admList[-1]))
        