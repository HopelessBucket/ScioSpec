from EnumClasses import CurrentRange, InjectionType

def CalculateValidImpedanceRange(injectionType:InjectionType, injectionValue, injectionCurrentRange:CurrentRange) -> tuple[float, float, float]:
    zMin = 0
    zMax = float("inf")
    
    match injectionCurrentRange:
        case CurrentRange.range10mA:
            currRange = 10e-3
        case CurrentRange.range100uA:
            currRange = 100e-6
        case CurrentRange.range1uA:
            currRange = 1e-6
        case CurrentRange.range10nA:
            currRange = 10e-9
        case _:
            raise ValueError("Invalid injectionCurrentRange.")
    
    iMax = 0.01
    uMax = 1
    
    if injectionType == InjectionType.current:
        if injectionValue > iMax:
            raise Exception("Requested injection current is too large.")
        zMax = uMax / injectionValue
    
    elif injectionType == InjectionType.voltage:
        if injectionValue > uMax:
            raise Exception("Requested injection voltage is too large.")
        
        if currRange is None:
            zMin = injectionValue / iMax
        else:
            zMin = max(injectionValue / iMax, injectionValue / currRange)
    
    else:
        raise TypeError("No other injection types are possible.")
    
    print(f"Impedance range: [{zMin}, {zMax}]")
    
    return zMin, zMax