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
                            if pName.lower() in ["system idle process", "idle"]:
                                continue
                            pCPU = proc_info.info['cpu_percent'] or 0.0
                            
                            # Only get memory info for processes with significant CPU usage
                            # This greatly reduces the number of expensive system calls
                            if pCPU > 0.1:  # Only get memory for processes using CPU
                                try:
                                    p = psutil.Process(proc_info.info['pid'])
                                    memMB = p.memory_info().rss / (1024*1024)
                                except:
                                    memMB = 0.0
                            else:
                                memMB = 0.0
                                
                            results.append((pName, pCPU, memMB))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Emit the results
                    self.dataReady.emit(results)
                except Exception as e:
                    print(f"Error in process data worker: {e}")
                
                # Sleep to prevent excessive CPU usage
                time.sleep(2)  # 2 second interval between updates
            else:
                # When paused, just check occasionally if we're still paused
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
        self.FPS_INTERVAL = 33  # ~30 FPS (reduced from 60 FPS)
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
        """Update CPU data and prepare animations."""
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
                    zScale = 0.8 if newPos > oldPos else 1.2  # Shrink if descending, grow if ascending
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
        # Skip if not visible
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
        # Skip if not visible or no data
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
        
        # Sort bars by z-scale for correct overlap (larger zScale on top)
        renderList = []
        for i in range(dataCount):
            oldName, oldUsage, _ = oldPadded[i]
            newName, newUsage, newPos = newPadded[i]
            usage = oldUsage + self.animFrac * (newUsage - oldUsage)
            
            # Position and scale
            if newName in self.transitions:
                trans = self.transitions[newName]
                currentPos = trans['currentPos']
                zScale = 1.0 + (trans['zScale'] - 1.0) * self.animFrac  # Interpolate scale
            else:
                currentPos = newPos
                zScale = 1.0
            
            topY = barSpacing + currentPos * (barHeight + barSpacing)
            waveOffset = math.sin(self.waveTime + newPos * 0.5) * 5
            topY += waveOffset
            displayLen = (usage / usageMax) * (w - xOffset - rightMargin) * 0.8 * zScale
            
            renderList.append((newName, usage, topY, displayLen, barHeight * zScale, zScale))
        
        # Sort by zScale (descending) so growing bars overlap shrinking ones
        renderList.sort(key=lambda x: x[5], reverse=True)
        
        # Draw bars
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
    
# --------------------- The Main ProcessTab Class ---------------------
class ProcessTab(QWidget):
    """
    The 'Process' tab has two sub-sub-tabs: 'List' and 'Graph'.
    - 'List' sub-sub-tab: displays a table of processes with columns [Process Name, CPU%, RAM(MB)].
    - 'Graph' sub-sub-tab: has smaller buttons 'CPU' and 'RAM'.
        * 'CPU' shows a sideways bar graph (top 10 CPU usage).
        * 'RAM' is just a placeholder for now.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.currentSubTab = None
        self.isVisible = False
        self.processData = []  # Cache for process data
        self.lastUpdateTime = 0  # Track when we last updated
        self.updatePending = False  # Flag to prevent multiple updates
        
        # Create the background worker thread
        self.dataWorker = ProcessDataWorker()
        self.dataWorker.dataReady.connect(self.onProcessDataReady)
        self.dataWorker.start()

        # Timer for UI updates - separate from data collection
        self.uiUpdateTimer = QTimer(self)
        self.uiUpdateTimer.setInterval(500)  # Update UI at most every 500ms
        self.uiUpdateTimer.timeout.connect(self.updateUI)
        self.uiUpdateTimer.start()

        # Styles for the top sub-sub-tab buttons (List, Graph)
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

        # Row with two sub-sub-tab buttons: "List" and "Graph"
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(10, 0, 0, 0)
        top_layout.setSpacing(0)

        self.btnList = QPushButton("List")
        self.btnGraph = QPushButton("Graph")

        # Vertical white line between the two sub-sub-tab buttons
        sep_vertical = QFrame()
        sep_vertical.setFixedWidth(1)
        sep_vertical.setStyleSheet("background-color: white;")

        top_layout.addWidget(self.btnList)
        top_layout.addWidget(sep_vertical)
        top_layout.addWidget(self.btnGraph)
        main_layout.addLayout(top_layout)

        # Horizontal white line below them
        sep_horizontal = QFrame()
        sep_horizontal.setFixedHeight(1)
        sep_horizontal.setStyleSheet("background-color: white;")
        main_layout.addWidget(sep_horizontal)

        # Subcontent area: either "List" or "Graph"
        self.subContentLayout = QVBoxLayout()
        # Add a bit of spacing so there's a gap below the sub-sub-tab header
        self.subContentLayout.setContentsMargins(0, 10, 0, 0)
        main_layout.addLayout(self.subContentLayout)

        # Build the "List" sub-sub-tab UI
        self.listWidget = self.buildListUI()

        # Build the "Graph" sub-sub-tab UI
        self.graphWidget = self.buildGraphUI()

        # Connect each sub-sub-tab button
        self.btnList.clicked.connect(lambda: self.setCurrentSubTab(self.btnList))
        self.btnGraph.clicked.connect(lambda: self.setCurrentSubTab(self.btnGraph))

        # Default to "List" sub-sub-tab
        self.setCurrentSubTab(self.btnList)

    def showEvent(self, event):
        """Called when the widget becomes visible"""
        super().showEvent(event)
        self.isVisible = True
        # Resume the worker thread
        self.dataWorker.resume()

    def hideEvent(self, event):
        """Called when the widget is hidden"""
        super().hideEvent(event)
        self.isVisible = False
        # Pause the worker thread to save resources
        self.dataWorker.pause()

    def closeEvent(self, event):
        """Clean up resources when the widget is closed"""
        self.dataWorker.stop()
        super().closeEvent(event)

    def onProcessDataReady(self, data):
        """Receive data from the worker thread"""
        self.processData = data
        self.updatePending = True
        # The actual UI update will happen in updateUI

    def updateUI(self):
        """Update the UI with the latest data"""
        if not self.isVisible or not self.updatePending:
            return
            
        self.updatePending = False
        
        # Update the appropriate view based on what's visible
        if self.currentSubTab == self.btnList:
            self.populateTable()
        elif self.currentSubTab == self.btnGraph and self.currentGraphSubTab == self.btnCPUGraph:
            self.updateCPUGraph()

    # -------------------- PART 1: The "List" Sub-Sub-Tab --------------------
    def buildListUI(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Row of column buttons
        colButtonsLayout = QHBoxLayout()
        colButtonsLayout.setContentsMargins(0, 0, 0, 0)
        colButtonsLayout.setSpacing(0)

        self.btnColProcess = QPushButton("Process Name")
        self.btnColCPU = QPushButton("CPU%")
        self.btnColRAM = QPushButton("RAM(MB)")

        self.colButtons = [
            self.btnColProcess,
            self.btnColCPU,
            self.btnColRAM
        ]

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
        self.table.setColumnCount(3)
        self.table.horizontalHeader().hide()
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont(sciFiFontName, 12))
        
        # Performance optimization: set row count once to a reasonable size
        # This prevents constant resizing which is expensive
        self.table.setRowCount(50)
        
        layout.addWidget(self.table)

        self.btnColProcess.clicked.connect(lambda: self.sortDataBy("process"))
        self.btnColCPU.clicked.connect(lambda: self.sortDataBy("cpu"))
        self.btnColRAM.clicked.connect(lambda: self.sortDataBy("ram"))

        self.sortKey = "cpu"
        self.sortDescending = True
        self.btnColCPU.setChecked(True)

        return container

    def populateTable(self):
        """Update the table with the cached process data"""
        if not self.processData or not self.isVisible:
            return
            
        if self.sortKey == "process":
            idx = 0
            self.sortDescending = False
        elif self.sortKey == "cpu":
            idx = 1
            self.sortDescending = True
        elif self.sortKey == "ram":
            idx = 2
            self.sortDescending = True
        else:
            idx = 1
            self.sortDescending = True

        # Sort data
        sorted_data = sorted(self.processData, key=lambda x: x[idx], reverse=self.sortDescending)
        
        # Limit to top 50 processes for performance
        sorted_data = sorted_data[:50]
        
        # Only update the table if it's visible
        if self.currentSubTab == self.btnList and self.isVisible:
            # Performance optimization: only set row count if it changed
            if self.table.rowCount() != len(sorted_data):
                self.table.setRowCount(len(sorted_data))
                
            # Update table in batches for smoother UI
            for row, (pName, pCPU, pRAM) in enumerate(sorted_data):
                # Only update cells if values changed
                current_name = self.table.item(row, 0)
                if not current_name or current_name.text() != str(pName):
                    itemName = QTableWidgetItem(str(pName))
                    itemName.setFont(QFont(sciFiFontName, 12))
                    itemName.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                    self.table.setItem(row, 0, itemName)

                current_cpu = self.table.item(row, 1)
                cpu_text = f"{pCPU:.1f}%"
                if not current_cpu or current_cpu.text() != cpu_text:
                    itemCPU = QTableWidgetItem(cpu_text)
                    itemCPU.setFont(QFont(sciFiFontName, 12))
                    itemCPU.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 1, itemCPU)

                current_ram = self.table.item(row, 2)
                ram_text = f"{pRAM:.1f}MB"
                if not current_ram or current_ram.text() != ram_text:
                    itemRAM = QTableWidgetItem(ram_text)
                    itemRAM.setFont(QFont(sciFiFontName, 12))
                    itemRAM.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 2, itemRAM)

    def sortDataBy(self, key):
        for b in self.colButtons:
            if key == "process" and b.text().lower().startswith("process"):
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
        """
        The 'Graph' sub-sub-tab has smaller 'CPU' and 'RAM' buttons,
        and a sideways bar graph for CPU usage, or a placeholder for RAM.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.currentGraphSubTab = None

        # We'll make the CPU/RAM buttons smaller
        graphTopLayout = QHBoxLayout()
        graphTopLayout.setContentsMargins(10, 0, 0, 0)
        graphTopLayout.setSpacing(0)

        self.btnCPUGraph = QPushButton("CPU")
        self.btnRAMGraph = QPushButton("RAM")

        # We'll define smaller style
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

        # Vertical line between them
        sep_graph_vertical = QFrame()
        sep_graph_vertical.setFixedWidth(1)
        sep_graph_vertical.setStyleSheet("background-color: white;")

        self.btnCPUGraph.setStyleSheet(self.graphStyleNormal)
        self.btnRAMGraph.setStyleSheet(self.graphStyleNormal)

        graphTopLayout.addWidget(self.btnCPUGraph)
        graphTopLayout.addWidget(sep_graph_vertical)
        graphTopLayout.addWidget(self.btnRAMGraph)
        layout.addLayout(graphTopLayout)

        # Horizontal line
        sep_graph_horizontal = QFrame()
        sep_graph_horizontal.setFixedHeight(1)
        sep_graph_horizontal.setStyleSheet("background-color: white;")
        layout.addWidget(sep_graph_horizontal)

        self.graphSubContentLayout = QVBoxLayout()
        self.graphSubContentLayout.setContentsMargins(0, 10, 0, 0)
        layout.addLayout(self.graphSubContentLayout)

        # The CPU bar graph widget
        self.cpuBarGraphWidget = CPUBarGraphWidget()
        # The RAM placeholder
        self.ramGraphWidget = QLabel("RAM Graph Placeholder")
        self.ramGraphWidget.setStyleSheet("color: white; font-size: 24px;")
        self.ramGraphWidget.setFont(QFont(sciFiFontName, 24))

        # Connect
        self.btnCPUGraph.clicked.connect(lambda: self.setCurrentGraphSubTab(self.btnCPUGraph))
        self.btnRAMGraph.clicked.connect(lambda: self.setCurrentGraphSubTab(self.btnRAMGraph))

        # Default to CPU sub-sub-sub-tab
        self.setCurrentGraphSubTab(self.btnCPUGraph)

        return container

    def setCurrentGraphSubTab(self, btn):
        self.currentGraphSubTab = btn
        self.updateGraphSubTabStyles()

        # Clear old content
        for i in reversed(range(self.graphSubContentLayout.count())):
            item = self.graphSubContentLayout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)

        if btn == self.btnCPUGraph:
            self.graphSubContentLayout.addWidget(self.cpuBarGraphWidget)
            # Update the CPU graph with current data if we have it
            if self.processData and self.isVisible:
                self.updateCPUGraph()
        else:
            self.graphSubContentLayout.addWidget(self.ramGraphWidget)

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

        # Clear old content from subContentLayout
        for i in reversed(range(self.subContentLayout.count())):
            item = self.subContentLayout.itemAt(i)
            w = item.widget()
            if w:
                w.setParent(None)

        if btn == self.btnList:
            self.subContentLayout.addWidget(self.listWidget)
            # Update the table with current data if we have it
            if self.processData and self.isVisible:
                self.populateTable()
        else:
            self.subContentLayout.addWidget(self.graphWidget)
            # Update the CPU graph with current data if we have it
            if self.processData and self.isVisible and self.currentGraphSubTab == self.btnCPUGraph:
                self.updateCPUGraph()

    def updateSubTabStyles(self):
        if self.currentSubTab == self.btnList:
            self.btnList.setStyleSheet(self.styleSelected)
            self.btnGraph.setStyleSheet(self.styleNormal)
        else:
            self.btnList.setStyleSheet(self.styleNormal)
            self.btnGraph.setStyleSheet(self.styleSelected)

    # -------------------- PART 4: Updating the 'CPU Graph' --------------------
    def updateCPUGraph(self):
        """Update the CPU graph with the top 10 processes by CPU usage"""
        if not self.processData or not self.isVisible:
            return
            
        # Extract just the name and CPU usage, sort by CPU usage
        cpu_data = [(name, cpu) for name, cpu, _ in self.processData]
        cpu_data.sort(key=lambda x: x[1], reverse=True)
        
        # Pass the top 10 to the graph widget
        self.cpuBarGraphWidget.setData(cpu_data[:10])