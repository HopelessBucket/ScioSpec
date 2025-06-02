import numpy as np
import pyqtgraph as pg
from pyqtgraph import InfiniteLine, LabelItem
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class TimeSeriesWindow(QWidget):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.mode = "Z"
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
        self.freq_combo.addItem("All Frequencies")
        unique_freqs = sorted(np.unique(self.df['Frequency']))
        self.freq_combo.addItems([str(f) for f in unique_freqs])
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
        self.crosshair_v_mag = InfiniteLine(angle=90, movable=False, pen=pg.mkPen('g', width=1))
        self.crosshair_h_mag = InfiniteLine(angle=0, movable=False, pen=pg.mkPen('g', width=1))
        self.label_mag = LabelItem(justify='left')

        self.crosshair_v_phase = InfiniteLine(angle=90, movable=False, pen=pg.mkPen('g', width=1))
        self.crosshair_h_phase = InfiniteLine(angle=0, movable=False, pen=pg.mkPen('g', width=1))
        self.label_phase = LabelItem(justify='left')

        self.plot_mag.addItem(self.crosshair_v_mag)
        self.plot_mag.addItem(self.crosshair_h_mag)
        self.plot_mag.getPlotItem().layout.addItem(self.label_mag, 4, 0)

        self.plot_phase.addItem(self.crosshair_v_phase)
        self.plot_phase.addItem(self.crosshair_h_phase)
        self.plot_phase.getPlotItem().layout.addItem(self.label_phase, 4, 0)

        self.plot_mag.scene().sigMouseMoved.connect(self.mouse_moved)

        self.setLayout(layout)
        self.update_plot()

    def set_mode_z(self):
        self.mode = "Z"
        self.update_plot()

    def set_mode_y(self):
        self.mode = "Y"
        self.update_plot()

    def update_plot(self):
        try:
            selected = self.freq_combo.currentText()
            if selected != "All Frequencies":
                freq = float(selected)
                df_filtered = self.df[self.df['Frequency'] == freq]
            else:
                df_filtered = self.df

            time = df_filtered['Offset'].to_numpy()
            Z = df_filtered['Impedance'].to_numpy()

            if self.mode == "Y":
                Z = 1 / Z

            self.current_time = time
            self.current_mag = np.abs(Z)
            self.current_phase = np.angle(Z, deg=True)

            self.plot_mag.clear()
            self.plot_phase.clear()
            self.plot_mag.plot(time, self.current_mag, pen=pg.mkPen(color='b', width=2))
            self.plot_phase.plot(time, self.current_phase, pen=pg.mkPen(color='r', width=2))

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot:\n{e}")

    def mouse_moved(self, pos):
        if not hasattr(self, 'current_time') or len(self.current_time) == 0:
            return

        vb = self.plot_mag.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            x_val = mouse_point.x()

            time = self.current_time
            mag = self.current_mag
            phase = self.current_phase

            index = (np.abs(time - x_val)).argmin()
            if index >= len(time):
                return

            self.crosshair_v_mag.setPos(time[index])
            self.crosshair_h_mag.setPos(mag[index])
            self.label_mag.setText(f"<span style='color: blue;'>Mag: {mag[index]:.4g} @ t={time[index]:.4g}</span>")

            self.crosshair_v_phase.setPos(time[index])
            self.crosshair_h_phase.setPos(phase[index])
            self.label_phase.setText(f"<span style='color: red;'>Phase: {phase[index]:.2f}° @ t={time[index]:.4g}</span>")

    def update_data(self, df):
        self.df = df
        self.update_plot()