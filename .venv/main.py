import sys
import math
import psutil

# For NVIDIA GPU usage (optional)
try:
    from pynvml import (
        nvmlInit, nvmlShutdown,
        nvmlDeviceGetCount, nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetUtilizationRates
    )
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

from PyQt5.QtCore import (
    Qt, QRectF, QPointF, QTimer, QPropertyAnimation,
    QEasingCurve, QEvent, pyqtSignal, pyqtProperty
)
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton
)

from process_tab import ProcessTab  # <-- If you have a separate file for process tab

# Utility functions to get system usage metrics
def get_cpu_usage_percent():
    return psutil.cpu_percent(interval=None)

def get_ram_usage_percent():
    return psutil.virtual_memory().percent

def get_disk_usage_percent(drive='C:'):
    return psutil.disk_usage(drive).percent

def get_nvidia_gpu_usage_percent(gpu_index=0):
    if not NVML_AVAILABLE:
        return 0
    nvmlInit()
    count = nvmlDeviceGetCount()
    if gpu_index >= count:
        nvmlShutdown()
        return 0
    handle = nvmlDeviceGetHandleByIndex(gpu_index)
    util = nvmlDeviceGetUtilizationRates(handle)
    nvmlShutdown()
    return util.gpu  # 0..100

sciFiFontName = "Conthrax"  # Replace with "Arial" if Conthrax is unavailable

# Custom gauge widget with animation support
class VerticalSemiGauge(QWidget):
    """
    Semi-circular gauge. Displays values from 0 to 100, top to bottom.
    """
    valueChanged = pyqtSignal(float)

    def __init__(self, title="CPU Usage", parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._maxValue = 100.0
        self.thickness = 25
        self.margin = 100
        self.setMinimumSize(500, 600)
        self.title = title

    def setValue(self, v):
        v = max(0.0, min(self._maxValue, float(v)))
        if v != self._value:
            self._value = v
            self.valueChanged.emit(self._value)
            self.update()

    def getValue(self):
        return self._value

    value = pyqtProperty(float, getValue, setValue, notify=valueChanged)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        width = rect.width()
        height = rect.height()
        R = min(width, height) / 2 - self.margin
        cx = rect.center().x()
        cy = rect.center().y()

        start_deg = 230
        total_deg = -210
        ratio = self._value / float(self._maxValue)
        active_deg = ratio * total_deg

        arcRect = QRectF(cx - R, cy - R, 2 * R, 2 * R)

        # Background arc
        pen_bg = QPen(QColor(80, 80, 80), self.thickness, cap=Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawArc(arcRect, int(start_deg * 16), int(total_deg * 16))

        # Active arc
        pen_active = QPen(QColor(255, 255, 255), self.thickness, cap=Qt.RoundCap)
        painter.setPen(pen_active)
        painter.drawArc(arcRect, int(start_deg * 16), int(active_deg * 16))

        # Needle
        needle_angle_deg = start_deg + active_deg
        needle_angle_rad = math.radians(needle_angle_deg)
        needle_len = R - self.thickness / 2 - 5
        needle_start = QPointF(cx, cy)
        needle_end = QPointF(
            cx + needle_len * math.cos(needle_angle_rad),
            cy - needle_len * math.sin(needle_angle_rad)
        )
        pen_needle = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen_needle)
        painter.drawLine(needle_start, needle_end)

        # Title
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont(sciFiFontName, 14, QFont.Bold))
        painter.drawText(cx + 15, cy + 30, self.title)

# Main application window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS Process Visualizer")
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        # Sidebar
        self.menuFrame = QWidget()
        self.menuFrame.setStyleSheet("background-color: #000000; font-family: Conthrax;")
        self.menuFrame.setFixedWidth(280)

        menuLayout = QVBoxLayout(self.menuFrame)
        menuLayout.setContentsMargins(0, 0, 0, 0)
        menuLayout.setSpacing(0)

        menuHeader = QLabel("MENU")
        menuHeader.setStyleSheet("color: white; font-size: 26px; padding: 18px;")
        menuLayout.addWidget(menuHeader)

        # Tab buttons
        self.btnOverview = QPushButton("Overview")
        self.btnCPU = QPushButton("CPU")
        self.btnGPU = QPushButton("GPU")
        self.btnRAM = QPushButton("RAM")
        self.btnDisk = QPushButton("Disk")
        self.btnProcesses = QPushButton("Processes")
        self.btnSched = QPushButton("Scheduling Algorithm")

        self.tabButtons = [
            self.btnOverview, self.btnCPU, self.btnGPU, self.btnRAM,
            self.btnDisk, self.btnProcesses, self.btnSched
        ]

        for btn in self.tabButtons:
            btn.setStyleSheet("""
                QPushButton {
                    color: #FFFFFF;
                    font-size: 18px;
                    text-align: left;
                    padding: 10px 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #3A3A3A;
                    border-left: 4px solid #00A2FF;
                }
            """)
            menuLayout.addWidget(btn)

        menuLayout.addStretch()
        central_layout.addWidget(self.menuFrame)

        # Separator
        separator = QWidget()
        separator.setFixedWidth(1)
        separator.setStyleSheet("background-color: #FFFFFF;")
        central_layout.addWidget(separator)

        from PyQt5.QtWidgets import QStackedWidget
        self.stacked = QStackedWidget()
        central_layout.addWidget(self.stacked, stretch=1)

        # 1) Create the "overview" widget:
        self.overviewWidget = QWidget()
        overviewLayout = QVBoxLayout(self.overviewWidget)
        overviewLayout.setContentsMargins(20, 20, 20, 20)
        overviewLayout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("OS Process Visualizer")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_font = QFont(sciFiFontName, 40, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background-color: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        overviewLayout.addLayout(header_layout)

        # The gauge grid
        grid = QGridLayout()
        self.cpuGauge = VerticalSemiGauge("CPU Usage")
        self.cpuLabel = QLabel("0.00%")
        self.setupLabel(self.cpuLabel)
        cpuPanel = QWidget()
        cpuLayout = QVBoxLayout(cpuPanel)
        cpuLayout.setContentsMargins(0,0,0,0)
        cpuLayout.setSpacing(5)
        cpuLayout.addWidget(self.cpuGauge)
        cpuLayout.addWidget(self.cpuLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(cpuPanel, 0, 0, alignment=Qt.AlignCenter)

        self.ramGauge = VerticalSemiGauge("RAM Usage")
        self.ramLabel = QLabel("0.00%")
        self.setupLabel(self.ramLabel)
        ramPanel = QWidget()
        ramLayout = QVBoxLayout(ramPanel)
        ramLayout.setContentsMargins(0,0,0,0)
        ramLayout.setSpacing(5)
        ramLayout.addWidget(self.ramGauge)
        ramLayout.addWidget(self.ramLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(ramPanel, 0, 1, alignment=Qt.AlignCenter)

        self.gpuGauge = VerticalSemiGauge("GPU Usage")
        self.gpuLabel = QLabel("0.00%")
        self.setupLabel(self.gpuLabel)
        gpuPanel = QWidget()
        gpuLayout = QVBoxLayout(gpuPanel)
        gpuLayout.setContentsMargins(0,0,0,0)
        gpuLayout.setSpacing(5)
        gpuLayout.addWidget(self.gpuGauge)
        gpuLayout.addWidget(self.gpuLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(gpuPanel, 1, 0, alignment=Qt.AlignCenter)

        self.diskGauge = VerticalSemiGauge("Disk Usage (C:)")
        self.diskLabel = QLabel("0.00%")
        self.setupLabel(self.diskLabel)
        diskPanel = QWidget()
        diskLayout = QVBoxLayout(diskPanel)
        diskLayout.setContentsMargins(0,0,0,0)
        diskLayout.setSpacing(5)
        diskLayout.addWidget(self.diskGauge)
        diskLayout.addWidget(self.diskLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(diskPanel, 1, 1, alignment=Qt.AlignCenter)

        overviewLayout.addLayout(grid, stretch=1)

        # 2) Create the "Processes" widget:
        self.processWidget = ProcessTab(self)  # from process_tab.py
        # If you want a placeholder: self.processWidget = QWidget()

        # 3) Add both to the stacked widget:
        self.stacked.addWidget(self.overviewWidget)  # index 0
        self.stacked.addWidget(self.processWidget)   # index 1

        # Connect signals
        self.cpuGauge.valueChanged.connect(lambda v: self.cpuLabel.setText(f"{v:.2f}%"))
        self.ramGauge.valueChanged.connect(lambda v: self.ramLabel.setText(f"{v:.2f}%"))
        self.gpuGauge.valueChanged.connect(lambda v: self.gpuLabel.setText(f"{v:.2f}%"))
        self.diskGauge.valueChanged.connect(lambda v: self.diskLabel.setText(f"{v:.2f}%"))

        self.currentTab = self.btnOverview
        self.updateTabStyles()

        for btn in self.tabButtons:
            btn.clicked.connect(lambda checked, b=btn: self.setCurrentTab(b))

        # Timer for updates
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateUsages)
        self.timer.start()

        # Make "Processes" show the second tab:
        self.btnProcesses.clicked.connect(self.showProcessTab)
        # Also "Overview" shows first tab:
        #self.btnOverview.clicked.connect(self.showOverviewTab)

    def setupLabel(self, label):
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont(sciFiFontName, 20, QFont.Bold))
        label.setStyleSheet("color: white;")

    def updateTabStyles(self):
        for btn in self.tabButtons:
            if btn == self.currentTab:
                btn.setStyleSheet("""
                    QPushButton {
                        color: #FFFFFF;
                        font-size: 18px;
                        text-align: left;
                        padding: 10px 10px;
                        border: none;
                        background-color: #1A1A1A;
                        border-left: 4px solid #00A2FF;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        color: #FFFFFF;
                        font-size: 18px;
                        text-align: left;
                        padding: 10px 10px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #3A3A3A;
                        border-left: 4px solid #00A2FF;
                    }
                """)

    def setCurrentTab(self, btn):
        self.currentTab = btn
        self.updateTabStyles()
        

    # NEW function to show processes tab
    def showProcessTab(self):
        self.setCurrentTab(self.btnProcesses)
        self.stacked.setCurrentIndex(1)

    # NEW function to show overview
    def showOverviewTab(self):
        self.setCurrentTab(self.btnOverview)
        self.stacked.setCurrentIndex(0)

    def updateUsages(self):
        print("updating")
        # *** Keep references to avoid garbage collection ***
        if not hasattr(self, '_animRefs'):
            self._animRefs = []

        # CPU
        cpu_val = get_cpu_usage_percent()
        animation_cpu = QPropertyAnimation(self.cpuGauge, b"value")
        animation_cpu.setStartValue(self.cpuGauge.value)
        animation_cpu.setEndValue(cpu_val)
        animation_cpu.setDuration(3000)
        animation_cpu.setEasingCurve(QEasingCurve.Linear)
        animation_cpu.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(animation_cpu)  # keep reference

        # RAM
        ram_val = get_ram_usage_percent()
        animation_ram = QPropertyAnimation(self.ramGauge, b"value")
        animation_ram.setStartValue(self.ramGauge.value)
        animation_ram.setEndValue(ram_val)
        animation_ram.setDuration(3000)
        animation_ram.setEasingCurve(QEasingCurve.Linear)
        animation_ram.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(animation_ram)

        # GPU
        gpu_val = get_nvidia_gpu_usage_percent(0)
        animation_gpu = QPropertyAnimation(self.gpuGauge, b"value")
        animation_gpu.setStartValue(self.gpuGauge.value)
        animation_gpu.setEndValue(gpu_val)
        animation_gpu.setDuration(3000)
        animation_gpu.setEasingCurve(QEasingCurve.Linear)
        animation_gpu.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(animation_gpu)

        # Disk
        disk_val = get_disk_usage_percent("C:")
        animation_disk = QPropertyAnimation(self.diskGauge, b"value")
        animation_disk.setStartValue(self.diskGauge.value)
        animation_disk.setEndValue(disk_val)
        animation_disk.setDuration(3000)
        animation_disk.setEasingCurve(QEasingCurve.Linear)
        animation_disk.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(animation_disk)

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.showMaximized()
    sys.exit(app.exec_())
