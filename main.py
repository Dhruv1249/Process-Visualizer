import sys
import psutil
import math
import GPUtil  # For GPU monitoring
import numpy as np
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QStackedWidget,
    QFormLayout, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import qdarkstyle
import pyqtgraph as pg

class GaugeWidget(pg.PlotWidget):
    """A custom speedometer-like gauge widget inspired by Ookla Speedtest."""
    def __init__(self, title="Gauge", max_value=100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_value = max_value
        self.setTitle(title, color='w', size='12pt')
        self.setAspectLocked(True)
        self.hideAxis('bottom')
        self.hideAxis('left')
        self.setRange(xRange=(-1.2, 1.2), yRange=(-0.2, 1.2))

        # Background arc (full range, gray)
        angles = np.linspace(180, 0, 100)  # Left (180°) to right (0°)
        radians = np.radians(angles)
        x = np.cos(radians)
        y = np.sin(radians)
        self.full_arc = pg.PlotCurveItem(x, y, pen=pg.mkPen(color=(50, 50, 50), width=4))
        self.addItem(self.full_arc)

        # Usage arc (dynamic, colored)
        self.usage_arc = pg.PlotCurveItem([], [], pen=pg.mkPen(color=(0, 255, 0), width=4))
        self.addItem(self.usage_arc)

        # Needle
        self.needle = pg.PlotCurveItem([0, 0], [0, 0], pen=pg.mkPen('r', width=3))
        self.addItem(self.needle)

        # Center point
        self.center = pg.ScatterPlotItem([0], [0], size=15, brush=pg.mkBrush(255, 0, 0))
        self.addItem(self.center)

        # Tick marks and labels at 20% intervals
        for i in range(0, 101, 20):
            angle_deg = 180 - (180 * (i / 100))
            angle_rad = math.radians(angle_deg)
            x1 = 0.9 * math.cos(angle_rad)
            y1 = 0.9 * math.sin(angle_rad)
            x2 = 1.0 * math.cos(angle_rad)
            y2 = 1.0 * math.sin(angle_rad)
            tick = pg.PlotCurveItem([x1, x2], [y1, y2], pen=pg.mkPen('w', width=1))
            self.addItem(tick)
            label = pg.TextItem(text=str(i), color='w', anchor=(0.5, 0.5))
            label.setPos(x2 * 1.1, y2 * 1.1)
            self.addItem(label)

        self.current_value = 0
        self.update_gauge(0)

    def update_gauge(self, value):
        """Update the needle and usage arc based on the input value."""
        self.current_value = min(max(value, 0), self.max_value)
        value_percent = self.current_value / self.max_value

        # Update usage arc
        angles = np.linspace(180, 180 - (180 * value_percent), int(100 * value_percent))
        radians = np.radians(angles)
        x = np.cos(radians)
        y = np.sin(radians)
        self.usage_arc.setData(x, y)

        # Color gradient: green (0%) to red (100%)
        hue = 0.33 - (0.33 * value_percent)  # Green (0.33) to red (0)
        color = pg.hsvColor(hue, 1, 1)
        self.usage_arc.setPen(pg.mkPen(color, width=4))

        # Update needle position
        angle_rad = math.radians(180 - (180 * value_percent))
        x = math.cos(angle_rad)
        y = math.sin(angle_rad)
        self.needle.setData([0, x], [0, y])

class HomeDashboard(QWidget):
    """System Monitor Dashboard with gauges and process table."""
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)

        # Section header for gauges
        metrics_label = QLabel("System Metrics")
        metrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        metrics_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        main_layout.addWidget(metrics_label)

        # Horizontal layout for gauges
        gauge_layout = QHBoxLayout()

        # CPU Gauge
        cpu_layout = QVBoxLayout()
        self.cpu_gauge = GaugeWidget(title="CPU Usage (%)", max_value=100)
        self.cpu_label = QLabel("0%")
        self.cpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cpu_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        cpu_layout.addWidget(self.cpu_gauge)
        cpu_layout.addWidget(self.cpu_label)
        gauge_layout.addLayout(cpu_layout)

        # GPU Gauge
        gpu_layout = QVBoxLayout()
        self.gpu_gauge = GaugeWidget(title="GPU Usage (%)", max_value=100)
        self.gpu_label = QLabel("0%")
        self.gpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gpu_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        gpu_layout.addWidget(self.gpu_gauge)
        gpu_layout.addWidget(self.gpu_label)
        gauge_layout.addLayout(gpu_layout)

        # RAM Gauge
        ram_layout = QVBoxLayout()
        self.ram_gauge = GaugeWidget(title="RAM Usage (%)", max_value=100)
        self.ram_label = QLabel("0%")
        self.ram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ram_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        ram_layout.addWidget(self.ram_gauge)
        ram_layout.addWidget(self.ram_label)
        gauge_layout.addLayout(ram_layout)

        # Disk Gauge
        disk_layout = QVBoxLayout()
        self.disk_gauge = GaugeWidget(title="Disk Usage (%)", max_value=100)
        self.disk_label = QLabel("0%")
        self.disk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disk_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        disk_layout.addWidget(self.disk_gauge)
        disk_layout.addWidget(self.disk_label)
        gauge_layout.addLayout(disk_layout)

        main_layout.addLayout(gauge_layout)
        main_layout.addSpacing(20)

        # Section header for process table
        processes_label = QLabel("Running Processes")
        processes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        processes_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        main_layout.addWidget(processes_label)

        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "Mem %"])
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.process_table.setSortingEnabled(True)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setStyleSheet("QTableWidget {background-color: #2e2e2e; color: white; font: 10pt Arial;}")
        main_layout.addWidget(self.process_table)

        # Timer for periodic updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1500)  # Update every 1.5 seconds

    def update_stats(self):
        """Update gauges and labels with current system metrics."""
        # Disk path for system drive
        disk_path = 'C:\\' if os.name == 'nt' else '/'

        # CPU Usage (system-wide)
        cpu_usage = psutil.cpu_percent(interval=0.1)
        self.cpu_gauge.update_gauge(cpu_usage)
        self.cpu_label.setText(f"{cpu_usage:.1f}%")

        # GPU Usage
        try:
            gpus = GPUtil.getGPUs()
            gpu_usage = gpus[0].load * 100 if gpus else 0
        except Exception:
            gpu_usage = 0
        self.gpu_gauge.update_gauge(gpu_usage)
        self.gpu_label.setText(f"{gpu_usage:.1f}%")

        # RAM Usage
        ram_info = psutil.virtual_memory()
        ram_percent = ram_info.percent
        self.ram_gauge.update_gauge(ram_percent)
        self.ram_label.setText(f"{ram_percent:.1f}%")

        # Disk Usage
        disk_info = psutil.disk_usage(disk_path)
        disk_percent = disk_info.percent
        self.disk_gauge.update_gauge(disk_percent)
        self.disk_label.setText(f"{disk_percent:.1f}%")

        self.update_process_table()

    def update_process_table(self):
        """Update the process table with the top 50 processes by CPU usage, excluding PID 0."""
        self.process_table.setRowCount(0)
        processes = []
        cpu_count = psutil.cpu_count()
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            if proc.info['pid'] == 0:  # Exclude system idle process
                continue
            # Normalize CPU usage to match Task Manager (total CPU %)
            cpu_percent = (proc.info['cpu_percent'] / cpu_count) if proc.info['cpu_percent'] is not None else 0.0
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'] or 'Unknown',
                'cpu_percent': cpu_percent,
                'memory_percent': proc.info['memory_percent'] or 0.0
            })
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        for row_idx, info in enumerate(processes[:50]):
            self.process_table.insertRow(row_idx)
            self.process_table.setItem(row_idx, 0, QTableWidgetItem(str(info['pid'])))
            self.process_table.setItem(row_idx, 1, QTableWidgetItem(info['name']))
            self.process_table.setItem(row_idx, 2, QTableWidgetItem(f"{info['cpu_percent']:.1f}"))
            self.process_table.setItem(row_idx, 3, QTableWidgetItem(f"{info['memory_percent']:.1f}"))

class ProcessScheduling(QWidget):
    """Process Scheduling page with polished table and Gantt chart."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Form for process input
        form_layout = QFormLayout()
        self.num_processes_input = QLineEdit("5")
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["FCFS", "SJF", "Round Robin"])
        self.quantum_input = QLineEdit("2")
        self.quantum_input.setEnabled(False)
        self.algorithm_combo.currentTextChanged.connect(self.toggle_quantum)
        form_layout.addRow("Number of Processes:", self.num_processes_input)
        form_layout.addRow("Algorithm:", self.algorithm_combo)
        form_layout.addRow("Time Quantum (RR):", self.quantum_input)
        layout.addLayout(form_layout)

        # Simulate button
        self.simulate_btn = QPushButton("Simulate")
        self.simulate_btn.clicked.connect(self.update_table_and_gantt)
        layout.addWidget(self.simulate_btn)

        # Process table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["PID", "Arrival Time", "Burst Time"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget {background-color: #2e2e2e; color: white; font: 10pt Arial;}")
        layout.addWidget(self.table)

        # Gantt chart
        self.gantt_view = pg.PlotWidget(title="Gantt Chart")
        self.gantt_view.setBackground('#1e1e1e')
        self.gantt_view.showGrid(x=True, y=False)
        layout.addWidget(self.gantt_view)

    def toggle_quantum(self, text):
        """Enable/disable time quantum input based on algorithm."""
        self.quantum_input.setEnabled(text == "Round Robin")

    def update_table_and_gantt(self):
        """Simulate scheduling and update table and Gantt chart."""
        try:
            n = int(self.num_processes_input.text())
            algorithm = self.algorithm_combo.currentText()
            quantum = int(self.quantum_input.text()) if algorithm == "Round Robin" else None
        except ValueError:
            return

        # Generate random processes
        processes = [{'pid': i+1, 'arrival': np.random.randint(0, 10), 'burst': np.random.randint(1, 10)} for i in range(n)]
        self.table.setRowCount(n)
        for i, proc in enumerate(processes):
            self.table.setItem(i, 0, QTableWidgetItem(str(proc['pid'])))
            self.table.setItem(i, 1, QTableWidgetItem(str(proc['arrival'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(proc['burst'])))

        # Simulate scheduling (simplified)
        gantt_data = []
        current_time = 0
        remaining = processes.copy()
        remaining.sort(key=lambda x: x['arrival'])

        if algorithm == "FCFS":
            for proc in sorted(processes, key=lambda x: x['arrival']):
                start = max(current_time, proc['arrival'])
                finish = start + proc['burst']
                gantt_data.append((proc['pid'], start, finish))
                current_time = finish
        elif algorithm == "SJF":
            while remaining:
                available = [p for p in remaining if p['arrival'] <= current_time]
                if not available:
                    current_time += 1
                    continue
                proc = min(available, key=lambda x: x['burst'])
                start = current_time
                finish = start + proc['burst']
                gantt_data.append((proc['pid'], start, finish))
                current_time = finish
                remaining.remove(proc)
        elif algorithm == "Round Robin":
            queue = []
            remaining.sort(key=lambda x: x['arrival'])
            arrivals = remaining.copy()
            remaining_burst = {p['pid']: p['burst'] for p in processes}
            while remaining_burst:
                while arrivals and arrivals[0]['arrival'] <= current_time:
                    queue.append(arrivals.pop(0))
                if not queue:
                    current_time += 1
                    continue
                proc = queue.pop(0)
                start = current_time
                time_slice = min(quantum, remaining_burst[proc['pid']])
                finish = start + time_slice
                gantt_data.append((proc['pid'], start, finish))
                remaining_burst[proc['pid']] -= time_slice
                current_time = finish
                if remaining_burst[proc['pid']] > 0:
                    queue.append(proc)
                else:
                    del remaining_burst[proc['pid']]

        # Update Gantt chart with polished styling
        self.gantt_view.clear()
        colors = ['#ff5555', '#55ff55', '#5555ff', '#ffff55', '#ff55ff', '#55ffff']
        y_base = 0
        for pid, start, finish in gantt_data:
            width = finish - start
            color = colors[(pid - 1) % len(colors)]
            rect = pg.BarGraphItem(x=[start], height=0.9, width=width, y=[y_base], brush=color)
            self.gantt_view.addItem(rect)
            text = pg.TextItem(text=f"P{pid}", color='w', anchor=(0.5, 0.5))
            text.setPos(start + width / 2, y_base + 0.45)
            self.gantt_view.addItem(text)
            y_base += 1
        self.gantt_view.setRange(yRange=(-0.5, y_base))

class MainWindow(QMainWindow):
    """Main application window with navigation and polished UI."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Visualization Tool")
        self.resize(1200, 800)

        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Navigation menu with polished styling
        self.menu = QListWidget()
        self.menu.addItems(["System Monitor", "Process Scheduling"])
        self.menu.setStyleSheet("""
            QListWidget {
                background-color: #2e2e2e;
                color: white;
                font: 12pt Arial;
                border: none;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #5a5a5a;
            }
        """)
        self.menu.setFixedWidth(200)
        layout.addWidget(self.menu)

        # Stacked widget for pages
        self.pages = QStackedWidget()
        self.pages.addWidget(HomeDashboard())
        self.pages.addWidget(ProcessScheduling())
        layout.addWidget(self.pages)

        # Connect menu to page switching
        self.menu.currentRowChanged.connect(self.display_page)

    def display_page(self, index):
        """Switch to the selected page."""
        self.pages.setCurrentIndex(index)

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())  # Apply dark theme
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    