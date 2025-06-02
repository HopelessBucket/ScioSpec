import itertools, struct

def GenElectrodeConf(electrodes:list = [], ordered:bool = True) -> list[list[int]]:
    
    if not electrodes:
        electrodes = list(range(1, 6))
    
    if ordered:
        return list(itertools.combinations(electrodes, 4))
    else:
        perms = []
        for combination in itertools.combinations(electrodes, 4):
            for permutation in itertools.permutations(combination):
                perms.append(permutation)
        return perms

def GetHex(freq) -> list[int]:
    
    h = hex(struct.unpack("!q", struct.pack("!d", freq))[0])
    word = [h[i:i+2] for i in range(2, len(h), 2)]
    retval = [int(x, 16) for x in word]
    
    return retval

def GetHexSingle(freq) -> list[int]:

    packed = struct.pack('!f', float(freq))
    h = ''.join(f'{byte:02x}' for byte in packed)
    word = [h[i:i+2] for i in range(0, len(h), 2)]
    retval = [int(x, 16) for x in word]
    
    return retval

def GetFloatFromBytes(bytedFloat:bytes) -> float:
    
    print(list(bytedFloat))
    return struct.unpack("!f", bytedFloat)
