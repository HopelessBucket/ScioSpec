from EnumClasses import CurrentRange, InjectionType

def CalculateValidImpedanceRange(injectionType:InjectionType, injectionValue, injectionCurrentRange:CurrentRange) -> tuple[float, float, float]:
    zMin = 0
    zMax = float("inf")
    
    match injectionCurrentRange:
        case CurrentRange.Auto:
            currRange = None
        case CurrentRange.Select10mA:
            currRange = 10e-3
        case CurrentRange.Select100uA:
            currRange = 100e-6
        case CurrentRange.Select1uA:
            currRange = 1e-6
        case CurrentRange.Select10nA:
            currRange = 10e-9
        case _:
            raise Exception("Invalid injectionCurrentRange.")
        
    iMax = 0.01
    uMax = 1
    
    if injectionType == InjectionType.Current:
        if injectionValue > iMax:
            raise Exception("Requested injection current is too large.")
        Zmax = uMax / injectionValue
        
    elif injectionType == InjectionType.Voltage:
        if injectionValue > uMax:
            raise Exception("Requested injection voltage is too large.")
        
        if currRange is None:
            zMin = injectionValue / iMax
        else:
            zMin = max(injectionValue / iMax, injectionValue / currRange)
    
    else:
        raise Exception("No other injection types are possible.")
    
    print(f"Impedance range: [{zMin}, {zMax}]")
    
    return zMin, zMax