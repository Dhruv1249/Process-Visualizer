from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QRectF
from PyQt5.QtCore import Qt
class DiskTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("Disk Tab Placeholder")
        label.setStyleSheet("color: white; font-size: 24px;")
        layout.addWidget(label)
        
        
import os
import psutil
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QProgressBar, QFrame, QGridLayout, QSplitter
)

class CircularProgressBar(QWidget):
    valueChanged = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._maxValue = 100.0
        self._title = ""
        self._subtitle = ""
        # Increase minimum size for a larger widget
        self.setMinimumSize(280, 280)
        
    def setValue(self, value):
        value = max(0.0, min(self._maxValue, float(value)))
        if value != self._value:
            self._value = value
            self.valueChanged.emit(self._value)
            self.update()
            
    def getValue(self):
        return self._value
        
    def setTitle(self, title):
        self._title = title
        self.update()
        
    def setSubtitle(self, subtitle):
        self._subtitle = subtitle
        self.update()
        
    value = pyqtProperty(float, getValue, setValue, notify=valueChanged)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        size = min(width, height)
        
        # Calculate circle dimensions - make the circle larger
        outer_radius = size * 0.48  # Increased from 0.45
        inner_radius = outer_radius * 0.88  # Increased from 0.85
        center_x = width / 2
        center_y = height / 2
        
        # Draw background circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(40, 40, 40))
        painter.drawEllipse(int(center_x - outer_radius), int(center_y - outer_radius), 
                   int(outer_radius * 2), int(outer_radius * 2))
        
        # Draw progress arc - slightly thicker
        pen = QPen(QColor(0, 162, 255), (outer_radius - inner_radius) * 1.3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Calculate start and span angles
        start_angle = 90 * 16  # Start at 12 o'clock position (90 degrees)
        span_angle = -int(self._value / self._maxValue * 360 * 16)  # Negative for clockwise
        
        painter.drawArc(int(center_x - inner_radius), int(center_y - inner_radius),
                int(inner_radius * 2), int(inner_radius * 2),
                int(start_angle), int(span_angle))
        
        # Draw title at the top of the circle
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Conthrax", 14)  # Smaller font size
        painter.setFont(font)
        rect_title = QRectF(center_x - inner_radius * 0.7, center_y - inner_radius * 0.5, 
                          inner_radius * 1.4, inner_radius * 0.3)
        painter.drawText(rect_title, Qt.AlignCenter, self._title)
        
        # Draw value text in the center - smaller than before
        font = QFont("Conthrax", 20, QFont.Bold)  # Reduced from 22
        painter.setFont(font)
        value_text = f"{self._value:.1f}%"
        rect_value = QRectF(center_x - inner_radius * 0.7, center_y - inner_radius * 0.2, 
                           inner_radius * 1.4, inner_radius * 0.4)
        painter.drawText(rect_value, Qt.AlignCenter, value_text)
        
        # Draw subtitle at the bottom - smaller font
        font = QFont("Conthrax", 9)  # Smaller font size
        painter.setFont(font)
        rect_subtitle = QRectF(center_x - inner_radius * 0.7, center_y + inner_radius * 0.2, 
                             inner_radius * 1.4, inner_radius * 0.3)
        
        # Handle potential line breaks in subtitle (like C:\)
        subtitle_elided = painter.fontMetrics().elidedText(self._subtitle, Qt.ElideRight, int(inner_radius * 1.4))
        painter.drawText(rect_subtitle, Qt.AlignCenter, subtitle_elided)

class DiskInfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setStyleSheet("background-color: #101010; border-radius: 10px;")
        
        # Title
        self.titleLabel = QLabel("Disk Information")
        self.titleLabel.setStyleSheet("color: white; font-size: 18px; font-family: Conthrax;")
        self.layout.addWidget(self.titleLabel)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #303030;")
        self.layout.addWidget(separator)
        
        # Info grid
        self.infoGrid = QGridLayout()
        self.infoGrid.setSpacing(10)
        self.layout.addLayout(self.infoGrid)
        
        # Create and style labels
        self.labelStyle = "color: #00A2FF; font-size: 12px; font-family: Conthrax;"
        self.valueStyle = "color: white; font-size: 12px; font-family: Conthrax;"
        
        # Add labels
        self.createInfoRow("File System:", "file_system", 0)
        self.createInfoRow("Mount Point:", "mount_point", 1)
        self.createInfoRow("Total Size:", "total_size", 2)
        self.createInfoRow("Used Space:", "used_space", 3)
        self.createInfoRow("Free Space:", "free_space", 4)
        self.createInfoRow("Usage:", "usage", 5)
        
        self.layout.addStretch()
        
    def createInfoRow(self, label_text, value_id, row):
        label = QLabel(label_text)
        label.setStyleSheet(self.labelStyle)
        value = QLabel("--")
        value.setObjectName(value_id)
        value.setStyleSheet(self.valueStyle)
        
        self.infoGrid.addWidget(label, row, 0)
        self.infoGrid.addWidget(value, row, 1)
        
    def updateInfo(self, disk_info):
        self.findChild(QLabel, "file_system").setText(disk_info["file_system"])
        self.findChild(QLabel, "mount_point").setText(disk_info["mount_point"])
        self.findChild(QLabel, "total_size").setText(disk_info["total_size"])
        self.findChild(QLabel, "used_space").setText(disk_info["used_space"])
        self.findChild(QLabel, "free_space").setText(disk_info["free_space"])
        self.findChild(QLabel, "usage").setText(f"{disk_info['usage']}%")

class DiskReadWritePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setStyleSheet("background-color: #101010; border-radius: 10px;")
        
        # Title
        self.titleLabel = QLabel("Disk I/O Performance")
        self.titleLabel.setStyleSheet("color: white; font-size: 18px; font-family: Conthrax;")
        self.layout.addWidget(self.titleLabel)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #303030;")
        self.layout.addWidget(separator)
        
        # Create read/write meters
        metersLayout = QGridLayout()
        
        # Read meter
        readLayout = QVBoxLayout()
        self.readLabel = QLabel("Read Speed")
        self.readLabel.setStyleSheet("color: #00A2FF; font-size: 14px; font-family: Conthrax;")
        self.readValue = QLabel("0 MB/s")
        self.readValue.setStyleSheet("color: white; font-size: 16px; font-family: Conthrax;")
        readLayout.addWidget(self.readLabel)
        readLayout.addWidget(self.readValue)
        
        # Write meter
        writeLayout = QVBoxLayout()
        self.writeLabel = QLabel("Write Speed")
        self.writeLabel.setStyleSheet("color: #00A2FF; font-size: 14px; font-family: Conthrax;")
        self.writeValue = QLabel("0 MB/s")
        self.writeValue.setStyleSheet("color: white; font-size: 16px; font-family: Conthrax;")
        writeLayout.addWidget(self.writeLabel)
        writeLayout.addWidget(self.writeValue)
        
        # Add to grid
        metersLayout.addLayout(readLayout, 0, 0)
        metersLayout.addLayout(writeLayout, 0, 1)
        
        self.layout.addLayout(metersLayout)
        
        # Add progress bars
        self.readProgress = QProgressBar()
        self.readProgress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #303030;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #202020;
            }
            QProgressBar::chunk {
                background-color: #00A2FF;
                border-radius: 5px;
            }
        """)
        self.readProgress.setMaximum(100)
        self.readProgress.setValue(0)
        self.layout.addWidget(self.readProgress)
        
        self.writeProgress = QProgressBar()
        self.writeProgress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #303030;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background-color: #202020;
            }
            QProgressBar::chunk {
                background-color: #FF5500;
                border-radius: 5px;
            }
        """)
        self.writeProgress.setMaximum(100)
        self.writeProgress.setValue(0)
        self.layout.addWidget(self.writeProgress)
        
        self.layout.addStretch()
        
        # Initialize disk I/O counters
        self.prev_read_bytes = 0
        self.prev_write_bytes = 0
        self.max_speed = 100  # MB/s, adjust dynamically
        
    def updateIO(self, read_bytes, write_bytes):
        # Calculate speeds
        read_speed = (read_bytes - self.prev_read_bytes) / 1024 / 1024  # MB/s
        write_speed = (write_bytes - self.prev_write_bytes) / 1024 / 1024  # MB/s
        
        # Update previous values
        self.prev_read_bytes = read_bytes
        self.prev_write_bytes = write_bytes
        
        # Update max speed if needed
        if read_speed > self.max_speed or write_speed > self.max_speed:
            self.max_speed = max(read_speed, write_speed) * 1.2  # Add 20% margin
        
        # Update UI
        self.readValue.setText(f"{read_speed:.2f} MB/s")
        self.writeValue.setText(f"{write_speed:.2f} MB/s")
        
        # Update progress bars
        self.readProgress.setValue(int(read_speed / self.max_speed * 100))
        self.writeProgress.setValue(int(write_speed / self.max_speed * 100))

class DiskPartitionsTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.setStyleSheet("background-color: #101010; border-radius: 10px;")
        
        # Title
        self.titleLabel = QLabel("Disk Partitions")
        self.titleLabel.setStyleSheet("color: white; font-size: 18px; font-family: Conthrax;")
        self.layout.addWidget(self.titleLabel)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #303030;")
        self.layout.addWidget(separator)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Device", "Mount Point", "File System", "Size", "Usage"])
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #101010;
                color: white;
                gridline-color: #303030;
                font-family: Conthrax;
            }
            QHeaderView::section {
                background-color: #202020;
                color: #00A2FF;
                border: 1px solid #303030;
                padding: 4px;
                font-family: Conthrax;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #303030;
            }
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)
        
    def updatePartitions(self, partitions):
        self.table.setRowCount(len(partitions))
        
        for row, partition in enumerate(partitions):
            self.table.setItem(row, 0, QTableWidgetItem(partition["device"]))
            self.table.setItem(row, 1, QTableWidgetItem(partition["mountpoint"]))
            self.table.setItem(row, 2, QTableWidgetItem(partition["fstype"]))
            self.table.setItem(row, 3, QTableWidgetItem(partition["size"]))
            
            # Create progress bar for usage
            usage_bar = QProgressBar()
            usage_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #303030;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #202020;
                }
                QProgressBar::chunk {
                    background-color: #00A2FF;
                    border-radius: 3px;
                }
            """)
            usage_bar.setMaximum(100)
            usage_bar.setValue(int(partition["usage"]))
            usage_bar.setFormat(f"{partition['usage']}%")
            
            self.table.setCellWidget(row, 4, usage_bar)

class DiskTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #000000; color: #FFFFFF;")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Disk Management")
        title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_font = QFont("Conthrax", 36, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background-color: transparent;")
        header_layout.addWidget(title_label)
        
        # Disk selector
        self.diskSelector = QComboBox()
        self.diskSelector.setStyleSheet("""
            QComboBox {
                background-color: #101010;
                color: white;
                border: 1px solid #303030;
                border-radius: 5px;
                padding: 5px;
                min-width: 150px;
                font-family: Conthrax;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #303030;
            }
        """)
        self.diskSelector.currentIndexChanged.connect(self.onDiskChanged)
        header_layout.addWidget(self.diskSelector)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Top section with disk usage visualization and disk info
        top_layout = QHBoxLayout()
        
        # Disk usage visualization
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #101010; border-radius: 10px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        # Disk usage label
        usage_label = QLabel("Disk Usage")
        usage_label.setStyleSheet("color: white; font-size: 18px; font-family: Conthrax;")
        left_layout.addWidget(usage_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #303030;")
        left_layout.addWidget(separator)
        
        # Disk usage circular progress
        self.diskUsageProgress = CircularProgressBar()
        self.diskUsageProgress.setTitle("Usage")
        self.diskUsageProgress.setValue(0)
        left_layout.addWidget(self.diskUsageProgress, alignment=Qt.AlignCenter)
        
        # Usage breakdown
        breakdown_layout = QHBoxLayout()
        
        # Used space
        used_layout = QVBoxLayout()
        used_label = QLabel("Used Space")
        used_label.setStyleSheet("color: #00A2FF; font-size: 14px; font-family: Conthrax;")
        self.usedValue = QLabel("0 GB")
        self.usedValue.setStyleSheet("color: white; font-size: 16px; font-family: Conthrax;")
        used_layout.addWidget(used_label)
        used_layout.addWidget(self.usedValue)
        
        # Free space
        free_layout = QVBoxLayout()
        free_label = QLabel("Free Space")
        free_label.setStyleSheet("color: #00A2FF; font-size: 14px; font-family: Conthrax;")
        self.freeValue = QLabel("0 GB")
        self.freeValue.setStyleSheet("color: white; font-size: 16px; font-family: Conthrax;")
        free_layout.addWidget(free_label)
        free_layout.addWidget(self.freeValue)
        
        breakdown_layout.addLayout(used_layout)
        breakdown_layout.addLayout(free_layout)
        left_layout.addLayout(breakdown_layout)
        
        # Right panel with disk info
        self.diskInfoPanel = DiskInfoPanel()
        
        top_layout.addWidget(left_panel, 1)
        top_layout.addWidget(self.diskInfoPanel, 1)
        main_layout.addLayout(top_layout)
        
        # Bottom section with disk I/O and partitions
        bottom_layout = QHBoxLayout()
        
        # Disk I/O panel
        self.diskIOPanel = DiskReadWritePanel()
        
        # Partitions table
        self.partitionsTable = DiskPartitionsTable()
        
        bottom_layout.addWidget(self.diskIOPanel, 1)
        bottom_layout.addWidget(self.partitionsTable, 2)
        main_layout.addLayout(bottom_layout)
        
        # Setup timer for updates
        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(2000)  # Update every 2 seconds
        self.updateTimer.timeout.connect(self.updateDiskInfo)
        self.updateTimer.start()
        
        # Initial disk info update
        self.populateDiskSelector()
        self.updateDiskInfo()
        
    def populateDiskSelector(self):
        self.diskSelector.clear()
        partitions = psutil.disk_partitions(all=False)
        
        for partition in partitions:
            if os.name == 'nt':  # Windows
                # Skip CD-ROM drives with no media
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
            self.diskSelector.addItem(f"{partition.device} ({partition.mountpoint})", partition.device)
    
    def onDiskChanged(self, index):
        self.updateDiskInfo()
    
    def updateDiskInfo(self):
        if self.diskSelector.count() == 0:
            return
            
        selected_device = self.diskSelector.currentData()
        selected_partition = None
        
        # Find the selected partition
        for partition in psutil.disk_partitions(all=False):
            if partition.device == selected_device:
                selected_partition = partition
                break
                
        if not selected_partition:
            return
            
        # Get disk usage information
        try:
            usage = psutil.disk_usage(selected_partition.mountpoint)
            
            # Update disk usage circular progress
            self.diskUsageProgress.setValue(usage.percent)
            self.diskUsageProgress.setSubtitle(selected_partition.device)
            
            # Update usage breakdown
            self.usedValue.setText(self.format_bytes(usage.used))
            self.freeValue.setText(self.format_bytes(usage.free))
            
            # Update disk info panel
            disk_info = {
                "file_system": selected_partition.fstype,
                "mount_point": selected_partition.mountpoint,
                "total_size": self.format_bytes(usage.total),
                "used_space": self.format_bytes(usage.used),
                "free_space": self.format_bytes(usage.free),
                "usage": f"{usage.percent}"
            }
            self.diskInfoPanel.updateInfo(disk_info)
            
        except Exception as e:
            print(f"Error getting disk usage: {e}")
            
        # Update disk I/O information
        try:
            disk_io = psutil.disk_io_counters(perdisk=False)
            self.diskIOPanel.updateIO(disk_io.read_bytes, disk_io.write_bytes)
        except Exception as e:
            print(f"Error getting disk I/O: {e}")
            
        # Update partitions table
        try:
            partitions = []
            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "size": self.format_bytes(usage.total),
                        "usage": usage.percent
                    })
                except Exception:
                    # Skip if unable to get usage
                    continue
                    
            self.partitionsTable.updatePartitions(partitions)
        except Exception as e:
            print(f"Error updating partitions: {e}")
    
    def format_bytes(self, bytes):
        """Format bytes to human-readable string"""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024**2:
            return f"{bytes/1024:.2f} KB"
        elif bytes < 1024**3:
            return f"{bytes/1024**2:.2f} MB"
        elif bytes < 1024**4:
            return f"{bytes/1024**3:.2f} GB"
        else:
            return f"{bytes/1024**4:.2f} TB"
            
    def showEvent(self, event):
        """Called when the tab is shown"""
        super().showEvent(event)
        self.updateTimer.start()
        
    def hideEvent(self, event):
        """Called when the tab is hidden"""
        super().hideEvent(event)
        self.updateTimer.stop()
