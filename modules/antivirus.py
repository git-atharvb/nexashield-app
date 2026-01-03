import sys
import os
import hashlib
import datetime
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QTabWidget, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QBrush, QDragEnterEvent, QDropEvent
from database import DatabaseManager

# Try importing watchdog for real-time protection
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

class ScanWorker(QThread):
    """Background thread for scanning files to prevent UI freezing."""
    progress_updated = pyqtSignal(int, str) # progress %, current file
    threat_found = pyqtSignal(dict)         # threat details
    scan_finished = pyqtSignal(int, int)    # total files, threats found

    def __init__(self, paths, scan_type, db):
        super().__init__()
        self.paths = paths
        self.scan_type = scan_type
        self.db = db
        self.is_running = True
        self.total_files = 0
        self.scanned_count = 0
        self.threats = 0

    def run(self):
        # First pass: count files for progress bar
        file_list = []
        for path in self.paths:
            if os.path.isfile(path):
                file_list.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        file_list.append(os.path.join(root, file))
        
        self.total_files = len(file_list)
        
        for file_path in file_list:
            if not self.is_running:
                break
            
            self.scanned_count += 1
            progress = int((self.scanned_count / self.total_files) * 100) if self.total_files > 0 else 0
            self.progress_updated.emit(progress, file_path)
            
            threat = self.scan_file(file_path)
            if threat:
                self.threats += 1
                self.threat_found.emit(threat)
            
            # Small sleep to allow UI updates if scanning is too fast
            # time.sleep(0.001) 

        self.scan_finished.emit(self.total_files, self.threats)

    def scan_file(self, file_path):
        """Hybrid detection engine."""
        try:
            # 1. Signature Check (SHA-256)
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            file_hash = sha256_hash.hexdigest()

            sig_match = self.db.check_signature(file_hash)
            if sig_match:
                return {
                    "path": file_path,
                    "name": sig_match[0],
                    "type": sig_match[1],
                    "severity": sig_match[2],
                    "method": "Signature",
                    "time": datetime.datetime.now().strftime("%H:%M:%S")
                }

            # 2. Heuristic Analysis (Basic)
            filename = os.path.basename(file_path).lower()
            
            # Double extension check
            if filename.count('.') > 1 and filename.endswith(('.exe', '.bat', '.vbs')):
                return {
                    "path": file_path,
                    "name": "Suspicious Double Extension",
                    "type": "Suspicious",
                    "severity": "Medium",
                    "method": "Heuristic",
                    "time": datetime.datetime.now().strftime("%H:%M:%S")
                }

            # 3. AI/ML Hooks (Placeholder)
            # prediction = self.ml_model.predict(features)
            
        except (PermissionError, OSError):
            pass # Skip locked/system files
        
        return None

    def stop(self):
        self.is_running = False

if WATCHDOG_AVAILABLE:
    class RealTimeHandler(FileSystemEventHandler):
        def __init__(self, callback):
            self.callback = callback

        def on_created(self, event):
            if not event.is_directory:
                self.callback(event.src_path)

        def on_modified(self, event):
            if not event.is_directory:
                self.callback(event.src_path)

class AntivirusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setAcceptDrops(True) # Enable Drag & Drop
        self.setup_ui()
        self.observer = None
        self.scan_thread = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header ---
        header_layout = QHBoxLayout()
        title = QLabel("Smart Antivirus Engine")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.rt_status = QLabel("Real-Time: OFF")
        self.rt_status.setStyleSheet("color: #dc3545; font-weight: bold;")
        header_layout.addWidget(self.rt_status)

        self.rt_btn = QPushButton("Enable Real-Time")
        self.rt_btn.clicked.connect(self.toggle_realtime)
        if not WATCHDOG_AVAILABLE:
            self.rt_btn.setEnabled(False)
            self.rt_btn.setToolTip("Install 'watchdog' library to enable")
        header_layout.addWidget(self.rt_btn)
        
        layout.addLayout(header_layout)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.scanner_tab = QWidget()
        self.history_tab = QWidget()
        
        self.setup_scanner_tab()
        self.setup_history_tab()
        
        self.tabs.addTab(self.scanner_tab, "Scanner")
        self.tabs.addTab(self.history_tab, "Scan History")
        layout.addWidget(self.tabs)

    def setup_scanner_tab(self):
        layout = QVBoxLayout(self.scanner_tab)
        
        # Control Panel
        controls = QHBoxLayout()
        
        btn_quick = QPushButton("Quick Scan")
        btn_quick.setStyleSheet("background-color: #0078d7; color: white; padding: 8px;")
        btn_quick.clicked.connect(lambda: self.start_scan("Quick"))
        
        btn_full = QPushButton("Full Scan")
        btn_full.setStyleSheet("background-color: #6c757d; color: white; padding: 8px;")
        btn_full.clicked.connect(lambda: self.start_scan("Full"))
        
        btn_custom = QPushButton("Custom Scan")
        btn_custom.setStyleSheet("background-color: #28a745; color: white; padding: 8px;")
        btn_custom.clicked.connect(self.select_custom_scan)

        controls.addWidget(btn_quick)
        controls.addWidget(btn_full)
        controls.addWidget(btn_custom)
        layout.addLayout(controls)

        # Status Area
        self.status_label = QLabel("Status: Idle - Drag & Drop files here to scan")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels(["File Path", "Threat", "Type", "Severity", "Method", "Time"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.results_table)

        # Action Buttons
        actions = QHBoxLayout()
        btn_del = QPushButton("Delete Selected")
        btn_del.setStyleSheet("background-color: #dc3545; color: white;")
        btn_del.clicked.connect(self.delete_threat)
        
        btn_ignore = QPushButton("Ignore")
        btn_ignore.clicked.connect(self.ignore_threat)
        
        actions.addWidget(btn_del)
        actions.addWidget(btn_ignore)
        actions.addStretch()
        layout.addLayout(actions)

    def setup_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Scan Type", "Files Scanned", "Threats Found", "Timestamp"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.history_table)
        
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self.load_history)
        layout.addWidget(refresh_btn)

    # --- Logic ---

    def start_scan(self, scan_type, custom_path=None):
        if self.scan_thread and self.scan_thread.isRunning():
            QMessageBox.warning(self, "Scan in Progress", "Please wait for the current scan to finish.")
            return

        paths = []
        if scan_type == "Quick":
            # Scan User Documents and Downloads
            home = os.path.expanduser("~")
            paths = [os.path.join(home, "Documents"), os.path.join(home, "Downloads")]
        elif scan_type == "Full":
            # Scan Root (This can take a long time, limiting to C:/Users for safety in demo)
            paths = [os.path.expanduser("~")] 
        elif scan_type == "Custom" and custom_path:
            paths = [custom_path]

        self.results_table.setRowCount(0)
        self.status_label.setText(f"Status: Scanning ({scan_type})...")
        self.progress_bar.setValue(0)

        self.scan_thread = ScanWorker(paths, scan_type, self.db)
        self.scan_thread.progress_updated.connect(self.update_progress)
        self.scan_thread.threat_found.connect(self.add_threat_row)
        self.scan_thread.scan_finished.connect(self.scan_finished)
        self.scan_thread.start()

    def select_custom_scan(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if path:
            self.start_scan("Custom", path)

    def update_progress(self, value, current_file):
        self.progress_bar.setValue(value)
        # Truncate file path for display
        display_path = (current_file[:50] + '...') if len(current_file) > 50 else current_file
        self.status_label.setText(f"Scanning: {display_path}")

    def add_threat_row(self, threat):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(threat['path']))
        self.results_table.setItem(row, 1, QTableWidgetItem(threat['name']))
        self.results_table.setItem(row, 2, QTableWidgetItem(threat['type']))
        
        sev_item = QTableWidgetItem(threat['severity'])
        if threat['severity'] == "High" or threat['severity'] == "Critical":
            sev_item.setForeground(QBrush(QColor("#dc3545")))
        self.results_table.setItem(row, 3, sev_item)
        
        self.results_table.setItem(row, 4, QTableWidgetItem(threat['method']))
        self.results_table.setItem(row, 5, QTableWidgetItem(threat['time']))

    def scan_finished(self, total, threats):
        self.status_label.setText(f"Scan Completed. Scanned {total} files. Found {threats} threats.")
        self.progress_bar.setValue(100)
        self.db.add_scan_history(self.scan_thread.scan_type, total, threats)
        self.load_history()
        
        if threats > 0:
            QMessageBox.warning(self, "Threats Detected", f"Scan found {threats} threats! Please review results.")
        else:
            QMessageBox.information(self, "Clean", "No threats found.")

    def load_history(self):
        history = self.db.get_scan_history()
        self.history_table.setRowCount(len(history))
        for i, row in enumerate(history):
            # row: id, type, files, threats, time
            self.history_table.setItem(i, 0, QTableWidgetItem(row[1]))
            self.history_table.setItem(i, 1, QTableWidgetItem(str(row[2])))
            self.history_table.setItem(i, 2, QTableWidgetItem(str(row[3])))
            self.history_table.setItem(i, 3, QTableWidgetItem(row[4]))

    def delete_threat(self):
        selected = self.results_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        file_path = self.results_table.item(row, 0).text()
        
        confirm = QMessageBox.question(self, "Confirm Delete", f"Permanently delete:\n{file_path}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.results_table.removeRow(row)
                    QMessageBox.information(self, "Success", "File deleted successfully.")
                else:
                    QMessageBox.warning(self, "Error", "File not found.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def ignore_threat(self):
        selected = self.results_table.selectedItems()
        if selected:
            self.results_table.removeRow(selected[0].row())

    # --- Drag & Drop ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            # If directory, scan it. If file, scan it.
            path = files[0] # Just take the first one for simplicity in this demo
            if os.path.isdir(path):
                self.start_scan("Custom", path)
            else:
                self.start_scan("Custom", os.path.dirname(path))

    # --- Real-Time Protection ---
    def toggle_realtime(self):
        if "OFF" in self.rt_status.text():
            # Start
            path_to_watch = os.path.expanduser("~") # Watch user home
            self.event_handler = RealTimeHandler(self.on_realtime_event)
            self.observer = Observer()
            self.observer.schedule(self.event_handler, path_to_watch, recursive=False)
            self.observer.start()
            
            self.rt_status.setText("Real-Time: ON")
            self.rt_status.setStyleSheet("color: #28a745; font-weight: bold;")
            self.rt_btn.setText("Disable Real-Time")
        else:
            # Stop
            if self.observer:
                self.observer.stop()
                self.observer.join()
            
            self.rt_status.setText("Real-Time: OFF")
            self.rt_status.setStyleSheet("color: #dc3545; font-weight: bold;")
            self.rt_btn.setText("Enable Real-Time")

    def on_realtime_event(self, file_path):
        # In a real app, queue this. For now, just print or log.
        print(f"Real-time detection: File modified/created: {file_path}")
        # Trigger a background scan of this specific file if needed