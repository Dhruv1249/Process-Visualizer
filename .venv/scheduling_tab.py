from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox,
                             QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QLineEdit, QHBoxLayout, QDialog, QScrollArea)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

class GanttChartWidget(QWidget):
    def __init__(self, algorithm, processSchedule, parent=None):
        super().__init__(parent)
        self.algorithm = algorithm
        self.processSchedule = processSchedule
        self.scale = 10.0  # pixels per time unit zoom factor
        self.baseWidth = 800
        self.baseHeight = 400
        self.setMinimumSize(self.baseWidth, self.baseHeight)
        # Use Arial small fonts for chart drawing.
        self.titleFont = QFont("Arial", 12, QFont.Bold)
        self.itemFont = QFont("Arial", 10)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill entire widget with black.
        painter.fillRect(self.rect(), QColor("black"))
        
        # Define margins.
        left_margin = 50
        bottom_margin = 50  # leave space for time axis at bottom.
        top_margin = 20
        right_margin = 50
        
        # Draw chart title at the top-left (in white, using Arial).
        painter.setPen(QPen(QColor("white")))
        painter.setFont(self.titleFont)
        painter.drawText(10, top_margin + 15, f"Gantt Chart - {self.algorithm}")
        
        # Determine the drawing area for the chart.
        chart_area = self.rect().adjusted(left_margin, top_margin + 30, -right_margin, -bottom_margin)
        # Fill chart area with black.
        painter.fillRect(chart_area, QColor("black"))
        
        # Draw dynamic grid lines on chart area
        painter.setPen(QPen(QColor(80, 80, 80), 1))  # dark gray grid lines
        # Vertical grid lines at each time unit.
        # Compute maximum finish time.
        maxFinish = 0
        for proc in self.processSchedule:
            if proc['finish'] > maxFinish:
                maxFinish = proc['finish']
        # Total width needed:
        total_width = left_margin + maxFinish * self.scale + 50
        # Draw vertical grid lines for each integer time.
        for t in range(0, int(maxFinish) + 1):
            x = left_margin + t * self.scale
            # Draw grid line spanning chart area.
            painter.drawLine(int(x), int(chart_area.top()), int(x), int(chart_area.bottom()))
            # Draw time labels at the bottom.
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(QColor("white")))
            painter.drawText(int(x)-5, self.height() - bottom_margin + 15, str(t))
            painter.setPen(QPen(QColor(80,80,80), 1))
        
        # Draw horizontal grid lines across process rows.
        rowHeight = 30
        gap = 10
        total_rows = len(self.processSchedule)
        # Draw lines for each row boundary inside chart_area.
        # Since we draw from bottom, the first process is drawn at the bottom row.
        for i in range(total_rows+1):
            # compute y coordinate from bottom of chart_area.
            y = chart_area.bottom() - i * (rowHeight + gap)
            painter.drawLine(int(chart_area.left()), int(y), int(chart_area.right()), int(y))
        
        # Draw each process bar from bottom upward.
        painter.setPen(QPen(QColor("black"), 1))
        for idx, proc in enumerate(self.processSchedule):
            # Draw processes in reverse order: last in list appears at the top.
            i = total_rows - idx - 1
            start = proc['start']
            finish = proc['finish']
            rect_x = left_margin + start * self.scale
            rect_width = (finish - start) * self.scale
            # y-coordinate from bottom of chart_area.
            rect_y = chart_area.bottom() - (i+1) * (rowHeight + gap) + gap
            rect = QRectF(rect_x, rect_y, rect_width, rowHeight)
            painter.setBrush(QColor("blue"))
            painter.drawRect(rect)
            # Draw process name inside the rectangle in white using Arial.
            painter.setFont(self.itemFont)
            painter.setPen(QPen(QColor("white")))
            painter.drawText(rect, Qt.AlignCenter, proc['name'])
            
            # Optionally, draw start and finish times just below the rectangle edge.
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(QColor("white")))
            painter.drawText(int(rect_x), int(rect_y - 2), str(start))
            painter.drawText(int(rect_x + rect_width - 20), int(rect_y - 2), str(finish))
            
        painter.end()
        
    def wheelEvent(self, event):
        # Use mouse wheel events to modify scale (zoom in/out)
        delta = event.angleDelta().y() / 120
        factor = 1.1
        if delta > 0:
            self.scale *= factor**delta
        else:
            self.scale /= factor**(-delta)
        self.scale = max(1.0, min(self.scale, 50))
        self.update()

class GanttChartWindow(QDialog):
    def __init__(self, algorithm, processSchedule, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gantt Chart")
        self.algorithm = algorithm
        self.processSchedule = processSchedule
        self.setStyleSheet("background-color: black;")
        # Create a scroll area for the dynamic GanttChartWidget.
        scrollArea = QScrollArea(self)
        scrollArea.setWidgetResizable(True)
        self.chartWidget = GanttChartWidget(algorithm, processSchedule)
        scrollArea.setWidget(self.chartWidget)
        layout = QVBoxLayout(self)
        layout.addWidget(scrollArea)
        self.setFixedSize(800, 400)
class SchedulingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set font Conthrax everywhere using style sheet
        self.setStyleSheet("background-color: #000000; color: #FFFFFF; font-family: Conthrax;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)  # Ensure everything is at the top
        
        # Heading styled like the main window's menu header:
        heading = QLabel("Scheduling Algorithms")
        heading.setStyleSheet("color: white; font-size: 68px; padding: 10px; font-family: Conthrax; font-weight: bold;")
        heading.setAlignment(Qt.AlignLeft)
        layout.addWidget(heading)
        
        # Add a label for the combobox
        algoLabel = QLabel("Algorithm:")
        algoLabel.setStyleSheet("color: white; font-size: 30px; padding-left: 10px; font-family: Conthrax;")
        algoLabel.setAlignment(Qt.AlignLeft)
        layout.addWidget(algoLabel)
        
        # Dropdown to select scheduling algorithm, positioned immediately below the label.
        self.schedAlgoCombo = QComboBox()
        self.schedAlgoCombo.setStyleSheet("background-color: #000000; color: white; font-size: 30px; font-family: Conthrax;")
        # Set the default prompt text
        self.schedAlgoCombo.addItem("Select Algorithm")
        self.schedAlgoCombo.addItems([
            "FCFS",
            "SJF (Non Preemptive)",
            "SJF (Preemptive)",
            "Priority Scheduling",
            "RMS",
            "EDF",
            "Round Robin"
        ])
        # Disable the default prompt option.
        self.schedAlgoCombo.model().item(0).setEnabled(False)
        layout.addWidget(self.schedAlgoCombo, alignment=Qt.AlignLeft)
        
        # Additional Options Container (for time quantum / priority order)
        self.additionalOptionsContainer = QWidget()
        additionalLayout = QVBoxLayout(self.additionalOptionsContainer)
        additionalLayout.setContentsMargins(0, 0, 0, 0)
        additionalLayout.setSpacing(5)
        
        # Time Quantum (for Round Robin)
        self.timeQuantumContainer = QWidget()
        tqLayout = QHBoxLayout(self.timeQuantumContainer)
        tqLayout.setContentsMargins(0, 0, 0, 0)
        tqLayout.setSpacing(5)
        tqLabel = QLabel("Time Quantum:")
        tqLabel.setStyleSheet("color: white; font-size: 28px; font-family: Conthrax;")
        self.timeQuantumEdit = QLineEdit()
        self.timeQuantumEdit.setStyleSheet("background-color: #3A3A3A; color: white; font-size: 28px; font-family: Conthrax;")
        tqLayout.addWidget(tqLabel)
        tqLayout.addWidget(self.timeQuantumEdit)
        self.timeQuantumContainer.hide()  # Hide by default
        additionalLayout.addWidget(self.timeQuantumContainer, alignment=Qt.AlignLeft)
        
        # Priority Order (for Priority Scheduling)
        self.priorityOrderContainer = QWidget()
        poLayout = QHBoxLayout(self.priorityOrderContainer)
        poLayout.setContentsMargins(0, 0, 0, 0)
        poLayout.setSpacing(5)
        poLabel = QLabel("Priority Order:")
        poLabel.setStyleSheet("color: white; font-size: 28px; font-family: Conthrax;")
        self.priorityOrderCombo = QComboBox()
        self.priorityOrderCombo.setStyleSheet("background-color: #000000; color: white; font-size: 28px; font-family: Conthrax;")
        self.priorityOrderCombo.addItems(["Greater Priority First", "Smaller Priority First"])
        poLayout.addWidget(poLabel)
        poLayout.addWidget(self.priorityOrderCombo)
        self.priorityOrderContainer.hide()  # Hide by default
        additionalLayout.addWidget(self.priorityOrderContainer, alignment=Qt.AlignLeft)
        
        layout.addWidget(self.additionalOptionsContainer)
        
        # Process Input Form Container
        self.processFormContainer = QWidget()
        self.processFormLayout = QVBoxLayout(self.processFormContainer)
        self.processFormLayout.setContentsMargins(0, 0, 0, 0)
        self.processFormLayout.setSpacing(10)
        
        # Table widget for process inputs
        self.processTable = QTableWidget()
        self.processTable.setStyleSheet(
            "QTableWidget { background-color: #000000; color: white; font-size: 16px; font-family: Conthrax; gridline-color: white; }"
            "QHeaderView::section { background-color: #000000; color: white; font-family: Conthrax; font-weight: bold; border: 1px solid white; }"
            "QTableWidget::item { border: 1px solid white; }"
            "QTableWidget::item:selected { background-color: blue; }"
        )
        self.processTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.processTable.verticalHeader().setStyleSheet("background-color: #000000; color: white; font-family: Conthrax;")
        self.processTable.setFixedHeight(600)
        
        self.processFormLayout.addWidget(self.processTable)
        
        # Button Container for "Add Process", "Clear Table", "Remove Process", and "Start Scheduling"
        buttonContainer = QWidget()
        buttonLayout = QHBoxLayout(buttonContainer)
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonLayout.setSpacing(10)
        
        # Add Process button
        self.addProcessButton = QPushButton("Add Process")
        self.addProcessButton.setStyleSheet("background-color: #3A3A3A; color: white; font-size: 30px; font-family: Conthrax;")
        self.addProcessButton.clicked.connect(self.addProcessRow)
        buttonLayout.addWidget(self.addProcessButton, alignment=Qt.AlignLeft)
        
        # Clear Table button
        self.clearTableButton = QPushButton("Clear Table")
        self.clearTableButton.setStyleSheet("background-color: #3A3A3A; color: white; font-size: 30px; font-family: Conthrax;")
        self.clearTableButton.clicked.connect(self.clearTable)
        buttonLayout.addWidget(self.clearTableButton, alignment=Qt.AlignLeft)
        
        # Remove Process button
        self.removeProcessButton = QPushButton("Remove Process")
        self.removeProcessButton.setStyleSheet("background-color: #3A3A3A; color: white; font-size: 30px; font-family: Conthrax;")
        self.removeProcessButton.clicked.connect(self.removeProcess)
        buttonLayout.addWidget(self.removeProcessButton, alignment=Qt.AlignLeft)
        
        # Start Scheduling button
        self.startSchedulingButton = QPushButton("Start Scheduling")
        self.startSchedulingButton.setStyleSheet("background-color: #3A3A3A; color: white; font-size: 30px; font-family: Conthrax;")
        self.startSchedulingButton.clicked.connect(self.startScheduling)
        buttonLayout.addWidget(self.startSchedulingButton, alignment=Qt.AlignLeft)
        
        self.processFormLayout.addWidget(buttonContainer)
        
        layout.addWidget(self.processFormContainer)
        
        # Set up the process input form based on the current algorithm.
        self.updateProcessInputForm(self.schedAlgoCombo.currentText())
        
        # Connect the combobox selection change:
        self.schedAlgoCombo.currentIndexChanged.connect(
            lambda: self.updateProcessInputForm(self.schedAlgoCombo.currentText()))
        
        # Keep a counter for default process names.
        self.processCount = 0

    def updateProcessInputForm(self, algo):
        """
        Update the process input form based on the selected scheduling algorithm.
        """
        if algo in ["Priority Scheduling"]:
            columns = ["Process Name", "Arrival Time", "Burst Time", "Priority"]
        elif algo in ["RMS"]:
            columns = ["Process Name", "Arrival Time", "Burst Time", "Period"]
        elif algo in ["EDF"]:
            columns = ["Process Name", "Arrival Time", "Burst Time", "Deadline"]
        else:
            columns = ["Process Name", "Arrival Time", "Burst Time"]
        
        self.processTable.clear()
        self.processTable.setColumnCount(len(columns))
        self.processTable.setHorizontalHeaderLabels(columns)
        self.processTable.setRowCount(0)
        self.processCount = 0
        
        self.updateAdditionalOptionsVisibility(algo)

    def updateAdditionalOptionsVisibility(self, algo):
        if algo == "Round Robin":
            self.timeQuantumContainer.show()
        else:
            self.timeQuantumContainer.hide()
            
        if algo == "Priority Scheduling":
            self.priorityOrderContainer.show()
        else:
            self.priorityOrderContainer.hide()
        
    def addProcessRow(self):
        currentRow = self.processTable.rowCount()
        self.processTable.insertRow(currentRow)
        self.processCount += 1
        defaultName = f"p{self.processCount}"
        
        colCount = self.processTable.columnCount()
        for col in range(colCount):
            if col == 0:
                item = QTableWidgetItem(defaultName)
            else:
                item = QTableWidgetItem("0")
            self.processTable.setItem(currentRow, col, item)
    
    def clearTable(self):
        self.processTable.setRowCount(0)
        self.processCount = 0
        
    def removeProcess(self):
        selected = self.processTable.selectedIndexes()
        if not selected:
            return
        row_to_remove = selected[0].row()
        self.processTable.removeRow(row_to_remove)
    
    
    
    def startScheduling(self):
        """
        When Start Scheduling is clicked, gather table data and compute a schedule
        based on the selected algorithm.
        Implementations provided for:
        - FCFS
        - SJF (Non Preemptive)
        - SJF (Preemptive) without context switch delay
        - Priority Scheduling (non-preemptive)
        - RMS (non-preemptive)
        - EDF (non-preemptive)
        - Round Robin without extra context switch seconds
        """
        # Determine selected algorithm.
        alg = self.schedAlgoCombo.currentText()

        # Gather process data from the table.
        rows = self.processTable.rowCount()
        processList = []
        for r in range(rows):
            proc = {}
            proc['name'] = self.processTable.item(r, 0).text() if self.processTable.item(r, 0) else f"p{r+1}"
            proc['arrival'] = float(self.processTable.item(r, 1).text()) if self.processTable.item(r, 1) else 0.0
            proc['burst'] = float(self.processTable.item(r, 2).text()) if self.processTable.item(r, 2) else 0.0
            # For algorithms that require extra info, get the fourth column.
            if self.processTable.columnCount() >= 4:
                cell = self.processTable.item(r, 3)
                try:
                    value = float(cell.text()) if cell else (proc['arrival'] + proc['burst'])
                except Exception:
                    value = proc['arrival'] + proc['burst']
                if alg == "Priority Scheduling":
                    proc['priority'] = value
                elif alg == "RMS":
                    proc['period'] = value
                elif alg == "EDF":
                    proc['deadline'] = value
            processList.append(proc)

        # Note: No context switch overhead is added (i.e. switching is instantaneous).

        # Helper scheduling functions.
        def fcfs_schedule(plist):
            plist_sorted = sorted(plist, key=lambda p: p['arrival'])
            currentTime = 0.0
            sched = []
            for p in plist_sorted:
                start = max(currentTime, p['arrival'])
                finish = start + p['burst']
                sched.append({'name': p['name'], 'arrival': p['arrival'], 'burst': p['burst'],
                            'start': start, 'finish': finish})
                currentTime = finish
            return sched

        def sjf_non_preemptive_schedule(plist):
            unscheduled = plist[:]
            sched = []
            currentTime = 0.0
            while unscheduled:
                available = [p for p in unscheduled if p['arrival'] <= currentTime]
                if not available:
                    currentTime = min(unscheduled, key=lambda p: p['arrival'])['arrival']
                    available = [p for p in unscheduled if p['arrival'] <= currentTime]
                chosen = min(available, key=lambda p: p['burst'])
                start = max(currentTime, chosen['arrival'])
                finish = start + chosen['burst']
                sched.append({'name': chosen['name'], 'arrival': chosen['arrival'], 'burst': chosen['burst'],
                            'start': start, 'finish': finish})
                currentTime = finish
                unscheduled.remove(chosen)
            return sched

        def sjf_preemptive_schedule(plist):
            # Shortest Remaining Time First without context switch delay.
            for p in plist:
                p['remaining'] = p['burst']
                p['segments'] = []  # Track execution segments for this process
            
            time = 0.0
            last_proc = None
            
            while any(p['remaining'] > 0 for p in plist):
                available = [p for p in plist if p['arrival'] <= time and p['remaining'] > 0]
                if not available:
                    next_arrivals = [p for p in plist if p['arrival'] > time and p['remaining'] > 0]
                    if next_arrivals:
                        time = min(next_arrivals, key=lambda p: p['arrival'])['arrival']
                        continue
                    else:
                        break
                current = min(available, key=lambda p: p['remaining'])
                
                seg_start = time
                time += 1  # Execute for 1 time unit
                seg_finish = time
                current['remaining'] -= 1
                
                # Always start a new segment if last process was different.
                if current['segments'] and current['name'] == last_proc and current['segments'][-1]['end'] == seg_start:
                    current['segments'][-1]['end'] = seg_finish
                else:
                    current['segments'].append({'start': seg_start, 'end': seg_finish})
                
                last_proc = current['name']
            
            sched = []
            for p in plist:
                for seg in p['segments']:
                    sched.append({
                        'name': p['name'],
                        'arrival': p['arrival'],
                        'burst': p['burst'],
                        'start': seg['start'],
                        'finish': seg['end']
                    })
            sched.sort(key=lambda s: s['start'])
            return sched

        def round_robin_schedule(plist, quantum):
            # Round Robin without context switch delay.
            plist_sorted = sorted(plist, key=lambda p: p['arrival'])
            for p in plist_sorted:
                p['remaining'] = p['burst']
                p['segments'] = []  # Track execution segments
            
            time = 0.0
            
            while any(p['remaining'] > 0 for p in plist_sorted):
                executed_in_round = False
                for p in plist_sorted:
                    if p['arrival'] <= time and p['remaining'] > 0:
                        exec_time = min(quantum, p['remaining'])
                        seg_start = time
                        time += exec_time
                        seg_finish = time
                        p['remaining'] -= exec_time
                        p['segments'].append({'start': seg_start, 'end': seg_finish})
                        executed_in_round = True
                if not executed_in_round:
                    # Advance time to the next arrival if no process was executed.
                    next_arrivals = [p for p in plist_sorted if p['arrival'] > time and p['remaining'] > 0]
                    if next_arrivals:
                        time = min(next_arrivals, key=lambda p: p['arrival'])['arrival']
                    else:
                        break

            sched = []
            for p in plist_sorted:
                for seg in p['segments']:
                    sched.append({
                        'name': p['name'],
                        'arrival': p['arrival'],
                        'burst': p['burst'],
                        'start': seg['start'],
                        'finish': seg['end']
                    })
            sched.sort(key=lambda s: s['start'])
            return sched

        def priority_schedule(plist, order="Smaller Priority First"):
            unscheduled = plist[:]
            sched = []
            currentTime = 0.0
            last_proc = None
            
            while unscheduled:
                available = [p for p in unscheduled if p['arrival'] <= currentTime]
                if not available:
                    currentTime = min(unscheduled, key=lambda p: p['arrival'])['arrival']
                    available = [p for p in unscheduled if p['arrival'] <= currentTime]
                
                if order == "Smaller Priority First":
                    chosen = min(available, key=lambda p: p.get('priority', 9999))
                else:
                    chosen = max(available, key=lambda p: p.get('priority', -9999))
                
                start = max(currentTime, chosen['arrival'])
                finish = start + chosen['burst']
                sched.append({
                    'name': chosen['name'],
                    'arrival': chosen['arrival'],
                    'burst': chosen['burst'],
                    'start': start,
                    'finish': finish
                })
                currentTime = finish
                last_proc = chosen['name']
                unscheduled.remove(chosen)
            return sched

        def rms_schedule(plist):
            for p in plist:
                if 'period' not in p:
                    p['period'] = p['arrival'] + p['burst']
            unscheduled = plist[:]
            sched = []
            currentTime = 0.0
            last_proc = None
            
            while unscheduled:
                available = [p for p in unscheduled if p['arrival'] <= currentTime]
                if not available:
                    currentTime = min(unscheduled, key=lambda p: p['arrival'])['arrival']
                    available = [p for p in unscheduled if p['arrival'] <= currentTime]
                chosen = min(available, key=lambda p: p['period'])
                start = max(currentTime, chosen['arrival'])
                finish = start + chosen['burst']
                sched.append({
                    'name': chosen['name'],
                    'arrival': chosen['arrival'],
                    'burst': chosen['burst'],
                    'start': start,
                    'finish': finish
                })
                currentTime = finish
                last_proc = chosen['name']
                unscheduled.remove(chosen)
            return sched

        def edf_schedule(plist):
            for p in plist:
                if 'deadline' not in p:
                    p['deadline'] = p['arrival'] + p['burst']
            plist_sorted = sorted(plist, key=lambda p: p['deadline'])
            currentTime = 0.0
            sched = []
            last_proc = None
            
            while plist_sorted:
                available = [p for p in plist_sorted if p['arrival'] <= currentTime]
                if not available:
                    currentTime = min(plist_sorted, key=lambda p: p['arrival'])['arrival']
                    available = [p for p in plist_sorted if p['arrival'] <= currentTime]
                chosen = min(available, key=lambda p: p['deadline'])
                start = max(currentTime, chosen['arrival'])
                finish = start + chosen['burst']
                sched.append({
                    'name': chosen['name'],
                    'arrival': chosen['arrival'],
                    'burst': chosen['burst'],
                    'start': start,
                    'finish': finish
                })
                currentTime = finish
                last_proc = chosen['name']
                plist_sorted.remove(chosen)
            return sched

        # Choose scheduler based on algorithm.
        if alg == "FCFS":
            schedule = fcfs_schedule(processList)
        elif alg == "SJF (Non Preemptive)":
            schedule = sjf_non_preemptive_schedule(processList)
        elif alg == "SJF (Preemptive)":
            schedule = sjf_preemptive_schedule(processList)
        elif alg == "Priority Scheduling":
            order = self.priorityOrderCombo.currentText() if self.priorityOrderCombo.currentText() in ["Greater Priority First", "Smaller Priority First"] else "Smaller Priority First"
            schedule = priority_schedule(processList, order)
        elif alg == "RMS":
            schedule = rms_schedule(processList)
        elif alg == "EDF":
            schedule = edf_schedule(processList)
        elif alg == "Round Robin":
            try:
                quantum = float(self.timeQuantumEdit.text())
                if quantum <= 0:
                    quantum = 1.0
            except Exception:
                quantum = 1.0
            schedule = round_robin_schedule(processList, quantum)
        else:
            schedule = fcfs_schedule(processList)

        # Open the Gantt Chart window with the computed schedule.
        ganttWindow = GanttChartWindow(alg, schedule, self)
        ganttWindow.exec_()