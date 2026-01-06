import psutil
import datetime
import csv
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMessageBox, QFileDialog,
    QAbstractItemView, QFrame, QProgressBar, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QAction, QPainter, QPainterPath, QLinearGradient, QPen, QTextDocument
from PyQt6.QtPrintSupport import QPrinter

# --- Constants ---
REFRESH_INTERVAL = 3000  # 3 seconds
HIGH_CPU_THRESHOLD = 80.0
HIGH_MEM_THRESHOLD = 80.0

class ProcessWorker(QThread):
    """
    Background thread to fetch system processes.
    Prevents UI freezing during data collection.
    """
    data_fetched = pyqtSignal(list)

    def run(self):
        processes = []
        # Fetch specific attributes to optimize performance
        attrs = ['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'username', 'create_time']
        
        for proc in psutil.process_iter(attrs):
            try:
                # process_iter yields a Process object, .info returns a dict
                pinfo = proc.info
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        self.data_fetched.emit(processes)

class ResourceChart(QWidget):
    """Custom widget to draw live resource usage charts."""
    def __init__(self, title, line_color="#0078d7"):
        super().__init__()
        self.title = title
        self.line_color = QColor(line_color)
        self.data = deque([0]*60, maxlen=60) # 60 data points
        self.setMinimumHeight(120)
        self.current_value = 0.0

    def update_value(self, value):
        self.current_value = value
        self.data.append(value)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#2b2b2b"))
        
        # Title & Value
        painter.setPen(QColor("white"))
        painter.drawText(10, 20, f"{self.title}: {self.current_value:.1f}%")
        
        if not self.data:
            return
            
        path = QPainterPath()
        # Calculate x step based on maxlen to ensure consistent width
        step_x = w / (self.data.maxlen - 1)
        
        # Start point (y is inverted)
        path.moveTo(0, h - (self.data[0] / 100.0 * h))
        
        for i, val in enumerate(self.data):
            x = i * step_x
            y = h - (val / 100.0 * h)
            path.lineTo(x, y)
            
        # Draw Line
        painter.setPen(QPen(self.line_color, 2))
        painter.drawPath(path)
        
        # Fill Gradient
        path.lineTo(w, h)
        path.lineTo(0, h)
        path.closeSubpath()
        
        grad = QLinearGradient(0, 0, 0, h)
        c = self.line_color
        grad.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 100))
        grad.setColorAt(1, QColor(c.red(), c.green(), c.blue(), 0))
        
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)

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
        self.timer.start(REFRESH_INTERVAL)
        
        # Initial load
        self.refresh_data()
        
        # Chart Timer (1 second updates)
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self.update_charts)
        self.chart_timer.start(1000)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Top Control Bar ---
        control_bar = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Process Name or PID...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.handle_search)
        control_bar.addWidget(self.search_input)

        self.btn_clear_search = QPushButton("✕")
        self.btn_clear_search.setFixedWidth(30)
        self.btn_clear_search.clicked.connect(self.clear_search)
        control_bar.addWidget(self.btn_clear_search)

        self.chk_select_all = QCheckBox("✅ Select All")
        self.chk_select_all.stateChanged.connect(self.toggle_select_all)
        control_bar.addWidget(self.chk_select_all)

        control_bar.addStretch()

        # Action Buttons
        self.btn_suspend = QPushButton("⏸️ Suspend")
        self.btn_suspend.clicked.connect(lambda: self.change_process_state("suspend"))
        control_bar.addWidget(self.btn_suspend)

        self.btn_resume = QPushButton("▶️ Resume")
        self.btn_resume.clicked.connect(lambda: self.change_process_state("resume"))
        control_bar.addWidget(self.btn_resume)

        self.btn_kill = QPushButton("💀 End Task")
        self.btn_kill.setObjectName("DangerButton") # For red styling in QSS
        self.btn_kill.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        self.btn_kill.clicked.connect(self.kill_process)
        control_bar.addWidget(self.btn_kill)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_data)
        control_bar.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("📄 Export CSV")
        self.btn_export.clicked.connect(self.export_csv)
        control_bar.addWidget(self.btn_export)

        self.btn_export_pdf = QPushButton("📑 Export PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        control_bar.addWidget(self.btn_export_pdf)

        layout.addLayout(control_bar)

        # --- Content Area (Split 2:1) ---
        content_layout = QHBoxLayout()

        # --- Process Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "", "🆔 PID", "⚙️ Name", "🚦 Status", "🧠 CPU %", "💾 Mem %", "👤 User", "⏱️ Start Time"
        ])
        
        # Table Styling & Behavior
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        
        # Header sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 30)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # PID
        
        content_layout.addWidget(self.table, 2) # Stretch 2

        # --- Resource Charts ---
        self.charts_panel = QWidget()
        charts_layout = QVBoxLayout(self.charts_panel)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cpu_chart = ResourceChart("🧠 CPU Usage", "#dc3545")
        self.mem_chart = ResourceChart("💾 RAM Usage", "#ffc107")
        charts_layout.addWidget(self.cpu_chart)
        charts_layout.addWidget(self.mem_chart)
        
        content_layout.addWidget(self.charts_panel, 1) # Stretch 1
        layout.addLayout(content_layout)

        # Status Bar / Footer
        self.status_label = QLabel("✅ Ready")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

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
        self.status_label.setText(f"Total Processes: {len(processes)}")

        # Save current state
        current_scroll = self.table.verticalScrollBar().value()
        selected_pids = self.get_selected_pids()

        # Filter data
        filtered_data = self.filter_data(processes)

        # Disable sorting during update to prevent jumping
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(filtered_data))

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
                font.setBold(bold)
                item.setFont(font)

        # 1: PID
        update_item(1, str(p['pid']))

        # 2: Name
        update_item(2, str(p['name']))

        # 3: Status
        status_color = None
        if p['status'] == 'running':
            status_color = "#28a745" # Green
        elif p['status'] == 'stopped':
            status_color = "#dc3545" # Red
        update_item(3, str(p['status']), color=status_color)

        # 4: CPU
        cpu_val = p['cpu_percent'] or 0.0
        cpu_color = "#dc3545" if cpu_val > HIGH_CPU_THRESHOLD else None
        update_item(4, f"{cpu_val:.1f}%", color=cpu_color, bold=(cpu_val > HIGH_CPU_THRESHOLD))

        # 5: Memory
        mem_val = p['memory_percent'] or 0.0
        mem_color = "#ffc107" if mem_val > HIGH_MEM_THRESHOLD else None
        update_item(5, f"{mem_val:.1f}%", color=mem_color)

        # 6: User
        user = p['username'] or "System"
        # Clean up Windows domain prefix if present
        if "\\" in user:
            user = user.split("\\")[-1]
        update_item(6, user)

        # 7: Start Time
        try:
            t = datetime.datetime.fromtimestamp(p['create_time'])
            time_str = t.strftime("%H:%M:%S")
        except Exception:
            time_str = "-"
        update_item(7, time_str)

    def filter_data(self, processes):
        if not self.filter_text:
            return processes
        
        filtered = []
        search_lower = self.filter_text.lower()
        for p in processes:
            # Search by Name or PID
            if search_lower in p['name'].lower() or search_lower in str(p['pid']):
                filtered.append(p)
        return filtered

    def handle_search(self, text):
        self.filter_text = text
        # Trigger immediate update using cached data
        self.update_table(self.process_data)

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
                    p.terminate()
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

    def get_bold_font(self):
        f = self.font()
        f.setBold(True)
        return f
