from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QMessageBox, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
from ui_components import AuthStyle, PasswordInput

class SignupWindow(AuthStyle):
    switch_to_login = pyqtSignal()
    signup_success = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.is_password_strong = False

        title = QLabel("Create Account")
        title.setObjectName("SignupTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.frame_layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose Username")
        self.frame_layout.addWidget(self.username_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        # Input Validation: Allow only digits
        rx = QRegularExpression("^[0-9]*$")
        self.phone_input.setValidator(QRegularExpressionValidator(rx))
        self.frame_layout.addWidget(self.phone_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Address")
        self.frame_layout.addWidget(self.address_input)

        # Replaced standard QLineEdit with custom PasswordInput
        self.password_input = PasswordInput("Choose Password")
        # Connect text change signal to strength checker
        self.password_input.line_edit.textChanged.connect(self.check_password_strength)
        self.frame_layout.addWidget(self.password_input)

        # Password Strength Meter
        self.strength_bar = QProgressBar()
        self.strength_bar.setObjectName("StrengthBar")
        self.strength_bar.setFixedHeight(5)
        self.strength_bar.setTextVisible(False)
        self.frame_layout.addWidget(self.strength_bar)

        self.strength_label = QLabel("Password Strength: None")
        self.strength_label.setObjectName("StrengthLabel")
        self.frame_layout.addWidget(self.strength_label)

        self.signup_btn = QPushButton("✅ Sign Up")
        self.signup_btn.setObjectName("SignupButton")
        self.signup_btn.clicked.connect(self.handle_signup)
        self.frame_layout.addWidget(self.signup_btn)

        self.login_link = QPushButton("⬅️ Back to Login")
        self.login_link.setObjectName("LinkButton")
        self.login_link.clicked.connect(self.switch_to_login.emit)
        self.frame_layout.addWidget(self.login_link)

    def check_password_strength(self):
        password = self.password_input.text()
        score = 0
        
        # Criteria
        if len(password) >= 8: score += 1
        if any(c.isdigit() for c in password): score += 1
        if any(c.isupper() for c in password): score += 1
        if any(not c.isalnum() for c in password): score += 1 # Special char

        # Update UI based on score
        self.strength_bar.setValue(score * 25)

        if score < 2:
            self.strength_bar.setProperty("strength", "weak")
            self.strength_label.setText("Weak (Need 8+ chars, numbers, symbols)")
            self.strength_label.setProperty("strength", "weak")
            self.is_password_strong = False
        elif score < 4:
            self.strength_bar.setProperty("strength", "medium")
            self.strength_label.setText("Medium (Add special chars & uppercase)")
            self.strength_label.setProperty("strength", "medium")
            self.is_password_strong = False
        else:
            self.strength_bar.setProperty("strength", "strong")
            self.strength_label.setText("Strong")
            self.strength_label.setProperty("strength", "strong")
            self.is_password_strong = True
            
        self.strength_bar.style().unpolish(self.strength_bar)
        self.strength_bar.style().polish(self.strength_bar)
        self.strength_label.style().unpolish(self.strength_label)
        self.strength_label.style().polish(self.strength_label)

    def handle_signup(self):
        username = self.username_input.text()
        password = self.password_input.text()
        phone = self.phone_input.text()
        address = self.address_input.text()

        if not all([username, password, phone, address]):
            QMessageBox.warning(self, "Error", "Fields cannot be empty")
            return

        if not self.is_password_strong:
            QMessageBox.warning(self, "Weak Password", "Please ensure your password meets all security requirements.")
            return

        if self.db.register_user(username, password, phone, address):
            QMessageBox.information(self, "Success", "Account created! Logging you in...")
            self.signup_success.emit(username)
        else:
            QMessageBox.warning(self, "Error", "Username already exists")