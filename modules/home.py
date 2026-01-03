from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget, QPushButton, QFrame, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from tabs.process import ProcessMonitorWidget
from tabs.network import NetworkMonitorWidget
from tabs.siem import SIEMDashboard
from tabs.phishing_detector import PhishingDetectorWidget
from tabs.antivirus import AntivirusWidget
from tabs.memory import MemoryMonitorWidget
from tabs.cloud import CloudSecurityWidget
from tabs.settings import SettingsWidget
from tabs.about import AboutWidget

class LogoutSuccessDialog(QDialog):
    """A custom, modern dialog for successful logout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 15px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(20, 20, 20, 20)

        # Icon
        icon = QLabel("👋")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("color: #0078d7; font-size: 48px; font-weight: bold; border: none;")
        
        # Text
        lbl_title = QLabel("Logged Out")
        lbl_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_msg = QLabel("Thank you for using\nNexaShield")
        lbl_msg.setStyleSheet("color: #aaaaaa; font-size: 14px; border: none;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(icon)
        container_layout.addWidget(lbl_title)
        container_layout.addWidget(lbl_msg)
        
        layout.addWidget(container)

        # Animation Setup
        self.setWindowOpacity(0.0)
        
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out.finished.connect(self.accept)

        # Sequence: Fade In -> Wait -> Fade Out
        self.fade_in.start()
        QTimer.singleShot(1500, self.fade_out.start)

class LogoutSuccessDialog(QDialog):
    """A custom, modern dialog for successful logout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 15px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(20, 20, 20, 20)

        # Icon
        icon = QLabel("👋")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("color: #0078d7; font-size: 48px; font-weight: bold; border: none;")
        
        # Text
        lbl_title = QLabel("Logged Out")
        lbl_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_msg = QLabel("Thank you for using\nNexaShield")
        lbl_msg.setStyleSheet("color: #aaaaaa; font-size: 14px; border: none;")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(icon)
        container_layout.addWidget(lbl_title)
        container_layout.addWidget(lbl_msg)
        
        layout.addWidget(container)

        # Animation Setup
        self.setWindowOpacity(0.0)
        
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(500)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out.finished.connect(self.accept)

        # Sequence: Fade In -> Wait -> Fade Out
        self.fade_in.start()
        QTimer.singleShot(1500, self.fade_out.start)

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
            ("Memory", "Memory Analysis"),
            ("Phishing", "Phishing Detector"),
            ("IDS/IPS", "IDS / IPS"),
            ("Firewall", "Firewall Control"),
            ("Antivirus", "Antivirus Scanner"),
            ("Cloud", "Cloud Security"),
            ("Settings", "Settings"),
            ("About", "About")
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
            elif name == "Memory":
                self.content_area.addWidget(MemoryMonitorWidget())
            elif name == "Antivirus":
                self.content_area.addWidget(AntivirusWidget())
            elif name == "Cloud":
                self.content_area.addWidget(CloudSecurityWidget())
            elif name == "Settings":
                self.content_area.addWidget(SettingsWidget())
            elif name == "About":
                self.content_area.addWidget(AboutWidget())
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
            dlg = LogoutSuccessDialog(self)
            dlg.exec()
            self.logout_requested.emit()