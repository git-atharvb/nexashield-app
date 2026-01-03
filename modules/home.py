from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QPushButton, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from process import ProcessMonitorWidget
from network import NetworkMonitorWidget
from siem import SIEMDashboard
from phishing_detector import PhishingDetectorWidget

class HomeWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Use 0 margins so the navbar touches the edges
        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- Top Navigation Bar ---
        self.navbar = QFrame()
        self.navbar.setObjectName("Navbar")
        self.navbar.setFixedHeight(60)
        nav_layout = QHBoxLayout(self.navbar)
        nav_layout.setContentsMargins(20, 0, 20, 0)
        nav_layout.setSpacing(15)

        # Logo / Title
        title = QLabel("NexaShield")
        title.setObjectName("NavbarTitle")
        nav_layout.addWidget(title)

        nav_layout.addStretch() # Push buttons to the right (or center if you prefer)

        # Navigation Buttons
        self.nav_buttons = []
        self.modules = [
            ("SIEM", "SIEM Dashboard"),
            ("Processes", "Process Management"),
            ("Network", "Network Management"),
            ("Phishing", "Phishing Detector"),
            ("IDS/IPS", "IDS / IPS"),
            ("Firewall", "Firewall Control"),
            ("Antivirus", "Antivirus Scanner")
        ]

        for i, (btn_text, _) in enumerate(self.modules):
            btn = QPushButton(btn_text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            # Use lambda with default argument to capture the current index 'i'
            btn.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Logout Button
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("LogoutButton")
        logout_btn.clicked.connect(self.confirm_logout)
        nav_layout.addWidget(logout_btn)

        self.layout.addWidget(self.navbar)

        # --- Content Area (Stacked) ---
        self.content_area = QStackedWidget()
        self.layout.addWidget(self.content_area)

        # Add placeholders to stack
        for name, placeholder_text in self.modules:
            if name == "SIEM":
                self.content_area.addWidget(SIEMDashboard())
            elif name == "Processes":
                self.content_area.addWidget(ProcessMonitorWidget())
            elif name == "Network":
                self.content_area.addWidget(NetworkMonitorWidget())
            elif name == "Phishing":
                self.content_area.addWidget(PhishingDetectorWidget())
            else:
                self.content_area.addWidget(self.create_placeholder(placeholder_text))

        # Set default selection
        self.switch_tab(0)

    def switch_tab(self, index):
        """Switches the stacked widget and updates button styles."""
        self.content_area.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def create_placeholder(self, text):
        widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"{text} Module\n(Under Construction)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("PlaceholderLabel")
        layout.addWidget(label)
        widget.setLayout(layout)
        return widget

    def confirm_logout(self):
        reply = QMessageBox.question(
            self, "Confirm Logout", 
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()