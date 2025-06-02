#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plots.py
Gemeinsame Matplotlib‑Hilfsfunktionen für Qt‑Widgets.
"""
from __future__ import annotations
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from PySide6.QtWidgets import QSizePolicy


class MplCanvas(FigureCanvas):
    def __init__(self, dpi: int = 100):
        fig = Figure(dpi=dpi, tight_layout=True)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # ------------------------------------------------------------------ #
    #  Plot Utilities                                                    #
    # ------------------------------------------------------------------ #
    def clear(self):
        self.axes.cla()
        self.draw_idle()

    def bode(self, freq: np.ndarray, z: np.ndarray, show_admitt: bool = False):
        self.clear()
        mag_ax = self.axes
        phase_ax = mag_ax.twinx()

        if show_admitt:
            z = 1.0 / z
            mag_label = "|Y| [S]"
        else:
            mag_label = "|Z| [Ω]"

        mag_ax.set_xscale("log")
        mag_ax.set_xlabel("Frequenz [Hz]")
        mag_ax.set_ylabel(mag_label)
        phase_ax.set_ylabel("Phase [°]")

        mag_ax.plot(freq, np.abs(z))
        phase_ax.plot(freq, np.angle(z, deg=True), linestyle="--")

        self.draw_idle()