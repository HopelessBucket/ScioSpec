import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pandas as pd

class BodeDiagramWindow(QWidget):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df if df is not None else pd.DataFrame()
        self.mode = "Z"
        self.initUI()

    def initUI(self):
        if 'Frequency' not in self.df.columns:
            self.df = pd.DataFrame({'Frequency': [], 'Impedance': []})

        self.setWindowTitle("Bode Diagram Viewer")
        self.setGeometry(300, 150, 1000, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        layout = QVBoxLayout()

        # Umschalter Z/Y
        control_layout = QHBoxLayout()
        label = QLabel("Select Mode:")
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("color: #000000;")
        control_layout.addWidget(label)

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

    def update_plot(self):
        if 'Frequency' not in self.df.columns or 'Impedance' not in self.df.columns:
            return

        freq = self.df['Frequency'].to_numpy()
        Z = self.df['Impedance'].to_numpy()

        if len(freq) == 0 or len(Z) == 0:
            return

        if self.mode == "Y":
            Z = 1 / Z

        mag_db = 20 * np.log10(np.abs(Z))
        phase = np.angle(Z, deg=True)

        self.plot_mag.clear()
        self.plot_phase.clear()

        self.plot_mag.plot(freq, mag_db, pen=pg.mkPen(color='b', width=2), symbol='o')
        self.plot_phase.plot(freq, phase, pen=pg.mkPen(color='r', width=2), symbol='o')

    def update_data(self, df):
        self.df = df if df is not None else pd.DataFrame()
        self.update_plot()
