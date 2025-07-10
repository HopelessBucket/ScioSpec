from __future__ import annotations
import numpy as np
import pyqtgraph as pg
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QListWidget, QListWidgetItem, QGridLayout, QButtonGroup, QMessageBox, QRadioButton

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont
from DataManager import EISData
from ImpedanceAnalyser import ImpedanceAnalyser
from EnumClasses import InjectionType, CurrentRange, FrequencyScale, FeMode, FeChannel, TimeStamp

class SettingsTab(QWidget):
    """Tab that allows user to set settings and read current settings from the device

    Args:
        QWidget (_type_): _description_
    """
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
        
        # Input controls for electrode combinations
        self.inputElComb1 = QLineEdit(text="1")
        self.inputElComb1.setFixedWidth(50)
        self.inputElComb2 = QLineEdit(text="2")
        self.inputElComb2.setFixedWidth(50)
        self.inputElComb3 = QLineEdit(text="3")
        self.inputElComb3.setFixedWidth(50)
        self.inputElComb4 = QLineEdit(text="4")
        self.inputElComb4.setFixedWidth(50)
        
        # Add and remove buttons for electrode combinations
        self.addCombButton = QPushButton("Add")
        self.addCombButton.clicked.connect(self.AddElectrodeCombination)
        self.removeButton = QPushButton("Remove")
        self.removeButton.clicked.connect(self.RemoveSelectedCombination)
        self.removeButton.setEnabled(False)
        # List with currently added electrode combinations
        self.electrodeListView = QListWidget()
        
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
        
        # Displaying the results of Get functions
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
        formLayout.addWidget(QLabel("Number of frequencies:"), 2, 0)
        formLayout.addWidget(self.lineFreqNum, 2, 1)
        formLayout.addWidget(QLabel("Frequency scale:"), 3, 0)
        formLayout.addWidget(self.comboFreqScale, 3, 1)
        formLayout.addWidget(QLabel("Measurement channel:"), 4, 0)
        formLayout.addWidget(self.comboChannel, 4, 1)
        formLayout.addWidget(QLabel("Measurement mode:"), 5, 0)
        formLayout.addWidget(self.comboMode, 5, 1)
        formLayout.addWidget(QLabel("Current range:"), 6, 0)
        formLayout.addWidget(self.comboRange, 6, 1)
        formLayout.addWidget(QLabel("Excitation type:"), 7, 0)
        formLayout.addWidget(self.comboExcitation, 7, 1)
        formLayout.addWidget(QLabel("Precision:"), 8, 0)
        formLayout.addWidget(self.linePrecision, 8, 1)
        formLayout.addWidget(QLabel("Excitation amplitude:"), 9, 0)
        formLayout.addWidget(self.lineAmplitude, 9, 1)
        formLayout.addWidget(QLabel("Timestamp:"), 10, 0)
        formLayout.addWidget(self.comboTimestamp, 10, 1)
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
        """Updates device with all the settings provided by the user
        """
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
        """Reads frequency list from the device
        """
        fList = self.impedanceAnalyser.GetFrequencyList()
        self.frequenciesListView.clear()
        for frequency in fList:
            newFrequency = QListWidgetItem()
            newFrequency.setText(str(frequency) + " Hz")
            self.frequenciesListView.addItem(newFrequency)
    
    def GetSettingsFe(self):
        """Reads FE settings from the device
        """
        mode, channel, currRange = self.impedanceAnalyser.GetFeSettings()
        self.modeLabel.setText(f"Mode: {mode.name[4]} point configuration")
        self.channelLabel.setText("Channel: " + channel.name)
        self.rangeLabel.setText("Range: " + currRange.name.replace("range",""))
    
    def GetSettingsPrecAmp(self):
        """Reads precision and amplitude for first frequency (should be same for all)
        """
        _, precision, amplitude = self.impedanceAnalyser.GetInformationOfFrequencyPoint(1)
        self.precisionLabel.setText(f"Precision: {precision}")
        self.amplitudeLabel.setText(f"Amplitude: {amplitude}")
    
    def GetSettingsTimestamp(self):
        """Reads current timestamp settings from the device
        """
        self.timestampLabel.setText("Timestamp: " + self.impedanceAnalyser.GetOptionsTimeStamp().name)
    
    def AddElectrodeCombination(self):
        """Adds electrode combination from current input
        """
        self.impedanceAnalyser.muxElConfig.append([int(self.inputElComb1.text()), int(self.inputElComb2.text()), int(self.inputElComb3.text()), int(self.inputElComb4.text())])
        newItem = QListWidgetItem()
        newItem.setText(f"[{self.inputElComb1.text()}, {self.inputElComb2.text()}, {self.inputElComb3.text()}, {self.inputElComb4.text()}]")
        self.electrodeListView.addItem(newItem)
    
    def RemoveSelectedCombination(self):
        """Removes selected electrode combination from the list
        """
        for item in self.electrodeListView.selectedItems():
            self.impedanceAnalyser.muxElConfig.remove(self.impedanceAnalyser.muxElConfig[self.electrodeListView.row(item)])
            self.electrodeListView.takeItem(self.electrodeListView.row(item))
            self.electrodeListView.clearSelection()

class BodeDiagramTab(QWidget):
    """Tab for displaying bode diagram

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.savedData:list[EISData] = []
        self.mode = "Z"
        self.initUI()

    def initUI(self):

        # self.setWindowTitle("Bode Diagram Viewer")
        # self.setGeometry(300, 150, 1000, 600)
        # self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Switch Z/Y, electrode combination combobox and measurement combobox
        control_layout = QHBoxLayout()
        labelMeasurement = QLabel("Measurement:")
        self.measurementComboBox = QComboBox()
        self.measurementComboBox.setMinimumWidth(120)
        self.measurementComboBox.currentIndexChanged.connect(self.update_plot)
        labelElComb = QLabel("Electrode Combination:")
        labelElComb.setFont(QFont("Arial", 12))
        self.electrodeComboBox = QComboBox()
        self.electrodeComboBox.currentIndexChanged.connect(self.update_plot)
        control_layout.addWidget(labelMeasurement)
        control_layout.addWidget(self.measurementComboBox)
        control_layout.addWidget(labelElComb)
        control_layout.addWidget(self.electrodeComboBox)
        control_layout.addStretch()

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
        self.plot_mag = pg.PlotWidget(title="Magnitude")
        self.plot_mag.setLogMode(x=True, y=False)
        self.plot_mag.setBackground('w')
        self.plot_mag.showGrid(x=True, y=True)
        self.plot_mag.getAxis('left').setLabel(text="Magnitude")
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
        """Switches display to impedance values
        """
        self.mode = "Z"
        self.update_plot()

    def set_mode_y(self):
        """Switches display to admittance values
        """
        self.mode = "Y"
        self.update_plot()

    def update_plot(self):
        """Updates plot with new data or if mode is changed
        """
        if not self.savedData:
            return
        
        # Takes measurement and electrode combinations currently chosen in comboboxes
        self.data = self.savedData[self.measurementComboBox.currentIndex()]
        indexEl = self.electrodeComboBox.currentIndex()

        freq = self.data.frequencies
        measurand = self.data.impedances[indexEl] if self.mode == "Z" else self.data.admittances[indexEl]

        if len(freq) == 0 or len(measurand) == 0:
            return

        # Calculating magnitude and phase
        mag = np.abs(measurand)
        phase = np.angle(measurand, deg=True)
        
        min_exp = int(np.floor(np.log10(freq.min())))
        max_exp = int(np.ceil(np.log10(freq.max())))
        major_ticks = [(10 ** i, f"{10 ** i:.0e}") for i in range(min_exp, max_exp + 1)]

        self.plot_mag.getAxis('bottom').setTicks([major_ticks])
        self.plot_phase.getAxis('bottom').setTicks([major_ticks])

        self.plot_mag.clear()
        self.plot_phase.clear()

        self.plot_mag.plot(freq, mag, pen=pg.mkPen(color='b', width=2), symbol='o')
        self.plot_phase.plot(freq, phase, pen=pg.mkPen(color='r', width=2), symbol='o')

    def update_data(self, data:EISData):
        """Updates plot with new data and adds it to saveddata list

        Args:
            data (EISData): _description_
        """
        if not self.savedData:
            self.electrodeComboBox.clear()
            self.electrodeComboBox.addItems([str(x) for x in data.electrodes])
            
        self.data = data
        self.savedData.append(data)
        self.measurementComboBox.addItem(f"{data.measurementIndex}: {data.startTimeShort} - {data.finishTimeShort}")
        self.measurementComboBox.setCurrentIndex(len(self.savedData) - 1)
        self.update_plot()


class TimeSeriesTab(QWidget):
    """Tab for displaying measurements across time

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.savedData:list[EISData] = []
        self.currentFrequencyIndex = None
        self.currentElCombIndex = None
        self.mode = "Z"
        self.currentTimes = None
        self.currentMags = None
        self.currentPhases = None
        self.initUI()

    def initUI(self):
        # self.setWindowTitle("Time Series Viewer")
        # self.setGeometry(300, 150, 1000, 600)
        # self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Header mit Dropdown & Toggle
        control_layout = QHBoxLayout()

        # Frequenzwahl
        freq_label = QLabel("Frequency:")
        freq_label.setFont(QFont("Arial", 12))
        # freq_label.setStyleSheet("color: #000000;")
        control_layout.addWidget(freq_label)

        self.freq_combo = QComboBox()
        self.freq_combo.setMinimumWidth(100)
        self.freq_combo.currentTextChanged.connect(self.update_plot)
        control_layout.addWidget(self.freq_combo)
        
        # Electrode combination choice
        electrodeLabel = QLabel("Electrodes:")
        electrodeLabel.setFont(QFont("Arial", 12))
        # electrodeLabel.setStyleSheet("color: #000000;")
        control_layout.addWidget(electrodeLabel)
        
        self.electrodeComboBox = QComboBox()
        self.electrodeComboBox.setFixedHeight(40)
        self.electrodeComboBox.currentIndexChanged.connect(self.update_plot)
        control_layout.addWidget(self.electrodeComboBox)
        
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
        """Changes display to impedance
        """
        self.mode = "Z"
        self.update_plot()

    def set_mode_y(self):
        """Changes display to admittance
        """
        self.mode = "Y"
        self.update_plot()

    def update_plot(self):
        """Updates plot with new data or when the mode is changed
        """
        try:
            if not self.savedData:
                return
            
            indexFreq = self.freq_combo.currentIndex()
            indexEl = self.electrodeComboBox.currentIndex()
            self.startTime = datetime.strptime(self.savedData[0].startTime, "%Y-%m-%d %H:%M:%S")
            self.currentTimes = [(datetime.strptime(x.startTime, "%Y-%m-%d %H:%M:%S") - self.startTime).total_seconds() for x in self.savedData]
            
            self.currentMags = [x.magnitudesZ[indexEl][indexFreq] for x in self.savedData] if self.mode == "Z" else [x.magnitudesY[indexEl][indexFreq] for x in self.savedData]
            self.currentPhases = [x.phasesZ[indexEl][indexFreq] for x in self.savedData] if self.mode == "Z" else [x.phasesY[indexEl][indexFreq] for x in self.savedData]

            self.plot_mag.clear()
            self.plot_phase.clear()
            self.plot_mag.plot(self.currentTimes, self.currentMags, pen=pg.mkPen(color='b', width=2))
            self.plot_phase.plot(self.currentTimes, self.currentPhases, pen=pg.mkPen(color='r', width=2))

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot:\n{e}")

    def mouse_moved(self, pos):
        if not hasattr(self, 'current_time') or len(self.currentTimes) == 0:
            return

        vb = self.plot_mag.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            x_val = mouse_point.x()

            time = self.currentTimes
            mag = self.currentMags
            phase = self.currentPhases

            index = (np.abs(time - x_val)).argmin()
            if index >= len(time):
                return

            self.crosshair_v_mag.setPos(time[index])
            self.crosshair_h_mag.setPos(mag[index])
            self.label_mag.setText(f"<span style='color: blue;'>Mag: {mag[index]:.4g} @ t={time[index]:.4g}</span>")

            self.crosshair_v_phase.setPos(time[index])
            self.crosshair_h_phase.setPos(phase[index])
            self.label_phase.setText(f"<span style='color: red;'>Phase: {phase[index]:.2f}° @ t={time[index]:.4g}</span>")

    def update_data(self, data:EISData):
        """Updates tab with new measurement data

        Args:
            data (EISData): _description_
        """
        if not self.savedData:
            self.freq_combo.addItems([str(f) for f in data.frequencies])
            self.electrodeComboBox.addItems([str(x) for x in data.electrodes])
        
        self.data = data
        self.savedData.append(data)
        self.update_plot()



class DerivedValueTab(QWidget):
    """Tab for displaying diagram with own function

    Args:
        QWidget (_type_): _description_
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.savedData:list[EISData] = []
        self.domainValues = None
        self.initUI()

    def initUI(self):
        # self.setWindowTitle("Derived Value Viewer")
        # self.setGeometry(300, 150, 1000, 600)
        # self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Eingabeformular
        form_layout = QHBoxLayout()
        label = QLabel("Enter function (use Z or Y):")
        label.setFont(QFont("Arial", 12))
        # label.setStyleSheet("color: #000000;")
        form_layout.addWidget(label)

        self.input_expr = QLineEdit()
        self.input_expr.setFont(QFont("Courier New", 12))
        self.input_expr.setPlaceholderText("e.g. abs(Z) or np.real(1/Z)")
        self.input_expr.returnPressed.connect(self.update_plot)
        
        self.electrodeComboBox = QComboBox()
        self.domainComboBox = QComboBox()
        self.frequencyButton = QRadioButton("Frequency")
        self.timeButton = QRadioButton("Time")
        self.frequencyButton.setChecked(True)
        self.domainButtonGroup = QButtonGroup()
        self.frequencyButton.clicked.connect(self.domainRadioStateChanged)
        self.timeButton.clicked.connect(self.domainRadioStateChanged)
        self.domainButtonGroup.addButton(self.frequencyButton)
        self.domainButtonGroup.addButton(self.timeButton)
        
        form_layout.addWidget(self.input_expr)
        form_layout.addStretch()
        form_layout.addWidget(self.frequencyButton)
        form_layout.addWidget(self.timeButton)
        form_layout.addWidget(self.domainComboBox)
        form_layout.addWidget(QLabel("Electrodes:"))
        form_layout.addWidget(self.electrodeComboBox)

        self.plot_btn = QPushButton("Plot")
        self.plot_btn.setFont(QFont("Arial", 12))
        self.plot_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 6px;")
        self.plot_btn.clicked.connect(self.update_plot)
        self.firstTimeClicked = False
        form_layout.addWidget(self.plot_btn)
        
        # Plot-Widget mit interaktiver ViewBox
        self.plot_widget = pg.PlotWidget(title="Derived Value vs Frequency")
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
        """Updates plot with new data or function

        Args:
            updateExisting (bool, optional): _description_. Defaults to False.

        Raises:
            ValueError: _description_
        """
        
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
        result = []
        try:
            indexEl = self.electrodeComboBox.currentIndex()
            if self.frequencyButton.isChecked():
                currentData = self.savedData[self.domainComboBox.currentIndex()]
                result = [eval(expr, {"np": np, "Z": currentData.impedances[indexEl][x], "Y": currentData.admittances[indexEl][x]}) for x in range(len(currentData.frequencies))]
            else:
                currentImpedances = [x.impedances[indexEl][self.domainComboBox.currentIndex()] for x in self.savedData]
                currentAdmittances = [x.admittances[indexEl][self.domainComboBox.currentIndex()] for x in self.savedData]
                result = [eval(expr, {"np": np, "Z": currentImpedances[x], "Y": currentAdmittances[x]}) for x in range(len(currentImpedances))]

            if len(result) != len(self.domainValues):
                raise ValueError("Result length mismatch.")

            self.plot_widget.clear()
            self.plot_widget.plot(self.domainValues, result, pen=pg.mkPen(color='m', width=2))
            self.plot_widget.getViewBox().autoRange()  # Nach dem Plot automatisch skalieren

        except Exception as e:
            if not updateExisting:
                QMessageBox.critical(self, "Plot Error", f"Failed to compute or plot expression:\n{e}")
            else:
                print(f"Failed to compute or plot expression:\n{e}")
    
    def update_data(self, data:EISData):
        """Updates data with new measurement data

        Args:
            data (EISData): _description_
        """
        
        if not self.savedData:
            self.electrodeComboBox.addItems([str(x) for x in data.electrodes])
        self.savedData.append(data)
        self.domainRadioStateChanged()
        if self.frequencyButton.isChecked():
            self.domainComboBox.setCurrentIndex(len(self.savedData) - 1)
        self.update_plot(True)
    
    def domainRadioStateChanged(self):
        """Switch between spectrum and continuous display
        """
        
        if self.frequencyButton.isChecked():
            self.plot_widget.setTitle("Derived Value vs Frequency")
            self.plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            self.domainComboBox.clear()
            if self.savedData:
                self.domainValues = self.savedData[0].frequencies
                measurements = [f"{x.measurementIndex}: {x.startTime} - {x.finishTime}" for x in self.savedData]
                self.domainComboBox.addItems(measurements)

        else:
            self.plot_widget.setTitle("Derived Value vs Time")
            self.plot_widget.setLabel('bottom', 'Time', units='s')
            self.domainComboBox.clear()
            if self.savedData:
                startTime = datetime.strptime(self.savedData[0].startTime, "%Y-%m-%d %H:%M:%S")
                self.domainValues = [(datetime.strptime(x.startTime, "%Y-%m-%d %H:%M:%S") - startTime).total_seconds() for x in self.savedData]
                measurements = [str(x) for x in self.savedData[0].frequencies]
                self.domainComboBox.addItems(measurements)

    def reset_zoom_on_doubleclick(self, event):
        if event.double():
            self.plot_widget.getViewBox().autoRange()
