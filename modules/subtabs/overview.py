import os
import psutil
import sqlite3
import socket
import platform
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QBrush, QPainter, QPen, QFont, QPalette, QPainterPath, QLinearGradient

class OverviewBarChart(QWidget):
    """Draws a real-time bar chart (histogram) for resource visualization."""
    def __init__(self, title, color="#28a745"):
        super().__init__()
        self.title = title
        self.primary_color = QColor(color)
        self.data = [0.0] * 40
        self.setMinimumHeight(160)

    def update_value(self, percent):
        self.data.pop(0)
        self.data.append(percent)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Title and Current Value
        text_color = self.palette().color(QPalette.ColorRole.WindowText)
        painter.setPen(text_color)
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(10, 25, f"{self.title}")
        
        painter.setPen(self.primary_color)
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        painter.drawText(w - 80, 25, 70, 25, Qt.AlignmentFlag.AlignRight, f"{self.data[-1]:.1f}%")

        # Grid lines
        top_pad = 40
        chart_h = h - top_pad - 10
        grid_col = QColor(128, 128, 128, 40)
        painter.setPen(QPen(grid_col, 1, Qt.PenStyle.DashLine))
        for i in range(3):
            y_line = top_pad + i * (chart_h / 2)
            painter.drawLine(10, int(y_line), w - 10, int(y_line))
            
        # Draw Bars (Histogram)
        bar_w = (w - 20) / len(self.data)
        
        for i, val in enumerate(self.data):
            if val <= 0: continue
            x = 10 + i * bar_w
            bar_h = (val / 100.0) * chart_h
            y = h - 10 - bar_h
            
            rect = QRectF(x + 1, y, max(1, bar_w - 2), bar_h)
            
            # Gradient for bar
            grad = QLinearGradient(0, y, 0, h - 10)
            c = self.primary_color
            grad.setColorAt(0, c)
            grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 30))
            
            painter.setBrush(grad)
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Draw rounded rect for the bar
            path = QPainterPath()
            path.addRoundedRect(rect, 3, 3)
            painter.drawPath(path)

class OverviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._tick_count = 0
        self.setup_ui()
        
        # Timer for real-time updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Header & Quick Status
        header_layout = QHBoxLayout()
        header = QLabel("⚡ Dashboard & Live Telemetry")
        header.setStyleSheet("font-size: 26px; font-weight: 800; color: #0078d7; letter-spacing: 1px;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # System Specs small badge
        sys_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        host_badge = QLabel(f"🖥️ {socket.gethostname()}  |  {sys_info}")
        host_badge.setStyleSheet("padding: 8px 15px; border-radius: 6px; font-weight: bold;")
        header_layout.addWidget(host_badge)
        
        layout.addLayout(header_layout)

        # 2. Histograms Row
        hist_frame = QFrame()
        hist_frame.setObjectName("CardContainer")
        hist_layout = QHBoxLayout(hist_frame)
        hist_layout.setContentsMargins(15, 15, 15, 15)
        hist_layout.setSpacing(15)
        
        self.cpu_hist = OverviewBarChart("CPU Utilization", "#0078d7")
        self.ram_hist = OverviewBarChart("Memory Usage", "#ffc107")
        self.disk_hist = OverviewBarChart("Storage I/O", "#dc3545")
        
        hist_layout.addWidget(self.cpu_hist)
        hist_layout.addWidget(self.ram_hist)
        hist_layout.addWidget(self.disk_hist)
        
        layout.addWidget(hist_frame, 2) # Give charts more vertical space

        # 3. Bottom Row: Health Modules & Recent Events
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        # Left: Device Health Checklist
        health_frame = QFrame()
        health_frame.setObjectName("CardContainer")
        health_layout = QVBoxLayout(health_frame)
        health_layout.setContentsMargins(15, 15, 15, 15)
        
        title_health = QLabel("🛡️ Protection Status")
        title_health.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        health_layout.addWidget(title_health)
        health_layout.addSpacing(10)
        
        self.lbl_cpu_stat = self.create_dynamic_status_row(health_layout, "🧠 CPU Thermals & Load")
        self.lbl_ram_stat = self.create_dynamic_status_row(health_layout, "💾 Memory Integrity")
        self.lbl_disk_stat = self.create_dynamic_status_row(health_layout, "💽 Disk Health (S.M.A.R.T)")
        self.lbl_net_stat = self.create_dynamic_status_row(health_layout, "🌐 Secure Network Tunnel")
        
        health_layout.addStretch()
        bottom_layout.addWidget(health_frame, 1)

        # Right: Security Events Table
        events_frame = QFrame()
        events_frame.setObjectName("CardContainer")
        events_layout = QVBoxLayout(events_frame)
        events_layout.setContentsMargins(15, 15, 15, 15)
        
        title_events = QLabel("🚨 Real-Time Security Feed")
        title_events.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        events_layout.addWidget(title_events)
        events_layout.addSpacing(5)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels(["🕒 Time", "🧩 Source", "📝 Description", "⚠️ Threat Level"])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alerts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.alerts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.alerts_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.alerts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.alerts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setShowGrid(False)
        self.alerts_table.setStyleSheet("border: none; background: transparent;")
        
        events_layout.addWidget(self.alerts_table)
        bottom_layout.addWidget(events_frame, 2)

        layout.addLayout(bottom_layout, 3)

    def create_dynamic_status_row(self, layout, name):
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        l = QHBoxLayout(row)
        l.setContentsMargins(0, 8, 0, 8)
        
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("background: transparent;")
        l.addWidget(lbl_name)
        l.addStretch()
        
        stat_lbl = QLabel("Checking...")
        stat_lbl.setStyleSheet("font-weight: bold; background: transparent;")
        l.addWidget(stat_lbl)
        layout.addWidget(row)
        
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #88888830;")
        layout.addWidget(sep)
        
        return stat_lbl

    def is_network_up(self):
        """Check if any primary network interface is up."""
        try:
            stats = psutil.net_if_stats()
            for name, stat in stats.items():
                if stat.isup and name != "lo" and "Loopback" not in name:
                    return True
        except Exception:
            pass
        return False

    def update_dashboard(self):
        # --- 1. Update Graphics ---
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        try:
            disk = psutil.disk_usage(os.path.abspath(os.sep)).percent
        except Exception:
            disk = 0.0
            
        self.cpu_hist.update_value(cpu)
        self.ram_hist.update_value(ram)
        self.disk_hist.update_value(disk)
        
        # --- 2. Update Statuses ---
        def set_stat(lbl, val, threshold):
            if val < threshold:
                lbl.setText("Good")
                lbl.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                lbl.setText("Warning")
                lbl.setStyleSheet("color: #dc3545; font-weight: bold;")
                
        set_stat(self.lbl_cpu_stat, cpu, 85)
        set_stat(self.lbl_ram_stat, ram, 85)
        set_stat(self.lbl_disk_stat, disk, 90)
        
        if self.is_network_up():
            self.lbl_net_stat.setText("Connected")
            self.lbl_net_stat.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.lbl_net_stat.setText("Disconnected")
            self.lbl_net_stat.setStyleSheet("color: #dc3545; font-weight: bold;")
            
        # --- 3. Update Database Events (Throttle to save Disk I/O) ---
        if self._tick_count % 3 == 0: # Every ~6 seconds
            self.update_events()
            
        self._tick_count += 1

    def update_events(self):
        events = []
        try:
            conn = sqlite3.connect("nexashield.db")
            cursor = conn.cursor()
            
            # Fetch Phishing Logs
            try:
                cursor.execute("SELECT timestamp, 'Phishing Detection', url, threat_level FROM phishing_history ORDER BY id DESC LIMIT 5")
                for row in cursor.fetchall():
                    events.append((row[0], row[1], row[2], row[3]))
            except sqlite3.Error:
                pass # Table might not exist yet
                
            # Fetch Antivirus Logs
            try:
                cursor.execute("SELECT timestamp, 'Antivirus', scan_type || ' Scan Completed', threats_found FROM scan_history ORDER BY id DESC LIMIT 5")
                for row in cursor.fetchall():
                    sev = "Critical" if row[3] > 0 else "Safe"
                    desc = f"{row[2]} - {row[3]} threat(s) found"
                    events.append((row[0], row[1], desc, sev))
            except sqlite3.Error:
                pass # Table might not exist yet
                
            conn.close()
        except Exception:
            pass
            
        # Sort merged events by timestamp and keep the top 6
        events.sort(key=lambda x: x[0], reverse=True)
        events = events[:6]
        
        self.alerts_table.setRowCount(len(events))
        for i, (time_str, mod, desc, sev) in enumerate(events):
            self.alerts_table.setItem(i, 0, QTableWidgetItem(time_str))
            self.alerts_table.setItem(i, 1, QTableWidgetItem(mod))
            self.alerts_table.setItem(i, 2, QTableWidgetItem(desc))
            
            sev_item = QTableWidgetItem(sev)
            if sev in ["High", "Critical", "High Risk"]:
                sev_item.setForeground(QBrush(QColor("#dc3545")))
            elif sev in ["Medium", "Medium Risk", "Warning"]:
                sev_item.setForeground(QBrush(QColor("#ffc107")))
            elif sev in ["Safe", "Low Risk"]:
                sev_item.setForeground(QBrush(QColor("#28a745")))
            
            self.alerts_table.setItem(i, 3, sev_item)

    # Manage timers automatically to save CPU when not visible
    def showEvent(self, event):
        super().showEvent(event)
        self.update_dashboard()
        self.timer.start(2000) # Update every 2 seconds

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()