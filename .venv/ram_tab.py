import sys
import psutil
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView

class RamTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Upper half: Graphs
        graphLayout = QGridLayout()
        graphLayout.setSpacing(10)
        
        # RAM Usage Graph
        self.ramUsageLabel = QLabel("RAM Usage: 0.00%")
        self.ramUsageLabel.setFont(QFont("Conthrax", 18, QFont.Bold))
        self.ramUsageLabel.setAlignment(Qt.AlignCenter)
        graphLayout.addWidget(self.ramUsageLabel, 0, 0)
        
        self.ramUsageGraph = pg.PlotWidget()
        self.ramUsageGraph.setBackground("#1A1A1A")
        self.ramUsageGraph.setTitle("RAM Usage Over Time", color="w", size="14pt")
        self.ramUsageGraph.setLabel("left", "Usage (%)", color="w", size="12pt")
        self.ramUsageGraph.setLabel("bottom", "Time (s)", color="w", size="12pt")
        self.ramUsageGraph.showGrid(x=True, y=True)
        graphLayout.addWidget(self.ramUsageGraph, 1, 0)
        
        self.ramUsageHistory = []
        self.timeHistory = []
        self.maxHistory = 50
        self.ramUsagePlot = self.ramUsageGraph.plot(pen=pg.mkPen(color=(0, 162, 255), width=2))
        self.ramUsageTextItem = pg.TextItem(color=(255, 255, 255), anchor=(0.5, 0))
        self.ramUsageGraph.addItem(self.ramUsageTextItem)
        
        layout.addLayout(graphLayout, stretch=1)
        
        # Lower half: RAM Information Table
        self.ramInfoTable = QTableWidget()
        self.ramInfoTable.setColumnCount(2)
        self.ramInfoTable.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.ramInfoTable.horizontalHeader().setStretchLastSection(True)
        self.ramInfoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ramInfoTable.setStyleSheet("background-color: #000000; color: #FFFFFF; font-size: 16px; border: 1px solid #444;")
        self.ramInfoTable.setFont(QFont("Conthrax", 16))
        self.ramInfoTable.verticalHeader().setVisible(False)
        self.ramInfoTable.setShowGrid(False)
        layout.addWidget(self.ramInfoTable, stretch=1)
        
        self.timer = QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateRamStats)
        self.timer.start()
    
    def updateRamStats(self):
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        self.ramUsageLabel.setText(f"RAM Usage: {ram_percent:.2f}%")
        
        if len(self.ramUsageHistory) >= self.maxHistory:
            self.ramUsageHistory.pop(0)
            self.timeHistory.pop(0)
        
        self.ramUsageHistory.append(ram_percent)
        self.timeHistory.append(len(self.timeHistory))
        self.ramUsagePlot.setData(self.timeHistory, self.ramUsageHistory)
        
        if self.ramUsageHistory:
            self.ramUsageTextItem.setText(f"{ram_percent:.2f}%")
            self.ramUsageTextItem.setPos(self.timeHistory[-1], self.ramUsageHistory[-1])
        
        # RAM Info Table
        ram_info = [
            ("Total RAM:", f"{ram.total / (1024 ** 3):.2f} GB"),
            ("Available RAM:", f"{ram.available / (1024 ** 3):.2f} GB"),
            ("Used RAM:", f"{ram.used / (1024 ** 3):.2f} GB"),
            ("Free RAM:", f"{ram.free / (1024 ** 3):.2f} GB"),
        ]
        
        # Add optional attributes if available
        optional_attrs = ["cached", "active", "inactive", "buffers", "shared"]
        for attr in optional_attrs:
            if hasattr(ram, attr):
                ram_info.append((f"{attr.capitalize()} Memory:", f"{getattr(ram, attr) / (1024 ** 3):.2f} GB"))
        
        ram_info.extend([
            ("Swap Memory:", f"{psutil.swap_memory().total / (1024 ** 3):.2f} GB"),
            ("Swap Used:", f"{psutil.swap_memory().used / (1024 ** 3):.2f} GB"),
            ("Swap Free:", f"{psutil.swap_memory().free / (1024 ** 3):.2f} GB"),
        ])
        
        self.ramInfoTable.setRowCount(len(ram_info))
        for row, (attribute, value) in enumerate(ram_info):
            item1 = QTableWidgetItem(attribute)
            item1.setForeground(Qt.blue)
            item1.setFont(QFont("Conthrax", 16, QFont.Bold))
            item2 = QTableWidgetItem(str(value))
            item2.setForeground(Qt.white)
            item2.setFont(QFont("Conthrax", 16))
            self.ramInfoTable.setItem(row, 0, item1)
            self.ramInfoTable.setItem(row, 1, item2)
