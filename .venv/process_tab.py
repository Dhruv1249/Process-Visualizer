
import psutil
import math
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QStyleOption, QStyle,
    QMenu, QMessageBox, QApplication
)
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush, QFontDatabase, QCursor
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
        self.pauseUpdates = False  # Flag to pause UI updates when context menu is active or Ctrl is held.
        
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
        if self.pauseUpdates or not self.isVisible or not self.updatePending:
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
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)  # Enable custom context menu
        self.table.customContextMenuRequested.connect(self.showProcessContextMenu)  # Connect to our handler
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

        sorted_data = sorted(self.processData, key=lambda x: x[idx], reverse=self.sortDescending)
        
        if self.currentSubTab == self.btnList and self.isVisible:
            if self.table.rowCount() != len(sorted_data):
                self.table.setRowCount(len(sorted_data))
                
            for row, (pName, pID, pCPU, pRAM) in enumerate(sorted_data):
                current_name = self.table.item(row, 0)
                if not current_name or current_name.text() != str(pName):
                    itemName = QTableWidgetItem(str(pName))
                    itemName.setFont(QFont(sciFiFontName, 12))
                    itemName.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    # Store the PID as item data for context menu actions
                    itemName.setData(Qt.UserRole, pID)
                    self.table.setItem(row, 0, itemName)

                current_pid = self.table.item(row, 1)
                if not current_pid or current_pid.text() != str(pID):
                    itemPID = QTableWidgetItem(str(pID))
                    itemPID.setFont(QFont(sciFiFontName, 12))
                    itemPID.setTextAlignment(Qt.AlignCenter)
                    # Store the PID as item data for context menu actions
                    itemPID.setData(Qt.UserRole, pID)
                    self.table.setItem(row, 1, itemPID)

                current_cpu = self.table.item(row, 2)
                cpu_text = f"{pCPU:.1f}%"
                if not current_cpu or current_cpu.text() != cpu_text:
                    itemCPU = QTableWidgetItem(cpu_text)
                    itemCPU.setFont(QFont(sciFiFontName, 12))
                    itemCPU.setTextAlignment(Qt.AlignCenter)
                    # Store the PID as item data for context menu actions
                    itemCPU.setData(Qt.UserRole, pID)
                    self.table.setItem(row, 2, itemCPU)

                current_ram = self.table.item(row, 3)
                ram_text = f"{pRAM:.1f}MB"
                if not current_ram or current_ram.text() != ram_text:
                    itemRAM = QTableWidgetItem(ram_text)
                    itemRAM.setFont(QFont(sciFiFontName, 12))
                    itemRAM.setTextAlignment(Qt.AlignCenter)
                    # Store the PID as item data for context menu actions
                    itemRAM.setData(Qt.UserRole, pID)
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

    # -------------------- Process Control Functions --------------------
    def showProcessContextMenu(self, position):
        """
        Show a sleek context menu when right-clicking on a process in the table.
        This menu uses the Conthrax font and cool styling. Additionally, list updates
        are paused when the menu is active or when the Ctrl key is held.
        """
        # Pause updates if Ctrl is held or on right-click
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            self.pauseUpdates = True
        else:
            self.pauseUpdates = True

        # Get the row at the clicked position
        row = self.table.rowAt(position.y())
        if row < 0:
            self.pauseUpdates = False
            return  # No valid row clicked
        
        # Get the process PID from the clicked row
        item = self.table.item(row, 0)  # Get item from first column
        if not item:
            self.pauseUpdates = False
            return
        
        pid = item.data(Qt.UserRole)
        process_name = item.text()
        
        # Create sleek context menu using Conthrax font and cool styling
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2B2B2B;
                border: 1px solid #444444;
                font-family: Conthrax;
                font-size: 16px;
                color: #FFFFFF;
            }
            QMenu::item {
                padding: 10px 25px;
            }
            QMenu::item:selected {
                background-color: #00A2FF;
            }
        """)
        
        # Add actions
        pauseAction = menu.addAction("Pause Process")
        resumeAction = menu.addAction("Resume Process")
        menu.addSeparator()
        killAction = menu.addAction("Kill Process")
        
        # Show menu and get selected action
        action = menu.exec_(QCursor.pos())
        
        # Handle action
        if action == pauseAction:
            self.pauseProcess(pid, process_name)
        elif action == resumeAction:
            self.resumeProcess(pid, process_name)
        elif action == killAction:
            self.killProcess(pid, process_name)
        
        # Unpause updates if Ctrl is not held
        if not (QApplication.keyboardModifiers() & Qt.ControlModifier):
            self.pauseUpdates = False

    def pauseProcess(self, pid, process_name):
        """Pause a process by suspending it"""
        try:
            process = psutil.Process(pid)
            process.suspend()
            QMessageBox.information(self, "Process Paused", 
                                   f"Process '{process_name}' (PID: {pid}) has been paused.")
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "Error", f"Process '{process_name}' (PID: {pid}) no longer exists.")
        except psutil.AccessDenied:
            QMessageBox.warning(self, "Access Denied", 
                               f"Cannot pause process '{process_name}' (PID: {pid}). Access denied.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error pausing process: {str(e)}")

    def resumeProcess(self, pid, process_name):
        """Resume a paused process"""
        try:
            process = psutil.Process(pid)
            process.resume()
            QMessageBox.information(self, "Process Resumed", 
                                   f"Process '{process_name}' (PID: {pid}) has been resumed.")
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "Error", f"Process '{process_name}' (PID: {pid}) no longer exists.")
        except psutil.AccessDenied:
            QMessageBox.warning(self, "Access Denied", 
                               f"Cannot resume process '{process_name}' (PID: {pid}). Access denied.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error resuming process: {str(e)}")

    def killProcess(self, pid, process_name):
        """Kill a process"""
        try:
            process = psutil.Process(pid)
            process.kill()
            QMessageBox.information(self, "Process Killed", 
                                   f"Process '{process_name}' (PID: {pid}) has been killed.")
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "Error", f"Process '{process_name}' (PID: {pid}) no longer exists.")
        except psutil.AccessDenied:
            QMessageBox.warning(self, "Access Denied", 
                               f"Cannot kill process '{process_name}' (PID: {pid}). Access denied.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error killing process: {str(e)}")

    # -------------------- GRAPH SUB-TAB METHODS --------------------
    def buildGraphUI(self):
        """Builds and returns the widget for the Graph sub-tab."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top buttons for CPU and RAM graphs
        topButtonLayout = QHBoxLayout()
        topButtonLayout.setContentsMargins(0, 0, 0, 0)
        topButtonLayout.setSpacing(0)
        
        self.btnCPUGraph = QPushButton("CPU")
        self.btnRAMGraph = QPushButton("RAM")
        for button in [self.btnCPUGraph, self.btnRAMGraph]:
            button.setCheckable(True)
            button.setStyleSheet(self.styleNormal)
        self.btnCPUGraph.setChecked(True)
        self.currentGraphSubTab = self.btnCPUGraph
        
        self.btnCPUGraph.clicked.connect(lambda: self.setCurrentGraphSubTab(self.btnCPUGraph))
        self.btnRAMGraph.clicked.connect(lambda: self.setCurrentGraphSubTab(self.btnRAMGraph))
        
        topButtonLayout.addWidget(self.btnCPUGraph)
        topButtonLayout.addWidget(self.btnRAMGraph)
        layout.addLayout(topButtonLayout)
        
        # Graph container area
        self.graphContainer = QWidget()
        graphLayout = QVBoxLayout(self.graphContainer)
        graphLayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.graphContainer)
        
        # Instantiate graph widgets
        self.cpuGraph = CPUBarGraphWidget()
        self.ramGraph = RAMBarGraphWidget()
        
        # Add default graph (CPU)
        graphLayout.addWidget(self.cpuGraph)
        
        return container

    def setCurrentGraphSubTab(self, tabButton):
        """Switch between the CPU and RAM graph views."""
        self.currentGraphSubTab = tabButton
        if tabButton == self.btnCPUGraph:
            self.btnCPUGraph.setChecked(True)
            self.btnRAMGraph.setChecked(False)
            # Apply selected styling with white border to CPU tab and normal styling with white border to RAM tab
            self.btnCPUGraph.setStyleSheet(f"{self.styleSelected}; border: 1px solid white;")
            self.btnRAMGraph.setStyleSheet(f"{self.styleNormal}; border: 1px solid white;")
            # Clear graphContainer and add CPU graph
            layout = self.graphContainer.layout()
            while layout.count():
                widgetToRemove = layout.takeAt(0).widget()
                if widgetToRemove is not None:
                    widgetToRemove.setParent(None)
            layout.addWidget(self.cpuGraph)
        elif tabButton == self.btnRAMGraph:
            self.btnCPUGraph.setChecked(False)
            self.btnRAMGraph.setChecked(True)
            # Apply selected styling with white border to RAM tab and normal styling with white border to CPU tab
            self.btnCPUGraph.setStyleSheet(f"{self.styleNormal}; border: 1px solid white;")
            self.btnRAMGraph.setStyleSheet(f"{self.styleSelected}; border: 1px solid white;")
            layout = self.graphContainer.layout()
            while layout.count():
                widgetToRemove = layout.takeAt(0).widget()
                if widgetToRemove is not None:
                    widgetToRemove.setParent(None)
            layout.addWidget(self.ramGraph)

    def updateCPUGraph(self):
        """Update CPU graph with top CPU usage processes."""
        if not self.processData:
            return
        sorted_cpu = sorted(self.processData, key=lambda x: x[2], reverse=True)
        # Map to (processName, CPU%) tuple for top 10 processes
        data = [(pName, pCPU) for (pName, pID, pCPU, pRAM) in sorted_cpu[:10]]
        self.cpuGraph.setData(data)

    def updateRAMGraph(self):
        """Update RAM graph with top RAM usage processes."""
        if not self.processData:
            return
        sorted_ram = sorted(self.processData, key=lambda x: x[3], reverse=True)
        data = [(pName, pRAM) for (pName, pID, pCPU, pRAM) in sorted_ram[:10]]
        self.ramGraph.setData(data)

    # -------------------- MAIN TAB SWITCHING METHOD --------------------
    def setCurrentSubTab(self, tabButton):
        """Switch between the List and Graph sub-tabs."""
        self.currentSubTab = tabButton
        # Clear the subContentLayout
        while self.subContentLayout.count():
            item = self.subContentLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        if tabButton == self.btnList:
            self.subContentLayout.addWidget(self.listWidget)
            self.btnList.setStyleSheet(self.styleSelected)
            self.btnGraph.setStyleSheet(self.styleNormal)
        elif tabButton == self.btnGraph:
            self.subContentLayout.addWidget(self.graphWidget)
            self.btnGraph.setStyleSheet(self.styleSelected)
            self.btnList.setStyleSheet(self.styleNormal)
