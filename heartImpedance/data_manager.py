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
from scipy.io import loadmat, matlab as _mlab
import h5py
from typing import List, Tuple


class EISData:
    """Container für eine einzelne Messung."""

    def __init__(
        self,
        time: np.ndarray,
        frequency: np.ndarray,
        impedance: np.ndarray,
        electrodes: np.ndarray | None = None,
    ):
        self.time = np.asarray(time).ravel()
        self.frequency = np.asarray(frequency).ravel()
        self.impedance = np.asarray(impedance)
        self.electrodes = electrodes

    # ------------------------------------------------------------------ #
    #  Helper: |Z|, Phase, Admittance                                    #
    # ------------------------------------------------------------------ #
    @property
    def magnitude(self) -> np.ndarray:
        return np.abs(self.impedance)

    @property
    def phase(self) -> np.ndarray:
        return np.angle(self.impedance, deg=True)

    @property
    def admittance(self) -> np.ndarray:
        with np.errstate(divide="ignore", invalid="ignore"):
            y = 1.0 / self.impedance
            y[np.isinf(y)] = np.nan
        return y


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

    return EISData(time=t, frequency=fvec, impedance=z, electrodes=el)


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
    return EISData(time=time, frequency=freq, impedance=z)