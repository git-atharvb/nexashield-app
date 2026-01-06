import os
import sys
import time
import psutil
import datetime
import subprocess
import platform
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QCheckBox, QFileDialog, QMessageBox, QSizePolicy, 
    QAbstractItemView, QApplication, QGroupBox, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QBuffer, QIODevice, QByteArray, QSize
from PyQt6.QtGui import (
    QColor, QPainter, QPainterPath, QLinearGradient, QPen, QFont, 
    QTextDocument, QBrush, QPalette, QIcon
)
from PyQt6.QtPrintSupport import QPrinter

# --- Custom UI Components ---

class ModernChart(QWidget):
    """Draws a live line chart with a modern gradient look."""
    def __init__(self, title, color="#0078d7", max_value=100.0, auto_scale=False, suffix="%"):
        super().__init__()
        self.title = title
        self.base_color = color
        self.data = deque([0]*60, maxlen=60)
        self.setMinimumHeight(120)
        self.current_value = 0.0
        self.max_value = max_value
        self.auto_scale = auto_scale
        self.suffix = suffix

    def update_value(self, value):
        self.current_value = value
        self.data.append(value)
        
        if self.auto_scale:
            local_max = max(self.data) if self.data else 1.0
            if local_max > self.max_value:
                self.max_value = local_max
            elif local_max < self.max_value * 0.5 and self.max_value > 100:
                self.max_value = max(100.0, self.max_value * 0.95)
        self.update()

    def _format_val(self, val):
        if self.suffix == "%":
            return f"{val:.1f}%"
        # Byte formatting
        n = val
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(n) < 1024.0:
                return f"{n:.1f} {unit}/s"
            n /= 1024.0
        return f"{n:.1f} TB/s"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Dynamic Colors
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        line_color = QColor(self.base_color)

        # Background (Transparent/Handled by parent Card)
        
        # Title & Value
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(10, 20, f"{self.title}")
        
        painter.setPen(line_color)
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(w - 100, 20, 90, 20, Qt.AlignmentFlag.AlignRight, self._format_val(self.current_value))

        if not self.data: return

        # Draw Graph
        path = QPainterPath()
        step_x = w / (self.data.maxlen - 1)
        scale = max(self.max_value, 1.0)
        
        # Chart area padding
        top_pad = 30
        chart_h = h - top_pad
        
        path.moveTo(0, h - (self.data[0] / scale * chart_h))
        
        for i, val in enumerate(self.data):
            x = i * step_x
            y = h - (val / scale * chart_h)
            path.lineTo(x, y)

        # Stroke
        painter.setPen(QPen(line_color, 2))
        painter.drawPath(path)

        # Fill Gradient
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()
        grad = QLinearGradient(0, top_pad, 0, h)
        c = line_color
        grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 80))
        grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

class DonutChart(QWidget):
    """Draws a donut chart for percentage visualization."""
    def __init__(self, title, color="#28a745"):
        super().__init__()
        self.title = title
        self.primary_color = QColor(color)
        self.bg_color = QColor(0, 0, 0, 50) # Semi-transparent black
        self.percent = 0.0
        self.setMinimumSize(140, 140)

    def update_value(self, percent):
        self.percent = percent
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Layout calculations to prevent overlap
        header_h = 25
        size = min(w, h - header_h) - 10
        rect = QRectF((w - size)/2, header_h + 5, size, size)

        # Title
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(0, 0, w, header_h), Qt.AlignmentFlag.AlignCenter, self.title)

        # Background Circle
        pen = QPen(self.bg_color, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Value Arc
        pen.setColor(self.primary_color)
        painter.setPen(pen)
        span = int(-self.percent * 3.6 * 16)
        painter.drawArc(rect, 90 * 16, span)

        # Text in center
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.percent:.1f}%")

class DiskPartitionPieChart(QWidget):
    """Pie chart to visualize disk partition division."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 150)
        self.partitions = [] # List of (name, value, color)
        self.colors = [
            QColor("#0078d7"), QColor("#28a745"), QColor("#ffc107"), 
            QColor("#dc3545"), QColor("#6f42c1"), QColor("#17a2b8")
        ]

    def update_data(self, partition_data):
        # partition_data: list of (name, size_bytes)
        self.partitions = []
        total = sum(p[1] for p in partition_data)
        if total == 0: return
        
        for i, (name, size) in enumerate(partition_data):
            color = self.colors[i % len(self.colors)]
            self.partitions.append((name, size, color))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Title
        painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, w, 20), Qt.AlignmentFlag.AlignLeft, "Disk Division (Total Size)")

        if not self.partitions:
            return

        # Pie Area
        size = min(w, h - 40) - 10
        rect = QRectF((w - size) / 2, 25, size, size)
        
        total = sum(p[1] for p in self.partitions)
        start_angle = 90 * 16
        
        for name, val, color in self.partitions:
            span = int((val / total) * 360 * 16)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect, start_angle, span)
            start_angle += span

        # Legend (Simple text at bottom)
        legend_y = h - 10
        painter.setFont(QFont("Segoe UI", 8))
        
        # Draw legend items horizontally
        x_cursor = 10
        for name, val, color in self.partitions:
            painter.setBrush(color)
            painter.drawEllipse(x_cursor, legend_y - 8, 8, 8)
            
            painter.setPen(self.palette().color(QPalette.ColorRole.WindowText))
            text = f"{name}"
            painter.drawText(x_cursor + 12, legend_y, text)
            
            fm = painter.fontMetrics()
            x_cursor += 12 + fm.horizontalAdvance(text) + 10
            if x_cursor > w - 20: break # Stop if overflow

class MetricCard(QFrame):
    """A styled card displaying a single metric."""
    def __init__(self, title, value="-", color="#0078d7"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame { 
                border-radius: 8px; 
                border: 1px solid rgba(128, 128, 128, 50);
                background-color: rgba(0, 0, 0, 20);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; opacity: 0.7; border: none; background: transparent;")
        layout.addWidget(self.lbl_title)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(self.lbl_value)
        
    def set_value(self, value):
        self.lbl_value.setText(value)

class InfoCard(QFrame):
    """A styled card for system information text."""
    def __init__(self, title, value, icon="ℹ️"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        header = QHBoxLayout()
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 14px; border: none; background: transparent;")
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #aaa; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        
        header.addWidget(lbl_icon)
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color: white; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        self.lbl_value.setWordWrap(True)
        layout.addWidget(self.lbl_value)

    def set_value(self, value):
        self.lbl_value.setText(value)

class DataFlowDiagram(QWidget):
    """Visual representation of system resource flow."""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(140)
        self.cpu_val = 0
        self.ram_val = 0
        self.swap_val = 0
        self.disk_active = False

    def update_values(self, cpu, ram, swap, disk_active):
        self.cpu_val = cpu
        self.ram_val = ram
        self.swap_val = swap
        self.disk_active = disk_active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        text_col = self.palette().color(QPalette.ColorRole.WindowText)
        
        # Colors
        col_cpu = QColor("#0078d7")
        col_ram = QColor("#28a745")
        col_disk = QColor("#dc3545") if self.disk_active else QColor("#666")
        
        # Draw Nodes (Circles)
        y_mid = h / 2
        r = 30
        
        def draw_node(x, label, val, color):
            rect = QRectF(x - r, y_mid - r, 2*r, 2*r)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            
            painter.setPen(QColor("white")) # Text inside node always white
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{val}%")
            
            painter.setPen(text_col)
            painter.drawText(int(x - r), int(y_mid + r + 15), int(2*r), 20, Qt.AlignmentFlag.AlignCenter, label)

        # Positions
        x_cpu = w * 0.2
        x_ram = w * 0.5
        x_disk = w * 0.8
        
        # Draw Connections
        painter.setPen(QPen(text_col, 2, Qt.PenStyle.DashLine))
        painter.drawLine(int(x_cpu + r), int(y_mid), int(x_ram - r), int(y_mid))
        painter.drawLine(int(x_ram + r), int(y_mid), int(x_disk - r), int(y_mid))
        
        draw_node(x_cpu, "CPU", int(self.cpu_val), col_cpu)
        draw_node(x_ram, "RAM", int(self.ram_val), col_ram)
        draw_node(x_disk, "Swap/Disk", int(self.swap_val), col_disk)

class MemoryMonitorWidget(QWidget):
    """
    Redesigned Memory & Storage Dashboard.
    Features: Real-time charts, S.M.A.R.T health, Temp Cleanup, PDF Export.
    """
    HIGH_RAM_THRESHOLD = 90.0
    HIGH_DISK_THRESHOLD = 95.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MemoryMonitorWidget")

        # --- Data State ---
        self.smart_cache = {}
        self.smart_last_check = 0
        self.alerted_drives = set()
        self.prev_disk_io = psutil.disk_io_counters()
        self.last_io_time = time.time()
        self.boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())

        # --- Main Layout ---
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(20)

        self._setup_ui()

        # --- Timer ---
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(2000) # 2 seconds
        self.refresh_timer.timeout.connect(self.update_all_stats)
        self.refresh_timer.start()
        
        self.update_all_stats()

    def _setup_ui(self):
        # --- Left Column: Visuals & Statistics ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. System Flow Diagram
        grp_flow = QGroupBox("System Resource Flow")
        l_flow = QVBoxLayout(grp_flow)
        self.flow_diagram = DataFlowDiagram()
        l_flow.addWidget(self.flow_diagram)
        left_layout.addWidget(grp_flow)

        # 2. Memory Composition (Donuts)
        grp_mem_vis = QGroupBox("Memory Composition")
        l_mem_vis = QHBoxLayout(grp_mem_vis)
        self.donut_ram = DonutChart("RAM Usage", "#0078d7")
        self.donut_swap = DonutChart("Swap Usage", "#ffc107")
        l_mem_vis.addWidget(self.donut_ram)
        l_mem_vis.addWidget(self.donut_swap)
        left_layout.addWidget(grp_mem_vis)

        # 3. Key Metrics Grid
        grp_metrics = QGroupBox("Key Statistics")
        l_metrics = QGridLayout(grp_metrics)
        self.card_total = MetricCard("Total RAM", color="#888888") # Neutral color
        self.card_used = MetricCard("Used RAM", color="#0078d7")
        self.card_avail = MetricCard("Available", color="#28a745")
        self.card_swap = MetricCard("Swap Used", color="#ffc107")
        l_metrics.addWidget(self.card_total, 0, 0)
        l_metrics.addWidget(self.card_used, 0, 1)
        l_metrics.addWidget(self.card_avail, 1, 0)
        l_metrics.addWidget(self.card_swap, 1, 1)
        left_layout.addWidget(grp_metrics)

        # 4. Historical Charts
        # Use TabWidget to save space and avoid scrolling
        self.chart_tabs = QTabWidget()
        self.chart_ram_hist = ModernChart("RAM History", "#0078d7")
        self.chart_read = ModernChart("Read Speed", "#28a745", max_value=1024*1024, auto_scale=True, suffix="B")
        self.chart_write = ModernChart("Write Speed", "#dc3545", max_value=1024*1024, auto_scale=True, suffix="B")
        
        self.chart_tabs.addTab(self.chart_ram_hist, "RAM")
        self.chart_tabs.addTab(self.chart_read, "Disk Read")
        self.chart_tabs.addTab(self.chart_write, "Disk Write")
        left_layout.addWidget(self.chart_tabs)

        left_layout.addStretch()

        # --- Right Column: Tables, Info & Operations ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Operations Toolbar
        grp_ops = QGroupBox("Operations")
        l_ops = QHBoxLayout(grp_ops)
        l_ops.setSpacing(10)
        
        btn_style = """
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setStyleSheet(btn_style + "background-color: #0078d7; color: white;")
        self.btn_refresh.clicked.connect(self.update_all_stats)
        
        self.btn_clean = QPushButton("Clean Temp")
        self.btn_clean.setStyleSheet(btn_style + "background-color: #dc3545; color: white;")
        self.btn_clean.clicked.connect(self.clean_temp_files)
        
        self.btn_export = QPushButton("Export PDF")
        self.btn_export.setStyleSheet(btn_style + "background-color: #fd7e14; color: white;")
        self.btn_export.clicked.connect(self.export_pdf)
        
        self.chk_auto = QCheckBox("Auto-Refresh")
        self.chk_auto.setChecked(True)
        self.chk_auto.stateChanged.connect(self._toggle_auto)

        l_ops.addWidget(self.btn_refresh)
        l_ops.addWidget(self.btn_clean)
        l_ops.addWidget(self.btn_export)
        l_ops.addWidget(self.chk_auto)
        right_layout.addWidget(grp_ops)

        # 2. System Info
        grp_sys = QGroupBox("Memory Information")
        l_sys = QGridLayout(grp_sys)
        l_sys.setSpacing(10)
        
        self.info_uptime = InfoCard("Uptime", "-", "⏱️")
        self.info_os = InfoCard("OS", sys.platform, "💻")
        self.info_cpu = InfoCard("CPU Cores", str(psutil.cpu_count(logical=True)), "🧠")
        self.info_host = InfoCard("Hostname", platform.node(), "🏠")
        self.info_kernel = InfoCard("Kernel", platform.release(), "⚙️")
        self.info_arch = InfoCard("Architecture", platform.machine(), "🏗️")
        self.info_proc = InfoCard("Processor", platform.processor(), "⚡")
        self.info_mem = InfoCard("Total Memory", "-", "💾")
        self.info_swap = InfoCard("Total Swap", "-", "🔄")
        
        l_sys.addWidget(self.info_uptime, 0, 0)
        l_sys.addWidget(self.info_os, 0, 1)
        l_sys.addWidget(self.info_cpu, 0, 2)
        l_sys.addWidget(self.info_host, 1, 0)
        l_sys.addWidget(self.info_kernel, 1, 1)
        l_sys.addWidget(self.info_arch, 1, 2)
        l_sys.addWidget(self.info_proc, 2, 0, 1, 3) # Span 3 cols
        l_sys.addWidget(self.info_mem, 3, 0)
        l_sys.addWidget(self.info_swap, 3, 1)
        
        right_layout.addWidget(grp_sys)

        # 4. Storage Partitions
        grp_disk = QGroupBox("Storage Partitions")
        l_disk = QHBoxLayout(grp_disk)
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(6)
        self.disk_table.setHorizontalHeaderLabels(["Drive", "Total", "Free", "Health", "FS", "Usage"])
        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.disk_table.setAlternatingRowColors(True)
        l_disk.addWidget(self.disk_table, 2)
        
        self.disk_chart = DiskPartitionPieChart()
        l_disk.addWidget(self.disk_chart, 1)
        
        right_layout.addWidget(grp_disk, 1)

        # 5. Top Processes
        grp_proc = QGroupBox("Top Memory Consumers")
        l_proc = QVBoxLayout(grp_proc)
        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(3)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Name", "Memory"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setAlternatingRowColors(True)
        self.proc_table.setMinimumHeight(120)
        l_proc.addWidget(self.proc_table)
        right_layout.addWidget(grp_proc, 1)

        # Add columns to main layout
        self.main_layout.addWidget(left_container, 4)
        self.main_layout.addWidget(right_container, 6)

    # --- Logic ---

    def update_all_stats(self):
        self._update_memory()
        self._update_storage()
        self._update_system_info()
        self._update_top_processes()

    def _update_system_info(self):
        uptime = datetime.datetime.now() - self.boot_time
        self.info_uptime.set_value(str(uptime).split('.')[0])
        
        # Update Flow Diagram
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        swap = psutil.swap_memory().percent
        disk_active = (self.chart_read.current_value > 0 or self.chart_write.current_value > 0)
        self.flow_diagram.update_values(cpu, ram, swap, disk_active)
        
        # Update totals
        self.info_mem.set_value(self._fmt(psutil.virtual_memory().total))
        self.info_swap.set_value(self._fmt(psutil.swap_memory().total))

    def _update_memory(self):
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            self.chart_ram_hist.update_value(mem.percent)
            self.donut_ram.update_value(mem.percent)
            self.donut_swap.update_value(swap.percent)
            
            self.card_total.set_value(self._fmt(mem.total))
            self.card_used.set_value(self._fmt(mem.used))
            self.card_avail.set_value(self._fmt(mem.available))
            self.card_swap.set_value(self._fmt(swap.used))
                
        except Exception:
            pass

    def _update_storage(self):
        # 1. Disk I/O
        try:
            curr_io = psutil.disk_io_counters()
            curr_time = time.time()
            delta = curr_time - self.last_io_time
            if delta > 0 and self.prev_disk_io:
                r_speed = (curr_io.read_bytes - self.prev_disk_io.read_bytes) / delta
                w_speed = (curr_io.write_bytes - self.prev_disk_io.write_bytes) / delta
                self.chart_read.update_value(r_speed)
                self.chart_write.update_value(w_speed)
            self.prev_disk_io = curr_io
            self.last_io_time = curr_time
        except: pass

        # 2. Partitions & Health
        self._refresh_smart()
        self.disk_table.setRowCount(0)
        
        partition_data = []
        
        try:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partition_data.append((part.mountpoint, usage.total))
                    
                    row = self.disk_table.rowCount()
                    self.disk_table.insertRow(row)
                    
                    self.disk_table.setItem(row, 0, QTableWidgetItem(part.mountpoint))
                    self.disk_table.setItem(row, 1, QTableWidgetItem(self._fmt(usage.total)))
                    self.disk_table.setItem(row, 2, QTableWidgetItem(self._fmt(usage.free)))
                    
                    # Health
                    health = self.smart_cache.get(part.mountpoint, "Unknown")
                    if health == "Unknown" and os.name == 'nt':
                        health = self.smart_cache.get(part.mountpoint.rstrip('\\'), "Unknown")
                    
                    h_item = QTableWidgetItem(health)
                    if health == "Good": h_item.setForeground(QBrush(QColor("#28a745")))
                    elif health in ["Warning", "Critical"]: h_item.setForeground(QBrush(QColor("#dc3545")))
                    self.disk_table.setItem(row, 3, h_item)
                    
                    self.disk_table.setItem(row, 4, QTableWidgetItem(part.fstype))
                    self.disk_table.setItem(row, 5, QTableWidgetItem(f"{usage.percent}%"))
                    
                except: continue
            
            self.disk_chart.update_data(partition_data)
                
        except: pass

    def _update_top_processes(self):
        try:
            # Get top 5 memory consumers
            procs = sorted(psutil.process_iter(['pid', 'name', 'memory_info']), 
                           key=lambda p: p.info['memory_info'].rss, reverse=True)[:5]
            
            self.proc_table.setRowCount(0)
            for p in procs:
                r = self.proc_table.rowCount()
                self.proc_table.insertRow(r)
                self.proc_table.setItem(r, 0, QTableWidgetItem(str(p.info['pid'])))
                self.proc_table.setItem(r, 1, QTableWidgetItem(p.info['name']))
                self.proc_table.setItem(r, 2, QTableWidgetItem(self._fmt(p.info['memory_info'].rss)))
        except: pass

    def _refresh_smart(self):
        if time.time() - self.smart_last_check < 60: return
        self.smart_last_check = time.time()
        
        if os.name == 'nt':
            try:
                cmd = "wmic volume get DriveLetter,Status"
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                out = subprocess.check_output(cmd, startupinfo=si, shell=False).decode()
                for line in out.splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        self.smart_cache[parts[0]] = "Good" if parts[1] == "OK" else "Warning"
            except: pass

    def clean_temp_files(self):
        temp_dir = os.environ.get('TEMP') or '/tmp'
        reply = QMessageBox.question(self, "Confirm", f"Delete temp files in {temp_dir}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        
        self.btn_clean.setText("Cleaning...")
        QApplication.processEvents()
        
        freed = 0
        count = 0
        for root, _, files in os.walk(temp_dir):
            for i, name in enumerate(files):
                if i % 50 == 0: QApplication.processEvents()
                try:
                    p = os.path.join(root, name)
                    s = os.path.getsize(p)
                    os.remove(p)
                    freed += s
                    count += 1
                except: pass
        
        self.btn_clean.setText("Clean Temp")
        QMessageBox.information(self, "Done", f"Deleted {count} files.\nFreed {self._fmt(freed)}.")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", "MemoryReport.pdf", "PDF (*.pdf)")
        if not path: return
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        
        # Helper to grab widget as base64 image
        def grab(w):
            b = QBuffer()
            b.open(QIODevice.OpenModeFlag.WriteOnly)
            w.grab().save(b, "PNG")
            return b.data().toBase64().data().decode()

        # Helper for tables
        def table_to_html(table):
            html = "<table border='1' cellspacing='0' cellpadding='4' width='100%'>"
            # Header
            html += "<thead><tr>"
            for c in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(c)
                header_text = header_item.text() if header_item else ""
                html += f"<th bgcolor='#f2f2f2'>{header_text}</th>"
            html += "</tr></thead><tbody>"
            # Rows
            for r in range(table.rowCount()):
                html += "<tr>"
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    text = item.text() if item else ""
                    html += f"<td>{text}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            return html
            
        # Capture Charts (Switch tabs to ensure they render)
        current_tab = self.chart_tabs.currentIndex()
        
        self.chart_tabs.setCurrentIndex(0)
        QApplication.processEvents()
        img_ram_hist = grab(self.chart_ram_hist)
        
        self.chart_tabs.setCurrentIndex(1)
        QApplication.processEvents()
        img_read = grab(self.chart_read)
        
        self.chart_tabs.setCurrentIndex(2)
        QApplication.processEvents()
        img_write = grab(self.chart_write)
        
        self.chart_tabs.setCurrentIndex(current_tab)

        img_flow = grab(self.flow_diagram)
        img_ram_donut = grab(self.donut_ram)
        img_swap_donut = grab(self.donut_swap)
        img_disk_pie = grab(self.disk_chart)

        # System Info Data
        sys_info = f"""
        <table width="100%" border="0">
            <tr><td><b>OS:</b> {self.info_os.lbl_value.text()}</td><td><b>Uptime:</b> {self.info_uptime.lbl_value.text()}</td></tr>
            <tr><td><b>Host:</b> {self.info_host.lbl_value.text()}</td><td><b>Kernel:</b> {self.info_kernel.lbl_value.text()}</td></tr>
            <tr><td><b>CPU:</b> {self.info_cpu.lbl_value.text()}</td><td><b>Arch:</b> {self.info_arch.lbl_value.text()}</td></tr>
            <tr><td colspan="2"><b>Processor:</b> {self.info_proc.lbl_value.text()}</td></tr>
            <tr><td><b>Total Mem:</b> {self.info_mem.lbl_value.text()}</td><td><b>Total Swap:</b> {self.info_swap.lbl_value.text()}</td></tr>
        </table>
        """

        # Key Metrics
        metrics = f"""
        <p>
        <b>Total RAM:</b> {self.card_total.lbl_value.text()} | 
        <b>Used RAM:</b> {self.card_used.lbl_value.text()} | 
        <b>Available:</b> {self.card_avail.lbl_value.text()} | 
        <b>Swap Used:</b> {self.card_swap.lbl_value.text()}
        </p>
        """
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                h1 {{ color: #0078d7; }}
                h2 {{ color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 20px; }}
                table {{ font-size: 10pt; }}
            </style>
        </head>
        <body>
            <h1 align="center">Memory Information Report</h1>
            <p align="center">Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <h2>Memory Information</h2>
            {sys_info}
            
            <h2>Resource Flow</h2>
            <div align="center"><img src="data:image/png;base64,{img_flow}" width="600"></div>
            
            <h2>Memory Statistics</h2>
            {metrics}
            <table width="100%">
                <tr>
                    <td align="center"><img src="data:image/png;base64,{img_ram_donut}" width="200"></td>
                    <td align="center"><img src="data:image/png;base64,{img_swap_donut}" width="200"></td>
                </tr>
            </table>
            <h3>RAM Usage History</h3>
            <div align="center"><img src="data:image/png;base64,{img_ram_hist}" width="600" height="150"></div>

            <h2>Storage Statistics</h2>
            <h3>Partitions</h3>
            {table_to_html(self.disk_table)}
            <br>
            <div align="center"><img src="data:image/png;base64,{img_disk_pie}" width="300"></div>
            
            <h3>Disk I/O Activity</h3>
            <table width="100%">
                <tr>
                    <td align="center"><b>Read Speed</b><br><img src="data:image/png;base64,{img_read}" width="300" height="120"></td>
                    <td align="center"><b>Write Speed</b><br><img src="data:image/png;base64,{img_write}" width="300" height="120"></td>
                </tr>
            </table>

            <h2>Top Memory Consumers</h2>
            {table_to_html(self.proc_table)}
        </body>
        </html>
        """
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(printer)
        QMessageBox.information(self, "Success", "Report exported successfully.")

    def _toggle_auto(self, state):
        if state:
            self.update_all_stats()
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    @staticmethod
    def _fmt(n):
        for u in ["B", "KB", "MB", "GB", "TB"]:
            if n < 1024: return f"{n:.2f} {u}"
            n /= 1024
        return f"{n:.2f} PB"
