import math, datetime
import serial
from EnumClasses import CurrentRange, InjectionType, FrequencyScale, FeMode, FeChannel, TimeStamp, ExternalModule, InternalModule
from HelperFunctions import GetHex, GetHexSingle, GetFloatFromBytes
import numpy as np
class ImpedanceAnalyser():
    
    def __init__(self, comPort:str):
        # communication
        self.device = comPort
        # self.device = serial.Serial(port=comPort, timeout=256000)
        self.timeout = 10
        
        # front end settings
        self.feMode = FeMode.mode4pt
        self.feChannel = FeChannel.BNC
        self.feRange = CurrentRange.Select10mA
        self.muxElConfig = [[1, 2, 3, 4]]
        
        # setup options
        self.precision = 1
        self.excitation = InjectionType.Voltage
        self.amplitude = 0.5
        self.resTimeStamp = TimeStamp.off
        self.resCurrentRange = True
        
        # frequency range
        self.fmin = 1e3
        self.fmax = 1e7
        self.fnum = 13
        self.fscale = FrequencyScale.Log
    
    
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
        if self.feChannel is FeChannel.BNC and len(self.muxElConfig) != 1:
            raise Exception("We measure with BNC, but have set multiple channels.")
        
        if self.excitation is InjectionType.Current and self.feRange is CurrentRange.Auto:
            raise Exception("Current measurement mode \"auto\" is not supported for Current injection.")
        
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
    
    
    def SendAndReceive(self, command:bytes) -> bytes:
        
        self.device.write(command)
        
        msg = bytes()
        while True:
            frame = self.ReadFrame()
            if self.IsAck(frame):
                ack = frame[3]
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
    
    
    def WarningACK(self, ack:bytes):
        
        match ack[2]:
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
    
    
    def DevSetOptions(self):
        
        match self.resTimeStamp:
            case TimeStamp.off:
                command = bytes([0x97, 0x02, 0x01, 0x00, 0x97])
            case TimeStamp.ms:
                command = bytes([0x97, 0x02, 0x01, 0x01, 0x97])
            case TimeStamp.us:
                command = bytes([0x97, 0x02, 0x02, 0x01, 0x97])
            case _:
                raise Exception(f"TimeStamp type not recognised: {self.resTimeStamp}")
        
        self.SendAndReceive(command)
        
        if self.resCurrentRange:
            command = bytes([0x97, 0x02, 0x04, 0x01, 0x97])
        else:
            command = bytes([0x97, 0x02, 0x04, 0x00, 0x97])
            
        self.SendAndReceive(command)
    
    
    def DevSetFeSettings(self):
        
        command = bytes([0xB0, 0x03, 0xFF, 0xFF, 0xFF, 0xB0])
        self.SendAndReceive(command)
        
        command = bytes([0xB0, 0x03, self.feMode.value, self.feChannel.value, self.feRange.value, 0xB0])
        self.SendAndReceive(command)
    
    
    def DevSetExtensionPortChannel(self, offset:int):
        
        if offset >= len(self.muxElConfig):
            raise IndexError("There are not enough configurations for this offset.")
        
        portBytes = self.muxElConfig[offset]
        
        command = bytes([0xB2, 0x04] + portBytes + [0xB2])
        self.SendAndReceive(command)
    

    def GetExtensionPortChannel(self) -> str:
        
        command = bytearray([0xB3, 0x00, 0xB3])
        msg = self.SendAndReceive(command)
        
        return list(msg[2:-1])
    
    
    def DevSetSetup(self):
        
        command = bytes([0xB6, 0x01, 0x01, 0xB6])
        self.SendAndReceive(command)
        
        command = bytes([0xB6, 0x25, 0x03])

        if self.fscale is FrequencyScale.Linear:
            freqScale = 0
        else:
            freqScale = 1
        # Required data bytes
        command += bytes(GetHexSingle(self.fmin) + GetHexSingle(self.fmax) + GetHexSingle(self.fnum) + [freqScale] + GetHex(self.precision) + GetHex(self.amplitude))
        
        # Optional data bytes
        command += bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00])
        
        if self.excitation is InjectionType.Voltage:
            command += bytes([0x01])
        else:
            command += bytes([0x02])
            
        # closing command tag
        command += bytes([0xB6])
        
        self.SendAndReceive(command)
    
    
    def DevGetSetup(self):
        pass
    
    def DevStartMeasurement(self):
        
        command = bytes([0xB8, 0x03, 0x01, 0x00, 0x01, 0xB8])
        self.SendAndReceive(command)
    
    
    def DeserializeResults(self, results:bytes) -> tuple[complex, int, CurrentRange, list]:
        
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
        
        zReal = list(results[(7 + lengthCurrent + lengthTime):(3 + lengthCurrent + lengthTime)])
        zImag = list(results[(11 + lengthCurrent + lengthTime):(8 + lengthTime + lengthCurrent)])
        impedance = zReal + 1j*zImag
        
        for possibleRange in CurrentRange:
            if possibleRange.value == currentRange:
                return impedance, warn, possibleRange, timeOffset

        return impedance, warn, None, timeOffset
    
    
    def GetMeasurements(self) -> tuple[list, list, list, list, list, list]:
        
        muxConfigLen = len(self.muxElConfig)
        resWarning = [[0 for x in range(muxConfigLen)] for y in range(self.fnum)]
        resImpedance = [[None for x in range(muxConfigLen)] for y in range(self.fnum)]
        resRange = [["" for x in range(muxConfigLen)] for y in range(self.fnum)]
        resTime = [[None for x in range(muxConfigLen)] for y in range(self.fnum)]
        
        counter = 0
        startTime = []
        finishTime = []
        
        for idxElChunks in range(math.ceil(muxConfigLen / 128)):
            
            if math.floor(muxConfigLen / (128 * idxElChunks)):
                numMeas = 128
            else:
                numMeas = muxConfigLen - 128 * (idxElChunks - 1)
                
            self.DevSetFeSettings()
            
            for j in range(numMeas):
                counter += 1
                self.DevSetExtensionPortChannel(counter)
                
            startTime.append(datetime.datetime.now().isoformat(" ", "seconds"))
            self.DevStartMeasurement()
            
            for measIdx in range(numMeas):
                for freqIdx in range(self.fnum):
                    results = self.ReadFrame()
                    impedance, warn, currentRange, timeOffset = self.DeserializeResults(results)
                    
                    resImpedance[measIdx + 128 * (idxElChunks - 1)][freqIdx] = impedance
                    resWarning[measIdx + 128 * (idxElChunks - 1)][freqIdx] = warn
                    resRange[measIdx + 128 * (idxElChunks - 1)][freqIdx] = currentRange
                    resTime[measIdx + 128 * (idxElChunks - 1)][freqIdx] = timeOffset
                    
            finishTime.append(datetime.datetime.now().isoformat(" ", "seconds"))
        
        return resImpedance, resWarning, resRange, resTime, startTime, finishTime
    
    
    def DoInitialSetup(self, fmin:float, fmax:float, fnum:int, fscale:FrequencyScale, channel:FeChannel, mode:FeMode, currRange:CurrentRange, precision:float, excitationType:InjectionType, excitationAmplitude:float, muxComb:list, timestamp:TimeStamp):
        
        self.SetFrequency(fmin, fmax, fnum, fscale)
        self.SetFeChannel(channel)
        self.SetFeMode(mode)
        self.SetRange(currRange)
        self.SetPrecision(precision)
        self.SetExcitationType(excitationType)
        self.SetExcitationAmplitude(excitationAmplitude)
        self.SetMuxChannels(muxComb)
        self.SetTimeStamp(timestamp)
        
        self.CheckSettings()
        self.DevSetSetup()
        self.DevSetOptions()
    
    
    def ResetSystem(self):
        
        command = bytes([0xA1, 0x00, 0xA1])
        self.SendAndReceive(command)
    
    
    def SaveSettings(self):
        
        command = bytes([0x90, 0x00, 0x90])
        self.SendAndReceive(command)
    
    
    def GetOptionsTimeStamp(self) -> (TimeStamp | None):
        
        command = bytes([0x98, 0x01, 0x01, 0x98])
        msg = self.SendAndReceive(command)
        
        for possibleTimeStamp in TimeStamp:
            if msg[3] == possibleTimeStamp.value:
                return possibleTimeStamp
        
        return None
    
    
    def GetFeSettings(self) -> tuple[FeMode | None, FeChannel | None, CurrentRange | None]:
        
        command = bytes([0xB1, 0x00, 0xB1])
        msg = self.SendAndReceive(command)
        
        # measurement mode
        mode = None
        for measMode in FeMode:
            if msg[2] == measMode.value:
                mode = measMode
                break
        
        # measurement channel
        channel = None
        for measChannel in FeChannel:
            if msg[3] == measChannel.value:
                channel = measChannel
                break
        
        # range
        currRange = None
        for possRange in CurrentRange:
            if msg[4] == possRange.value:
                currRange = possRange
                break
        
        return mode, channel, currRange
    
    
    def GetExtensionPortModule(self) -> tuple[ExternalModule | None, InternalModule | None, int | None, int | None]:
        
        command = bytes([0xB5, 0x00, 0xB5])
        msg = self.SendAndReceive(command)
        
        externalModule = None
        for extModule in ExternalModule:
            if msg[2] == extModule.value:
                externalModule = extModule
                break
        
        internalModule = None
        for intModule in InternalModule:
            if msg[3] == intModule.value:
                internalModule = intModule
                break
        
        channelCountExt = None
        channelCountInt = None
        if externalModule is ExternalModule.Mux32Any2Any2202:
            channelCountExt = msg[4]
            if internalModule is InternalModule.Mux32Any2Any2202:
                channelCountInt = msg[5]
        elif internalModule is InternalModule.Mux32Any2Any2202:
            channelCountInt = msg[4]
        
        return externalModule, internalModule, channelCountExt, channelCountInt
    
    # Get Setup functions
    def GetTotalNumberOfFrequencies(self):
        
        command = bytes([0xB7, 0x01, 0x01, 0xB7])
        msg = self.SendAndReceive(command)
        
        return int.from_bytes(msg[3:5], "big")
    
    
    def GetInformationOfFrequencyPoint(self, frequencyPoint:int):
        
        command = bytes([0xB7, 0x03]) + frequencyPoint.to_bytes(2, "big") + bytes([0xB7])
        msg = self.SendAndReceive(command)
        
        frequency = GetFloatFromBytes(msg[3:7])
        precision = GetFloatFromBytes(msg[7:11])
        amplitude = GetFloatFromBytes(msg[11:15])
        
        return frequency, precision, amplitude
    
    
    def GetFrequencyList(self):
        
        command = bytes([0xB7, 0x01, 0x04, 0xB7])
        msg = self.SendAndReceive(command)
        
        return [GetFloatFromBytes(msg[i:i+4]) for i in range(2, len(msg), 4)]
    
    
    def SaveSetupToSlot(self, slot:int):
        
        if slot < 1 or slot > 255:
            raise ValueError("Slot must be of one byte size.")
        
        command = bytes([0xB7, 0x02, 0x20, slot, 0xB7])
        self.SendAndReceive(command)
    
    
    def GetDCBias(self):
        
        command = bytes([0xB7, 0x01, 0x33, 0xB7])
        msg = self.SendAndReceive(command)
        
        return GetFloatFromBytes(msg[3:7])
    
    
    def GetSyncTime(self) -> int:
        
        command = bytes([0xBA, 0x00, 0xBA])
        msg = self.SendAndReceive(command)
        
        return int.from_bytes(msg[2:6], "big")
    
    
    def SetIPAddress(self, ipAddress:str = "0.0.0.0"):
        
        addressSubStrings = ipAddress.split(".")
        addressInts = [int(a) for a in addressSubStrings]
        
        command = bytes([0xBD, 0x05, 0x01] + addressInts + [0xBD])
        self.SendAndReceive(command)
    
    
    def SetDHCPSwitch(self, switch:bool):
        
        if switch:
            switchInt = 1
        else:
            switchInt = 0
        
        command = bytes([0xBD, 0x02, 0x03, switchInt, 0xBD])
        self.SendAndReceive(command)
    
    
    def GetIPAddress(self) -> str:
        
        command = bytes([0xBE, 0x01, 0x01, 0xBE])
        msg = self.SendAndReceive(command)
        
        return ".".join(list(msg[3:7]))
    
    
    def GetMACAddress(self) -> str:
        
        command = bytes([0xBE, 0x01, 0x02, 0xBE])
        msg = self.SendAndReceive(command)
        
        return msg[3:9].hex("-")
    
    
    def GetDHCPSwitch(self) -> bool:
        
        command = bytes([0xBE, 0x01, 0x03, 0xBE])
        msg = self.SendAndReceive(command)
        
        if msg[3] == 1:
            return True
        else:
            return False
    
    
    def TCPConnectionWatchdog(self, interval:int):
        
        command = bytes([0xCF, 0x05, 0x00]) + interval.to_bytes(4, "big") + bytes([0xCF])
        self.SendAndReceive(command)
    
    
    def GetARMFirmwareID(self) -> tuple[int]:
        
        command = bytes([0xD0, 0x00, 0xD0])
        msg = self.SendAndReceive(command)
        
        revisionNumber = int.from_bytes(msg[4, 5], "big")
        buildNumber = int.from_bytes(msg[6, 7], "big")
        
        return revisionNumber, buildNumber
    
    
    def GetDeviceID(self) -> tuple[int, int, int, int]:
        
        command = bytes([0xD1, 0x00, 0xD1])
        msg = self.SendAndReceive(command)
        
        version = msg[2]
        deviceID = int.from_bytes(msg[3, 4], "big")
        serialNumber = int.from_bytes(msg[5, 6], "big")
        deliveryDate = 2010 + int.from_bytes(msg[7, 8], "big")
        
        return version, deviceID, serialNumber, deliveryDate
    
    
    def GetFPGAFirmwareID(self) -> tuple[int, int]:
        
        command = bytes([0xD2, 0x00, 0xD2])
        msg = self.SendAndReceive(command)
        
        revisionNumber = int.from_bytes(msg[7, 8], "big")
        buildNumber = int.from_bytes(msg[9, 10], "big")
        
        return revisionNumber, buildNumber
    
    
    