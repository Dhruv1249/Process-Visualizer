
import sys
import psutil
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView

class CpuTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Upper half: Graphs
        graphLayout = QGridLayout()
        graphLayout.setSpacing(10)
        
        # CPU Usage Graph
        self.cpuUsageLabel = QLabel("CPU Usage: 0.00%")
        self.cpuUsageLabel.setFont(QFont("Conthrax", 18, QFont.Bold))
        self.cpuUsageLabel.setAlignment(Qt.AlignCenter)
        graphLayout.addWidget(self.cpuUsageLabel, 0, 0)
        
        self.cpuUsageGraph = pg.PlotWidget()
        self.cpuUsageGraph.setBackground("#1A1A1A")
        self.cpuUsageGraph.setTitle("CPU Usage Over Time", color="w", size="14pt")
        self.cpuUsageGraph.setLabel("left", "Usage (%)", color="w", size="12pt")
        self.cpuUsageGraph.setLabel("bottom", "Time (s)", color="w", size="12pt")
        self.cpuUsageGraph.showGrid(x=True, y=True)
        graphLayout.addWidget(self.cpuUsageGraph, 1, 0)
        
        self.cpuUsageHistory = []
        self.timeHistory = []
        self.maxHistory = 50
        self.cpuUsagePlot = self.cpuUsageGraph.plot(pen=pg.mkPen(color=(0, 162, 255), width=2))
        self.cpuUsageTextItem = pg.TextItem(color=(255, 255, 255), anchor=(0.5, 0))
        self.cpuUsageGraph.addItem(self.cpuUsageTextItem)
        
        # CPU Clock Speed Graph
        self.cpuClockLabel = QLabel("CPU Clock Speed: 0.0 GHz")
        self.cpuClockLabel.setFont(QFont("Conthrax", 18, QFont.Bold))
        self.cpuClockLabel.setAlignment(Qt.AlignCenter)
        graphLayout.addWidget(self.cpuClockLabel, 0, 1)
        
        self.cpuClockGraph = pg.PlotWidget()
        self.cpuClockGraph.setBackground("#1A1A1A")
        self.cpuClockGraph.setTitle("CPU Clock Speed Over Time", color="w", size="14pt")
        self.cpuClockGraph.setLabel("left", "Clock Speed (GHz)", color="w", size="12pt")
        self.cpuClockGraph.setLabel("bottom", "Time (s)", color="w", size="12pt")
        self.cpuClockGraph.showGrid(x=True, y=True)
        graphLayout.addWidget(self.cpuClockGraph, 1, 1)
        
        self.cpuClockHistory = []
        self.cpuClockPlot = self.cpuClockGraph.plot(pen=pg.mkPen(color=(255, 94, 77), width=2))
        
        layout.addLayout(graphLayout, stretch=1)
        
        # Lower half: CPU Information Table
        self.cpuInfoTable = QTableWidget()
        self.cpuInfoTable.setColumnCount(2)
        self.cpuInfoTable.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.cpuInfoTable.horizontalHeader().setStretchLastSection(True)
        self.cpuInfoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cpuInfoTable.setStyleSheet("background-color: #000000; color: #FFFFFF; font-size: 16px; border: 1px solid #444;")
        self.cpuInfoTable.setFont(QFont("Conthrax", 16))
        self.cpuInfoTable.verticalHeader().setVisible(False)
        self.cpuInfoTable.setShowGrid(False)
        layout.addWidget(self.cpuInfoTable, stretch=1)
        
        # Initialize a persistent time counter for proper x-axis values
        self.timeCounter = 0

        self.timer = QTimer()
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateCpuStats)
        self.timer.start()
    
    def updateCpuStats(self):
        # Update CPU usage graph
        cpu_percent = psutil.cpu_percent()
        self.cpuUsageLabel.setText(f"CPU Usage: {cpu_percent:.2f}%")
        
        # Maintain fixed history length
        if len(self.cpuUsageHistory) >= self.maxHistory:
            self.cpuUsageHistory.pop(0)
            self.timeHistory.pop(0)
        
        # Append new data point using a continuously increasing time counter
        self.cpuUsageHistory.append(cpu_percent)
        self.timeHistory.append(self.timeCounter)
        self.timeCounter += 1
        self.cpuUsagePlot.setData(self.timeHistory, self.cpuUsageHistory)
        
        if self.cpuUsageHistory:
            self.cpuUsageTextItem.setText(f"{cpu_percent:.2f}%")
            self.cpuUsageTextItem.setPos(self.timeHistory[-1], self.cpuUsageHistory[-1])
        
        # Update CPU clock speed graph
        try:
            cpu_freq = psutil.cpu_freq().current / 1000  # Convert MHz to GHz
            self.cpuClockLabel.setText(f"CPU Clock Speed: {cpu_freq:.2f} GHz")
            if len(self.cpuClockHistory) >= self.maxHistory:
                self.cpuClockHistory.pop(0)
            self.cpuClockHistory.append(cpu_freq)
            self.cpuClockPlot.setData(self.timeHistory, self.cpuClockHistory)
        except Exception:
            self.cpuClockLabel.setText("CPU Clock Speed: N/A")
        
        # Update CPU Information Table
        freq = psutil.cpu_freq()
        # Show physical & logical cores, base frequency (using min as base), and current frequency.
        cpu_info = [
            ("Physical Cores:", psutil.cpu_count(logical=False)),
            ("Logical Cores:", psutil.cpu_count(logical=True)),
            ("Base Frequency (GHz):", f"{freq.max / 1000:.2f} GHz"),
            ("Current Frequency (GHz):", f"{freq.current / 1000:.2f} GHz"),
            ("CPU Usage (%):", f"{cpu_percent:.2f}%"),
            ("Processor Architecture:", "x86_64"),
            ("Threads Per Core:", "2")
        ]
        
        self.cpuInfoTable.setRowCount(len(cpu_info))
        for row, (attribute, value) in enumerate(cpu_info):
            item1 = QTableWidgetItem(attribute)
            item1.setForeground(Qt.blue)
            item1.setFont(QFont("Conthrax", 12, QFont.Bold))
            item2 = QTableWidgetItem(str(value))
            item2.setForeground(Qt.white)
            item2.setFont(QFont("Conthrax", 16))
            self.cpuInfoTable.setItem(row, 0, item1)
            self.cpuInfoTable.setItem(row, 1, item2)
        
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    tab = CpuTab()
    tab.show()
    sys.exit(app.exec_())
