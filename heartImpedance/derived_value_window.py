import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class DerivedValueWindow(QWidget):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
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
        form_layout.addWidget(self.input_expr)

        self.plot_btn = QPushButton("Plot")
        self.plot_btn.setFont(QFont("Arial", 12))
        self.plot_btn.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 6px;")
        self.plot_btn.clicked.connect(self.update_plot)
        form_layout.addWidget(self.plot_btn)

        layout.addLayout(form_layout)

        # Plot-Widget mit interaktiver ViewBox
        self.plot_widget = pg.PlotWidget(title="Derived Value vs Time")
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('bottom', 'Time', units='ms')
        self.plot_widget.setLabel('left', 'Derived Value')

        self.plot_widget.getViewBox().setMouseEnabled(x=True, y=True)  # Zoomen & Drag
        self.plot_widget.getViewBox().enableAutoRange()  # Automatischer Bereich bei Plot
        self.plot_widget.getViewBox().setLimits(xMin=0)  # Keine negativen Zeiten

        # Optional: Reset Zoom durch Doppelklick
        self.plot_widget.scene().sigMouseClicked.connect(self.reset_zoom_on_doubleclick)

        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_plot(self):
        expr = self.input_expr.text().strip()
        if not expr:
            QMessageBox.warning(self, "Input Required", "Please enter a function using Z or Y.")
            return

        try:
            offset = self.df['Offset'].to_numpy()
            Z = self.df['Impedance'].to_numpy()

            # Expression auswerten
            if 'Y' in expr and 'Z' not in expr:
                Y = 1 / Z
                result = eval(expr, {"np": np, "Y": Y})
            else:
                result = eval(expr, {"np": np, "Z": Z, "Y": 1 / Z})

            if len(result) != len(offset):
                raise ValueError("Result length mismatch.")

            self.plot_widget.clear()
            self.plot_widget.plot(offset, result, pen=pg.mkPen(color='m', width=2))
            self.plot_widget.getViewBox().autoRange()  # Nach dem Plot automatisch skalieren

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to compute or plot expression:\n{e}")

    def reset_zoom_on_doubleclick(self, event):
        if event.double():
            self.plot_widget.getViewBox().autoRange()