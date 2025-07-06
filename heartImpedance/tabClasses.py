from __future__ import annotations
import numpy as np
import pyqtgraph as pg
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QListWidget, QListWidgetItem, QGridLayout, QButtonGroup, QMessageBox, QRadioButton

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
from DataManager import EISData
from Plots import MplCanvas
from ImpedanceAnalyser import ImpedanceAnalyser
from EnumClasses import InjectionType, CurrentRange, FrequencyScale, FeMode, FeChannel, TimeStamp


class TimeseriesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data: EISData | None = None

        # Widgets
        self.canvas_mag = MplCanvas()
        self.canvas_phase = MplCanvas()
        self.cbo_quantity = QComboBox()
        self.cbo_quantity.addItems(["Impedance", "Admittance"])
        self.cbo_el = QComboBox()
        self.cbo_freq = QComboBox()
        self.comboBoxMeasurement = QComboBox()

        # Layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Measurand:"))
        top.addWidget(self.cbo_quantity)
        top.addWidget(QLabel("Electrodes:"))
        top.addWidget(self.cbo_el)
        top.addWidget(QLabel("Frequency:"))
        top.addWidget(self.cbo_freq)
        top.addStretch()
        top.addWidget(QLabel("Measurement:"))
        top.addWidget(self.comboBoxMeasurement)

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
        self.cbo_el.addItems([str(x) for x in data.electrodes])

        self.cbo_freq.clear()
        self.cbo_freq.addItems([f"{f:.3g}" for f in data.frequencies])
        self.repaint_plots()

    # ------------------------------------------------------------------ #
    @Slot()
    def repaint_plots(self):
        if self.data is None:
            return
        idx_f = self.cbo_freq.currentIndex()
        idx_el = self.cbo_el.currentIndex()
        z = self.data.impedances.reshape(-1, len(self.data.frequencies))
        z = z[idx_el, idx_f]

        ydata = 1 / z if self.cbo_quantity.currentText() == "Admittanz" else z
        self.canvas_mag.clear()
        self.canvas_phase.clear()

        self.canvas_mag.axes.set_xlabel("Zeitindex")
        self.canvas_mag.axes.set_ylabel("|{}|".format(self.cbo_quantity.currentText()))
        self.canvas_phase.axes.set_xlabel("Zeitindex")
        self.canvas_phase.axes.set_ylabel("Phase [°]")

        self.canvas_mag.axes.plot(self.data.timeStamps, np.abs(ydata))
        self.canvas_phase.axes.plot(self.data.timeStamps, np.angle(ydata, deg=True))
        self.canvas_mag.draw_idle()
        self.canvas_phase.draw_idle()


class SpectraTab(QWidget):
    def __init__(self):
        super().__init__()
        self.currentData: EISData | None = None
        self.savedData: list[EISData] = []

        # Controls
        self.canvas = MplCanvas()
        self.cbo_quantity = QComboBox()
        self.cbo_quantity.addItems(["Impedance", "Admittance"])
        self.cbo_el = QComboBox()
        self.cbo_measurement = QComboBox()

        # Layout
        top = QHBoxLayout()
        top.addWidget(QLabel("Measurand:"))
        top.addWidget(self.cbo_quantity)
        top.addWidget(QLabel("Electrodes:"))
        top.addWidget(self.cbo_el)
        top.addWidget(QLabel("Measurement:"))
        top.addWidget(self.cbo_measurement)
        top.addStretch()

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas, stretch=1)

        # Signals
        self.cbo_quantity.currentIndexChanged.connect(self.repaint_plot)
        self.cbo_el.currentIndexChanged.connect(self.repaint_plot)
        self.cbo_measurement.currentIndexChanged.connect(self.repaint_plot)

    def set_data(self, data: EISData):
        self.currentData = data
        self.cbo_el.clear()
        self.cbo_el.addItems([str(x) for x in data.electrodes])
        self.cbo_measurement.clear()
        self.cbo_measurement.addItems(f"{data.measurementIndex}: {data.startTime} - {data.finishTime}")
        self.repaint_plot()

    @Slot()
    def repaint_plot(self):
        if self.currentData is None:
            return
        idx_el = self.cbo_el.currentIndex()
        idx_t = self.cbo_measurement.currentIndex()
        z = self.currentData.impedances.reshape(-1, len(self.currentData.frequencies))
        z = z[idx_el, :]
        self.canvas.bode(self.currentData.frequencies, z, show_admitt=self.cbo_quantity.currentText() == "Admittanz")


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
        self.cbo_el.addItems([str(x) for x in data.electrodes])
        self.cbo_freq.clear()
        self.cbo_freq.addItems([f"{f:.3g}" for f in data.frequencies])
        self.repaint_plot()

    @Slot()
    def repaint_plot(self):
        if self.data is None:
            return
        idx_el = self.cbo_el.currentIndex()
        idx_f = self.cbo_freq.currentIndex()
        z = self.data.impedances.reshape(-1, len(self.data.frequencies))
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
        self.canvas.axes.plot(self.data.timeStamps, y)
        self.canvas.draw_idle()

class SettingsTab(QWidget):
    def __init__(self, impedanceAnalyser:ImpedanceAnalyser):
        super().__init__()
        self.impedanceAnalyser = impedanceAnalyser
        # Controls
        self.lineFreqMin = QLineEdit(text="1000")
        self.lineFreqMin.setFixedWidth(100)
        self.lineFreqMax = QLineEdit(text="1000000")
        self.lineFreqMax.setFixedWidth(100)
        self.lineFreqNum = QLineEdit(text="10")
        self.lineFreqNum.setFixedWidth(100)
        self.comboFreqScale = QComboBox()
        self.comboFreqScale.addItems(["linear", "logarithmic"])
        self.comboChannel = QComboBox()
        self.comboChannel.addItems(["BNC", "ExtensionPort", "InternalMux"])
        self.comboMode = QComboBox()
        self.comboMode.addItems(["4 point configuration", "3 point configuration", "2 point configuration"])
        self.comboRange = QComboBox()
        self.comboRange.addItems(["10mA", "100uA", "1uA", "10nA"])
        self.linePrecision = QLineEdit(text="1")
        self.comboExcitation = QComboBox()
        self.comboExcitation.addItems(["voltage", "current"])
        self.lineAmplitude = QLineEdit(text="0.5")
        self.comboTimestamp = QComboBox()
        self.comboTimestamp.addItems(["off", "ms", "us"])
        
        self.inputElComb1 = QLineEdit(text="1")
        self.inputElComb1.setFixedWidth(50)
        self.inputElComb2 = QLineEdit(text="2")
        self.inputElComb2.setFixedWidth(50)
        self.inputElComb3 = QLineEdit(text="3")
        self.inputElComb3.setFixedWidth(50)
        self.inputElComb4 = QLineEdit(text="4")
        self.inputElComb4.setFixedWidth(50)
        
        self.addCombButton = QPushButton("Add")
        self.addCombButton.clicked.connect(self.AddElectrodeCombination)
        self.removeButton = QPushButton("Remove")
        self.removeButton.clicked.connect(self.RemoveSelectedCombination)
        self.removeButton.setEnabled(False)
        self.electrodeListView = QListWidget()
        self.electrodeListView.currentRowChanged.connect(self.EnableRemoveButton)
        
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
        
        self.frequenciesListView = QListWidget()
        self.modeLabel = QLabel("Mode: ")
        self.channelLabel = QLabel("Channel: ")
        self.rangeLabel = QLabel("Range: ")
        self.precisionLabel = QLabel("Precision: ")
        self.amplitudeLabel = QLabel("Amplitude: ")
        self.timestampLabel = QLabel("Timestamp: ")
        
        # Layout
        formLayout = QGridLayout(self)
        formLayout.addWidget(QLabel("Min Frequency[Hz]:"), 0, 0)
        formLayout.addWidget(self.lineFreqMin, 0, 1)
        formLayout.addWidget(QLabel("Max Frequency[Hz]:"), 1, 0)
        formLayout.addWidget(self.lineFreqMax, 1, 1)
        # formLayout.addWidget(self.freqMaxGet, 1, 2)
        formLayout.addWidget(QLabel("Number of frequencies:"), 2, 0)
        formLayout.addWidget(self.lineFreqNum, 2, 1)
        formLayout.addWidget(QLabel("Frequency scale:"), 3, 0)
        formLayout.addWidget(self.comboFreqScale, 3, 1)
        formLayout.addWidget(QLabel("Measurement channel:"), 4, 0)
        formLayout.addWidget(self.comboChannel, 4, 1)
        formLayout.addWidget(QLabel("Measurement mode:"), 5, 0)
        formLayout.addWidget(self.comboMode, 5, 1)
        # formLayout.addWidget(self.modeGet, 5, 2)
        formLayout.addWidget(QLabel("Current range:"), 6, 0)
        formLayout.addWidget(self.comboRange, 6, 1)
        formLayout.addWidget(QLabel("Excitation type:"), 7, 0)
        formLayout.addWidget(self.comboExcitation, 7, 1)
        formLayout.addWidget(QLabel("Precision:"), 8, 0)
        formLayout.addWidget(self.linePrecision, 8, 1)
        # formLayout.addWidget(self.precisionGet, 8, 2)
        formLayout.addWidget(QLabel("Excitation amplitude:"), 9, 0)
        formLayout.addWidget(self.lineAmplitude, 9, 1)
        formLayout.addWidget(QLabel("Timestamp:"), 10, 0)
        formLayout.addWidget(self.comboTimestamp, 10, 1)
        # formLayout.addWidget(self.timestampGet, 10, 2)
        formLayout.addWidget(self.setSettings, 11, 1)
        
        formLayout.addWidget(QLabel("Read current settings"), 12, 0, Qt.AlignmentFlag.AlignBottom)
        formLayout.addWidget(self.freqMaxGet, 13, 0, Qt.AlignmentFlag.AlignTop)
        formLayout.addWidget(self.modeGet, 13, 1, Qt.AlignmentFlag.AlignTop)
        formLayout.addWidget(self.precisionGet, 13, 2, Qt.AlignmentFlag.AlignTop)
        formLayout.addWidget(self.timestampGet, 13, 3, 1, 4, Qt.AlignmentFlag.AlignTop)
        formLayout.addWidget(self.frequenciesListView, 14, 0, 5, 1)
        formLayout.addWidget(self.modeLabel, 14, 1)
        formLayout.addWidget(self.channelLabel, 15, 1)
        formLayout.addWidget(self.rangeLabel, 16, 1)
        formLayout.addWidget(self.precisionLabel, 14, 2)
        formLayout.addWidget(self.amplitudeLabel, 15, 2)
        formLayout.addWidget(self.timestampLabel, 14, 3, 1, 4)
        
        formLayout.addWidget(QLabel("Enter electrode combination:"), 0, 3, 1, 4)
        formLayout.addWidget(QLabel("Current electrode combinations"), 5, 3, 1, 4)
        formLayout.addWidget(self.electrodeListView, 6, 3, 6, 4)
        formLayout.addWidget(self.addCombButton, 3, 3, 1, 2)
        formLayout.addWidget(self.removeButton, 3, 5, 1, 2)
        formLayout.addWidget(self.inputElComb1, 1, 3)
        formLayout.addWidget(self.inputElComb2, 1, 4)
        formLayout.addWidget(self.inputElComb3, 1, 5)
        formLayout.addWidget(self.inputElComb4, 1, 6)
        formLayout.addWidget(QLabel("C"), 2, 3, Qt.AlignmentFlag.AlignHCenter)
        formLayout.addWidget(QLabel("R"), 2, 4, Qt.AlignmentFlag.AlignHCenter)
        formLayout.addWidget(QLabel("WS"), 2, 5, Qt.AlignmentFlag.AlignHCenter)
        formLayout.addWidget(QLabel("W"), 2, 6, Qt.AlignmentFlag.AlignHCenter)
    
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
        self.frequenciesListView.clear()
        for frequency in fList:
            newFrequency = QListWidgetItem()
            newFrequency.setText(str(frequency) + " Hz")
            self.frequenciesListView.addItem(newFrequency)
    
    def GetSettingsFe(self):
        
        mode, channel, currRange = self.impedanceAnalyser.GetFeSettings()
        self.modeLabel.setText(f"Mode: {mode.name[4]} point configuration")
        self.channelLabel.setText("Channel: " + channel.name)
        self.rangeLabel.setText("Range: " + currRange.name.replace("range",""))
    
    def GetSettingsPrecAmp(self):
        
        _, precision, amplitude = self.impedanceAnalyser.GetInformationOfFrequencyPoint(1)
        self.precisionLabel.setText(f"Precision: {precision}")
        self.amplitudeLabel.setText(f"Amplitude: {amplitude}")
    
    def GetSettingsTimestamp(self):
        
        self.timestampLabel.setText("Timestamp: " + self.impedanceAnalyser.GetOptionsTimeStamp().name)
    
    def AddElectrodeCombination(self):
        
        self.impedanceAnalyser.muxElConfig.append([int(self.inputElComb1.text()), int(self.inputElComb2.text()), int(self.inputElComb3.text()), int(self.inputElComb4.text())])
        newItem = QListWidgetItem()
        newItem.setText(f"[{self.inputElComb1.text()}, {self.inputElComb2.text()}, {self.inputElComb3.text()}, {self.inputElComb4.text()}]")
        self.electrodeListView.addItem(newItem)
    
    def RemoveSelectedCombination(self):
        
        for item in self.electrodeListView.selectedItems():
            self.impedanceAnalyser.muxElConfig.remove(self.impedanceAnalyser.muxElConfig[self.electrodeListView.row(item)])
            self.electrodeListView.takeItem(self.electrodeListView.row(item))
            self.electrodeListView.clearSelection()
            if len(self.electrodeListView.items()) == 0:
                self.removeButton.setEnabled(False)
    
    def EnableRemoveButton(self):
        
        self.removeButton.setEnabled(True)
        

class BodeDiagramTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.savedData:list[EISData] = []
        self.currentElCombIndex = None
        self.mode = "Z"
        self.initUI()

    def initUI(self):

        self.setWindowTitle("Bode Diagram Viewer")
        self.setGeometry(300, 150, 1000, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Umschalter Z/Y
        control_layout = QHBoxLayout()
        labelMeasurement = QLabel("Measurement:")
        self.measurementComboBox = QComboBox()
        self.measurementComboBox.currentIndexChanged.connect(self.measurementComboBoxSelectionChanged)
        labelElComb = QLabel("Electrode Combination:")
        labelElComb.setFont(QFont("Arial", 12))
        labelElComb.setStyleSheet("color: #000000;")
        self.electrodeComboBox = QComboBox()
        self.electrodeComboBox.currentIndexChanged.connect(self.electrodeComboBoxSelectionChanged)
        self.lastElectrodeCombination = None
        control_layout.addWidget(labelMeasurement)
        control_layout.addWidget(self.measurementComboBox)
        control_layout.addWidget(labelElComb)
        control_layout.addWidget(self.electrodeComboBox)

        self.z_button = QPushButton("Z: Impedance")
        self.y_button = QPushButton("Y: Admittance")

        for btn in [self.z_button, self.y_button]:
            btn.setCheckable(True)
            btn.setFixedSize(140, 40)
            btn.setFont(QFont('Arial', 11))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #dddddd;
                    color: black;
                    border-radius: 8px;
                    border: 1px solid #aaa;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #4CAF50;
                }
                QPushButton:hover {
                    background-color: #c8e6c9;
                }
            """)

        self.z_button.setChecked(True)
        self.z_button.clicked.connect(self.set_mode_z)
        self.y_button.clicked.connect(self.set_mode_y)

        self.toggle_group = QButtonGroup()
        self.toggle_group.setExclusive(True)
        self.toggle_group.addButton(self.z_button)
        self.toggle_group.addButton(self.y_button)

        control_layout.addWidget(self.z_button)
        control_layout.addWidget(self.y_button)

        layout.addLayout(control_layout)

        # Plot Widgets
        self.plot_mag = pg.PlotWidget(title="Magnitude [dB]")
        self.plot_mag.setLogMode(x=True, y=False)
        self.plot_mag.setBackground('w')
        self.plot_mag.showGrid(x=True, y=True)
        self.plot_mag.getAxis('left').setLabel(text="Magnitude [dB]")
        self.plot_mag.getAxis('bottom').setLabel(text="Frequency [Hz]")
        self.plot_mag.getAxis('left').setPen(pg.mkPen(color='k'))
        self.plot_mag.getAxis('bottom').setPen(pg.mkPen(color='k'))
        self.plot_mag.getAxis('left').setTextPen(pg.mkPen(color='k'))
        self.plot_mag.getAxis('bottom').setTextPen(pg.mkPen(color='k'))

        self.plot_phase = pg.PlotWidget(title="Phase [°]")
        self.plot_phase.setLogMode(x=True, y=False)
        self.plot_phase.setBackground('w')
        self.plot_phase.showGrid(x=True, y=True)
        self.plot_phase.getAxis('left').setLabel(text="Phase [°]")
        self.plot_phase.getAxis('bottom').setLabel(text="Frequency [Hz]")
        self.plot_phase.getAxis('left').setPen(pg.mkPen(color='k'))
        self.plot_phase.getAxis('bottom').setPen(pg.mkPen(color='k'))
        self.plot_phase.getAxis('left').setTextPen(pg.mkPen(color='k'))
        self.plot_phase.getAxis('bottom').setTextPen(pg.mkPen(color='k'))

        layout.addWidget(self.plot_mag)
        layout.addWidget(self.plot_phase)

        self.setLayout(layout)
        self.update_plot()

    def set_mode_z(self):
        self.mode = "Z"
        self.update_plot()

    def set_mode_y(self):
        self.mode = "Y"
        self.update_plot()
    
    def measurementComboBoxSelectionChanged(self):
        
        self.data = self.savedData[self.measurementComboBox.currentIndex()]
        self.update_plot()
    
    def electrodeComboBoxSelectionChanged(self):
        
        self.currentElCombIndex = self.electrodeComboBox.currentIndex()
        self.lastElectrodeCombination = self.currentElCombIndex
        self.update_plot()

    def update_plot(self):
        
        if self.data is None:
            return

        freq = self.data.frequencies
        measurand = self.data.impedances[self.currentElCombIndex] if self.mode == "Z" else self.data.admittances[self.currentElCombIndex]

        if len(freq) == 0 or len(measurand) == 0:
            return

        mag_db = 20 * np.log10(np.abs(measurand))
        phase = np.angle(measurand, deg=True)
        
        min_exp = int(np.floor(np.log10(freq.min())))
        max_exp = int(np.ceil(np.log10(freq.max())))
        major_ticks = [(10 ** i, f"{10 ** i:.0e}") for i in range(min_exp, max_exp + 1)]

        self.plot_mag.getAxis('bottom').setTicks([major_ticks])
        self.plot_phase.getAxis('bottom').setTicks([major_ticks])

        self.plot_mag.clear()
        self.plot_phase.clear()

        self.plot_mag.plot(freq, mag_db, pen=pg.mkPen(color='b', width=2), symbol='o')
        self.plot_phase.plot(freq, phase, pen=pg.mkPen(color='r', width=2), symbol='o')

    def update_data(self, data:EISData):
        
        if not self.savedData:
            self.electrodeComboBox.clear()
            self.electrodeComboBox.addItems(data.electrodes)
            
        self.data = data
        self.savedData.append(data)
        self.measurementComboBox.addItem(f"{data.measurementIndex}: {data.startTimeShort} - {data.finishTimeShort}")
        if self.lastElectrodeCombination is not None:
            self.electrodeComboBox.setCurrentIndex(self.lastElectrodeCombination)
        else:
            self.electrodeComboBox.setCurrentIndex(0)
        self.update_plot()


class TimeSeriesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.savedData:list[EISData] = []
        self.mode = "Z"
        self.currentTimes = None
        self.currentMags = None
        self.currentTimes = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Time Series Viewer")
        self.setGeometry(300, 150, 1000, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Header mit Dropdown & Toggle
        control_layout = QHBoxLayout()

        # Frequenzwahl
        freq_label = QLabel("Select Frequency:")
        freq_label.setFont(QFont("Arial", 12))
        freq_label.setStyleSheet("color: #000000;")
        control_layout.addWidget(freq_label)

        self.freq_combo = QComboBox()
        self.freq_combo.setFixedWidth(150)
        self.freq_combo.currentTextChanged.connect(self.update_plot)
        control_layout.addWidget(self.freq_combo)

        # Z/Y Umschalter
        self.z_button = QPushButton("Z: Impedance")
        self.y_button = QPushButton("Y: Admittance")

        for btn in [self.z_button, self.y_button]:
            btn.setCheckable(True)
            btn.setFixedSize(140, 40)
            btn.setFont(QFont('Arial', 11))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #dddddd;
                    color: black;
                    border-radius: 8px;
                    border: 1px solid #aaa;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #4CAF50;
                }
                QPushButton:hover {
                    background-color: #c8e6c9;
                }
            """)

        self.z_button.setChecked(True)
        self.z_button.clicked.connect(self.set_mode_z)
        self.y_button.clicked.connect(self.set_mode_y)

        self.toggle_group = QButtonGroup()
        self.toggle_group.setExclusive(True)
        self.toggle_group.addButton(self.z_button)
        self.toggle_group.addButton(self.y_button)

        control_layout.addWidget(self.z_button)
        control_layout.addWidget(self.y_button)

        layout.addLayout(control_layout)

        # Plot Widgets
        self.plot_mag = pg.PlotWidget(title="Magnitude over Time")
        self.plot_mag.setLabel('bottom', 'Time', units='s')
        self.plot_mag.setLabel('left', 'Magnitude', units='Ω')

        self.plot_phase = pg.PlotWidget(title="Phase over Time")
        self.plot_phase.setLabel('bottom', 'Time', units='s')
        self.plot_phase.setLabel('left', 'Phase', units='°')

        layout.addWidget(self.plot_mag)
        layout.addWidget(self.plot_phase)

        # Crosshair + Labels (jeweils eigene Items pro Plot!)
        self.crosshair_v_mag = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('g', width=1))
        self.crosshair_h_mag = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('g', width=1))
        self.label_mag = pg.LabelItem(justify='left')

        self.crosshair_v_phase = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('g', width=1))
        self.crosshair_h_phase = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('g', width=1))
        self.label_phase = pg.LabelItem(justify='left')

        self.plot_mag.addItem(self.crosshair_v_mag)
        self.plot_mag.addItem(self.crosshair_h_mag)
        self.plot_mag.getPlotItem().layout.addItem(self.label_mag, 4, 0)

        self.plot_phase.addItem(self.crosshair_v_phase)
        self.plot_phase.addItem(self.crosshair_h_phase)
        self.plot_phase.getPlotItem().layout.addItem(self.label_phase, 4, 0)

        # self.plot_mag.scene().sigMouseMoved.connect(self.mouse_moved)

        self.setLayout(layout)
        self.update_plot()

    def set_mode_z(self):
        self.mode = "Z"
        self.update_plot()

    def set_mode_y(self):
        self.mode = "Y"
        self.update_plot()

    def update_plot(self):
        # try:
            if not self.savedData:
                return
            
            index = self.freq_combo.currentIndex()
            self.startTime = datetime.strptime(self.savedData[0].startTime, "%Y-%m-%d %H:%M:%S")
            self.currentTimes = [(datetime.strptime(x.startTime, "%Y-%m-%d %H:%M:%S") - self.startTime).total_seconds() for x in self.savedData]
            
            self.currentMags = [x.magnitudesZ[0][index] for x in self.savedData] if self.mode == "Z" else [x.magnitudesY[0][index] for x in self.savedData]
            self.currentPhases = [x.phasesZ[0][index] for x in self.savedData] if self.mode == "Z" else [x.phasesY[0][index] for x in self.savedData]

            self.plot_mag.clear()
            self.plot_phase.clear()
            self.plot_mag.plot(self.currentTimes, self.currentMags, pen=pg.mkPen(color='b', width=2))
            self.plot_phase.plot(self.currentTimes, self.currentPhases, pen=pg.mkPen(color='r', width=2))

        # except Exception as e:
        #     QMessageBox.critical(self, "Plot Error", f"Failed to plot:\n{e}")

    # def mouse_moved(self, pos):
    #     if not hasattr(self, 'current_time') or len(self.currentTimes) == 0:
    #         return

    #     vb = self.plot_mag.getViewBox()
    #     if vb.sceneBoundingRect().contains(pos):
    #         mouse_point = vb.mapSceneToView(pos)
    #         x_val = mouse_point.x()

    #         time = self.currentTimes
    #         mag = self.currentMags
    #         phase = self.currentPhases

    #         index = (np.abs(time - x_val)).argmin()
    #         if index >= len(time):
    #             return

    #         self.crosshair_v_mag.setPos(time[index])
    #         self.crosshair_h_mag.setPos(mag[index])
    #         self.label_mag.setText(f"<span style='color: blue;'>Mag: {mag[index]:.4g} @ t={time[index]:.4g}</span>")

    #         self.crosshair_v_phase.setPos(time[index])
    #         self.crosshair_h_phase.setPos(phase[index])
    #         self.label_phase.setText(f"<span style='color: red;'>Phase: {phase[index]:.2f}° @ t={time[index]:.4g}</span>")

    def update_data(self, data:EISData):
        
        if data.measurementIndex == 1:
            self.freq_combo.addItems([str(f) for f in data.frequencies])
        
        self.data = data
        self.savedData.append(data)
        self.update_plot()



class DerivedValueTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data:EISData = None
        self.savedData:list[EISData] = []
        self.domainValues = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Derived Value Viewer")
        self.setGeometry(300, 150, 1000, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Eingabeformular
        form_layout = QHBoxLayout()
        label = QLabel("Enter function (use Z or Y):")
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("color: #000000;")
        form_layout.addWidget(label)

        self.input_expr = QLineEdit()
        self.input_expr.setFont(QFont("Courier New", 12))
        self.input_expr.setPlaceholderText("e.g. abs(Z) or np.real(1/Z)")
        self.input_expr.returnPressed.connect(self.update_plot)
        
        self.domainComboBox = QComboBox()
        self.frequencyButton = QRadioButton("Frequency")
        self.timeButton = QRadioButton("Time")
        self.frequencyButton.setChecked(True)
        self.domainButtonGroup = QButtonGroup()
        self.domainButtonGroup.buttonToggled.connect(self.domainRadioStateChanged)
        self.domainButtonGroup.addButton(self.frequencyButton)
        self.domainButtonGroup.addButton(self.timeButton)
        
        form_layout.addWidget(self.input_expr)
        form_layout.addStretch()
        form_layout.addWidget(self.frequencyButton)
        form_layout.addWidget(self.timeButton)
        form_layout.addWidget(self.domainComboBox)

        self.plot_btn = QPushButton("Plot")
        self.plot_btn.setFont(QFont("Arial", 12))
        self.plot_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 6px;")
        self.plot_btn.clicked.connect(self.update_plot)
        self.firstTimeClicked = False
        form_layout.addWidget(self.plot_btn)
        
        # Plot-Widget mit interaktiver ViewBox
        self.plot_widget = pg.PlotWidget(title="Derived Value vs Time")
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', 'Derived Value')            
        self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')

        layout.addLayout(form_layout)

        self.plot_widget.getViewBox().setMouseEnabled(x=True, y=True)  # Zoomen & Drag
        self.plot_widget.getViewBox().enableAutoRange()  # Automatischer Bereich bei Plot
        self.plot_widget.getViewBox().setLimits(xMin=0)  # Keine negativen Zeiten

        # Optional: Reset Zoom durch Doppelklick
        self.plot_widget.scene().sigMouseClicked.connect(self.reset_zoom_on_doubleclick)

        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_plot(self, updateExisting:bool = False):
        
        if not self.savedData:
            return

        if not updateExisting:
            self.firstTimeClicked = True
        
        if not self.firstTimeClicked:
            return
        
        expr = self.input_expr.text().strip()
        if not expr:
            QMessageBox.warning(self, "Input Required", "Please enter a function using Z or Y.")
            return

        try:
            if self.frequencyButton.isChecked():
                currentData = self.savedData[self.domainComboBox.currentIndex()]
                result = eval(expr, {"np": np, "Z": currentData.impedances[0], "Y": currentData.admittances[0]})
            else:
                currentImpedances = [x.impedances[0][self.domainComboBox.currentIndex()] for x in self.savedData]
                currentAdmittances = [x.admittances[0][self.domainComboBox.currentIndex()] for x in self.savedData]
                result = eval(expr, {"np": np, "Z": currentImpedances, "Y": currentAdmittances})

            if len(result) != len(self.domainValues):
                raise ValueError("Result length mismatch.")

            self.plot_widget.clear()
            self.plot_widget.plot(self.domainValues, result, pen=pg.mkPen(color='m', width=2))
            self.plot_widget.getViewBox().autoRange()  # Nach dem Plot automatisch skalieren

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to compute or plot expression:\n{e}")
    
    def update_data(self, data:EISData):
        
        self.savedData.append(data)
        self.domainRadioStateChanged()
        self.update_plot(True)
    
    def domainRadioStateChanged(self):
        
        if not self.savedData:
            return
        
        if (self.frequencyButton.isChecked()):
            self.domainValues = self.savedData[0].frequencies
            self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            self.domainComboBox.clear()
            measurements = [f"{x.measurementIndex}: {x.startTime} - {x.finishTime}" for x in self.savedData]
            self.domainComboBox.addItems(measurements)

        else:
            startTime = datetime.strptime(self.savedData[0].startTime, "%Y-%m-%d %H:%M:%S")
            self.domainValues = [(datetime.strptime(x.startTime, "%Y-%m-%d %H:%M:%S") - startTime).total_seconds() for x in self.savedData]
            self.plot_widget.setLabel('bottom', 'Time', units='s')
            self.domainComboBox.clear()
            measurements = [str(x) for x in self.savedData[0].frequencies]
            self.domainComboBox.addItems(measurements)

    def reset_zoom_on_doubleclick(self, event):
        if event.double():
            self.plot_widget.getViewBox().autoRange()
