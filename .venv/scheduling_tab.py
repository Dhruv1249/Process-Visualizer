from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class SchedulingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Scheduling Tab Placeholder")
        label.setStyleSheet("color: white; font-size: 24px;")
        layout.addWidget(label)
