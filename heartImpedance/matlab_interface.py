#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
matlab_interface.py
Startet MATLAB – ruft Measurement_Script_new.m auf – liefert Pfad der Ergebnisdatei(en).
"""
from __future__ import annotations
import pathlib
import tempfile
import matlab.engine
from datetime import datetime
from typing import Sequence, Union


class MatlabBridge:
    def __init__(self):
        self._eng = None

    # --------------------------------------------------------------------- #
    #  Verbindung zu MATLAB herstellen / beenden                            #
    # --------------------------------------------------------------------- #
    def start(self, reuse: bool = True) -> None:
        """MATLAB‑Engine starten (oder bestehende Sitzungen wiederverwenden)."""
        if reuse:
            for sess in matlab.engine.find_matlab():
                self._eng = matlab.engine.connect_matlab(sess)  # type: ignore
                break
        if self._eng is None:
            self._eng = matlab.engine.start_matlab()  # type: ignore
        self._eng.addpath(self._eng.genpath(str(pathlib.Path(__file__).parent)))

    def stop(self) -> None:
        if self._eng:
            self._eng.quit()
            self._eng = None

    # --------------------------------------------------------------------- #
    #  Messung (oder Simulation)                                            #
    # --------------------------------------------------------------------- #
    def run_measurement(
        self,
        script: Union[str, pathlib.Path] = "Measurement_Script_new.m",
        simulate: bool = False,
    ) -> Sequence[pathlib.Path]:
        """
        Ruft ein MATLAB‑Skript auf.
        Gibt die .mat‑Dateien zurück, die während des Aufrufs erzeugt wurden.
        """
        if self._eng is None:
            self.start()

        # Parameter ins MATLAB‑Workspace
        self._eng.workspace["simulateHardware"] = bool(simulate)

        # Temporäres Ergebnis‑Verzeichnis anlegen
        result_dir = pathlib.Path(tempfile.mkdtemp(prefix="eis_gui_"))
        self._eng.workspace["root_folder"] = str(result_dir)
        self._eng.workspace["meas_name"] = datetime.now().strftime("Run_%Y%m%dT%H%M%S")

        # Skript ausführen
        self._eng.eval(f"run('{script}')", nargout=0)

        # Aufzeichnen, was erzeugt wurde
        created = list(result_dir.glob("**/*.mat"))
        return created


# Komfort‑Funktion (für externen Import)
_bridge: MatlabBridge | None = None


def get_matlab_bridge() -> MatlabBridge:
    global _bridge
    if _bridge is None:
        _bridge = MatlabBridge()
        _bridge.start()
    return _bridge