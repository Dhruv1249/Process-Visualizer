import sys
import math
import psutil

try:
    from pynvml import *
    gpu_avilable = True
except ImportError:
    gpu_avilable = False

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# ----------------IMPORTS FOR TABS ----------------
from cpu_tab import CpuTab
from ram_tab import RamTab
from disk_tab import DiskTab
from process_tab import ProcessTab
from scheduling_tab import SchedulingTab
# ------------------------------------------------------

def cpu_usage():
    return psutil.cpu_percent(interval=None)

def ram_usage():
    return psutil.virtual_memory().percent

def disk_usage(drive='C:'):
    return psutil.disk_usage(drive).percent

def get_nvidia_gpu_usage_percent(gpu_index=0):
    try:
        if not  gpu_avilable:
            return 0
        nvmlInit()
        count = nvmlDeviceGetCount()
        if gpu_index >= count:
            nvmlShutdown()
            return 0
        handle = nvmlDeviceGetHandleByIndex(gpu_index)
        util = nvmlDeviceGetUtilizationRates(handle)
        nvmlShutdown()
        return util.gpu  
    except:
        return 0

mainFont = "Conthrax"  #It will automatically take Arial as default if conthrax not installed so dw abt installing it

#The main widget class
class dial(QWidget):
   
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
        
        #Might change the degrees here later
        start_deg = 230
        total_deg = -210
        ratio = self._value / float(self._maxValue)
        active_deg = ratio * total_deg

        arcRect = QRectF(cx - R, cy - R, 2 * R, 2 * R)

        stick_bg = QPen(QColor(80, 80, 80), self.thickness, cap=Qt.RoundCap)
        painter.setPen(stick_bg)
        painter.drawArc(arcRect, int(start_deg * 16), int(total_deg * 16))

        stick_ac = QPen(QColor(255, 255, 255), self.thickness, cap=Qt.RoundCap)
        painter.setPen(stick_ac)
        painter.drawArc(arcRect, int(start_deg * 16), int(active_deg * 16))

        angle = start_deg + active_deg
        rad = math.radians(angle)
        leng = R - self.thickness / 2 - 5
        start = QPointF(cx, cy)
        end = QPointF(
            cx + leng * math.cos(rad),
            cy - leng * math.sin(rad)
        )
        pen_needle = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen_needle)
        painter.drawLine(start, end)

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont(mainFont, 14, QFont.Bold))
        painter.drawText(cx + 15, cy + 30, self.title)

class window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS Process Visualizer")
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")

        wid = QWidget()
        self.setCentralWidget(wid)
        layout = QHBoxLayout(wid)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.menuf = QWidget()
        self.menuf.setStyleSheet("background-color: #000000; font-family: Conthrax;")
        self.menuf.setFixedWidth(280)

        menu = QVBoxLayout(self.menuf)
        menu.setContentsMargins(0, 0, 0, 0)
        menu.setSpacing(0)

        head = QLabel("MENU")
        head.setStyleSheet("color: white; font-size: 26px; padding: 18px;")
        menu.addWidget(head)

        self.btnOv = QPushButton("Overview")
        self.btnCPU = QPushButton("CPU")
        self.btnRAM = QPushButton("RAM")
        self.btnDisk = QPushButton("Disk")
        self.btnProcesses = QPushButton("Processes")
        self.btnSched = QPushButton("Scheduling Algorithm")

        self.tabBtn = [
            self.btnOv, self.btnCPU, self.btnRAM,
            self.btnDisk, self.btnProcesses, self.btnSched
        ]

        for btn in self.tabBtn:
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
            menu.addWidget(btn)

        menu.addStretch()
        layout.addWidget(self.menuf)

        sep = QWidget()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background-color: #FFFFFF;")
        layout.addWidget(sep)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, stretch=1)

        self.ovWid = QWidget()
        ovLayout = QVBoxLayout(self.ovWid)
        ovLayout.setContentsMargins(20, 20, 20, 20)
        ovLayout.setSpacing(20)

        header_layout = QHBoxLayout()
        title_label = QLabel("OS Process Visualizer")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_font = QFont(mainFont, 40, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background-color: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        ovLayout.addLayout(header_layout)

        grid = QGridLayout()

        self.cpuGauge = dial("CPU Usage")
        self.cpuLabel = QLabel("0.00%")
        self.setLab(self.cpuLabel)
        cpuPanel = QWidget()
        cpuLayout = QVBoxLayout(cpuPanel)
        cpuLayout.setContentsMargins(0,0,0,0)
        cpuLayout.setSpacing(5)
        cpuLayout.addWidget(self.cpuGauge)
        cpuLayout.addWidget(self.cpuLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(cpuPanel, 0, 0, alignment=Qt.AlignCenter)

        self.ramGauge = dial("RAM Usage")
        self.ramLabel = QLabel("0.00%")
        self.setLab(self.ramLabel)
        ramPanel = QWidget()
        ramLayout = QVBoxLayout(ramPanel)
        ramLayout.setContentsMargins(0,0,0,0)
        ramLayout.setSpacing(5)
        ramLayout.addWidget(self.ramGauge)
        ramLayout.addWidget(self.ramLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(ramPanel, 0, 1, alignment=Qt.AlignCenter)

        self.gpuGauge = dial("GPU Usage")
        self.gpuLabel = QLabel("0.00%")
        self.setLab(self.gpuLabel)
        gpuPanel = QWidget()
        gpuLayout = QVBoxLayout(gpuPanel)
        gpuLayout.setContentsMargins(0,0,0,0)
        gpuLayout.setSpacing(5)
        gpuLayout.addWidget(self.gpuGauge)
        gpuLayout.addWidget(self.gpuLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(gpuPanel, 1, 0, alignment=Qt.AlignCenter)

        self.diskGauge = dial("Disk Usage (C:)")
        self.diskLabel = QLabel("0.00%")
        self.setLab(self.diskLabel)
        diskPanel = QWidget()
        diskLayout = QVBoxLayout(diskPanel)
        diskLayout.setContentsMargins(0,0,0,0)
        diskLayout.setSpacing(5)
        diskLayout.addWidget(self.diskGauge)
        diskLayout.addWidget(self.diskLabel, alignment=Qt.AlignHCenter)
        grid.addWidget(diskPanel, 1, 1, alignment=Qt.AlignCenter)

        ovLayout.addLayout(grid, stretch=1)
        # 1) Overview tab
        self.stack.addWidget(self.ovWid)

        # 2) CPU tab
        self.cpuTab = CpuTab(self)
        self.stack.addWidget(self.cpuTab)

        #3 Gpu Tab removed for now

        # 4) RAM tab
        from ram_tab import RamTab
        self.ramTab = RamTab(self)
        self.stack.addWidget(self.ramTab)

        # 5) Disk tab
        from disk_tab import DiskTab
        self.diskTab = DiskTab(self)
        self.stack.addWidget(self.diskTab)

        # 6) Processes tab 
        from process_tab import ProcessTab
        self.processTab = ProcessTab(self)
        self.stack.addWidget(self.processTab)

        # 7) Scheduling tab
        from scheduling_tab import SchedulingTab
        self.schedTab = SchedulingTab(self)
        self.stack.addWidget(self.schedTab)

        self.cpuGauge.valueChanged.connect(lambda v: self.cpuLabel.setText(f"{v:.2f}%"))
        self.ramGauge.valueChanged.connect(lambda v: self.ramLabel.setText(f"{v:.2f}%"))
        self.gpuGauge.valueChanged.connect(lambda v: self.gpuLabel.setText(f"{v:.2f}%"))
        self.diskGauge.valueChanged.connect(lambda v: self.diskLabel.setText(f"{v:.2f}%"))

        self.currentTab = self.btnOv
        self.upTb()

        self.btnOv.clicked.connect(lambda: self.showTab(0, self.btnOv))
        self.btnCPU.clicked.connect(lambda: self.showTab(1, self.btnCPU))
        self.btnRAM.clicked.connect(lambda: self.showTab(2, self.btnRAM))
        self.btnDisk.clicked.connect(lambda: self.showTab(3, self.btnDisk))
        self.btnProcesses.clicked.connect(lambda: self.showTab(4, self.btnProcesses))
        self.btnSched.clicked.connect(lambda: self.showTab(5, self.btnSched))

        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.updateUsages)
        self.timer.start()

    def setLab(self, label):
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont(mainFont, 20, QFont.Bold))
        label.setStyleSheet("color: white;")

    def upTb(self):
        for btn in self.tabBtn:
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

    def showTab(self, index, button):
        self.stack.setCurrentIndex(index)
        self.currentTab = button
        self.upTb()
        if index == 0:  # Overview tab
            self.timer.start()
        else:
            self.timer.stop()

    def updateUsages(self):
        if not hasattr(self, '_animRefs'):
            self._animRefs = []

        # CPU
        cpu_val = cpu_usage()
        anim_cpu = QPropertyAnimation(self.cpuGauge, b"value")
        anim_cpu.setStartValue(self.cpuGauge.value)
        anim_cpu.setEndValue(cpu_val)
        anim_cpu.setDuration(3000)
        anim_cpu.setEasingCurve(QEasingCurve.Linear)
        anim_cpu.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(anim_cpu)

        # RAM
        ram_val = ram_usage()
        anim_ram = QPropertyAnimation(self.ramGauge, b"value")
        anim_ram.setStartValue(self.ramGauge.value)
        anim_ram.setEndValue(ram_val)
        anim_ram.setDuration(3000)
        anim_ram.setEasingCurve(QEasingCurve.Linear)
        anim_ram.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(anim_ram)

        # GPU
        gpu_val = get_nvidia_gpu_usage_percent(0)
        anim_gpu = QPropertyAnimation(self.gpuGauge, b"value")
        anim_gpu.setStartValue(self.gpuGauge.value)
        anim_gpu.setEndValue(gpu_val)
        anim_gpu.setDuration(3000)
        anim_gpu.setEasingCurve(QEasingCurve.Linear)
        anim_gpu.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(anim_gpu)

        # Disk
        disk_val = disk_usage("C:")
        anim_disk = QPropertyAnimation(self.diskGauge, b"value")
        anim_disk.setStartValue(self.diskGauge.value)
        anim_disk.setEndValue(disk_val)
        anim_disk.setDuration(3000)
        anim_disk.setEasingCurve(QEasingCurve.Linear)
        anim_disk.start(QPropertyAnimation.DeleteWhenStopped)
        self._animRefs.append(anim_disk)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = window()
    w.showMaximized()
    sys.exit(app.exec_())
