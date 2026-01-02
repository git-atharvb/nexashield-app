import json
import os
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QMessageBox, QWidget
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QLinearGradient, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui_components import AuthStyle, PasswordInput
from google_auth import GoogleAuthWorker

class NexaLogo(QWidget):
    """Custom painted logo for NexaShield."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(120, 105)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale drawing to fit new size (Original design was 160px wide)
        scale = self.width() / 160.0
        painter.scale(scale, scale)
        w = 160
        
        # --- Draw Lock ---
        # Shackle
        painter.setPen(QPen(QColor("#cccccc"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        shackle_w = 40
        shackle_x = int(w/2 - shackle_w/2)
        shackle_y = 10
        
        # Draw arc (x, y, w, h, startAngle, spanAngle)
        painter.drawArc(shackle_x, shackle_y, shackle_w, shackle_w, 0, 180 * 16)
        
        # Legs
        leg_top = int(shackle_y + shackle_w/2)
        leg_bottom = 50
        painter.drawLine(shackle_x, leg_top, shackle_x, leg_bottom)
        painter.drawLine(shackle_x + shackle_w, leg_top, shackle_x + shackle_w, leg_bottom)

        # Body
        body_w = 70
        body_h = 55
        body_x = int(w/2 - body_w/2)
        body_y = 45
        
        gradient = QLinearGradient(0, body_y, 0, body_y + body_h)
        gradient.setColorAt(0, QColor("#0078d7"))  # Nexa Blue
        gradient.setColorAt(1, QColor("#005a9e"))  # Darker Blue

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(body_x, body_y, body_w, body_h, 8, 8)
        
        # Keyhole
        painter.setBrush(QColor("white"))
        cx = int(w/2)
        cy = int(body_y + body_h/2)
        painter.drawEllipse(cx - 4, cy - 8, 8, 8)
        painter.drawRoundedRect(cx - 2, cy, 4, 12, 2, 2)

        # --- Draw Text ---
        painter.setPen(QPen(QColor("white")))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        font.setFamily("Arial")
        painter.setFont(font)
        
        painter.drawText(0, body_y + body_h + 5, w, 30, Qt.AlignmentFlag.AlignCenter, "NextGen Security Shield")

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
            msg = QMessageBox(self)
            msg.setWindowTitle("Welcome")
            msg.setText(f"Login Successful!\nWelcome, {username}.")
            msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
            QTimer.singleShot(3000, msg.accept)
            msg.exec()
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
        QMessageBox.information(self, "Login Successful", f"Welcome, {email}!")
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