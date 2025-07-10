import math, datetime
from EnumClasses import CurrentRange, InjectionType, FrequencyScale, FeMode, FeChannel, TimeStamp, ExternalModule, InternalModule
from HelperFunctions import GetHexSingle, GetFloatFromBytes, GetFloatResultsFromBytes
import numpy as np
import random
class ImpedanceAnalyserFake():
    """Fake class for GUI testing without device
    """
    
    #region Constructor
    def __init__(self, comPort:str):
        # communication
        self.device = comPort
        self.timeout = 10
        
        # front end settings
        self.feMode = FeMode.mode4pt
        self.feChannel = FeChannel.BNC
        self.feRange = CurrentRange.range10mA
        self.muxElConfig = []
        
        # setup options
        self.precision = 1
        self.excitation = InjectionType.voltage
        self.amplitude = 0.5
        self.resTimeStamp = TimeStamp.off
        self.resCurrentRange = True
        
        # frequency range
        self.fmin = 1e3
        self.fmax = 1e7
        self.fnum = 13
        self.fscale = FrequencyScale.logarithmic
    #endregion
    
    #region Class variable setting functions
    def SetFrequency(self, fmin:float, fmax:float, fnum:int, fscale:FrequencyScale):
        
        self.fmin = fmin
        self.fmax = fmax
        
        if isinstance(fnum, int) and fnum > 0 and fnum < 2048:
            self.fnum = fnum
        else:
            raise Exception(f"Number of requested frequencies {fnum} is out of range [1, 2048]")
        
        if isinstance(fscale, FrequencyScale):
            self.fscale = fscale
        else:
            raise Exception(f"Unknown frequency scailing {fscale} requested")
    
    
    def SetFeMode(self, mode:FeMode):
        if isinstance(mode, FeMode):
            self.feMode = mode
        else:
            raise Exception(f"Unknown measurement mode {mode} requested.")
    
    
    def SetFeChannel(self, channel:FeChannel):
        if isinstance(channel, FeChannel):
            self.feChannel = channel
        else:
            raise Exception(f"Unknown measurement channel {channel} requested.")
    
    
    def SetRange(self, currRange:CurrentRange):
        
        if isinstance(currRange, CurrentRange):
            self.feRange = currRange
        else:
            raise Exception(f"Unknown current range {currRange} requested.")
    
    
    def SetPrecision(self, precision:float):
        
        if precision >= 0 and precision <= 10:
            self.precision = np.float32(precision)
        else:
            raise Exception(f"Requested precision of {precision} is out of range [0, 10].")
    
    
    def SetExcitationType(self, excitation:InjectionType):
        
        if isinstance(excitation, InjectionType):
            self.excitation = excitation
        else:
            raise Exception(f"Unknown excitation type {excitation} requested.")
    
    
    def SetExcitationAmplitude(self, amplitude:float):
        
        self.amplitude = np.float32(amplitude)
        
        
    def SetTimeStamp(self, timeStamp:TimeStamp):
        
        if isinstance(timeStamp, TimeStamp):
            self.resTimeStamp = timeStamp
        else:
            raise Exception(f"Unknown time stamp setting {timeStamp} requested.")
    
    
    def SetMuxChannels(self, elComb:list):
        
        for combination in elComb:                
            if len(combination) != 4:        
                raise Exception("Electrode combinations must be matching the measurement mode.")
        
        self.muxElConfig = elComb
    
    
    def CheckSettings(self):
        # if self.feChannel is FeChannel.BNC and len(self.muxElConfig) != 1:
        #     raise Exception("We measure with BNC, but have set multiple channels.")
        
        if self.feMode is FeMode.mode2pt:
            for combination in self.muxElConfig:
                if combination[0] != combination[1] or combination[2] != combination[3] or combination[0] == combination[3]:
                    raise Exception(f"Electorde config does not match mode: {self.feMode}")
                
        if self.feMode is FeMode.mode3pt:
            for combination in self.muxElConfig:
                if combination[0] == combination[1] or combination[2] != combination[3] or combination[1] == combination[4] or combination[0] == combination[3]:
                    raise Exception(f"Electorde config does not match mode: {self.feMode}")
                
        if self.feMode is FeMode.mode4pt:
            for combination in self.muxElConfig:
                if len(set(combination)) != len(combination):
                    raise Exception(f"Electorde config does not match mode: {self.feMode}")
    
    
    def DoInitialSetup(self, fmin:float, fmax:float, fnum:int, fscale:FrequencyScale, channel:FeChannel, mode:FeMode, currRange:CurrentRange, precision:float, excitationType:InjectionType, excitationAmplitude:float, timestamp:TimeStamp):
        self.SetFrequency(fmin, fmax, fnum, fscale)
        self.SetFeChannel(channel)
        self.SetFeMode(mode)
        self.SetRange(currRange)
        self.SetPrecision(precision)
        self.SetExcitationType(excitationType)
        self.SetExcitationAmplitude(excitationAmplitude)
        self.SetTimeStamp(timestamp)
        
        self.CheckSettings()
        self.SetSetup()
        self.SetOptions()
    #endregion
    
    #region ScioSpec commands
    def SaveSettings(self):
        """0x90 - Save Settings
        """
        
        command = bytes([0x90, 0x00, 0x90])
        print(list(command))
    
    
    def SetOptions(self):
        """0x97 - Set Options

        Raises:
            ValueError: Timestamp must be from enum class
        """
        
        match self.resTimeStamp:
            case TimeStamp.off:
                command = bytes([0x97, 0x02, 0x01, 0x00, 0x97])
            case TimeStamp.ms:
                command = bytes([0x97, 0x02, 0x01, 0x01, 0x97])
            case TimeStamp.us:
                command = bytes([0x97, 0x02, 0x02, 0x01, 0x97])
            case _:
                raise ValueError(f"TimeStamp type not recognised: {self.resTimeStamp}")
        
        print(list(command))
        
        if self.resCurrentRange:
            command = bytes([0x97, 0x02, 0x04, 0x01, 0x97])
        else:
            command = bytes([0x97, 0x02, 0x04, 0x00, 0x97])
            
        print(list(command))
    
    
    def GetOptionsTimeStamp(self) -> (TimeStamp | None):
        """0x98 - Get Options - Get Time stamp

        Args:
            self (_type_): _description_

        Returns:
            _type_: _description_
        """
        
        command = bytes([0x98, 0x01, 0x01, 0x98])
        print(list(command))
        
        msg = bytes([0x98, 0x02, 0x01, self.resTimeStamp.value, 0x98])
        
        if msg[2] == 1:
            return TimeStamp(msg[3])
        
        return None
    
    
    def ResetSystem(self):
        """0xA1 - Reset System
        """
        
        command = bytes([0xA1, 0x00, 0xA1])
        print(list(command))
    
    
    def SetFeSettings(self):
        """0xB0 - Set FE Settings
        """
        
        command = bytes([0xB0, 0x03, 0xFF, 0xFF, 0xFF, 0xB0])
        print(list(command))
        
        command = bytes([0xB0, 0x03, self.feMode.value, self.feChannel.value, self.feRange.value, 0xB0])
        print(list(command))
    
    
    def GetFeSettings(self) -> tuple[FeMode | None, FeChannel | None, CurrentRange | None]:
        """0xB1 - Get FE Settings

        Returns:
            tuple[FeMode | None, FeChannel | None, CurrentRange | None]: _description_
        """
        
        command = bytes([0xB1, 0x00, 0xB1])
        print(list(command))
        
        msg = bytes([0xB1, 0x03, self.feMode.value, self.feChannel.value, self.feRange.value, 0xB1])
        # measurement mode
        mode = FeMode(msg[2])
        channel = FeChannel(msg[3])
        currRange = CurrentRange(msg[4])
        
        return mode, channel, currRange
    
    
    def SetExtensionPortChannel(self, offset:int):
        """0xB2 - Set ExtenstionPort Channel
        
        Args:
            offset (int): index of channel configuration to be set
        
        Raises:
            IndexError: Thrown if the index is out of list bounds
        """
        
        if offset >= len(self.muxElConfig):
            raise IndexError("There are not enough configurations for this offset.")
        
        portBytes = self.muxElConfig[offset]
        
        command = bytes([0xB2, 0x04] + portBytes + [0xB2])
        print(f"Send command:  {list(command)}")
    
    
    def GetExtensionPortChannel(self) -> list[int]:
        """0xB3 - Get ExtensionPort Channel

        Returns:
            list[int]: list with currently configured channels
        """
        
        command = bytearray([0xB3, 0x00, 0xB3])
        print(list(command))
        muxNumber = len(self.muxElConfig)
        msg = [0xB3, muxNumber * 4]
        for config in self.muxElConfig:           
            msg.extend(config)
        msg.append(0xB3)
        msg = bytes(msg)
        
        return [list(msg[x:x+4]) for x in range(2, len(msg) - 1, 4)]
    
    
    def GetExtensionPortModule(self) -> tuple[ExternalModule | None, InternalModule | None, int | None, int | None]:
        """0xB5 - Get ExtenstionPort Module

        Returns:
            tuple[ExternalModule | None, InternalModule | None, int | None, int | None]: _description_
        """
        
        command = bytes([0xB5, 0x00, 0xB5])
        print(list(command))
        
        msg = bytes([0xB5, 0x03, 0x09, 0x02, 0x05, 0x05, 0xB5])
        
        externalModule = ExternalModule(msg[2])
        internalModule = InternalModule(msg[3])
        
        channelCountExt = None
        channelCountInt = None
        if externalModule is ExternalModule.Mux32Any2Any2202:
            channelCountExt = msg[4:6]
            if internalModule is InternalModule.Mux32Any2Any2202:
                channelCountInt = msg[6:8]
        elif internalModule is InternalModule.Mux32Any2Any2202:
            channelCountInt = msg[4:6]
        
        return externalModule, internalModule, channelCountExt, channelCountInt
    
    
    def SetSetup(self):
        """0xB6 - Set Setup
        """
        
        command = bytes([0xB6, 0x01, 0x01, 0xB6])
        print(list(command))
        
        command = bytes([0xB6, 0x25, 0x03])

        if self.fscale is FrequencyScale.linear:
            freqScale = 0
        else:
            freqScale = 1
        # Required data bytes
        command += bytes(GetHexSingle(self.fmin) + GetHexSingle(self.fmax) + GetHexSingle(self.fnum) + [freqScale] + GetHexSingle(self.precision) + GetHexSingle(self.amplitude))
        
        # Optional data bytes
        command += bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00])
        
        if self.excitation is InjectionType.voltage:
            command += bytes([0x01])
        else:
            command += bytes([0x02])
            
        # closing command tag
        command += bytes([0xB6])
        
        print(list(command))
    
    
    # Get Setup functions
    def GetTotalNumberOfFrequencies(self) -> int:
        """0xB7 - Get Setup - Get Total Number of Frequencies

        Returns:
            int: number of frequencies configured in the setup
        """
        
        command = bytes([0xB7, 0x01, 0x01, 0xB7])
        print(list(command))
        msg = bytes([0xB7, 0x02]) + int.to_bytes(self.fnum, 2) + bytes([0xB7])
        
        return int.from_bytes(msg[3:5], "big")
    
    
    def GetInformationOfFrequencyPoint(self, frequencyPoint:int) -> tuple[float, float, float]:
        """0xB7 - Get Setup - Get Information of Frequency Point

        Args:
            frequencyPoint (int): _description_

        Returns:
            tuple(float, float, float): (frequency[Hz], precision, amplitude)
        """
        
        command = bytes([0xB7, 0x03]) + frequencyPoint.to_bytes(2, "big") + bytes([0xB7])
        print(list(command))
        msg = bytes([0xB7, 0x0D, 0x02]) + bytes(GetHexSingle(self.fmin) + GetHexSingle(self.precision) + GetHexSingle(self.amplitude)) + bytes([0xB7])
        
        
        frequency = GetFloatFromBytes(msg[3:7])
        precision = GetFloatFromBytes(msg[7:11])
        amplitude = GetFloatFromBytes(msg[11:15])
        
        return frequency, precision, amplitude
    
    
    def GetFrequencyList(self) -> list[float]:
        """0xB7 - Get Setup - Get Frequency List

        Returns:
            list[float]: list of frequencies as floats
        """
        command = bytes([0xB7, 0x01, 0x04, 0xB7])
        print(list(command))
        if self.fscale is FrequencyScale.logarithmic:
            return np.geomspace(self.fmin, self.fmax, self.fnum)
        else:
            return np.linspace(self.fmin, self.fmax, self.fnum)
    
    
    def StartMeasure(self):
        """0xB8 - Start Measure
        """
        
        command = bytes([0xB8, 0x03, 0x01, 0x00, 0x01, 0xB8])
        print(list(command))
    #endregion
    
    #region Result processing
    def DeserializeResults(self, results:bytes) -> tuple[float, float, int, CurrentRange, list]:
        
        warn = 0
        
        if self.resTimeStamp is TimeStamp.off:
            lengthTime = 0
            timeOffset = None
        elif self.resTimeStamp is TimeStamp.ms:
            lengthTime = 4
            timeOffset = list(results[7:3:-1])
        else:
            lengthTime = 5
            timeOffset = [0, 0, 0] + list(results[8:3:-1])
            
        if not self.resCurrentRange:
            lengthCurrent = 0
            currentRange = 0
        else:
            lengthCurrent = 1
            currentRange = results[4 + lengthTime]

        zReal = GetFloatResultsFromBytes(results[(7 + lengthCurrent + lengthTime):(3 + lengthCurrent + lengthTime):-1])
        zImag = GetFloatResultsFromBytes(results[(11 + lengthCurrent + lengthTime):(7 + lengthTime + lengthCurrent):-1])

        return zReal, zImag, warn, CurrentRange(currentRange), timeOffset
    
    
    def GetMeasurements(self) -> tuple[list, list, list, list, str, str]:
        
        muxConfigLen = len(self.muxElConfig)
        resWarning = [[0 for _ in range(self.fnum)] for _ in range(muxConfigLen)]
        resReal = [[None for _ in range(self.fnum)] for _ in range(muxConfigLen)]
        resImag = [[None for _ in range(self.fnum)] for _ in range(muxConfigLen)]
        resRange = [["" for _ in range(self.fnum)] for _ in range(muxConfigLen)]
        resTime = [[None for _ in range(self.fnum)] for _ in range(muxConfigLen)]
        
        counter = 0
        
        startTime = datetime.datetime.now().isoformat(" ", "seconds")
        
        for idxElChunks in range(math.ceil(muxConfigLen / 128)):
            
            numMeas = muxConfigLen - 128 * idxElChunks
                
            self.SetFeSettings()
            
            for _ in range(numMeas):
                self.SetExtensionPortChannel(counter)
                counter += 1
            
            self.StartMeasure()
            
            for measIdx in range(numMeas):
                for freqIdx in range(self.fnum):
                    results = bytes([184, 11, 0, 0, 1, random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 184])
                    real, imag, warn, currentRange, timeOffset = self.DeserializeResults(results)
                    
                    resReal[measIdx + 128 * idxElChunks][freqIdx] = real
                    resImag[measIdx + 128 * idxElChunks][freqIdx] = imag
                    resWarning[measIdx + 128 * idxElChunks][freqIdx] = warn
                    resRange[measIdx + 128 * idxElChunks][freqIdx] = currentRange
                    resTime[measIdx + 128 * idxElChunks][freqIdx] = timeOffset
                    
        finishTime = datetime.datetime.now().isoformat(" ", "seconds")
        
        return resReal, resImag, resWarning, resRange, resTime, startTime, finishTime
    #endregion