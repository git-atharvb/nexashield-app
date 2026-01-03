import json
import os
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QMessageBox, QWidget, QDialog, QVBoxLayout, QFrame
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QLinearGradient, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from ui_components import AuthStyle, PasswordInput
from google_auth import GoogleAuthWorker

class NexaLogo(QWidget):
    """Custom painted logo for NexaShield."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(120, 120)
        
        # Animation state
        self.node_alpha = 150
        self.alpha_step = 4
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_nodes)
        self.timer.start(50)

    def animate_nodes(self):
        self.node_alpha += self.alpha_step
        if self.node_alpha >= 200:
            self.node_alpha = 200
            self.alpha_step = -4
        elif self.node_alpha <= 60:
            self.node_alpha = 60
            self.alpha_step = 4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale drawing to fit new size (Base canvas 160x160)
        scale = self.width() / 160.0
        painter.scale(scale, scale)
        
        # --- Draw Shield ---
        path = QPainterPath()
        path.moveTo(30, 30)
        path.lineTo(130, 30)
        # Curve down to bottom point (80, 150)
        path.cubicTo(130, 30, 130, 110, 80, 150)
        path.cubicTo(30, 110, 30, 30, 30, 30)
        
        gradient = QLinearGradient(80, 30, 80, 150)
        gradient.setColorAt(0, QColor("#0078d7"))  # Nexa Blue
        gradient.setColorAt(1, QColor("#004a80"))  # Darker Blue
        
        painter.setPen(QPen(QColor("#003355"), 2))
        painter.setBrush(gradient)
        painter.drawPath(path)
        
        # --- Draw Circuit Lines (Decoration) ---
        painter.setPen(QPen(QColor(255, 255, 255, 50), 2)) # Semi-transparent white
        painter.drawLine(80, 150, 80, 110)
        painter.drawLine(80, 110, 50, 90)
        painter.drawLine(80, 110, 110, 90)
        
        painter.setBrush(QColor(255, 255, 255, self.node_alpha))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(77, 107, 6, 6) # Center node
        painter.drawEllipse(47, 87, 6, 6)  # Left node
        painter.drawEllipse(107, 87, 6, 6) # Right node

        # --- Draw Lock ---
        # Shackle
        painter.setPen(QPen(QColor("#eeeeee"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(60, 45, 40, 40, 0, 180 * 16)
        
        # Lock Body
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("white"))
        painter.drawRoundedRect(55, 65, 50, 40, 6, 6)
        
        # Keyhole
        painter.setBrush(QColor("#005a9e"))
        painter.drawEllipse(76, 80, 8, 8)
        painter.drawRoundedRect(78, 80, 4, 15, 2, 2)

class LoginSuccessDialog(QDialog):
    """A custom, modern dialog for successful login."""
    def __init__(self, username, parent=None):
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

        # Success Icon
        icon = QLabel("✔")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("color: #28a745; font-size: 48px; font-weight: bold; border: none;")
        
        # Text
        lbl_title = QLabel("Login Successful")
        lbl_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; border: none;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_user = QLabel(f"Welcome, {username}")
        lbl_user.setStyleSheet("color: #aaaaaa; font-size: 14px; border: none;")
        lbl_user.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container_layout.addWidget(icon)
        container_layout.addWidget(lbl_title)
        container_layout.addWidget(lbl_user)
        
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

class LoginWindow(AuthStyle):
    switch_to_signup = pyqtSignal()
    switch_to_forgot = pyqtSignal()
    login_success = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db

        # --- Logo Section ---
        self.logo = NexaLogo()
        self.frame_layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addSpacing(10)

        title = QLabel("NexaShield Login")
        title.setObjectName("LoginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.frame_layout.addWidget(self.username_input)

        # Replaced standard QLineEdit with custom PasswordInput
        self.password_input = PasswordInput("Password")
        self.frame_layout.addWidget(self.password_input)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        self.frame_layout.addWidget(self.login_btn)

        self.google_btn = QPushButton("Sign in with Google")
        self.google_btn.setObjectName("GoogleButton")
        self.google_btn.clicked.connect(self.handle_google_login)
        self.frame_layout.addWidget(self.google_btn)

        self.forgot_link = QPushButton("Forgot Password?")
        self.forgot_link.setObjectName("LinkButton")
        self.forgot_link.clicked.connect(self.switch_to_forgot.emit)
        self.frame_layout.addWidget(self.forgot_link)

        self.signup_link = QPushButton("Create an Account")
        self.signup_link.setObjectName("LinkButton")
        self.signup_link.clicked.connect(self.switch_to_signup.emit)
        self.frame_layout.addWidget(self.signup_link)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.db.verify_user(username, password):
            dlg = LoginSuccessDialog(username, self)
            dlg.exec()
            self.login_success.emit()
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")

    def handle_google_login(self):
        # Load credentials from client_secret.json
        client_id = None
        client_secret = None
        
        # --- CONFIGURATION: Set your manual path here if needed ---
        manual_path = r"C:\Users\ATHARV\Downloads\client_secret.json"
        # ---------------------------------------------------------

        # Look for the file in the same directory as this script or one level up
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        possible_paths = [
            manual_path,
            os.path.join(current_dir, "client_secret.json"),
            os.path.join(project_root, "client_secret.json"),
            os.path.join(project_root, "assets", "client_secret.json")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        # Check for 'installed' (desktop) or 'web' keys
                        creds = data.get('installed') or data.get('web')
                        if creds:
                            client_id = creds.get('client_id')
                            client_secret = creds.get('client_secret')
                            break
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to parse client_secret.json: {e}")
                    return

        if not client_id or not client_secret:
            QMessageBox.critical(self, "Config Error", "client_secret.json not found or invalid.\nPlease place it in the project root.")
            return

        self.google_worker = GoogleAuthWorker(client_id, client_secret)
        self.google_worker.auth_success.connect(self.on_google_success)
        self.google_worker.auth_error.connect(self.on_google_error)
        
        self.login_btn.setEnabled(False)
        self.google_btn.setText("Waiting for browser...")
        self.google_worker.start()

    def on_google_success(self, user_info):
        email = user_info.get('email', 'Google User')
        # Here you could register the user in your DB if they don't exist
        dlg = LoginSuccessDialog(email, self)
        dlg.exec()
        self.login_success.emit()
        self.login_btn.setEnabled(True)
        self.google_btn.setText("Sign in with Google")

    def on_google_error(self, error_msg):
        QMessageBox.critical(self, "Google Login Error", error_msg)
        self.login_btn.setEnabled(True)
        self.google_btn.setText("Sign in with Google")

    def clear_inputs(self):
        self.username_input.clear()
        self.password_input.line_edit.clear()