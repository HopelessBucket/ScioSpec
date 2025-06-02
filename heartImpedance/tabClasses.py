from __future__ import annotations
import sys
import pathlib
import numpy as np
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QGridLayout
)
from PySide6.QtCore import Qt, Slot
from data_manager import EISData
from plots import MplCanvas
from ImpedanceAnalyser import ImpedanceAnalyser
from EnumClasses import InjectionType, CurrentRange, FrequencyScale, FeMode, FeChannel, TimeStamp, ExternalModule, InternalModule


class TimeseriesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data: EISData | None = None

        # Widgets
        self.canvas_mag = MplCanvas()
        self.canvas_phase = MplCanvas()
        self.cbo_quantity = QComboBox()
        self.cbo_quantity.addItems(["Impedanz", "Admittanz"])
        self.cbo_el = QComboBox()
        self.cbo_freq = QComboBox()

        # Layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Größe:"))
        top.addWidget(self.cbo_quantity)
        top.addWidget(QLabel("El. Comb.:"))
        top.addWidget(self.cbo_el)
        top.addWidget(QLabel("Frequenz:"))
        top.addWidget(self.cbo_freq)
        top.addStretch()

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas_mag, stretch=1)
        lay.addWidget(self.canvas_phase, stretch=1)

        # Signals
        self.cbo_quantity.currentIndexChanged.connect(self.repaint_plots)
        self.cbo_el.currentIndexChanged.connect(self.repaint_plots)
        self.cbo_freq.currentIndexChanged.connect(self.repaint_plots)

    # ------------------------------------------------------------------ #
    def set_data(self, data: EISData):
        self.data = data
        # Kombinations‑/Frequenz‑Dropdowns befüllen
        self.cbo_el.clear()
        el = (
            np.unique(data.electrodes[:, 0])
            if data.electrodes is not None
            else np.arange(1)
        )
        self.cbo_el.addItems([str(int(x)) for x in el])

        self.cbo_freq.clear()
        self.cbo_freq.addItems([f"{f:.3g}" for f in data.frequency])
        self.repaint_plots()

    # ------------------------------------------------------------------ #
    @Slot()
    def repaint_plots(self):
        if self.data is None:
            return
        idx_f = self.cbo_freq.currentIndex()
        idx_el = self.cbo_el.currentIndex()
        z = self.data.impedance.reshape(-1, len(self.data.frequency))
        z = z[idx_el, idx_f]

        ydata = 1 / z if self.cbo_quantity.currentText() == "Admittanz" else z
        self.canvas_mag.clear()
        self.canvas_phase.clear()

        self.canvas_mag.axes.set_xlabel("Zeitindex")
        self.canvas_mag.axes.set_ylabel("|{}|".format(self.cbo_quantity.currentText()))
        self.canvas_phase.axes.set_xlabel("Zeitindex")
        self.canvas_phase.axes.set_ylabel("Phase [°]")

        self.canvas_mag.axes.plot(self.data.time, np.abs(ydata))
        self.canvas_phase.axes.plot(self.data.time, np.angle(ydata, deg=True))
        self.canvas_mag.draw_idle()
        self.canvas_phase.draw_idle()


class SpectraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data: EISData | None = None

        # Controls
        self.canvas = MplCanvas()
        self.cbo_quantity = QComboBox()
        self.cbo_quantity.addItems(["Impedanz", "Admittanz"])
        self.cbo_el = QComboBox()
        self.cbo_time = QComboBox()

        # Layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Größe:"))
        top.addWidget(self.cbo_quantity)
        top.addWidget(QLabel("El. Comb.:"))
        top.addWidget(self.cbo_el)
        top.addWidget(QLabel("Zeitindex:"))
        top.addWidget(self.cbo_time)
        top.addStretch()

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas, stretch=1)

        # Signals
        self.cbo_quantity.currentIndexChanged.connect(self.repaint_plot)
        self.cbo_el.currentIndexChanged.connect(self.repaint_plot)
        self.cbo_time.currentIndexChanged.connect(self.repaint_plot)

    def set_data(self, data: EISData):
        self.data = data
        self.cbo_el.clear()
        n_comb = (
            np.unique(data.electrodes[:, 0])
            if data.electrodes is not None
            else np.arange(1)
        )
        self.cbo_el.addItems([str(int(x)) for x in n_comb])
        self.cbo_time.clear()
        self.cbo_time.addItems([str(i) for i in range(len(data.time))])
        self.repaint_plot()

    @Slot()
    def repaint_plot(self):
        if self.data is None:
            return
        idx_el = self.cbo_el.currentIndex()
        idx_t = self.cbo_time.currentIndex()
        z = self.data.impedance.reshape(-1, len(self.data.frequency))
        z = z[idx_el, :]
        if self.cbo_quantity.currentText() == "Admittanz":
            z = 1.0 / z
        self.canvas.bode(self.data.frequency, z, show_admitt=self.cbo_quantity.currentText() == "Admittanz")


class DerivedTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data: EISData | None = None
        # Controls
        self.canvas = MplCanvas()
        self.cbo_value = QComboBox()
        self.cbo_value.addItems(["|Z|", "|Y|", "Phase(Z)", "Phase(Y)"])
        self.cbo_el = QComboBox()
        self.cbo_freq = QComboBox()
        # Layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Wert:"))
        top.addWidget(self.cbo_value)
        top.addWidget(QLabel("El. Comb.:"))
        top.addWidget(self.cbo_el)
        top.addWidget(QLabel("Frequenz:"))
        top.addWidget(self.cbo_freq)
        top.addStretch()
        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas, stretch=1)
        # Signals
        self.cbo_value.currentIndexChanged.connect(self.repaint_plot)
        self.cbo_el.currentIndexChanged.connect(self.repaint_plot)
        self.cbo_freq.currentIndexChanged.connect(self.repaint_plot)

    def set_data(self, data: EISData):
        self.data = data
        self.cbo_el.clear()
        n_comb = (
            np.unique(data.electrodes[:, 0])
            if data.electrodes is not None
            else np.arange(1)
        )
        self.cbo_el.addItems([str(int(x)) for x in n_comb])
        self.cbo_freq.clear()
        self.cbo_freq.addItems([f"{f:.3g}" for f in data.frequency])
        self.repaint_plot()

    @Slot()
    def repaint_plot(self):
        if self.data is None:
            return
        idx_el = self.cbo_el.currentIndex()
        idx_f = self.cbo_freq.currentIndex()
        z = self.data.impedance.reshape(-1, len(self.data.frequency))
        z = z[idx_el, idx_f]

        mapping = {
            "|Z|": np.abs(z),
            "|Y|": np.abs(1 / z),
            "Phase(Z)": np.angle(z, deg=True),
            "Phase(Y)": np.angle(1 / z, deg=True),
        }
        y = mapping[self.cbo_value.currentText()]

        self.canvas.clear()
        self.canvas.axes.set_xlabel("Zeitindex")
        self.canvas.axes.set_ylabel(self.cbo_value.currentText())
        self.canvas.axes.plot(self.data.time, y)
        self.canvas.draw_idle()

class SettingsTab(QWidget):
    def __init__(self, impedanceAnalyser:ImpedanceAnalyser):
        super().__init__()
        self.data: EISData | None = None
        self.impedanceAnalyser = impedanceAnalyser
        # Controls
        self.lineFreqMin = QLineEdit(text="1000")
        self.lineFreqMax = QLineEdit(text="1000000")
        self.lineFreqNum = QLineEdit(text="10")
        self.comboFreqScale = QComboBox()
        self.comboFreqScale.addItems(["linear", "logarithmic"])
        self.comboChannel = QComboBox()
        self.comboChannel.addItems(["BNC", "ExtensionPort", "InternalMux"])
        self.comboMode = QComboBox()
        self.comboMode.addItems(["4 point configuration", "3 point configuration", "2 point configuration"])
        self.comboRange = QComboBox()
        self.comboRange.addItems(["Auto", "10mA", "100uA", "1uA", "10nA"])
        self.linePrecision = QLineEdit(text="1")
        self.comboExcitation = QComboBox()
        self.comboExcitation.addItems(["voltage", "current"])
        self.lineAmplitude = QLineEdit(text="0.5")
        self.comboTimestamp = QComboBox()
        self.comboTimestamp.addItems(["off", "ms", "us"])
        
        # Buttons for get commands 
        self.freqMaxGet = QPushButton("Get current frequencies")
        self.freqMaxGet.clicked.connect(self.GetSettingsFreq)
        self.modeGet = QPushButton("Get current FE settings")
        self.modeGet.clicked.connect(self.GetSettingsFe)
        self.precisionGet = QPushButton("Get current precision and amplitude")
        self.precisionGet.clicked.connect(self.GetSettingsPrecAmp)
        self.timestampGet = QPushButton("Get current timestamp")
        self.timestampGet.clicked.connect(self.GetSettingsTimestamp)
        self.setSettings = QPushButton("Set current settings")
        self.setSettings.clicked.connect(self.SetSettings)
        # Layout
        formLayout = QGridLayout(self)
        formLayout.addWidget(QLabel("Min Frequency[Hz]:"), 0, 0)
        formLayout.addWidget(self.lineFreqMin, 0, 1)
        formLayout.addWidget(QLabel("Max Frequency[Hz]:"), 1, 0)
        formLayout.addWidget(self.lineFreqMax, 1, 1)
        formLayout.addWidget(self.freqMaxGet, 1, 2)
        formLayout.addWidget(QLabel("Number of frequencies:"), 2, 0)
        formLayout.addWidget(self.lineFreqNum, 2, 1)
        formLayout.addWidget(QLabel("Frequency scale:"), 3, 0)
        formLayout.addWidget(self.comboFreqScale, 3, 1)
        formLayout.addWidget(QLabel("Measurement channel:"), 4, 0)
        formLayout.addWidget(self.comboChannel, 4, 1)
        formLayout.addWidget(QLabel("Measurement mode:"), 5, 0)
        formLayout.addWidget(self.comboMode, 5, 1)
        formLayout.addWidget(self.modeGet, 5, 2)
        formLayout.addWidget(QLabel("Current range:"), 6, 0)
        formLayout.addWidget(self.comboRange, 6, 1)
        formLayout.addWidget(QLabel("Excitation type:"), 7, 0)
        formLayout.addWidget(self.comboExcitation, 7, 1)
        formLayout.addWidget(QLabel("Precision:"), 8, 0)
        formLayout.addWidget(self.linePrecision, 8, 1)
        formLayout.addWidget(self.precisionGet, 8, 2)
        formLayout.addWidget(QLabel("Excitation amplitude:"), 9, 0)
        formLayout.addWidget(self.lineAmplitude, 9, 1)
        formLayout.addWidget(QLabel("Timestamp:"), 10, 0)
        formLayout.addWidget(self.comboTimestamp, 10, 1)
        formLayout.addWidget(self.timestampGet, 10, 2)
        formLayout.addWidget(self.setSettings, 11, 1)
    
    @Slot()
    def SetSettings(self):
        
        self.impedanceAnalyser.DoInitialSetup(  float(self.lineFreqMin.text()), 
                                                float(self.lineFreqMax.text()), 
                                                int(self.lineFreqNum.text()), 
                                                FrequencyScale[self.comboFreqScale.currentText().lower()], 
                                                FeChannel[self.comboChannel.currentText()], 
                                                FeMode[f"mode{self.comboMode.currentText()[0]}pt"], 
                                                CurrentRange[f"range{self.comboRange.currentText()}"], 
                                                float(self.linePrecision.text()), 
                                                InjectionType[self.comboExcitation.currentText()], 
                                                float(self.lineAmplitude.text()), 
                                                TimeStamp[self.comboTimestamp.currentText()])
    @Slot()
    def GetSettingsFreq(self):

        fList = self.impedanceAnalyser.GetFrequencyList()
        self.lineFreqMin.setText(f"{fList[0]}")
        self.lineFreqMax.setText(f"{fList[-1]}")
        self.lineFreqNum.setText(f"{len(fList)}")
    
    def GetSettingsFe(self):
        
        mode, channel, currRange = self.impedanceAnalyser.GetFeSettings()
        self.comboMode.setCurrentText(f"{mode.name[4]} point configuration")
        self.comboChannel.setCurrentText(channel.name)
        self.comboRange.setCurrentText(currRange.name.replace("range",""))
    
    def GetSettingsPrecAmp(self):
        
        frequency, precision, amplitude = self.impedanceAnalyser.GetInformationOfFrequencyPoint(0)
        self.lineFreqMin.setText(f"{frequency}")
        self.linePrecision.setText(f"{precision}")
        self.lineAmplitude.setText(f"{amplitude}")
    
    def GetSettingsTimestamp(self):
        
        self.comboTimestamp.setCurrentText(self.impedanceAnalyser.GetOptionsTimeStamp().value)