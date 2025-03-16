# process_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

sciFiFontName = "Conthrax"

class ProcessTab(QWidget):
    """
    A Process tab with two top buttons: "List" and "Graph".
    Shows a vertical white line between them, a horizontal white line below,
    and a blue left border on whichever sub-tab is selected.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.currentSubTab = None

        # Normal vs. Selected button styles
        # NOTE: We add 'margin-left' or extra padding in selected style
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
                /* Additional left padding so border is clearly visible: */
                padding: 18px 18px 18px 18px;
                background-color: #1A1A1A;
                /* Blue left border: */
                border-left: 4px solid #00A2FF;
            }}
        """

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Row with two buttons + vertical line
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.btnList = QPushButton("List")
        self.btnGraph = QPushButton("Graph")

        # Vertical white line between the two buttons
        sep_vertical = QFrame()
        sep_vertical.setFixedWidth(1)
        sep_vertical.setStyleSheet("background-color: white;")

        top_layout.addWidget(self.btnList)
        top_layout.addWidget(sep_vertical)
        top_layout.addWidget(self.btnGraph)
        main_layout.addLayout(top_layout)

        # Horizontal white line below
        sep_horizontal = QFrame()
        sep_horizontal.setFixedHeight(1)
        sep_horizontal.setStyleSheet("background-color: white;")
        main_layout.addWidget(sep_horizontal)

        # Placeholder
        self.placeholderLabel = QLabel("Process tab content here")
        self.placeholderLabel.setStyleSheet("color: white; font-size: 24px;")
        self.placeholderLabel.setFont(QFont(sciFiFontName, 24, QFont.Bold))
        main_layout.addWidget(self.placeholderLabel, alignment=Qt.AlignCenter)

        # Connect each button to switch sub-tab
        self.btnList.clicked.connect(lambda: self.setCurrentSubTab(self.btnList))
        self.btnGraph.clicked.connect(lambda: self.setCurrentSubTab(self.btnGraph))

        # Default to "List" sub-tab
        self.setCurrentSubTab(self.btnList)

    def setCurrentSubTab(self, btn):
        """Marks 'btn' as selected and updates the styles."""
        self.currentSubTab = btn
        self.updateSubTabStyles()

    def updateSubTabStyles(self):
        """Apply 'selected' style to currentSubTab, normal style to the other."""
        if self.currentSubTab == self.btnList:
            self.btnList.setStyleSheet(self.styleSelected)
            self.btnGraph.setStyleSheet(self.styleNormal)
        else:
            self.btnList.setStyleSheet(self.styleNormal)
            self.btnGraph.setStyleSheet(self.styleSelected)
