import random
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from ui_components import AuthStyle, PasswordInput

class ForgotPasswordWindow(AuthStyle):
    switch_to_login = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.generated_otp = None
        self.current_username = None

        title = QLabel("Reset Password")
        title.setObjectName("LoginTitle") # Reuse login title style
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addWidget(title)

        # --- STEP 1: Username Input ---
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        self.frame_layout.addWidget(self.username_input)

        self.send_otp_btn = QPushButton("📨 Send OTP")
        self.send_otp_btn.clicked.connect(self.handle_send_otp)
        self.frame_layout.addWidget(self.send_otp_btn)

        # --- STEP 2: OTP & New Password (Hidden initially) ---
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter 6-digit OTP")
        self.otp_input.hide()
        self.frame_layout.addWidget(self.otp_input)

        self.new_password_input = PasswordInput("New Password")
        self.new_password_input.hide()
        self.frame_layout.addWidget(self.new_password_input)

        self.reset_btn = QPushButton("🔐 Reset Password")
        self.reset_btn.clicked.connect(self.handle_reset_password)
        self.reset_btn.hide()
        self.frame_layout.addWidget(self.reset_btn)

        # Back Button
        self.back_btn = QPushButton("⬅️ Back to Login")
        self.back_btn.setObjectName("LinkButton")
        self.back_btn.clicked.connect(self.switch_to_login.emit)
        self.frame_layout.addWidget(self.back_btn)

    def handle_send_otp(self):
        username = self.username_input.text()
        if not username:
            QMessageBox.warning(self, "Error", "Please enter your username.")
            return

        phone = self.db.get_user_phone(username)
        if not phone:
            QMessageBox.warning(self, "Error", "User not found.")
            return

        # Generate 6-digit OTP
        self.generated_otp = str(random.randint(100000, 999999))
        self.current_username = username

        # Simulate SMS Gateway
        masked_phone = phone[:2] + "****" + phone[-2:] if len(phone) > 4 else "****"
        QMessageBox.information(self, "OTP Sent", 
                                f"OTP sent to registered phone ending in {masked_phone}.\n\n"
                                f"(SIMULATION: Your OTP is {self.generated_otp})")

        # Switch UI to Step 2
        self.username_input.hide()
        self.send_otp_btn.hide()
        
        self.otp_input.show()
        self.new_password_input.show()
        self.reset_btn.show()

    def handle_reset_password(self):
        otp = self.otp_input.text()
        new_pw = self.new_password_input.text()

        if otp != self.generated_otp:
            QMessageBox.warning(self, "Error", "Invalid OTP.")
            return
        
        if not new_pw:
            QMessageBox.warning(self, "Error", "Enter a new password.")
            return

        if self.db.update_password(self.current_username, new_pw):
            QMessageBox.information(self, "Success", "Password reset successfully.")
            self.switch_to_login.emit()
            self.reset_ui()
        else:
            QMessageBox.critical(self, "Error", "Failed to update password.")

    def reset_ui(self):
        """Reset the form state for next use."""
        self.username_input.clear()
        self.username_input.show()
        self.send_otp_btn.show()
        self.otp_input.clear()
        self.otp_input.hide()
        self.new_password_input.line_edit.clear()
        self.new_password_input.hide()
        self.reset_btn.hide()
        self.generated_otp = None
        self.current_username = None