import psutil
import math
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QStyleOption, QStyle
)
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, QRectF, QPoint, QThread, pyqtSignal

sciFiFontName = "Conthrax"

# --------------------- Background Worker Thread for Process Data ---------------------
class ProcessDataWorker(QThread):
    """Worker thread to fetch process data without blocking the UI"""
    dataReady = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.paused = False
    
    def run(self):
        while self.running:
            if not self.paused:
                try:
                    results = []
                    # Use batch processing with pre-fetched info to reduce overhead
                    for proc_info in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                        try:
                            pName = proc_info.info['name'] or "Unknown"
                            # Skip known idle processes
                            if pName.lower() in ["system idle process", "idle"]:
                                continue
                            pID = proc_info.info['pid']
                            pCPU = proc_info.info['cpu_percent'] or 0.0
                            
                            # Only get memory info for processes with significant CPU usage.
                            if pCPU > 0.1:  # Only get memory for processes using CPU
                                try:
                                    p = psutil.Process(proc_info.info['pid'])
                                    memMB = p.memory_info().rss / (1024*1024)
                                except:
                                    memMB = 0.0
                            else:
                                memMB = 0.0
                                
                            # New tuple now includes the PID as the second element.
                            results.append((pName, pID, pCPU, memMB))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Emit the results
                    self.dataReady.emit(results)
                except Exception as e:
                    print(f"Error in process data worker: {e}")
                
                # Sleep to prevent excessive CPU usage
                time.sleep(2)  # 2 second interval between updates
            else:
                time.sleep(0.5)
    
    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False
    
    def stop(self):
        self.running = False
        self.wait()


# --------------------- A Custom Widget for the CPU Bar Graph ---------------------
class CPUBarGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Data for animation
        self.oldData = []  # List of (name, usage, position)
        self.newData = []  # List of (name, usage, position)
        self.animFrac = 1.0  # Animation fraction (0 to 1)
        self.animationActive = False
        
        # Animation parameters - reduced for better performance
        self.ANIM_DURATION = 500  # Reduced from 1000ms to 500ms
        self.FPS_INTERVAL = 16  # ~30 FPS (reduced from 60 FPS)
        self.waveTime = 0.0  # For wave effect
        self.waveSpeed = 1.0  # Reduced from 2.0
        
        # Transition states
        self.transitions = {}  # {name: {'startPos': int, 'endPos': int, 'zScale': float, 'currentPos': float}}
        
        # Timer
        self.animTimer = QTimer(self)
        self.animTimer.timeout.connect(self.onAnimFrame)
        self.animTimer.start(self.FPS_INTERVAL)
        
        self.setMinimumSize(400, 300)
        
        # Performance optimization: track if widget is visible
        self.isVisible = False

    def showEvent(self, event):
        super().showEvent(event)
        self.isVisible = True
    
    def hideEvent(self, event):
        super().hideEvent(event)
        self.isVisible = False

    def setData(self, data):
        """Update graph data and prepare animations.
           data should be a list of tuples: (name, usage)
        """
        # Skip if not visible
        if not self.isVisible:
            return
            
        if not self.oldData:
            self.oldData = [(name, usage, i) for i, (name, usage) in enumerate(data[:10])]
        self.newData = [(name, usage, i) for i, (name, usage) in enumerate(data[:10])]
        
        # Detect position changes
        self.transitions = {}
        for old in self.oldData:
            oldName, oldUsage, oldPos = old
            for new in self.newData:
                newName, newUsage, newPos = new
                if oldName == newName and oldPos != newPos:
                    # Determine z-scale: moving down shrinks, moving up grows
                    zScale = 0.8 if newPos > oldPos else 1.2
                    self.transitions[oldName] = {
                        'startPos': oldPos,
                        'endPos': newPos,
                        'zScale': zScale,
                        'currentPos': oldPos
                    }
        
        self.animFrac = 0.0
        self.animationActive = True if self.transitions else False

    def onAnimFrame(self):
        """Update animation state."""
        if not self.isVisible:
            return
            
        step = self.FPS_INTERVAL / 1000.0
        self.waveTime += step * self.waveSpeed
        
        if self.animationActive:
            self.animFrac += self.FPS_INTERVAL / self.ANIM_DURATION
            if self.animFrac >= 1.0:
                self.animFrac = 1.0
                self.animationActive = False
                self.oldData = self.newData[:]
                self.transitions.clear()
            else:
                for trans in self.transitions.values():
                    trans['currentPos'] = self.easeInOutQuad(
                        self.animFrac, trans['startPos'], trans['endPos'] - trans['startPos'], 1.0
                    )
            self.update()

    def easeInOutQuad(self, t, b, c, d):
        """Easing function for smooth animation."""
        t /= d / 2
        if t < 1:
            return c / 2 * t * t + b
        t -= 1
        return -c / 2 * (t * (t - 2) - 1) + b

    def paintEvent(self, event):
        """Render the bar graph with z-axis animation."""
        if not self.isVisible or (not self.oldData and not self.newData):
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        w, h = rect.width(), rect.height()
        
        dataCount = max(len(self.newData), len(self.oldData))
        if dataCount == 0:
            return
        
        # Layout
        barSpacing = 10
        totalSpacing = (dataCount + 1) * barSpacing
        barHeight = (h - totalSpacing) / dataCount
        xOffset = 150  # Space for names
        rightMargin = 20
        
        # Pad data
        oldPadded = self.oldData + [("", 0, i) for i in range(len(self.oldData), dataCount)]
        newPadded = self.newData + [("", 0, i) for i in range(len(self.newData), dataCount)]
        
        # Max usage for scaling
        usageMax = max([u for (_, u, _) in oldPadded + newPadded], default=1.0)
        
        # Prepare render list
        renderList = []
        for i in range(dataCount):
            oldName, oldUsage, _ = oldPadded[i]
            newName, newUsage, newPos = newPadded[i]
            usage = oldUsage + self.animFrac * (newUsage - oldUsage)
            
            if newName in self.transitions:
                trans = self.transitions[newName]
                currentPos = trans['currentPos']
                zScale = 1.0 + (trans['zScale'] - 1.0) * self.animFrac
            else:
                currentPos = newPos
                zScale = 1.0
            
            topY = barSpacing + currentPos * (barHeight + barSpacing)
            waveOffset = math.sin(self.waveTime + newPos * 0.5) * 5
            topY += waveOffset
            displayLen = (usage / usageMax) * (w - xOffset - rightMargin) * 0.8 * zScale
            
            renderList.append((newName, usage, topY, displayLen, barHeight * zScale, zScale))
        
        renderList.sort(key=lambda x: x[5], reverse=True)
        
        for name, usage, topY, displayLen, scaledHeight, zScale in renderList:
            barRect = QRectF(xOffset, topY, displayLen, scaledHeight)
            painter.setPen(QPen(QColor("#007FFF"), 1.0))
            painter.setBrush(QBrush(QColor("#00A2FF")))
            painter.drawRoundedRect(barRect, 5, 5)
            
            # Draw name and usage
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 12))
            truncatedName = (name[:7] + "...") if len(name) > 7 else name
            painter.drawText(QPoint(10, int(topY + scaledHeight * 0.7)), truncatedName)
            painter.drawText(int(xOffset + displayLen + 5), int(topY + scaledHeight * 0.7), f"{usage:.1f}%")

# --------------------- New Custom Widget for the RAM Bar Graph ---------------------
class RAMBarGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Data for animation
        self.oldData = []  # List of (name, usage, position)
        self.newData = []  # List of (name, usage, position)
        self.animFrac = 1.0  # Animation fraction (0 to 1)
        self.animationActive = False
        
        # Animation parameters - same as CPU graph
        self.ANIM_DURATION = 500
        self.FPS_INTERVAL = 16
        self.waveTime = 0.0
        self.waveSpeed = 1.0
        
        # Transition states
        self.transitions = {}
        
        # Timer for animation
        self.animTimer = QTimer(self)
        self.animTimer.timeout.connect(self.onAnimFrame)
        self.animTimer.start(self.FPS_INTERVAL)
        
        self.setMinimumSize(400, 300)
        self.isVisible = False

    def showEvent(self, event):
        super().showEvent(event)
        self.isVisible = True

    def hideEvent(self, event):
        super().hideEvent(event)
        self.isVisible = False

    def setData(self, data):
        """Update graph data; data is list of (name, usage) where usage represents RAM in MB."""
        if not self.isVisible:
            return
            
        if not self.oldData:
            self.oldData = [(name, usage, i) for i, (name, usage) in enumerate(data[:10])]
        self.newData = [(name, usage, i) for i, (name, usage) in enumerate(data[:10])]
        
        self.transitions = {}
        for old in self.oldData:
            oldName, oldUsage, oldPos = old
            for new in self.newData:
                newName, newUsage, newPos = new
                if oldName == newName and oldPos != newPos:
                    zScale = 0.8 if newPos > oldPos else 1.2
                    self.transitions[oldName] = {
                        'startPos': oldPos,
                        'endPos': newPos,
                        'zScale': zScale,
                        'currentPos': oldPos
                    }
        
        self.animFrac = 0.0
        self.animationActive = True if self.transitions else False

    def onAnimFrame(self):
        if not self.isVisible:
            return
        
        step = self.FPS_INTERVAL / 1000.0
        self.waveTime += step * self.waveSpeed
        
        if self.animationActive:
            self.animFrac += self.FPS_INTERVAL / self.ANIM_DURATION
            if self.animFrac >= 1.0:
                self.animFrac = 1.0
                self.animationActive = False
                self.oldData = self.newData[:]
                self.transitions.clear()
            else:
                for trans in self.transitions.values():
                    trans['currentPos'] = self.easeInOutQuad(
                        self.animFrac, trans['startPos'], trans['endPos'] - trans['startPos'], 1.0
                    )
            self.update()

    def easeInOutQuad(self, t, b, c, d):
        t /= d / 2
        if t < 1:
            return c / 2 * t * t + b
        t -= 1
        return -c / 2 * (t * (t - 2) - 1) + b

    def paintEvent(self, event):
        if not self.isVisible or (not self.oldData and not self.newData):
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        w, h = rect.width(), rect.height()
        
        dataCount = max(len(self.newData), len(self.oldData))
        if dataCount == 0:
            return
        
        barSpacing = 10
        totalSpacing = (dataCount + 1) * barSpacing
        barHeight = (h - totalSpacing) / dataCount
        xOffset = 150
        rightMargin = 20
        
        oldPadded = self.oldData + [("", 0, i) for i in range(len(self.oldData), dataCount)]
        newPadded = self.newData + [("", 0, i) for i in range(len(self.newData), dataCount)]
        
        usageMax = max([u for (_, u, _) in oldPadded + newPadded], default=1.0)
        
        renderList = []
        for i in range(dataCount):
            oldName, oldUsage, _ = oldPadded[i]
            newName, newUsage, newPos = newPadded[i]
            usage = oldUsage + self.animFrac * (newUsage - oldUsage)
            
            if newName in self.transitions:
                trans = self.transitions[newName]
                currentPos = trans['currentPos']
                zScale = 1.0 + (trans['zScale'] - 1.0) * self.animFrac
            else:
                currentPos = newPos
                zScale = 1.0
            
            topY = barSpacing + currentPos * (barHeight + barSpacing)
            waveOffset = math.sin(self.waveTime + newPos * 0.5) * 5
            topY += waveOffset
            displayLen = (usage / usageMax) * (w - xOffset - rightMargin) * 0.8 * zScale
            
            renderList.append((newName, usage, topY, displayLen, barHeight * zScale, zScale))
        
        renderList.sort(key=lambda x: x[5], reverse=True)
        
        for name, usage, topY, displayLen, scaledHeight, zScale in renderList:
            barRect = QRectF(xOffset, topY, displayLen, scaledHeight)
            painter.setPen(QPen(QColor("#007FFF"), 1.0))
            painter.setBrush(QBrush(QColor("#00A2FF")))
            painter.drawRoundedRect(barRect, 5, 5)
            
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 12))
            truncatedName = (name[:7] + "...") if len(name) > 7 else name
            painter.drawText(QPoint(10, int(topY + scaledHeight * 0.7)), truncatedName)
            painter.drawText(int(xOffset + displayLen + 5), int(topY + scaledHeight * 0.7), f"{usage:.1f}MB")

# --------------------- Modifications in ProcessTab ---------------------
class ProcessTab(QWidget):
    """
    The 'Process' tab has two sub-sub-tabs: 'List' and 'Graph'.
    'List' displays a table of processes with columns [Process Name, PID, CPU%, RAM(MB)].
    'Graph' displays buttons 'CPU' and 'RAM' to show corresponding sideways bar graphs.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentSubTab = None
        self.isVisible = False
        self.processData = []  # Cached process data
        self.lastUpdateTime = 0
        self.updatePending = False
        
        self.dataWorker = ProcessDataWorker()
        self.dataWorker.dataReady.connect(self.onProcessDataReady)
        self.dataWorker.start()

        self.uiUpdateTimer = QTimer(self)
        self.uiUpdateTimer.setInterval(500)
        self.uiUpdateTimer.timeout.connect(self.updateUI)
        self.uiUpdateTimer.start()

        self.styleNormal = f"""
            QPushButton {{
                color: #FFFFFF;
                font-family: {sciFiFontName};
                font-size: 26px;
                padding: 18px;
                background-color: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
        """

        self.styleSelected = f"""
            QPushButton {{
                color: #FFFFFF;
                font-family: {sciFiFontName};
                font-size: 26px;
                padding: 18px;
                background-color: #1A1A1A;
                border-left: 4px solid #00A2FF;
            }}
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 0, 0, 0)
        top_layout.setSpacing(0)

        self.btnList = QPushButton("List")
        self.btnGraph = QPushButton("Graph")

        sep_vertical = QFrame()
        sep_vertical.setFixedWidth(1)
        sep_vertical.setStyleSheet("background-color: white;")

        top_layout.addWidget(self.btnList)
        top_layout.addWidget(sep_vertical)
        top_layout.addWidget(self.btnGraph)
        main_layout.addLayout(top_layout)

        sep_horizontal = QFrame()
        sep_horizontal.setFixedHeight(1)
        sep_horizontal.setStyleSheet("background-color: white;")
        main_layout.addWidget(sep_horizontal)

        self.subContentLayout = QVBoxLayout()
        self.subContentLayout.setContentsMargins(0, 10, 0, 0)
        main_layout.addLayout(self.subContentLayout)

        self.listWidget = self.buildListUI()
        self.graphWidget = self.buildGraphUI()

        self.btnList.clicked.connect(lambda: self.setCurrentSubTab(self.btnList))
        self.btnGraph.clicked.connect(lambda: self.setCurrentSubTab(self.btnGraph))

        self.setCurrentSubTab(self.btnList)

    def showEvent(self, event):
        super().showEvent(event)
        self.isVisible = True
        self.dataWorker.resume()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.isVisible = False
        self.dataWorker.pause()

    def closeEvent(self, event):
        self.dataWorker.stop()
        super().closeEvent(event)

    def onProcessDataReady(self, data):
        self.processData = data
        self.updatePending = True

    def updateUI(self):
        if not self.isVisible or not self.updatePending:
            return
            
        self.updatePending = False
        
        if self.currentSubTab == self.btnList:
            self.populateTable()
        elif self.currentSubTab == self.btnGraph:
            if self.currentGraphSubTab == self.btnCPUGraph:
                self.updateCPUGraph()
            elif self.currentGraphSubTab == self.btnRAMGraph:
                self.updateRAMGraph()

    # -------------------- PART 1: The "List" Sub-Sub-Tab --------------------
    def buildListUI(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        colButtonsLayout = QHBoxLayout()
        colButtonsLayout.setContentsMargins(0, 0, 0, 0)
        colButtonsLayout.setSpacing(0)

        self.btnColProcess = QPushButton("Process Name")
        self.btnColPID = QPushButton("PID")
        self.btnColCPU = QPushButton("CPU%")
        self.btnColRAM = QPushButton("RAM(MB)")

        self.colButtons = [ self.btnColProcess, self.btnColPID, self.btnColCPU, self.btnColRAM ]

        colStyle = f"""
            QPushButton {{
                color: #FFFFFF;
                font-family: {sciFiFontName};
                font-size: 22px;
                padding: 8px;
                background-color: #000000;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
            QPushButton:checked {{
                background-color: #1A1A1A;
                border-left: 4px solid #00A2FF;
            }}
        """

        for b in self.colButtons:
            b.setCheckable(True)
            b.setStyleSheet(colStyle)
            colButtonsLayout.addWidget(b)

        layout.addLayout(colButtonsLayout)

        sep_cols = QFrame()
        sep_cols.setFixedHeight(1)
        sep_cols.setStyleSheet("background-color: white;")
        layout.addWidget(sep_cols)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont(sciFiFontName, 12))
        self.table.setRowCount(50)
        layout.addWidget(self.table)

        self.btnColProcess.clicked.connect(lambda: self.sortDataBy("process"))
        self.btnColPID.clicked.connect(lambda: self.sortDataBy("pid"))
        self.btnColCPU.clicked.connect(lambda: self.sortDataBy("cpu"))
        self.btnColRAM.clicked.connect(lambda: self.sortDataBy("ram"))

        self.sortKey = "cpu"
        self.sortDescending = True
        self.btnColCPU.setChecked(True)

        return container

    def populateTable(self):
        if not self.processData or not self.isVisible:
            return
            
        if self.sortKey == "process":
            idx = 0; self.sortDescending = False
        elif self.sortKey == "pid":
            idx = 1; self.sortDescending = False
        elif self.sortKey == "cpu":
            idx = 2; self.sortDescending = True
        elif self.sortKey == "ram":
            idx = 3; self.sortDescending = True
        else:
            idx = 2; self.sortDescending = True

        sorted_data = sorted(self.processData, key=lambda x: x[idx], reverse=self.sortDescending)[:50]
        
        if self.currentSubTab == self.btnList and self.isVisible:
            if self.table.rowCount() != len(sorted_data):
                self.table.setRowCount(len(sorted_data))
                
            for row, (pName, pID, pCPU, pRAM) in enumerate(sorted_data):
                current_name = self.table.item(row, 0)
                if not current_name or current_name.text() != str(pName):
                    itemName = QTableWidgetItem(str(pName))
                    itemName.setFont(QFont(sciFiFontName, 12))
                    itemName.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    self.table.setItem(row, 0, itemName)

                current_pid = self.table.item(row, 1)
                if not current_pid or current_pid.text() != str(pID):
                    itemPID = QTableWidgetItem(str(pID))
                    itemPID.setFont(QFont(sciFiFontName, 12))
                    itemPID.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 1, itemPID)

                current_cpu = self.table.item(row, 2)
                cpu_text = f"{pCPU:.1f}%"
                if not current_cpu or current_cpu.text() != cpu_text:
                    itemCPU = QTableWidgetItem(cpu_text)
                    itemCPU.setFont(QFont(sciFiFontName, 12))
                    itemCPU.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 2, itemCPU)

                current_ram = self.table.item(row, 3)
                ram_text = f"{pRAM:.1f}MB"
                if not current_ram or current_ram.text() != ram_text:
                    itemRAM = QTableWidgetItem(ram_text)
                    itemRAM.setFont(QFont(sciFiFontName, 12))
                    itemRAM.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 3, itemRAM)

    def sortDataBy(self, key):
        for b in self.colButtons:
            if key == "process" and b.text().lower().startswith("process"):
                b.setChecked(True)
            elif key == "pid" and b.text().lower() == "pid":
                b.setChecked(True)
            elif key == "cpu" and b.text().lower().startswith("cpu"):
                b.setChecked(True)
            elif key == "ram" and b.text().lower().startswith("ram"):
                b.setChecked(True)
            else:
                b.setChecked(False)
        self.sortKey = key
        self.populateTable()

    # -------------------- PART 2: The "Graph" Sub-Sub-Tab --------------------
    def buildGraphUI(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.currentGraphSubTab = None

        graphTopLayout = QHBoxLayout()
        graphTopLayout.setContentsMargins(10, 0, 0, 0)
        graphTopLayout.setSpacing(0)

        self.btnCPUGraph = QPushButton("CPU")
        self.btnRAMGraph = QPushButton("RAM")

        self.graphStyleNormal = f"""
            QPushButton {{
                color: #FFFFFF;
                font-family: {sciFiFontName};
                font-size: 20px;
                padding: 12px;
                background-color: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
        """
        self.graphStyleSelected = f"""
            QPushButton {{
                color: #FFFFFF;
                font-family: {sciFiFontName};
                font-size: 20px;
                padding: 12px;
                background-color: #1A1A1A;
                border-left: 4px solid #00A2FF;
            }}
        """

        sep_graph_vertical = QFrame()
        sep_graph_vertical.setFixedWidth(1)
        sep_graph_vertical.setStyleSheet("background-color: white;")

        self.btnCPUGraph.setStyleSheet(self.graphStyleNormal)
        self.btnRAMGraph.setStyleSheet(self.graphStyleNormal)

        graphTopLayout.addWidget(self.btnCPUGraph)
        graphTopLayout.addWidget(sep_graph_vertical)
        graphTopLayout.addWidget(self.btnRAMGraph)
        layout.addLayout(graphTopLayout)

        sep_graph_horizontal = QFrame()
        sep_graph_horizontal.setFixedHeight(1)
        sep_graph_horizontal.setStyleSheet("background-color: white;")
        layout.addWidget(sep_graph_horizontal)

        self.graphSubContentLayout = QVBoxLayout()
        self.graphSubContentLayout.setContentsMargins(0, 10, 0, 0)
        layout.addLayout(self.graphSubContentLayout)

        self.cpuBarGraphWidget = CPUBarGraphWidget()
        # Replace the RAM placeholder with our new bar graph widget:
        self.ramBarGraphWidget = RAMBarGraphWidget()

        self.btnCPUGraph.clicked.connect(lambda: self.setCurrentGraphSubTab(self.btnCPUGraph))
        self.btnRAMGraph.clicked.connect(lambda: self.setCurrentGraphSubTab(self.btnRAMGraph))

        self.setCurrentGraphSubTab(self.btnCPUGraph)

        return container

    def setCurrentGraphSubTab(self, btn):
        self.currentGraphSubTab = btn
        self.updateGraphSubTabStyles()

        for i in reversed(range(self.graphSubContentLayout.count())):
            item = self.graphSubContentLayout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)

        if btn == self.btnCPUGraph:
            self.graphSubContentLayout.addWidget(self.cpuBarGraphWidget)
            if self.processData and self.isVisible:
                self.updateCPUGraph()
        elif btn == self.btnRAMGraph:
            self.graphSubContentLayout.addWidget(self.ramBarGraphWidget)
            if self.processData and self.isVisible:
                self.updateRAMGraph()

    def updateGraphSubTabStyles(self):
        if self.currentGraphSubTab == self.btnCPUGraph:
            self.btnCPUGraph.setStyleSheet(self.graphStyleSelected)
            self.btnRAMGraph.setStyleSheet(self.graphStyleNormal)
        else:
            self.btnCPUGraph.setStyleSheet(self.graphStyleNormal)
            self.btnRAMGraph.setStyleSheet(self.graphStyleSelected)

    # -------------------- PART 3: Switching between "List" and "Graph" --------------------
    def setCurrentSubTab(self, btn):
        self.currentSubTab = btn
        self.updateSubTabStyles()

        for i in reversed(range(self.subContentLayout.count())):
            item = self.subContentLayout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)

        if btn == self.btnList:
            self.subContentLayout.addWidget(self.listWidget)
            if self.processData and self.isVisible:
                self.populateTable()
        else:
            self.subContentLayout.addWidget(self.graphWidget)
            if self.processData and self.isVisible:
                if self.currentGraphSubTab == self.btnCPUGraph:
                    self.updateCPUGraph()
                elif self.currentGraphSubTab == self.btnRAMGraph:
                    self.updateRAMGraph()

    def updateSubTabStyles(self):
        if self.currentSubTab == self.btnList:
            self.btnList.setStyleSheet(self.styleSelected)
            self.btnGraph.setStyleSheet(self.styleNormal)
        else:
            self.btnList.setStyleSheet(self.styleNormal)
            self.btnGraph.setStyleSheet(self.styleSelected)

    # -------------------- PART 4: Updating the Graphs --------------------
    def updateCPUGraph(self):
        """Update the CPU graph with the top 10 processes by CPU usage."""
        if not self.processData or not self.isVisible:
            return
            
        cpu_data = [(name, cpu) for name, _, cpu, _ in self.processData]
        cpu_data.sort(key=lambda x: x[1], reverse=True)
        
        self.cpuBarGraphWidget.setData(cpu_data[:10])
        
    def updateRAMGraph(self):
        """Update the RAM graph with the top 10 processes by RAM usage."""
        if not self.processData or not self.isVisible:
            return
            
        ram_data = [(name, ram) for name, _, _, ram in self.processData]
        ram_data.sort(key=lambda x: x[1], reverse=True)
        
        self.ramBarGraphWidget.setData(ram_data[:10])