import psutil
import datetime
import csv
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QFileDialog,
    QAbstractItemView, QFrame, QProgressBar, QCheckBox, QComboBox, QStyle
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QAction, QPainter, QPainterPath, QLinearGradient, QRadialGradient, QPen, QTextDocument, QPalette, QFont
from PyQt6.QtPrintSupport import QPrinter

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import DatabaseManager

# --- Constants ---
REFRESH_INTERVAL = 3000  # 3 seconds
HIGH_CPU_THRESHOLD = 80.0
HIGH_MEM_THRESHOLD = 80.0

class SortableTableWidgetItem(QTableWidgetItem):
    """Custom item to ensure proper sorting by UserRole (handles both numeric and strings)."""
    def __lt__(self, other):
        val1 = self.data(Qt.ItemDataRole.UserRole)
        val2 = other.data(Qt.ItemDataRole.UserRole)
        try:
            return float(val1) < float(val2)
        except (ValueError, TypeError):
            return str(val1) < str(val2)

class ProcessWorker(QThread):
    """
    Background thread to fetch system processes.
    Prevents UI freezing during data collection.
    """
    data_fetched = pyqtSignal(list)

    def run(self):
        processes = []
        # Fetch specific attributes to optimize performance
        attrs = ['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'username', 'create_time', 'io_counters']
        
        for proc in psutil.process_iter(attrs):
            try:
                pinfo = proc.info
                # Format io_counters to simple string for Disk/Net deltas
                # psutil provides read_bytes, write_bytes for io_counters
                if pinfo.get('io_counters'):
                    io = pinfo['io_counters']
                    # We will just pass the raw bytes, the UI can format them or calculate deltas
                    pinfo['disk_read'] = getattr(io, 'read_bytes', 0)
                    pinfo['disk_write'] = getattr(io, 'write_bytes', 0)
                else:
                    pinfo['disk_read'] = 0
                    pinfo['disk_write'] = 0
                    
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        self.data_fetched.emit(processes)

class ResourceChart(QFrame):
    """Custom widget to draw live resource usage charts."""
    def __init__(self, title, line_color="#0078d7"):
        super().__init__()
        self.setObjectName("ChartCard")
        self.title = title
        self.line_color = QColor(line_color)
        self.data = deque([0]*60, maxlen=60) # 60 data points
        self.setMinimumHeight(150)
        self.current_value = 0.0

    def update_value(self, value):
        self.current_value = value
        self.data.append(value)
        self.update()

    def paintEvent(self, event):
        # Let QSS handle the background
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        top_pad = 40
        chart_h = h - top_pad
        
        grid_col = QColor(128, 128, 128, 30)
        
        # 1. Draw Grid Lines (Underneath graph)
        painter.setPen(QPen(grid_col, 1, Qt.PenStyle.DashLine))
        for i in range(4):
            y_line = top_pad + i * (chart_h / 3)
            painter.drawLine(0, int(y_line), w, int(y_line))
        
        if not self.data:
            return
            
        # 2. Draw Graph Path (Smooth Bezier)
        path = QPainterPath()
        step_x = w / (self.data.maxlen - 1)
        
        prev_x = 0
        prev_y = h - (self.data[0] / 100.0 * chart_h)
        path.moveTo(prev_x, prev_y)
        
        for i in range(1, len(self.data)):
            x = i * step_x
            y = h - (self.data[i] / 100.0 * chart_h)
            
            # Control points for smooth bezier curve
            ctrl_x1 = prev_x + (x - prev_x) * 0.5
            ctrl_y1 = prev_y
            ctrl_x2 = prev_x + (x - prev_x) * 0.5
            ctrl_y2 = y
            
            path.cubicTo(ctrl_x1, ctrl_y1, ctrl_x2, ctrl_y2, x, y)
            prev_x = x
            prev_y = y
            
        # Fill Gradient
        fill_path = QPainterPath(path)
        fill_path.lineTo(w, h)
        fill_path.lineTo(0, h)
        fill_path.closeSubpath()
        
        grad = QLinearGradient(0, top_pad, 0, h)
        c = self.line_color
        grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 120))
        grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 10))
        
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(fill_path)

        # Draw Line
        painter.setPen(QPen(self.line_color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Draw Leading Dot Glow
        glow = QRadialGradient(prev_x, prev_y, 20)
        glow.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 180))
        glow.setColorAt(1, Qt.GlobalColor.transparent)
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(prev_x - 20), int(prev_y - 20), 40, 40)

        # Draw Leading Dot
        painter.setBrush(c)
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawEllipse(int(prev_x - 5), int(prev_y - 5), 10, 10)

        # 3. Draw Text & Labels
        text_col = self.palette().color(QPalette.ColorRole.WindowText)
        label_col = QColor(128, 128, 128, 150)
        
        painter.setFont(QFont("Segoe UI", 8))
        painter.setPen(label_col)
        for i in range(4):
            y_line = top_pad + i * (chart_h / 3)
            lbl = ["100%", "66%", "33%", "0%"][i]
            painter.drawText(w - 35, int(y_line) - 4, lbl)
            
        painter.setPen(text_col)
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(15, 28, f"{self.title}: {self.current_value:.1f}%")

class ProcessMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("ProcessMonitor")
        
        # State
        self.process_data = []
        self.filter_text = ""
        
        # UI Setup
        self.setup_ui()
        
        # Worker & Timer
        self.worker = ProcessWorker()
        self.worker.data_fetched.connect(self.update_table)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        
        # Chart Timer (1 second updates)
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_charts)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_data()
        self.timer.start(REFRESH_INTERVAL)
        self.chart_timer.start(1000)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()
        self.chart_timer.stop()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Top Control Bar ---
        self.control_frame = QFrame()
        self.control_frame.setObjectName("ProcessToolbar")
        control_bar = QHBoxLayout(self.control_frame)
        control_bar.setContentsMargins(15, 10, 15, 10)
        control_bar.setSpacing(15)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Process Name or PID...")
        self.search_input.setFixedWidth(400)
        self.search_input.textChanged.connect(self.handle_search)
        control_bar.addWidget(self.search_input)

        self.btn_clear_search = QPushButton("X")
        self.btn_clear_search.setObjectName("ClearSearchBtn")
        self.btn_clear_search.setFixedSize(32, 32)
        self.btn_clear_search.setToolTip("Clear Search")
        self.btn_clear_search.clicked.connect(self.clear_search)
        control_bar.addWidget(self.btn_clear_search)

        # Smart Filtering Dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("FilterDropdown")
        self.filter_combo.addItems(["All", "System", "User Apps", "Suspicious"])
        self.filter_combo.setFixedWidth(150)
        self.filter_combo.currentTextChanged.connect(self.set_category_filter)
        control_bar.addWidget(self.filter_combo)
        self.current_category = "All"

        control_bar.addStretch()

        # Action Buttons
        self.btn_suspend = QPushButton("⏸️ Suspend")
        self.btn_suspend.setObjectName("BtnOutline")
        self.btn_suspend.clicked.connect(lambda: self.change_process_state("suspend"))
        control_bar.addWidget(self.btn_suspend)

        self.btn_resume = QPushButton("▶️ Resume")
        self.btn_resume.setObjectName("BtnOutline")
        self.btn_resume.clicked.connect(lambda: self.change_process_state("resume"))
        control_bar.addWidget(self.btn_resume)

        self.btn_kill = QPushButton("💀 End Task")
        self.btn_kill.setObjectName("BtnDanger") 
        self.btn_kill.clicked.connect(self.kill_process)
        control_bar.addWidget(self.btn_kill)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setObjectName("BtnPrimary")
        self.btn_refresh.clicked.connect(self.refresh_data)
        control_bar.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("📄 CSV")
        self.btn_export.setObjectName("BtnInfo")
        self.btn_export.clicked.connect(self.export_csv)
        control_bar.addWidget(self.btn_export)

        self.btn_export_pdf = QPushButton("📑 PDF")
        self.btn_export_pdf.setObjectName("BtnWarning")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        control_bar.addWidget(self.btn_export_pdf)

        layout.addWidget(self.control_frame)

        # --- Content Area (Split 1:2) ---
        content_layout = QHBoxLayout()

        # --- Resource Charts (Vertical Layout on left) ---
        self.charts_panel = QFrame()
        charts_layout = QVBoxLayout(self.charts_panel)
        charts_layout.setContentsMargins(0, 0, 15, 0)
        charts_layout.setSpacing(15)
        
        self.cpu_chart = ResourceChart("🧠 CPU Usage", "#00c6ff")
        self.mem_chart = ResourceChart("💾 RAM Usage", "#ff5e7e")
        charts_layout.addWidget(self.cpu_chart)
        charts_layout.addWidget(self.mem_chart)
        
        content_layout.addWidget(self.charts_panel, 1) # Stretch 1

        # --- Process Table ---
        self.table_container = QFrame()
        self.table_container.setObjectName("ProcessTableContainer")
        table_layout = QVBoxLayout(self.table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setObjectName("ProcessTable")
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "", "PID", "Name", "Status", "CPU", "Memory", "Disk I/O", "Net I/O", "User", "Start Time"
        ])
        
        # Table Styling & Behavior
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Header sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # PID
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # CPU bar
        self.table.setColumnWidth(4, 120)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed) # Mem bar
        self.table.setColumnWidth(5, 100)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed) # Disk
        self.table.setColumnWidth(6, 80)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed) # Net
        self.table.setColumnWidth(7, 80)
        
        self.table.itemSelectionChanged.connect(self.on_process_selected)
        
        table_layout.addWidget(self.table)
        content_layout.addWidget(self.table_container, 2) # Stretch 2
        
        # --- Deep Dive Panel (Hidden initially) ---
        self.details_panel = QFrame()
        self.details_panel.setObjectName("DetailsPanel")
        self.details_panel.setFixedWidth(300)
        self.details_panel.hide()
        
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(10)
        
        self.lbl_details_title = QLabel("Process Forensics")
        self.lbl_details_title.setObjectName("DetailsTitle")
        details_layout.addWidget(self.lbl_details_title)
        
        self.lbl_details_info = QLabel("Select a process to inspect.")
        self.lbl_details_info.setObjectName("DetailsInfo")
        self.lbl_details_info.setWordWrap(True)
        self.lbl_details_info.setAlignment(Qt.AlignmentFlag.AlignTop)
        details_layout.addWidget(self.lbl_details_info, 1)
        
        content_layout.addWidget(self.details_panel)
        
        layout.addLayout(content_layout)

        # Status Bar / Footer
        self.status_label = QLabel("✅ Ready")
        self.status_label.setObjectName("StatusBarLabel")
        layout.addWidget(self.status_label)

    def reset_ui(self):
        """Clears filters and triggers a data refresh."""
        self.search_input.clear()
        self.chk_select_all.setChecked(False)
        self.refresh_data()

    def clear_search(self):
        self.search_input.clear()

    def toggle_select_all(self, state):
        check_state = Qt.CheckState(state)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(check_state)

    def update_charts(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.cpu_chart.update_value(cpu)
        self.mem_chart.update_value(mem)

    def refresh_data(self):
        """Triggers the background worker if not already running."""
        if not self.worker.isRunning():
            self.status_label.setText("Updating...")
            self.worker.start()

    def update_table(self, processes):
        """Updates the table with new data while preserving scroll and selection."""
        self.process_data = processes

        # Save current state
        current_scroll = self.table.verticalScrollBar().value()
        selected_pids = self.get_selected_pids()

        # Filter data
        filtered_data = self.filter_data(processes)

        # Disable sorting during update to prevent jumping
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(filtered_data))
        
        # Update Status bar with rich information
        cpu_usage = psutil.cpu_percent()
        mem_usage = psutil.virtual_memory().percent
        status_text = f"✅ System Status: Active | Global CPU: {cpu_usage}% | Global RAM: {mem_usage}% | Showing {len(filtered_data)} of {len(processes)} Processes"
        self.status_label.setText(status_text)

        for row_idx, p in enumerate(filtered_data):
            self.set_row_data(row_idx, p)

        # Restore State
        self.table.setSortingEnabled(True)
        self.table.verticalScrollBar().setValue(current_scroll)
        if selected_pids:
            self.select_rows_by_pids(selected_pids)

    def set_row_data(self, row, p):
        """Populates a single row in the table."""
        # 0: Checkbox
        chk_item = self.table.item(row, 0)
        if not chk_item:
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, chk_item)
        
        chk_item.setData(Qt.ItemDataRole.UserRole, p['pid'])

        # Helper to update text items efficiently
        def update_item(col, text, color=None, bold=False):
            item = self.table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, col, item)
            
            if item.text() != text:
                item.setText(text)
            
            # Update Color
            if color:
                item.setForeground(QBrush(QColor(color)))
            else:
                item.setData(Qt.ItemDataRole.ForegroundRole, None)
            
            # Update Font
            font = item.font()
            if font.bold() != bold:
                # Prevent Qt warning for uninitialized font sizes (-1)
                if font.pointSize() <= 0 and font.pixelSize() <= 0:
                    font.setPointSize(10) 
                font.setBold(bold)
                item.setFont(font)

        # Helper to update numeric items for sorting
        def update_sortable_item(col, sort_val, display_text=""):
            item = self.table.item(row, col)
            if not isinstance(item, SortableTableWidgetItem):
                item = SortableTableWidgetItem()
                self.table.setItem(row, col, item)
            item.setData(Qt.ItemDataRole.UserRole, sort_val)
            item.setData(Qt.ItemDataRole.DisplayRole, display_text)
            
            # Ensure proper font if displaying text
            if display_text:
                font = item.font()
                if font.pointSize() <= 0 and font.pixelSize() <= 0:
                    font.setPointSize(10)
                item.setFont(font)
            return item

        # 1: PID
        update_sortable_item(1, p['pid'], str(p['pid']))

        # 2: Name
        update_item(2, str(p['name']))

        # 3: Status Badge
        status_str = str(p['status']).upper()
        # Create an invisible sortable item for the status column so it can be clicked/sorted properly
        update_sortable_item(3, status_str, "")
        
        status_widget = self.table.cellWidget(row, 3)
        if not status_widget:
            status_widget = QLabel()
            status_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setCellWidget(row, 3, status_widget)
            
        if status_widget.text() != status_str:
            status_widget.setText(status_str)
            if p['status'] == 'running':
                status_widget.setStyleSheet("background-color: #27ae60; color: white; border-radius: 4px; padding: 2px 6px; font-weight: bold; font-size: 10px; margin: 4px;")
            elif p['status'] == 'stopped':
                status_widget.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 4px; padding: 2px 6px; font-weight: bold; font-size: 10px; margin: 4px;")
            else:
                status_widget.setStyleSheet("background-color: #7f8c8d; color: white; border-radius: 4px; padding: 2px 6px; font-weight: bold; font-size: 10px; margin: 4px;")

        # 4: CPU
        cpu_val = p['cpu_percent'] or 0.0
        update_sortable_item(4, cpu_val)
        cpu_bar = self.table.cellWidget(row, 4)
        if not cpu_bar:
            cpu_bar = QProgressBar()
            cpu_bar.setTextVisible(True)
            cpu_bar.setMaximum(100)
            cpu_bar.setObjectName("ProcessResourceBar")
            self.table.setCellWidget(row, 4, cpu_bar)
            
        cpu_bar.setValue(int(cpu_val))
        cpu_bar.setFormat(f"{cpu_val:.1f}%")
        
        # Colorize CPU bar if high
        if cpu_val > HIGH_CPU_THRESHOLD:
            cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
        else:
            cpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #00c6ff; }")

        # 5: Memory
        mem_val = p['memory_percent'] or 0.0
        update_sortable_item(5, mem_val)
        mem_bar = self.table.cellWidget(row, 5)
        if not mem_bar:
            mem_bar = QProgressBar()
            mem_bar.setTextVisible(True)
            mem_bar.setMaximum(100)
            mem_bar.setObjectName("ProcessResourceBar")
            self.table.setCellWidget(row, 5, mem_bar)
            
        mem_bar.setValue(int(mem_val))
        mem_bar.setFormat(f"{mem_val:.1f}%")
        
        # Colorize Mem bar if high
        if mem_val > HIGH_MEM_THRESHOLD:
            mem_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
        else:
            mem_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff5e7e; }")

        # 6: Disk Read
        disk_r = p.get('disk_read', 0)
        update_sortable_item(6, disk_r)
        update_item(6, f"{disk_r / (1024*1024):.1f} MB", color="#a29bfe")

        # 7: Disk Write
        disk_w = p.get('disk_write', 0)
        update_sortable_item(7, disk_w)
        update_item(7, f"{disk_w / (1024*1024):.1f} MB", color="#74b9ff")

        # 8: User
        user = p.get('username') or "System"
        # Clean up Windows domain prefix if present
        if "\\" in user:
            user = user.split("\\")[-1]
        update_item(8, user)

        # 9: Start Time
        try:
            t = datetime.datetime.fromtimestamp(p['create_time'])
            time_str = t.strftime("%H:%M:%S")
        except Exception:
            time_str = "-"
        update_item(9, time_str)
        
        # Suspicious Highlight Heuristic
        is_suspicious = (p.get('cpu_percent') or 0) > 85 or (p.get('memory_percent') or 0) > 85
        bg_color = QColor(231, 76, 60, 40) if is_suspicious else None
        
        for col in range(1, 10):
            item = self.table.item(row, col)
            if item:
                if bg_color:
                    item.setBackground(QBrush(bg_color))
                else:
                    item.setData(Qt.ItemDataRole.BackgroundRole, None)

    def filter_data(self, processes):
        filtered = processes
        
        # Apply Category Filter
        if hasattr(self, 'current_category'):
            if self.current_category == "System":
                filtered = [p for p in filtered if p.get('username') and (p['username'].upper() in ['SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE'])]
            elif self.current_category == "User Apps":
                filtered = [p for p in filtered if p.get('username') and (p['username'].upper() not in ['SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE', ''])]
            elif self.current_category == "Suspicious":
                filtered = [p for p in filtered if (p.get('cpu_percent') or 0) > 50 or (p.get('memory_percent') or 0) > 50]

        # Apply Text Filter
        if self.filter_text:
            search_lower = self.filter_text.lower()
            filtered = [p for p in filtered if search_lower in p.get('name', '').lower() or search_lower in str(p.get('pid', ''))]
            
        return filtered

    def set_category_filter(self, category):
        self.current_category = category
        if hasattr(self, 'process_data'):
            self.update_table(self.process_data)

    def handle_search(self, text):
        self.filter_text = text
        self.update_table(self.process_data)
        
    def on_process_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            self.details_panel.hide()
            return
            
        row = selected[0].row()
        pid_item = self.table.item(row, 1)
        if not pid_item:
            return
            
        pid = int(pid_item.text())
        self.details_panel.show()
        self.lbl_details_info.setText(f"Loading forensics for PID {pid}...")
        
        # One-off forensic pull
        try:
            proc = psutil.Process(pid)
            exe = proc.exe() or "Unknown"
            cmd = " ".join(proc.cmdline()) or "Unknown"
            threads = proc.num_threads()
            
            try:
                conns = len(proc.connections())
            except psutil.AccessDenied:
                conns = "Access Denied"
            
            details = f"<b style='color:#0078d7;'>Executable:</b><br>{exe}<br><br>"
            details += f"<b style='color:#0078d7;'>Command Line:</b><br>{cmd}<br><br>"
            details += f"<b style='color:#0078d7;'>Threads:</b> {threads}<br><br>"
            details += f"<b style='color:#0078d7;'>Network Connections:</b> {conns}<br>"
            
            self.lbl_details_info.setText(details)
        except psutil.AccessDenied:
            self.lbl_details_info.setText(f"Access Denied for PID {pid}.<br><br>Run NexaShield as Administrator to view deep forensics.")
        except psutil.NoSuchProcess:
            self.lbl_details_info.setText(f"Process {pid} has terminated.")
        except Exception as e:
            self.lbl_details_info.setText(f"Error fetching forensics: {str(e)}")

    def get_selected_pids(self):
        pids = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                pids.append(item.data(Qt.ItemDataRole.UserRole))
        return pids

    def select_rows_by_pids(self, pids):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) in pids:
                item.setCheckState(Qt.CheckState.Checked)

    def kill_process(self):
        pids = self.get_selected_pids()
        if not pids:
            QMessageBox.warning(self, "No Selection", "Please select process(es) to terminate.")
            return

        count = len(pids)
        reply = QMessageBox.question(
            self, "Confirm Kill", 
            f"Are you sure you want to terminate {count} process(es)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            errors = []
            for pid in pids:
                if pid in [0, 4]: continue
                try:
                    p = psutil.Process(pid)
                    p_name = p.name()
                    p.terminate()
                    DatabaseManager().log_siem_event("Process Monitor", f"Terminated process '{p_name}' (PID: {pid})", "Warning")
                except psutil.AccessDenied:
                    errors.append(f"PID {pid}: Access Denied")
                except Exception as e:
                    errors.append(f"PID {pid}: {str(e)}")
            
            if errors:
                QMessageBox.warning(self, "Partial Errors", "\n".join(errors[:5]))
            else:
                QMessageBox.information(self, "Success", "Selected processes terminated.")
            self.refresh_data()

    def change_process_state(self, action):
        pids = self.get_selected_pids()
        if not pids:
            return

        count = 0
        for pid in pids:
            try:
                p = psutil.Process(pid)
                if action == "suspend":
                    p.suspend()
                elif action == "resume":
                    p.resume()
                count += 1
            except Exception:
                pass
        
        self.status_label.setText(f"{action.capitalize()}ed {count} processes.")
        self.refresh_data()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Processes", "processes.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["PID", "Name", "Status", "CPU%", "Mem%", "User", "Created"])
                    for p in self.process_data:
                        writer.writerow([
                            p['pid'], p['name'], p['status'], 
                            p['cpu_percent'], p['memory_percent'], 
                            p['username'], p['create_time']
                        ])
                QMessageBox.information(self, "Export", "Process list exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Processes", "processes.pdf", "PDF Files (*.pdf)")
        if not path:
            return
            
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            
            # Build HTML Table
            html = """
            <html>
            <head>
                <style>
                    h1 { text-align: center; font-family: Arial, sans-serif; }
                    table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10pt; }
                    th, td { border: 1px solid #333; padding: 4px; text-align: left; }
                    th { background-color: #f2f2f2; font-weight: bold; }
                </style>
            </head>
            <body>
                <h1>System Processes Report</h1>
                <p>Generated: %s</p>
                <table>
                    <thead>
                        <tr>
                            <th>PID</th><th>Name</th><th>Status</th><th>CPU%</th><th>Mem%</th><th>User</th><th>Start Time</th>
                        </tr>
                    </thead>
                    <tbody>
            """ % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for p in self.process_data:
                try:
                    t = datetime.datetime.fromtimestamp(p['create_time'])
                    time_str = t.strftime("%H:%M:%S")
                except:
                    time_str = "-"
                
                user = p.get('username') or "System"
                if "\\" in user:
                    user = user.split("\\")[-1]

                html += f"<tr><td>{p['pid']}</td><td>{p['name']}</td><td>{p['status']}</td>" \
                        f"<td>{p['cpu_percent']:.1f}</td><td>{p['memory_percent']:.1f}</td>" \
                        f"<td>{user}</td><td>{time_str}</td></tr>"

            html += "</tbody></table></body></html>"
            
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print(printer)
            QMessageBox.information(self, "Export", "PDF exported successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
