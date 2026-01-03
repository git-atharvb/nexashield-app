import os
import sys
import time
import psutil
import datetime
import subprocess
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QCheckBox, QFileDialog, QMessageBox, QSizePolicy, 
    QAbstractItemView, QApplication, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QBuffer, QIODevice, QByteArray
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QPen, QFont, QTextDocument, QBrush
from PyQt6.QtPrintSupport import QPrinter

# --- Custom UI Components ---

class ModernChart(QWidget):
    """Draws a live line chart with a modern gradient look."""
    def __init__(self, title, color="#0078d7", max_value=100.0, auto_scale=False, suffix="%"):
        super().__init__()
        self.title = title
        self.line_color = QColor(color)
        self.data = deque([0]*60, maxlen=60)
        self.setMinimumHeight(160)
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

        # Background (Transparent/Handled by parent Card)
        
        # Title & Value
        painter.setPen(QColor("#e0e0e0"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(10, 20, f"{self.title}")
        
        painter.setPen(self.line_color)
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
        painter.setPen(QPen(self.line_color, 2))
        painter.drawPath(path)

        # Fill Gradient
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()
        grad = QLinearGradient(0, top_pad, 0, h)
        c = self.line_color
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
        self.bg_color = QColor("#3e3e42")
        self.percent = 0.0
        self.setMinimumSize(120, 120)

    def update_value(self, percent):
        self.percent = percent
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        size = min(w, h) - 10
        rect = QRectF((w - size)/2, (h - size)/2 + 10, size, size)

        # Title
        painter.setPen(QColor("#cccccc"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(0, 0, w, 20), Qt.AlignmentFlag.AlignCenter, self.title)

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
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.percent:.1f}%")

class MetricCard(QFrame):
    """A styled card displaying a single metric."""
    def __init__(self, title, value="-", color="#0078d7"):
        super().__init__()
        self.setObjectName("MetricCard")
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background-color: #252526;
                border-radius: 8px;
                border: 1px solid #3e3e42;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #aaaaaa; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.lbl_title)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(self.lbl_value)
        
    def set_value(self, value):
        self.lbl_value.setText(value)

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

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        self._setup_header()
        self._setup_dashboard()

        # --- Timer ---
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(2000) # 2 seconds
        self.refresh_timer.timeout.connect(self.update_all_stats)
        self.refresh_timer.start()
        
        self.update_all_stats()

    def _setup_header(self):
        header = QHBoxLayout()
        
        title = QLabel("System Resources")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.update_all_stats)
        
        self.btn_export = QPushButton("Export PDF")
        self.btn_export.clicked.connect(self.export_pdf)
        
        self.chk_auto = QCheckBox("Auto-Refresh")
        self.chk_auto.setChecked(True)
        self.chk_auto.stateChanged.connect(self._toggle_auto)
        
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_export)
        header.addWidget(self.chk_auto)
        
        self.main_layout.addLayout(header)

    def _setup_dashboard(self):
        # Two Column Layout
        content = QHBoxLayout()
        
        # --- Left Column: Memory ---
        mem_card = QFrame()
        mem_card.setObjectName("Card")
        mem_card.setStyleSheet("#Card { background-color: #1e1e1e; border-radius: 10px; border: 1px solid #333; }")
        mem_layout = QVBoxLayout(mem_card)
        mem_layout.setSpacing(15)
        
        mem_layout.addWidget(QLabel("Memory Performance"))
        
        # Charts
        self.chart_ram_hist = ModernChart("RAM History", "#0078d7")
        mem_layout.addWidget(self.chart_ram_hist)
        
        donuts = QHBoxLayout()
        self.donut_ram = DonutChart("RAM Load", "#0078d7")
        self.donut_swap = DonutChart("Swap Load", "#ffc107")
        donuts.addWidget(self.donut_ram)
        donuts.addWidget(self.donut_swap)
        mem_layout.addLayout(donuts)
        
        # Metrics Grid
        metrics = QGridLayout()
        self.card_total = MetricCard("Total RAM", color="#ffffff")
        self.card_used = MetricCard("Used RAM", color="#0078d7")
        self.card_avail = MetricCard("Available", color="#28a745")
        self.card_swap = MetricCard("Swap Used", color="#ffc107")
        
        metrics.addWidget(self.card_total, 0, 0)
        metrics.addWidget(self.card_used, 0, 1)
        metrics.addWidget(self.card_avail, 1, 0)
        metrics.addWidget(self.card_swap, 1, 1)
        mem_layout.addLayout(metrics)
        
        mem_layout.addStretch()
        content.addWidget(mem_card, 4)

        # --- Right Column: Storage ---
        store_card = QFrame()
        store_card.setObjectName("Card")
        store_card.setStyleSheet("#Card { background-color: #1e1e1e; border-radius: 10px; border: 1px solid #333; }")
        store_layout = QVBoxLayout(store_card)
        store_layout.setSpacing(15)
        
        store_layout.addWidget(QLabel("Storage Health & Activity"))
        
        # I/O Charts
        io_charts = QHBoxLayout()
        self.chart_read = ModernChart("Read Speed", "#28a745", max_value=1024*1024, auto_scale=True, suffix="B")
        self.chart_write = ModernChart("Write Speed", "#dc3545", max_value=1024*1024, auto_scale=True, suffix="B")
        io_charts.addWidget(self.chart_read)
        io_charts.addWidget(self.chart_write)
        store_layout.addLayout(io_charts)
        
        # Table
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(6)
        self.disk_table.setHorizontalHeaderLabels(["Drive", "Total", "Free", "Health", "FS", "Usage"])
        self.disk_table.verticalHeader().setVisible(False)
        self.disk_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.disk_table.setAlternatingRowColors(True)
        self.disk_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.disk_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.disk_table.setStyleSheet("QTableWidget { background-color: #252526; border: none; } QHeaderView::section { background-color: #333; color: white; }")
        store_layout.addWidget(self.disk_table)
        
        # Actions
        actions = QHBoxLayout()
        self.btn_clean = QPushButton("🧹 Clean Temp Files")
        self.btn_clean.setStyleSheet("background-color: #dc3545; color: white; padding: 8px; border-radius: 4px;")
        self.btn_clean.clicked.connect(self.clean_temp_files)
        actions.addStretch()
        actions.addWidget(self.btn_clean)
        store_layout.addLayout(actions)
        
        content.addWidget(store_card, 6)
        self.main_layout.addLayout(content)

    # --- Logic ---

    def update_all_stats(self):
        self._update_memory()
        self._update_storage()

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
        try:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
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
        
        self.btn_clean.setText("🧹 Clean Temp Files")
        QMessageBox.information(self, "Done", f"Deleted {count} files.\nFreed {self._fmt(freed)}.")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", "SystemReport.pdf", "PDF (*.pdf)")
        if not path: return
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        
        # Capture Charts
        def grab(w):
            b = QBuffer()
            b.open(QIODevice.OpenModeFlag.WriteOnly)
            w.grab().save(b, "PNG")
            return b.data().toBase64().data().decode()
            
        img_ram = grab(self.chart_ram_hist)
        img_read = grab(self.chart_read)
        img_write = grab(self.chart_write)
        
        html = f"""
        <h1>System Resource Report</h1>
        <p>Generated: {datetime.datetime.now()}</p>
        <h2>Memory</h2>
        <img src="data:image/png;base64,{img_ram}" width="500">
        <p>Total RAM: {self.card_total.lbl_value.text()} | Used: {self.card_used.lbl_value.text()}</p>
        <h2>Storage I/O</h2>
        <img src="data:image/png;base64,{img_read}" width="400"><br><br>
        <img src="data:image/png;base64,{img_write}" width="400">
        """
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print(printer)
        QMessageBox.information(self, "Success", "Report exported.")

    def _toggle_auto(self, state):
        if state: self.refresh_timer.start()
        else: self.refresh_timer.stop()

    @staticmethod
    def _fmt(n):
        for u in ["B", "KB", "MB", "GB", "TB"]:
            if n < 1024: return f"{n:.2f} {u}"
            n /= 1024
        return f"{n:.2f} PB"
