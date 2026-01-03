import psutil
import socket
import time
from collections import deque
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QComboBox, QGroupBox,
    QAbstractItemView, QMessageBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QBrush, QPainter, QPainterPath, QLinearGradient, QPen, QFont

# --- Constants ---
REFRESH_INTERVAL = 1000  # 1 second for smoother charts

class NetworkWorker(QThread):
    """
    Background thread to fetch network connections and interface stats.
    """
    data_fetched = pyqtSignal(dict)

    def run(self):
        # Optimize: Fetch all process names at once to avoid O(N) system calls
        pid_names = {}
        try:
            for p in psutil.process_iter(['pid', 'name']):
                pid_names[p.info['pid']] = p.info['name']
        except Exception:
            pass

        # 1. Fetch Connections
        connections = []
        try:
            # kind='inet' fetches both IPv4 and IPv6, TCP and UDP
            for conn in psutil.net_connections(kind='inet'):
                try:
                    # Resolve process name if PID exists
                    proc_name = pid_names.get(conn.pid, "-") if conn.pid else "-"
                    
                    connections.append({
                        'fd': conn.fd,
                        'family': conn.family,
                        'type': conn.type,
                        'laddr': conn.laddr,
                        'raddr': conn.raddr,
                        'status': conn.status,
                        'pid': conn.pid,
                        'proc_name': proc_name
                    })
                except Exception:
                    continue
        except psutil.AccessDenied:
            # Non-admin users might not see all connections
            pass

        # 2. Fetch Interface Stats
        io_counters = psutil.net_io_counters(pernic=True)
        if_addrs = psutil.net_if_addrs()
        
        data = {
            'connections': connections,
            'io_counters': io_counters,
            'if_addrs': if_addrs,
            'timestamp': time.time()
        }
        self.data_fetched.emit(data)

class NetworkChart(QWidget):
    """Custom widget to draw live network traffic charts with dynamic scaling."""
    def __init__(self, title, line_color="#0078d7"):
        super().__init__()
        self.title = title
        self.line_color = QColor(line_color)
        self.data = deque([0]*60, maxlen=60)
        self.setMinimumHeight(150)
        self.current_value = 0.0
        self.max_val = 1024.0 # Start with 1KB scale

    def update_value(self, value):
        self.current_value = value
        self.data.append(value)
        # Dynamic scaling: look at recent history
        local_max = max(self.data)
        if local_max > self.max_val:
            self.max_val = local_max
        elif local_max < self.max_val * 0.5 and self.max_val > 1024:
            # Decay max scale slowly if activity drops
            self.max_val *= 0.95
        
        self.update()

    def format_bytes(self, size):
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:.1f} {power_labels.get(n, '')}B/s"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#2b2b2b"))
        
        # Title & Value
        painter.setPen(QColor("white"))
        painter.drawText(10, 20, f"{self.title}: {self.format_bytes(self.current_value)}")
        
        if not self.data:
            return
            
        path = QPainterPath()
        step_x = w / (self.data.maxlen - 1)
        
        # Calculate points
        # y = h - (value / max_val * h)
        # Ensure we don't divide by zero
        scale_max = max(self.max_val, 1.0)
        
        path.moveTo(0, h - (self.data[0] / scale_max * h))
        for i, val in enumerate(self.data):
            x = i * step_x
            y = h - (val / scale_max * h)
            path.lineTo(x, y)
            
        painter.setPen(QPen(self.line_color, 2))
        painter.drawPath(path)
        
        # Gradient fill
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

class ProtocolPieChart(QWidget):
    """Visualizes the distribution of TCP vs UDP connections."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(150, 150)
        self.tcp_count = 0
        self.udp_count = 0
        self.title = "Protocol Distribution"

    def update_counts(self, tcp, udp):
        self.tcp_count = tcp
        self.udp_count = udp
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Background
        painter.fillRect(0, 0, w, h, QColor("#2b2b2b"))
        
        # Title
        painter.setPen(QColor("white"))
        painter.drawText(10, 20, self.title)

        # Pie Chart
        size = min(w, h) - 40
        rect = QRectF((w - size) / 2, 30, size, size)
        
        total = self.tcp_count + self.udp_count
        if total == 0:
            painter.setBrush(QColor("#444"))
            painter.drawEllipse(rect)
        else:
            start_angle = 90 * 16
            tcp_span = int((self.tcp_count / total) * 360 * 16)
            
            # TCP (Blue)
            painter.setBrush(QColor("#0078d7"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(rect, start_angle, tcp_span)
            
            # UDP (Orange)
            painter.setBrush(QColor("#ffc107"))
            painter.drawPie(rect, start_angle + tcp_span, 360 * 16 - tcp_span)

        # Legend
        painter.setPen(QColor("white"))
        legend_y = h - 10
        painter.drawText(10, legend_y, f"TCP: {self.tcp_count}")
        
        # Draw UDP text aligned right
        udp_text = f"UDP: {self.udp_count}"
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(udp_text)
        painter.drawText(w - text_w - 10, legend_y, udp_text)

class NetworkMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("NetworkMonitor")
        
        # State
        self.network_data = {}
        self.prev_io_counters = {}
        self.prev_timestamp = 0
        self.filter_text = ""
        self.interface_filter = "All"
        self.protocol_filter = "All"
        
        # UI Setup
        self.setup_ui()
        
        # Worker & Timer
        self.worker = NetworkWorker()
        self.worker.data_fetched.connect(self.update_ui)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(REFRESH_INTERVAL)
        
        # Initial load
        self.refresh_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Top Control Bar ---
        control_bar = QHBoxLayout()
        
        # Interface Selector
        self.combo_interface = QComboBox()
        self.combo_interface.addItem("All")
        self.combo_interface.currentTextChanged.connect(self.handle_interface_change)
        control_bar.addWidget(QLabel("Interface:"))
        control_bar.addWidget(self.combo_interface)

        # Protocol Selector
        self.combo_protocol = QComboBox()
        self.combo_protocol.addItems(["All", "TCP", "UDP"])
        self.combo_protocol.currentTextChanged.connect(self.handle_protocol_change)
        control_bar.addWidget(QLabel("Protocol:"))
        control_bar.addWidget(self.combo_protocol)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search IP, Port, PID, Name...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.handle_search)
        control_bar.addWidget(self.search_input)

        control_bar.addStretch()

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_data)
        control_bar.addWidget(self.btn_refresh)

        layout.addLayout(control_bar)

        # --- Dashboard Area (Top) ---
        dashboard_group = QGroupBox("Network Dashboard")
        dashboard_layout = QHBoxLayout(dashboard_group)
        dashboard_layout.setSpacing(15)
        
        # Info Card
        info_panel = QFrame()
        info_panel.setStyleSheet("background-color: #2b2b2b; border-radius: 5px;")
        info_layout = QVBoxLayout(info_panel)
        
        self.lbl_interface_name = QLabel("Interface: -")
        self.lbl_interface_name.setStyleSheet("color: #aaa; font-weight: bold;")
        info_layout.addWidget(self.lbl_interface_name)
        
        self.lbl_hostname = QLabel(f"Host: {socket.gethostname()}")
        self.lbl_hostname.setStyleSheet("color: white; font-weight: bold; margin-bottom: 5px;")
        info_layout.addWidget(self.lbl_hostname)

        self.lbl_ip = QLabel("IP: -")
        self.lbl_mac = QLabel("MAC: -")
        self.lbl_netmask = QLabel("Mask: -")
        self.lbl_broadcast = QLabel("Broadcast: -")
        self.lbl_sent = QLabel("Sent: -")
        self.lbl_recv = QLabel("Recv: -")
        
        self.lbl_ip.setStyleSheet("color: white; font-size: 11pt;")
        self.lbl_mac.setStyleSheet("color: #ccc; font-size: 9pt;")
        self.lbl_netmask.setStyleSheet("color: #ccc; font-size: 9pt;")
        self.lbl_broadcast.setStyleSheet("color: #ccc; font-size: 9pt;")
        self.lbl_sent.setStyleSheet("color: #28a745;")
        self.lbl_recv.setStyleSheet("color: #0078d7;")
        
        info_layout.addWidget(self.lbl_ip)
        info_layout.addWidget(self.lbl_mac)
        info_layout.addWidget(self.lbl_netmask)
        info_layout.addWidget(self.lbl_broadcast)
        info_layout.addWidget(self.lbl_sent)
        info_layout.addWidget(self.lbl_recv)
        info_layout.addStretch()
        
        dashboard_layout.addWidget(info_panel, 1)
        
        # Charts
        self.chart_down = NetworkChart("Download", "#28a745") # Green
        self.chart_up = NetworkChart("Upload", "#0078d7")     # Blue
        self.pie_chart = ProtocolPieChart()
        
        dashboard_layout.addWidget(self.chart_down, 2)
        dashboard_layout.addWidget(self.chart_up, 2)
        dashboard_layout.addWidget(self.pie_chart, 1)
        
        layout.addWidget(dashboard_group)

        # --- Active Connections Table (Bottom) ---
        conn_group = QGroupBox("Active Connections")
        conn_layout = QVBoxLayout(conn_group)

        self.conn_table = QTableWidget()
        self.conn_table.setColumnCount(6)
        self.conn_table.setHorizontalHeaderLabels([
            "Process", "PID", "Protocol", "Local Address", "Remote Address", "Status"
        ])
        self.conn_table.verticalHeader().setVisible(False)
        self.conn_table.setAlternatingRowColors(True)
        self.conn_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.conn_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Column Sizing
        header = self.conn_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Process Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Local
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Remote
        
        conn_layout.addWidget(self.conn_table)
        layout.addWidget(conn_group)

        # Status Bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

    def refresh_data(self):
        if not self.worker.isRunning():
            self.status_label.setText("Updating network data...")
            self.worker.start()

    def update_ui(self, data):
        self.network_data = data
        self.update_interface_stats(data)
        self.update_connections_table(data)
        self.status_label.setText(f"Last updated: {time.strftime('%H:%M:%S')}")
        
        # Update Pie Chart
        connections = data.get('connections', [])
        tcp = sum(1 for c in connections if c['type'] == socket.SOCK_STREAM)
        udp = sum(1 for c in connections if c['type'] == socket.SOCK_DGRAM)
        self.pie_chart.update_counts(tcp, udp)

    def update_interface_stats(self, data):
        io_counters = data['io_counters']
        if_addrs = data['if_addrs']
        timestamp = data['timestamp']
        
        # Calculate time delta for speed
        time_delta = timestamp - self.prev_timestamp if self.prev_timestamp > 0 else 0
        
        # Update Interface Combo if needed (only once or if count changes)
        if self.combo_interface.count() <= 1:
            current_selection = self.combo_interface.currentText()
            self.combo_interface.clear()
            self.combo_interface.addItem("All")
            for nic in if_addrs.keys():
                self.combo_interface.addItem(nic)
            self.combo_interface.setCurrentText(current_selection)

        for row, (nic, addrs) in enumerate(if_addrs.items()):
            # Get IP, MAC, Netmask, Broadcast
            ip_addr = "-"
            mac_addr = "-"
            netmask = "-"
            broadcast = "-"

            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip_addr = addr.address
                    netmask = addr.netmask if addr.netmask else "-"
                    broadcast = addr.broadcast if addr.broadcast else "-"
                elif addr.family == psutil.AF_LINK:
                    mac_addr = addr.address
            
            # Get Stats
            sent = 0
            recv = 0
            up_speed = 0.0
            down_speed = 0.0
            
            if nic in io_counters:
                stats = io_counters[nic]
                sent = stats.bytes_sent
                recv = stats.bytes_recv
                
                # Calculate Speed
                if time_delta > 0 and nic in self.prev_io_counters:
                    prev_stats = self.prev_io_counters[nic]
                    up_speed = (sent - prev_stats.bytes_sent) / time_delta
                    down_speed = (recv - prev_stats.bytes_recv) / time_delta

            # Update Dashboard if this is the selected interface (or first one if All)
            if (self.interface_filter == "All" and row == 0) or (self.interface_filter == nic):
                self.lbl_interface_name.setText(f"Interface: {nic}")
                self.lbl_ip.setText(f"IP: {ip_addr}")
                self.lbl_mac.setText(f"MAC: {mac_addr}")
                self.lbl_netmask.setText(f"Mask: {netmask}")
                self.lbl_broadcast.setText(f"Broadcast: {broadcast}")
                self.lbl_sent.setText(f"Sent: {self.format_bytes(sent)}")
                self.lbl_recv.setText(f"Recv: {self.format_bytes(recv)}")
                self.chart_up.update_value(up_speed)
                self.chart_down.update_value(down_speed)

        # Update history
        self.prev_io_counters = io_counters
        self.prev_timestamp = timestamp

    def update_connections_table(self, data):
        connections = data.get('connections', [])
        filtered_conns = self.filter_connections(connections, data.get('if_addrs', {}))
        
        self.conn_table.setRowCount(len(filtered_conns))
        self.conn_table.setSortingEnabled(False) # Disable sorting during update

        def update_conn_item(row, col, text, color=None):
            item = self.conn_table.item(row, col)
            if not item:
                item = QTableWidgetItem()
                self.conn_table.setItem(row, col, item)
            
            if item.text() != text:
                item.setText(text)
            
            if color:
                item.setForeground(QBrush(QColor(color)))
            else:
                item.setData(Qt.ItemDataRole.ForegroundRole, None)

        for row, conn in enumerate(filtered_conns):
            # 0: Process Name
            update_conn_item(row, 0, str(conn['proc_name']))
            
            # 1: PID
            update_conn_item(row, 1, str(conn['pid']))
            
            # 2: Protocol
            proto = "TCP" if conn['type'] == socket.SOCK_STREAM else "UDP"
            update_conn_item(row, 2, proto)
            
            # 3: Local Address
            laddr = f"{conn['laddr'].ip}:{conn['laddr'].port}" if conn['laddr'] else "-"
            update_conn_item(row, 3, laddr)
            
            # 4: Remote Address
            raddr = f"{conn['raddr'].ip}:{conn['raddr'].port}" if conn['raddr'] else "-"
            update_conn_item(row, 4, raddr)
            
            # 5: Status
            status_color = None
            if conn['status'] == "ESTABLISHED":
                status_color = "#28a745"
            elif conn['status'] == "LISTEN":
                status_color = "#0078d7"
            update_conn_item(row, 5, conn['status'], status_color)

        self.conn_table.setSortingEnabled(True)

    def filter_connections(self, connections, if_addrs):
        filtered = []
        search_lower = self.filter_text.lower()
        
        # Determine IP for selected interface
        selected_ip = None
        if self.interface_filter != "All" and self.interface_filter in if_addrs:
            for addr in if_addrs[self.interface_filter]:
                if addr.family == socket.AF_INET:
                    selected_ip = addr.address
                    break

        for conn in connections:
            # 1. Protocol Filter
            conn_proto = "TCP" if conn['type'] == socket.SOCK_STREAM else "UDP"
            if self.protocol_filter != "All" and self.protocol_filter != conn_proto:
                continue

            # 2. Interface Filter (Match Local IP)
            if selected_ip:
                if not conn['laddr'] or conn['laddr'].ip != selected_ip:
                    continue

            # 3. Search Filter
            if search_lower:
                laddr_str = f"{conn['laddr'].ip}:{conn['laddr'].port}" if conn['laddr'] else ""
                raddr_str = f"{conn['raddr'].ip}:{conn['raddr'].port}" if conn['raddr'] else ""
                search_terms = [
                    str(conn['pid']), 
                    conn['proc_name'].lower(), 
                    laddr_str, 
                    raddr_str
                ]
                if not any(search_lower in term for term in search_terms):
                    continue
            
            filtered.append(conn)
            
        return filtered

    def handle_interface_change(self, text):
        self.interface_filter = text
        self.update_connections_table(self.network_data)

    def handle_protocol_change(self, text):
        self.protocol_filter = text
        self.update_connections_table(self.network_data)

    def handle_search(self, text):
        self.filter_text = text
        self.update_connections_table(self.network_data)

    def format_bytes(self, size):
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:.1f} {power_labels.get(n, '')}B"
