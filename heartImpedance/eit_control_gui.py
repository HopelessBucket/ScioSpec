import sys
import os
import matlab.engine
import pandas as pd
import numpy as np
from scipy.io import loadmat
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout,
    QHBoxLayout, QMessageBox, QButtonGroup, QTextEdit, QToolButton,
    QMenu, QFileDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from load_measurement_from_matlab import load_measurement
from time_series_window import TimeSeriesWindow
from bode_diagram_window import BodeDiagramWindow
from derived_value_window import DerivedValueWindow

class EITControlCenter(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self.actions = {}
        self.time_window = None
        self.bode_window = None
        self.derived_window = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('EIT Control Center')
        self.setGeometry(200, 100, 900, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel('EIT Control Center')
        title.setFont(QFont('Arial', 26, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #000000;")
        main_layout.addWidget(title)

        row_layout = QHBoxLayout()
        row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_layout.setSpacing(30)

        self.start_btn = QPushButton('Start Measurement')
        self.start_btn.setFont(QFont('Arial', 14))
        self.start_btn.setFixedSize(200, 50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.run_matlab_script)
        row_layout.addWidget(self.start_btn)

        self.load_btn = QPushButton('Load from .mat')
        self.load_btn.setFont(QFont('Arial', 14))
        self.load_btn.setFixedSize(200, 50)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.load_btn.clicked.connect(self.load_from_mat_file)
        row_layout.addWidget(self.load_btn)

        self.z_button = QPushButton("Z: Impedance")
        self.y_button = QPushButton("Y: Admittance")

        for btn in [self.z_button, self.y_button]:
            btn.setCheckable(True)
            btn.setFixedSize(140, 50)
            btn.setFont(QFont('Arial', 13))
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

        self.toggle_group = QButtonGroup()
        self.toggle_group.setExclusive(True)
        self.toggle_group.addButton(self.z_button)
        self.toggle_group.addButton(self.y_button)

        self.z_button.clicked.connect(self.apply_toggle_styles)
        self.y_button.clicked.connect(self.apply_toggle_styles)

        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(0)
        toggle_layout.addWidget(self.z_button)
        toggle_layout.addWidget(self.y_button)
        row_layout.addLayout(toggle_layout)

        self.view_mode_btn = QToolButton()
        self.view_mode_btn.setText("View Modes")
        self.view_mode_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.view_mode_btn.setFont(QFont("Arial", 12))
        self.view_mode_btn.setFixedSize(160, 50)
        self.view_mode_btn.setStyleSheet("""
            QToolButton {
                background-color: #ffffff;
                border: 1px solid #aaa;
                border-radius: 8px;
                padding: 6px 12px;
                color: #000;
                text-align: center;
            }
            QToolButton::menu-indicator {
                image: none;
            }
            QToolButton:hover {
                border: 1px solid #666;
                background-color: #f5f5f5;
            }
        """)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #aaa;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)

        for mode in ["Time Series", "Bode Diagram", "Derived Value"]:
            action = menu.addAction(mode)
            action.setCheckable(True)
            action.setChecked(mode == "Time Series")
            self.actions[mode] = action

        menu.triggered.connect(self.handle_view_mode_selection)
        self.view_mode_btn.setMenu(menu)
        row_layout.addWidget(self.view_mode_btn)

        main_layout.addLayout(row_layout)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont('Courier New', 14))
        self.output_display.setMinimumHeight(300)
        self.output_display.setStyleSheet(
            "color: #000000; background-color: #ffffff; padding: 8px;"
        )
        main_layout.addWidget(self.output_display)

        self.setLayout(main_layout)

    def handle_view_mode_selection(self, action):
        checked_modes = [name for name, act in self.actions.items() if act.isChecked()]
        if "Time Series" in checked_modes:
            if self.df is None:
                QMessageBox.warning(self, "No Data", "Please run a measurement or load a .mat file first.")
                return
            self.time_window = TimeSeriesWindow(self.df)
            self.time_window.show()
        if "Bode Diagram" in checked_modes:
            if self.df is None:
                QMessageBox.warning(self, "No Data", "Please run a measurement or load a .mat file first.")
                return
            self.bode_window = BodeDiagramWindow(self.df)
            self.bode_window.show()
        if "Derived Value" in checked_modes:
            if self.df is None:
                QMessageBox.warning(self, "No Data", "Please run a measurement or load a .mat file first.")
                return
            self.derived_window = DerivedValueWindow(self.df)
            self.derived_window.show()

    def apply_toggle_styles(self):
        if self.df is None:
            return

        if self.z_button.isChecked():
            self.output_display.setPlainText(
                self.df[['Offset', 'Frequency', 'Impedance']].to_string(index=False)
            )
        else:
            Y = 1 / self.df['Impedance']
            y_df = self.df.copy()
            y_df['Admittance'] = Y
            self.output_display.setPlainText(
                y_df[['Offset', 'Frequency', 'Admittance']].to_string(index=False)
            )

    def run_matlab_script(self):
        try:
            eng = matlab.engine.start_matlab()
            eng.cd(os.getcwd(), nargout=0)
            eng.eval("Measurement_Script_new", nargout=0)
            self.df = load_measurement(eng)
            QMessageBox.information(self, "Success", "Measurement started successfully.")
            self.apply_toggle_styles()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start MATLAB script:\n{e}")

    def load_from_mat_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open .mat File", "", "MAT-files (*.mat)")
        if not file_path:
            return
        try:
            mat_data = loadmat(file_path)
            time = mat_data.get("resTimeOffset", np.array([])).flatten()
            freq = mat_data.get("resFrequencies", np.array([])).flatten()
            imp  = mat_data.get("resImpedColumn", np.array([])).flatten()
            imp = np.array([complex(z) for z in imp])
            self.df = pd.DataFrame({
                "Offset": time,
                "Frequency": freq,
                "Impedance": imp
            })
            QMessageBox.information(self, "Success", "Data loaded successfully from .mat file.")
            self.apply_toggle_styles()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load .mat file:\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EITControlCenter()
    window.show()
    sys.exit(app.exec())