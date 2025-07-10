from __future__ import annotations
import numpy as np
import pandas as pd
import ast

class EISData:
    """Class acting as container for measurement data

    Returns:
        _type_: _description_
    """
    # Measurement index as static variable, increases after each instantiation of this class
    index = 1

    def __init__(
        self,
        timeStamp: list[list[float | None]],
        frequencies: list[float],
        electrodes: list[list[int]] | None = None,
        realParts: list[list[float]] | None = None,
        imagParts: list[list[float]] | None = None,
        impedances: list[list[complex]] | None = None, 
        startTime: str | None = None,
        finishTime: str | None = None
    ):
        self.timeStamps = np.asarray(timeStamp)
        self.frequencies = np.asarray(frequencies).ravel()  # list[float]
        if realParts and imagParts:
            self.impedances = np.asarray([[complex(realParts[i][x], imagParts[i][x]) for x in range(len(frequencies))] for i in range(len(electrodes))]) # list[list[complex]]
            self.realParts = np.asarray(realParts)
            self.imagParts = np.asarray(imagParts)
        elif impedances:
            self.realParts = np.asarray([[impedances[i][x].real for x in range(len(frequencies))] for i in range(len(electrodes))])
            self.imagParts = np.asarray([[impedances[i][x].imag for x in range(len(frequencies))] for i in range(len(electrodes))])
            self.impedances = np.asarray(impedances)         
        self.electrodes = electrodes
        self.startTime = startTime
        self.finishTime = finishTime
        self.startTimeShort = startTime.split(" ")[1]
        self.finishTimeShort = finishTime.split(" ")[1]
        self.measurementIndex = EISData.index
        EISData.index += 1
        # Debug
        # print(f"Frequencies: {self.frequencies}")
        # print(f"Electrodes{self.electrodes}")
        # print(f"RealPart: {self.realParts}")
        # print(f"ImagPart: {self.imagParts}")
        # print(f"Time: {self.timeStamps}")
        # print(f"Impedance: {self.impedances}")
        # print(f"StartTime: {self.startTime}")
        # print(f"FinishTime: {self.finishTime}")

    # ------------------------------------------------------------------ #
    #  Helper: |Z|, Phase, Admittance                                    #
    # ------------------------------------------------------------------ #
    @property
    def magnitudesZ(self) -> np.ndarray:
        return np.abs(self.impedances)

    @property
    def phasesZ(self) -> np.ndarray:
        return np.angle(self.impedances, deg=True)

    @property
    def admittances(self) -> np.ndarray:
        with np.errstate(divide="ignore", invalid="ignore"):
            y = 1.0 / self.impedances
            y[np.isinf(y)] = np.nan
        return y
    
    @property
    def magnitudesY(self) -> np.ndarray:
        return np.abs(self.admittances)
    
    @property
    def phasesY(self) -> np.ndarray:
        return np.angle(self.admittances, deg=True)

    def SaveToDataframe(self) -> pd.DataFrame:
    
        dfRows = []
        for elIndex, elComb in enumerate(self.electrodes):
            for freqIndex, frequency in enumerate(self.frequencies):
                dfRows.append([self.measurementIndex, str(elComb), frequency, self.impedances[elIndex][freqIndex], self.timeStamps[elIndex][freqIndex], self.startTime, self.finishTime])
        return pd.DataFrame(dfRows, columns=["MeasurementIndex", "Electrodes", "Frequency", "Impedance", "Timestamp", "StartTime", "FinishTime"])

def LoadFromDataframe(df:pd.DataFrame) -> EISData:
    
    electrodes = list(set(df["Electrodes"].to_list()))
    electrodes = [ast.literal_eval(electrodes[i]) for i in range(len(electrodes))]
    frequencies = list(set(df["Frequency"].to_list()))
    impedances = [list(map(complex, df["Impedance"].to_list()[i:i+len(frequencies)])) for i in range(0, df.shape[0], len(frequencies))]
    timestamps = [df["Timestamp"].to_list()[i:i+len(frequencies)] for i in range(0, df.shape[0], len(frequencies))]
    startTime = df["StartTime"][0]
    finishTime = df["FinishTime"][0]
    
    data =  EISData( timeStamp=timestamps, 
                    frequencies=frequencies, 
                    electrodes=electrodes, 
                    impedances=impedances, 
                    startTime=startTime,
                    finishTime=finishTime)
    data.measurementIndex = df["MeasurementIndex"][0]
    
    return data