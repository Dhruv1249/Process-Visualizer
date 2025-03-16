# process_tab.py
import psutil
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QTimer, QRectF, QPoint

sciFiFontName = "Conthrax"

# --------------------- A Custom Widget for the CPU Bar Graph ---------------------
class CPUBarGraphWidget(QWidget):
    """
    A custom widget that draws a sideways bar graph of top-10 processes by CPU usage.
    - Each bar has rounded edges and a blue fill.
    - The data is a list of (processName, cpuPercent).
    - We'll update it every 2 seconds from the parent 'ProcessTab'.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # list of (pName, pCPU)
        self.setMinimumSize(400, 300)

    def setData(self, data):
        """Set the list of (processName, cpuPercent) for top 10 processes."""
        self.data = data[:10]  # top 10
        self.update()          # trigger repaint

def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing, True)

    rect = self.rect()
    width = rect.width()
    height = rect.height()

    barSpacing = 10
    barHeight = (height - (len(self.data)+1)*barSpacing) / (len(self.data) if self.data else 1)

    maxCPU = max((pCPU for _, pCPU in self.data), default=1)
    xOffset = 150  # space on left for text

    for i, (pName, pCPU) in enumerate(self.data):
        topY = barSpacing + i*(barHeight + barSpacing)
        usageRatio = pCPU / maxCPU if maxCPU > 0 else 0
        barLen = usageRatio * (width - xOffset - 20)

        # Draw the rounded bar
        barRect = QRectF(xOffset, topY, barLen, barHeight)
        pen = QPen(QColor("#007FFF"))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        brush = QBrush(QColor("#00A2FF"))
        painter.setBrush(brush)
        painter.drawRoundedRect(barRect, 5, 5)

        # Draw the process name on the left (truncate if too long)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Conthrax", 12))
        # Cast coords to int
        painter.drawText(QPoint(10, int(topY + barHeight * 0.7)), pName[:15])

        # Draw CPU usage at the right end of the bar
        usageStr = f"{pCPU:.1f}%"
        painter.drawText(int(xOffset + barLen + 5), int(topY + barHeight * 0.7), usageStr)


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

        # Timer to refresh the process list & CPU graph every 2 seconds
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(2000)
        self.updateTimer.timeout.connect(self.refreshProcessList)

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

        # Start the timer
        self.updateTimer.start()

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
        layout.addWidget(self.table)

        self.btnColProcess.clicked.connect(lambda: self.sortDataBy("process"))
        self.btnColCPU.clicked.connect(lambda: self.sortDataBy("cpu"))
        self.btnColRAM.clicked.connect(lambda: self.sortDataBy("ram"))

        self.processData = self.fetchProcessData()
        self.sortKey = "cpu"
        self.sortDescending = True
        self.populateTable()
        self.btnColCPU.setChecked(True)

        return container

    def fetchProcessData(self):
        results = []
        for proc_info in psutil.process_iter(['pid','name','cpu_percent']):
            try:
                pName = proc_info.info['name'] or "Unknown"
                if pName.lower() in ["system idle process", "idle"]:
                    continue
                pCPU = proc_info.info['cpu_percent'] or 0.0
                p = psutil.Process(proc_info.info['pid'])
                memMB = p.memory_info().rss / (1024*1024)
                results.append((pName, pCPU, memMB))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return results

    def populateTable(self):
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

        self.processData.sort(key=lambda x: x[idx], reverse=self.sortDescending)
        self.table.setRowCount(len(self.processData))
        for row, (pName, pCPU, pRAM) in enumerate(self.processData):
            itemName = QTableWidgetItem(str(pName))
            itemName.setFont(QFont(sciFiFontName, 12))
            itemName.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 0, itemName)

            itemCPU = QTableWidgetItem(f"{pCPU:.1f}%")
            itemCPU.setFont(QFont(sciFiFontName, 12))
            itemCPU.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, itemCPU)

            itemRAM = QTableWidgetItem(f"{pRAM:.1f}MB")
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
        else:
            self.subContentLayout.addWidget(self.graphWidget)

    def updateSubTabStyles(self):
        if self.currentSubTab == self.btnList:
            self.btnList.setStyleSheet(self.styleSelected)
            self.btnGraph.setStyleSheet(self.styleNormal)
        else:
            self.btnList.setStyleSheet(self.styleNormal)
            self.btnGraph.setStyleSheet(self.styleSelected)

    # -------------------- PART 4: Refreshing the 'List' & 'CPU Graph' --------------------
    def refreshProcessList(self):
        """
        Called every 2 seconds by the QTimer.
        1) If we're on the 'List' sub-sub-tab, re-fetch process data & re-populate table.
        2) If we're on 'Graph' -> 'CPU' sub-sub-sub-tab, fetch top-10 CPU usage, pass to cpuBarGraphWidget.
        """
        # 1) If 'List' is active, update the table
        if self.currentSubTab == self.btnList:
            self.processData = self.fetchProcessData()
            self.populateTable()

        # 2) If 'Graph' is active, check if 'CPU' sub-sub-sub-tab is active
        if self.currentSubTab == self.btnGraph and self.currentGraphSubTab == self.btnCPUGraph:
            top10 = self.fetchTop10CPU()
            self.cpuBarGraphWidget.setData(top10)

    def fetchTop10CPU(self):
        """
        Returns a sorted list of top 10 (pName, pCPU) by CPU usage.
        """
        data = []
        for proc_info in psutil.process_iter(['pid','name','cpu_percent']):
            try:
                pName = proc_info.info['name'] or "Unknown"
                if pName.lower() in ["system idle process", "idle"]:
                    continue
                pCPU = proc_info.info['cpu_percent'] or 0.0
                data.append((pName, pCPU))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        

        # sort descending by CPU
        data.sort(key=lambda x: x[1], reverse=True)
        return data[:10]
