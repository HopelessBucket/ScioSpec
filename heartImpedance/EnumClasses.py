from enum import Enum

class InjectionType(Enum):
    voltage = 0x01
    current = 0x02

class CurrentRange(Enum):
    rangeAuto = 0x00
    range10mA =  0x01
    range100uA = 0x02
    range1uA = 0x04
    range10nA = 0x06

class FrequencyScale(Enum):
    logarithmic = 0x01
    linear = 0x00
    
class FeMode(Enum):
    mode2pt = 0x01
    mode3pt = 0x03
    mode4pt = 0x02
    
class FeChannel(Enum):
    BNC = 0x01
    ExtensionPort = 0x02
    InternalMux = 0x03
    
class TimeStamp(Enum):
    off = "off"
    ms = "ms"
    us = "us"

class ExternalModule(Enum):
    NoModule = 0x00
    MEArack = 0x01
    MuxModule32 = 0x02
    ECISAdapter = 0x03
    ExtPAdapter = 0x05
    SlideChipAdapter = 0x06
    Mux32Any2Any = 0x07
    DaQEisMux = 0x08
    Mux32Any2Any2202 = 0x09

class InternalModule(Enum):
    NoModule = 0x00
    MuxModule16x4 = 0x01
    MuxModule32x2 = 0x02
    Mux32Any2Any = 0x07
    Mux32Any2Any2202 = 0x09


