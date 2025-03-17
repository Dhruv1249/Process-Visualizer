from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox,
                             QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt

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
        # Set overall table style along with header styling:
        # We add gridline-color and specify cell border via QTableWidget::item
        # Adding QTableWidget::item:selected rule to make selected cell blue.
        self.processTable.setStyleSheet(
            "QTableWidget { background-color: #000000; color: white; font-size: 16px; font-family: Conthrax; gridline-color: white; }"
            "QHeaderView::section { background-color: #000000; color: white; font-family: Conthrax; font-weight: bold; border: 1px solid white; }"
            "QTableWidget::item { border: 1px solid white; }"
            "QTableWidget::item:selected { background-color: blue; }"
        )
        self.processTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.processTable.verticalHeader().setStyleSheet("background-color: #000000; color: white; font-family: Conthrax;")
        # Change the height here by updating the value passed to setFixedHeight.
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
        # Example connection: self.startSchedulingButton.clicked.connect(self.startScheduling)
        buttonLayout.addWidget(self.startSchedulingButton, alignment=Qt.AlignLeft)
        
        self.processFormLayout.addWidget(buttonContainer)
        
        layout.addWidget(self.processFormContainer)
        
        # Set up the process input form based on the default (non-selected) algorithm.
        # This will create a default 3-column table.
        self.updateProcessInputForm(self.schedAlgoCombo.currentText())
        
        # Connect the selection change to update the process input fields:
        self.schedAlgoCombo.currentIndexChanged.connect(
            lambda: self.updateProcessInputForm(self.schedAlgoCombo.currentText()))
        
        # Keep a counter for default process names.
        self.processCount = 0

    def updateProcessInputForm(self, algo):
        """
        Update the process input form (the QTableWidget) based on the selected scheduling algorithm.
        For FCFS, SJF (both), and Round Robin, we display 3 columns:
            ["Process Name", "Arrival Time", "Burst Time"]
        For Priority Scheduling:
            ["Process Name", "Arrival Time", "Burst Time", "Priority"]
        For RMS:
            ["Process Name", "Arrival Time", "Burst Time", "Period"]
        For EDF:
            ["Process Name", "Arrival Time", "Burst Time", "Deadline"]
        """
        # Determine columns based on the algorithm.
        if algo in ["Priority Scheduling"]:
            columns = ["Process Name", "Arrival Time", "Burst Time", "Priority"]
        elif algo in ["RMS"]:
            columns = ["Process Name", "Arrival Time", "Burst Time", "Period"]
        elif algo in ["EDF"]:
            columns = ["Process Name", "Arrival Time", "Burst Time", "Deadline"]
        else:
            # For "Select Algorithm", FCFS, SJF variants, Round Robin, etc.
            columns = ["Process Name", "Arrival Time", "Burst Time"]
        
        self.processTable.clear()
        self.processTable.setColumnCount(len(columns))
        self.processTable.setHorizontalHeaderLabels(columns)
        self.processTable.setRowCount(0)  # Clear existing rows
        # Reset process count when form structure changes
        self.processCount = 0
        
        # Update visibility of additional options based on chosen algorithm.
        self.updateAdditionalOptionsVisibility(algo)

    def updateAdditionalOptionsVisibility(self, algo):
        """
        For Round Robin, show the time quantum entry.
        For Priority Scheduling, show the priority order dropdown.
        Hide the additional options for other algorithms.
        """
        if algo == "Round Robin":
            self.timeQuantumContainer.show()
        else:
            self.timeQuantumContainer.hide()
            
        if algo == "Priority Scheduling":
            self.priorityOrderContainer.show()
        else:
            self.priorityOrderContainer.hide()
        
    def addProcessRow(self):
        """
        Add a new row to the process input table with default values.
        The default process name is p{n} where n is the next process number.
        Default arrival and burst times are set to 0.
        For additional columns like priority/period/deadline, set 0 as well.
        """
        currentRow = self.processTable.rowCount()
        self.processTable.insertRow(currentRow)
        self.processCount += 1
        defaultName = f"p{self.processCount}"
        
        # Insert default values in columns.
        colCount = self.processTable.columnCount()
        for col in range(colCount):
            if col == 0:
                # Process Name column
                item = QTableWidgetItem(defaultName)
            else:
                # Default numeric value as "0"
                item = QTableWidgetItem("0")
            self.processTable.setItem(currentRow, col, item)
    
    def clearTable(self):
        """
        Clear all rows from the process table and reset the process count.
        """
        self.processTable.setRowCount(0)
        self.processCount = 0
        
    def removeProcess(self):
        """
        Remove the currently selected row from the process table.
        If no row is selected, do nothing.
        """
        # Get the selected ranges.
        selected = self.processTable.selectedIndexes()
        if not selected:
            return
        # Remove row corresponding to the first selected index.
        row_to_remove = selected[0].row()
        self.processTable.removeRow(row_to_remove)
