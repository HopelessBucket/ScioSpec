import math, datetime
import serial
from EnumClasses import CurrentRange, InjectionType, FrequencyScale, FeMode, FeChannel, TimeStamp, ExternalModule, InternalModule
from HelperFunctions import GetHexSingle, GetFloatFromBytes, GetFloatResultsFromBytes
class ImpedanceAnalyser():
    """Device for handling communication with ScioSpec device
    """
    
    #region Constructor
    def __init__(self, comPort:str):
        # communication
        self.device = serial.Serial(port=comPort, timeout=256000)
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
            self.precision = precision
        else:
            raise Exception(f"Requested precision of {precision} is out of range [0, 10].")
    
    
    def SetExcitationType(self, excitation:InjectionType):
        
        if isinstance(excitation, InjectionType):
            self.excitation = excitation
        else:
            raise Exception(f"Unknown excitation type {excitation} requested.")
    
    
    def SetExcitationAmplitude(self, amplitude:float):
        
        self.amplitude = amplitude
        
        
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
        if self.feChannel is FeChannel.BNC and len(self.muxElConfig) != 1:
            raise Exception("We measure with BNC, but have set multiple channels.")

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
        
        print(f"Precision: {precision}, amplitude: {excitationAmplitude}")
        self.SetSetup()
        self.SetFeSettings()
        self.SetOptions()
    #endregion
    
    #region SerialPort Communication
    def SendAndReceive(self, command:bytes) -> bytes:
        
        self.device.write(command)
        
        msg = bytes()
        while True:
            frame = self.ReadFrame()
            print(list(frame))
            if self.IsAck(frame):
                ack = frame[2]
                self.WarningACK(ack)
                break
            
            msg += frame
                
        return msg
    
    
    def ReadFrame(self) -> bytes:
        
        msgHeader = self.device.read(2)
        ct = msgHeader[0]
        le = msgHeader[1]
        
        msgBody = self.device.read(le+1)
        if ct != msgBody[-1]:
            raise Warning("Malformed message received.")
        
        return msgHeader + msgBody
    
    
    def ReadBuffer(self) -> tuple[list, bytes]:
        
        buffer = self.device.read(self.device.bytesize)
        
        bytePos = 1
        msgs = bytes()
        while bytePos < len(buffer):
            le = buffer[bytePos]
            
            msgThis = buffer[bytePos:(bytePos + le + 2)]
            bytePos += le + 3
            
            msgs += msgThis
            
        return msgs, buffer
    
    
    def IsAck(self, msg:bytes) -> bool:
        
        if len(msg) == 4 and msg[0] == 0x18 and msg[1] == 0x01 and msg[3] == 0x18:
            return True
        
        return False
    
    
    def WarningACK(self, ack:int):
        
        match ack:
            case 0x01:
                raise Exception("Ack: 0x01 Frame-Not-Acknowledge: Incorrect syntax.")
            case 0x02:
                raise Exception("Ack: 0x02 Timeout: Communication-timeout (less data than expected).")
            case 0x04:
                print("Ack: 0x04 Wake-Up Message: System boot ready.")
            case 0x11:
                print("Ack: 0x11 TCP-Socket: Valid TCP client-socket connection.")
            case 0x81:
                raise Exception("Ack: 0x81 Not-Acknowledge: Command has not been executed.")
            case 0x82:
                raise Exception("Ack: 0x82 Not-Acknowledge: Command could not be recognized.")
            case 0x83:
                print("Command-Acknowledge")
            case 0x84:
                print("Ack: 0x84 System-Ready Message: System is operational and ready to receive data.")
            case 0x90:
                print("Ack: 0x90 Overcurrent Detected.")
            case 0x91:
                print("Ack: 0x91 Overvoltage Detected.")
            case _:
                print(f"ACK: Unknown! Msg: {ack}")
    #endregion
    
    #region ScioSpec commands
    def SaveSettings(self):
        """0x90 - Save Settings
        """
        
        command = bytes([0x90, 0x00, 0x90])
        self.SendAndReceive(command)
    
    
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
        
        self.SendAndReceive(command)
        
        if self.resCurrentRange:
            command = bytes([0x97, 0x02, 0x04, 0x01, 0x97])
        else:
            command = bytes([0x97, 0x02, 0x04, 0x00, 0x97])
            
        self.SendAndReceive(command)
    
    
    def GetOptionsTimeStamp(self) -> (TimeStamp | None):
        """0x98 - Get Options - Get Time stamp

        Args:
            self (_type_): _description_

        Returns:
            _type_: _description_
        """
        
        command = bytes([0x98, 0x01, 0x01, 0x98])
        msg = self.SendAndReceive(command)
        
        if msg[2] == 1 and msg[3] == 0:
            self.resTimeStamp = TimeStamp.off
        if msg[2] == 1 and msg[3] == 1:
            self.resTimeStamp = TimeStamp.ms
        if msg[2] == 1 and msg[3] == 2:
            self.resTimeStamp = TimeStamp.us
        
        return self.resTimeStamp
    
    
    def ResetSystem(self):
        """0xA1 - Reset System
        """
        
        command = bytes([0xA1, 0x00, 0xA1])
        self.SendAndReceive(command)
    
    
    def SetFeSettings(self):
        """0xB0 - Set FE Settings
        """
        
        command = bytes([0xB0, 0x03, 0xFF, 0xFF, 0xFF, 0xB0])
        self.SendAndReceive(command)
        
        command = bytes([0xB0, 0x03, self.feMode.value, self.feChannel.value, self.feRange.value, 0xB0])
        self.SendAndReceive(command)
    
    
    def GetFeSettings(self) -> tuple[FeMode | None, FeChannel | None, CurrentRange | None]:
        """0xB1 - Get FE Settings

        Returns:
            tuple[FeMode | None, FeChannel | None, CurrentRange | None]: _description_
        """
        
        command = bytes([0xB1, 0x00, 0xB1])
        msg = self.SendAndReceive(command)
        
        # measurement mode
        mode = None
        for measMode in FeMode:
            if msg[2] == measMode.value:
                self.feMode = measMode
                mode = measMode
                break
        
        # measurement channel
        channel = None
        for measChannel in FeChannel:
            if msg[3] == measChannel.value:
                self.feChannel = measChannel
                channel = measChannel
                break
        
        # range
        currRange = None
        for possRange in CurrentRange:
            if msg[4] == possRange.value:
                self.feRange = possRange
                currRange = possRange
                break
        
        
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
        self.SendAndReceive(command)
    
    
    def GetExtensionPortChannel(self) -> list[int]:
        """0xB3 - Get ExtensionPort Channel

        Returns:
            list[int]: list with currently configured channels
        """
        
        command = bytearray([0xB3, 0x00, 0xB3])
        msg = self.SendAndReceive(command)
        
        return [list(msg[x:x+4]) for x in range(2, len(msg) - 1, 4)]
    
    
    def GetExtensionPortModule(self) -> tuple[ExternalModule | None, InternalModule | None, int | None, int | None]:
        """0xB5 - Get ExtenstionPort Module

        Returns:
            tuple[ExternalModule | None, InternalModule | None, int | None, int | None]: _description_
        """
        
        command = bytes([0xB5, 0x00, 0xB5])
        msg = self.SendAndReceive(command)
        
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
        self.SendAndReceive(command)
        
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
        
        self.SendAndReceive(command)
    
    
    # Get Setup functions
    def GetTotalNumberOfFrequencies(self) -> int:
        """0xB7 - Get Setup - Get Total Number of Frequencies

        Returns:
            int: number of frequencies configured in the setup
        """
        
        command = bytes([0xB7, 0x01, 0x01, 0xB7])
        msg = self.SendAndReceive(command)
        
        return int.from_bytes(msg[3:5], "big")
    
    
    def GetInformationOfFrequencyPoint(self, frequencyPoint:int) -> tuple[float, float, float]:
        """0xB7 - Get Setup - Get Information of Frequency Point

        Args:
            frequencyPoint (int): _description_

        Returns:
            tuple(float, float, float): (frequency[Hz], precision, amplitude)
        """
        
        command = bytes([0xB7, 0x03, 0x02]) + frequencyPoint.to_bytes(2, "big") + bytes([0xB7])
        msg = self.SendAndReceive(command)
        
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
        msg = self.SendAndReceive(command)
        
        return [GetFloatFromBytes(msg[i:i+4]) for i in range(3, len(msg) - 2, 4)]
    
    
    def SaveSetupToSlot(self, slot:int):
        """0xB7 - Get Setup - Save Setup to Slot

        Args:
            slot (int): slot number between 1 and 255

        Raises:
            ValueError: _description_
        """
        
        if slot < 1 or slot > 255:
            raise ValueError("Slot must be of one byte size.")
        
        command = bytes([0xB7, 0x02, 0x20, slot, 0xB7])
        self.SendAndReceive(command)
    
    
    def GetDCBias(self) -> float:
        """0xB7 - Get Setup - Get DC Bias

        Returns:
            float: dc bias in volts
        """
        
        command = bytes([0xB7, 0x01, 0x33, 0xB7])
        msg = self.SendAndReceive(command)
        
        return GetFloatFromBytes(msg[3:7])
    
    
    def StartMeasure(self):
        """0xB8 - Start Measure
        """
        
        command = bytes([0xB8, 0x03, 0x01, 0x00, 0x01, 0xB8])
        self.SendAndReceive(command)
    
    def StopMeasure(self):
        """0xB8 - Stop Measure
        """
        
        command = bytes([0xB8, 0x01, 0x00, 0xB8])
        self.SendAndReceive(command)
    
    def SetSyncTime(self, syncTime:int):
        """0xB9 - Set Sync Time

        Args:
            syncTime (int): sync time in microseconds, needs to be between 0 and 180e6

        Raises:
            ValueError: _description_
        """
        
        if syncTime < 0 or syncTime > 180e6:
            raise ValueError("SyncTime needs to be between 0 and 180 seconds")
        
        command = bytes([0xB9, 0x04, syncTime.to_bytes(4, "big")])
        self.SendAndReceive(command)
    
    
    def GetSyncTime(self) -> int:
        """0xBA

        Returns:
            int: synchronization time in microseonds
        """
        
        command = bytes([0xBA, 0x00, 0xBA])
        msg = self.SendAndReceive(command)
        
        return int.from_bytes(msg[2:6], "big")
    
    
    def SetIPAddress(self, ipAddress:str = "0.0.0.0"):
        """0xBD - Set Ethernet Configuration - Set IP Address

        Args:
            ipAddress (str, optional): IP address to be set. Defaults to "0.0.0.0".
        """
        
        addressSubStrings = ipAddress.split(".")
        addressInts = [int(a) for a in addressSubStrings]
        
        command = bytes([0xBD, 0x05, 0x01] + addressInts + [0xBD])
        self.SendAndReceive(command)
    
    
    def SetDHCPSwitch(self, switch:bool):
        """0xBD - Set Ethernet Configuration - Set DHPC Switch

        Args:
            switch (bool): True for on, False for off
        """
        
        if switch:
            switchInt = 1
        else:
            switchInt = 0
        
        command = bytes([0xBD, 0x02, 0x03, switchInt, 0xBD])
        self.SendAndReceive(command)
    
    
    def GetIPAddress(self) -> str:
        """0xBE - Get Ethernet Configuration - Get IP Address

        Returns:
            str: string with IP address
        """
        
        command = bytes([0xBE, 0x01, 0x01, 0xBE])
        msg = self.SendAndReceive(command)
        
        return ".".join(list(msg[3:7]))
    
    
    def GetMACAddress(self) -> str:
        """0xBE - Get Ethernet Configuration - Get MAC Address

        Returns:
            str: string with mac address
        """
        
        command = bytes([0xBE, 0x01, 0x02, 0xBE])
        msg = self.SendAndReceive(command)
        
        return msg[3:9].hex("-")
    
    
    def GetDHCPSwitch(self) -> bool:
        """0xBE Get Ethernet Configuration - Get DHCP Switch

        Returns:
            bool: Current DHCP switch state, True - on, False - off
        """
        
        command = bytes([0xBE, 0x01, 0x03, 0xBE])
        msg = self.SendAndReceive(command)
        
        if msg[3] == 1:
            return True
        else:
            return False
    
    
    def TCPConnectionWatchdog(self, interval:int = 60):
        """0xCF - TCP Connection Watchdog

        Args:
            interval (int): interval in seconds, minimum 1s, maximum 600s, must be int type
        """
        
        command = bytes([0xCF, 0x05, 0x00]) + interval.to_bytes(4, "big") + bytes([0xCF])
        self.SendAndReceive(command)
    
    
    def GetARMFirmwareID(self) -> tuple[int, int]:
        """0xD0 - Get ARM firmware ID

        Returns:
            tuple[int, int]: (revision number, build number)
        """
        
        command = bytes([0xD0, 0x00, 0xD0])
        msg = self.SendAndReceive(command)
        
        revisionNumber = int.from_bytes(msg[4, 5], "big")
        buildNumber = int.from_bytes(msg[6, 7], "big")
        
        return revisionNumber, buildNumber
    
    
    def GetDeviceID(self) -> tuple[int, int, int, int]:
        """0xD1 - Get Device ID

        Returns:
            tuple[int, int, int, int]: (version of the general information part, device identifier, serial number, date of delivery)
        """
        
        command = bytes([0xD1, 0x00, 0xD1])
        msg = self.SendAndReceive(command)
        
        version = msg[2]
        deviceID = int.from_bytes(msg[3, 4], "big")
        serialNumber = int.from_bytes(msg[5, 6], "big")
        deliveryDate = 2010 + int.from_bytes(msg[7, 8], "big")
        
        return version, deviceID, serialNumber, deliveryDate
    
    
    def GetFPGAFirmwareID(self) -> tuple[int, int]:
        """0xD2 - Get FPGA Firmware ID

        Returns:
            tuple[int, int]: (revision number, build number)
        """
        
        command = bytes([0xD2, 0x00, 0xD2])
        msg = self.SendAndReceive(command)
        
        revisionNumber = int.from_bytes(msg[7, 8], "big")
        buildNumber = int.from_bytes(msg[9, 10], "big")
        
        return revisionNumber, buildNumber
    #endregion
    
    #region Result processing
    def DeserializeResults(self, results:bytes) -> tuple[float, float, int, CurrentRange, list]:
        
        warn = 0
        if self.IsAck(results):
            warn = results[2]
            results = self.ReadFrame()
            
            if self.IsAck(results):
                warn += results[2] * 1000
                results = self.ReadFrame()
        
        
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
    
    
    def GetMeasurements(self) -> tuple[list, list, list, list, list, str, str]:
        
        self.CheckSettings()
        
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
                    results = self.ReadFrame()
                    real, imag, warn, currentRange, timeOffset = self.DeserializeResults(results)
                    
                    resReal[measIdx + 128 * idxElChunks][freqIdx] = real
                    resImag[measIdx + 128 * idxElChunks][freqIdx] = imag
                    resWarning[measIdx + 128 * idxElChunks][freqIdx] = warn
                    resRange[measIdx + 128 * idxElChunks][freqIdx] = currentRange
                    resTime[measIdx + 128 * idxElChunks][freqIdx] = timeOffset
            
        finishTime = datetime.datetime.now().isoformat(" ", "seconds")
        
        return resReal, resImag, resWarning, resRange, resTime, startTime, finishTime
    #endregion