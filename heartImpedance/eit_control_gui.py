
import sys
import numpy as np
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QMessageBox, QButtonGroup, QTextEdit, QToolButton, QMenu, QInputDialog, QLineEdit
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from bode_diagram_window import BodeDiagramWindow
from derived_value_window import DerivedValueWindow
from time_series_window import TimeSeriesWindow

# Python-Treiber
from ImpedanceAnalyser import ImpedanceAnalyser           # echte Hardware
#from ImpedanceAnalyserFake import ImpedanceAnalyserFake   # Dummy (offline-Test)
from EnumClasses import InjectionType, CurrentRange, FrequencyScale
from CalculateValidImpedanceRange import CalculateValidImpedanceRange


class EITControlCenter(QWidget):

    def __init__(self):
        super().__init__()
        self.df: pd.DataFrame | None = None
        self.analyser = None            # wird in run_measurement() instanziiert
        self.initUI()

    # ------------------------------------------------------------------ UI-Aufbau
    def initUI(self):
        self.setWindowTitle('EIT Control Center')
        self.setGeometry(200, 100, 900, 600)
        self.setStyleSheet("background-color: #f0f0f0;")

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel('Impedance Analyzer')
        title.setFont(QFont('Arial', 26, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333333;")   # dunkle Schrift, damit sie kontrastiert
        main_layout.addWidget(title)

        # -------------------- erste Zeile: Start-Button + Z/Y-Toggle + View-Menü
        row_layout = QHBoxLayout()
        row_layout.setSpacing(20)

        # Start-Button
        self.start_btn = QPushButton('Measurement Starten')
        self.start_btn.setFont(QFont('Arial', 14))
        self.start_btn.setFixedSize(220, 50)
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
        self.start_btn.clicked.connect(self.run_measurement)
        row_layout.addWidget(self.start_btn)

        # Z↔Y Umschalter
        self.z_button = QPushButton('Z-Mode')
        self.y_button = QPushButton('Y-Mode')
        for btn in (self.z_button, self.y_button):
            btn.setCheckable(True)
            btn.setFixedSize(100, 50)
            btn.setFont(QFont('Arial', 14))
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

        self.toggle_group = QButtonGroup(self)
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

        # Elektroden-Auswahl
        el_label = QLabel("Elektroden (C-R-WS-W):")
        el_label.setFont(QFont('Arial', 12))
        row_layout.addWidget(el_label)

        self.electrode_input = QLineEdit()
        self.electrode_input.setPlaceholderText("z.B. 1-2-3-4")
        self.electrode_input.setFixedWidth(120)
        row_layout.addWidget(self.electrode_input)

        self.view_mode_btn = QToolButton()
        self.view_mode_btn.setText("View Modes")
        self.view_mode_btn.setFixedSize(100, 50)
        self.view_mode_btn.setFont(QFont('Arial', 12))
        self.view_mode_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
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
        menu.setStyleSheet("font-size: 14px;")
        menu.addAction("Zeitserie").setCheckable(True)
        menu.addAction("Bode Diagram").setCheckable(True)
        menu.addAction("Derived Value").setCheckable(True)
        menu.triggered.connect(self.handle_view_mode_selection)
        self.view_mode_btn.setMenu(menu)

        row_layout.addWidget(self.view_mode_btn)
        main_layout.addLayout(row_layout)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont('Courier New', 14))
        self.output_display.setMinimumHeight(300)
        self.output_display.setStyleSheet(
            "color: #000000; background-color: #ffffff; padding: 8px;")
        main_layout.addWidget(self.output_display)

        self.setLayout(main_layout)

    def run_measurement(self):
        """Konfiguriert den Treiber, führt einen Sweep aus, füllt self.df."""

        com_port, ok = QInputDialog.getText(
            self, "COM-Port", "Bitte COM-Port eingeben (z. B. COM3 oder /dev/ttyUSB0):")
        if not ok or not com_port:
            return


        try:
                self.analyser = ImpedanceAnalyser(com_port)
        except Exception as e:
                QMessageBox.critical(self, "Verbindungsfehler",
                                     f"Konnte Gerät nicht öffnen:\n{e}\n\n(Offline weiter im Fake-Modus)")

        combo_str = self.electrode_input.text().strip()
        if not combo_str:
            QMessageBox.warning(self, "Fehlende Eingabe",
                                "Bitte eine Elektrodenkombination eingeben (z.B. 1-2-3-4).")
            return
        try:
            sel_combo = [int(x) for x in combo_str.split('-')]
            if len(sel_combo) != 4 or not all(1 <= x <= 16 for x in sel_combo):
                raise ValueError
        except ValueError:
            QMessageBox.critical(
                self,
                "Ungültiges Format",
                "Eingabe muss vier Zahlen zwischen 1 und 16 enthalten, getrennt durch '-'.\n"
                "Beispiel: 1-2-3-4",
            )
            return

        self.analyser.SetMuxChannels([sel_combo])
        # Sicherheitscheck Impedanzbereich

        try:
            CalculateValidImpedanceRange(
                self.analyser.excitation,
                self.analyser.feRange,
                self.analyser.resCurrentRange
            )
        except Exception as e:
            QMessageBox.critical(self, "Ungültige Einstellungen", str(e))
            return

        # ------------------------------------------------ Sweep starten
        try:
            resReal, resImag, resWarn, resRange, resTime, startTime, finishTime = (
                self.analyser.GetMeasurements()
            )
        except Exception as e:
            QMessageBox.critical(self, "Messfehler", str(e))
            return

        # ------------------------------------------------ DataFrame bauen
        fnum = self.analyser.fnum
        if self.analyser.fscale == FrequencyScale.logarithmic:
            freqs = np.logspace(np.log10(self.analyser.fmin),
                                np.log10(self.analyser.fmax),
                                fnum)
        else:
            freqs = np.linspace(self.analyser.fmin,
                                self.analyser.fmax,
                                fnum)

        # Nur erstes Mux-Set anzeigen → Dim: (fnum,)
        Z = resReal[0] + 1j * resImag[0]
        offset = resTime[0] if resTime is not None else np.zeros_like(freqs)

        self.df = pd.DataFrame({
            "Offset": offset,
            "Frequency": freqs,
            "Impedance": Z
        })

        # ------------------------------------------------ UI aktualisieren
        self.apply_toggle_styles()
        QMessageBox.information(
            self,
            "Messung beendet",
            f"Start: {startTime}\nEnde: {finishTime}\nTreiber: Hardware"
        )
    # ------------------------------------------------------------------ Text-/Anzeige-Hilfen
    def apply_toggle_styles(self):
        """Aktualisiert die Anzeige im großen Textfeld gemäß Z/Y-Modus."""
        if self.df is None:
            self.output_display.setPlainText("Bitte zuerst eine Messung starten.")
            return

        if self.z_button.isChecked():
            Z = self.df['Impedance']
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

    # ------------------------------------------------------------------ Fenster öffnende Aktionen
    def handle_view_mode_selection(self, action):
        checked_modes = [act.text() for act in action.parent().actions() if act.isChecked()]

        if "Zeitserie" in checked_modes:
            if self.df is None:
                QMessageBox.warning(self, "Keine Daten", "Bitte zuerst eine Messung starten.")
                return
            self.time_window = TimeSeriesWindow(self.df)
            self.time_window.show()

        if "Bode Diagram" in checked_modes:
            if self.df is None:
                QMessageBox.warning(self, "Keine Daten", "Bitte zuerst eine Messung starten.")
                return
            self.bode_window = BodeDiagramWindow(self.df)
            self.bode_window.show()

        if "Derived Value" in checked_modes:
            if self.df is None:
                QMessageBox.warning(self, "Keine Daten", "Bitte zuerst eine Messung starten.")
                return
            self.derived_window = DerivedValueWindow(self.df)
            self.derived_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EITControlCenter()
    window.show()
    sys.exit(app.exec())
