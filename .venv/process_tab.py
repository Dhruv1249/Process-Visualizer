# process_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

class ProcessTab(QWidget):
    """
    A simple Process tab with two top buttons: "List" and "Graph".
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        self.btnList = QPushButton("List")
        self.btnGraph = QPushButton("Graph")

        # Add them side by side at the top
        top_layout.addWidget(self.btnList)
        top_layout.addWidget(self.btnGraph)

        main_layout.addLayout(top_layout)

        # Placeholder for future content
        self.placeholderLabel = QLabel("Process tab content here")
        main_layout.addWidget(self.placeholderLabel)
