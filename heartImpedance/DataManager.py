#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_manager.py
Lädt ISX‑3‑Messdaten (.mat oder .spec) in pandas‑DataFrames.
"""
from __future__ import annotations
import pathlib
import numpy as np
import pandas as pd
from scipy.io import loadmat
import h5py


class EISData:
    """Container für eine einzelne Messung."""
    
    index = 1

    def __init__(
        self,
        timeStamp: np.ndarray,
        frequencies: np.ndarray,
        electrodes: np.ndarray | None = None,
        realParts: np.ndarray | None = None,
        imagParts: np.ndarray | None = None,
        impedances: np.ndarray | None = None, 
        startTime: str | None = None,
        finishTime: str | None = None
    ):
        self.timeStamps = np.asarray(timeStamp)
        self.frequencies = np.asarray(frequencies).ravel()  # list[float]
        if realParts and imagParts:
            self.impedances = np.asarray([[complex(realParts[i][x], imagParts[i][x]) for x in range(len(frequencies))] for i in range(len(electrodes))]) # list[list[complex]]
            self.realParts = np.asarray(realParts)        # list[list[float]]
            self.imagParts = np.asarray(imagParts)        # list[list[float]]
        elif impedances:
            self.impedances = impedances          
            self.realParts = np.real(impedances)
            self.imagParts = np.imag(impedances) 
        self.electrodes = electrodes                    # list[list[int]]
        self.startTime = startTime                      # str
        self.finishTime = finishTime                    # str
        self.startTimeShort = startTime.split(" ")[1]
        self.finishTimeShort = finishTime.split(" ")[1]
        self.measurementIndex = EISData.index           # int
        EISData.index += 1
        # print(f"Frequencies: {self.frequencies}")
        # print(f"Electrodes{electrodes}")
        # print(f"RealPart: {realParts}")
        # print(f"ImagPart: {imagParts}")
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


# ---------------------------------------------------------------------- #
#  .mat‑Loader – kompatibel zu Measurement_Script_new.m                  #
# ---------------------------------------------------------------------- #
def _load_mat_file(path: pathlib.Path) -> EISData:
    try:
        dat = loadmat(path, squeeze_me=True)
    except NotImplementedError:
        with h5py.File(path, "r") as f:
            dat = {k: f[k][()] for k in f.keys()}

    # Erforderliche Variablen laut originalem Skript
    z = _to_complex(dat.get("resImpedColumn"))
    fvec = dat.get("resFrequencies")
    t = dat.get("resTimeOffset") or np.arange(z.shape[0])
    el = dat.get("resElectrodes")

    return EISData(timeStamp=t, frequencies=fvec, impedances=z, electrodes=el)


def _to_complex(vec):
    """Falls Real + Imag separat vorliegen, zusammenführen."""
    vec = np.asarray(vec)
    if vec.ndim == 2 and vec.shape[1] == 2:
        return vec[:, 0] + 1j * vec[:, 1]
    return vec.astype(np.complex128)


# ---------------------------------------------------------------------- #
#  Dispatcher – erkennt Dateityp                                         #
# ---------------------------------------------------------------------- #
def load_measurement(file_path: pathlib.Path) -> EISData:
    ext = file_path.suffix.lower()
    if ext == ".mat":
        return _load_mat_file(file_path)
    elif ext == ".spec":
        return _load_spec(file_path)
    else:
        raise ValueError(f"Unbekanntes Dateiformat: {file_path}")


# ---------------------------------------------------------------------- #
#  .spec (ASCII)‑Loader                                                  #
# ---------------------------------------------------------------------- #
def _load_spec(path: pathlib.Path) -> EISData:
    with open(path, encoding="utf-8") as f:
        header_rows = int(f.readline())
    df = pd.read_csv(path, skiprows=header_rows, sep=",")
    time = df["Time"].to_numpy()
    freq = df["Frequency"].to_numpy()
    z = df["Zreal"].to_numpy() + 1j * df["Zimag"].to_numpy()
    return EISData(timeStamp=time, frequencies=freq, impedances=z)