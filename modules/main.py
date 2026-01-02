import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget
)
from database import DatabaseManager
from login import LoginWindow
from signup import SignupWindow
from forgot_password import ForgotPasswordWindow
from home import HomeWindow

# MAIN APPLICATION CONTROLLER

class NexaShieldApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NexaShield Cybersecurity Suite")
        self.setGeometry(100, 100, 1200, 800)
        self.center()

        self.db = DatabaseManager()

        # Stacked Widget to manage screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize Screens
        self.login_screen = LoginWindow(self.db)
        self.signup_screen = SignupWindow(self.db)
        self.forgot_screen = ForgotPasswordWindow(self.db)
        self.home_screen = HomeWindow()

        # Add screens to stack
        self.stack.addWidget(self.login_screen)  # Index 0
        self.stack.addWidget(self.signup_screen) # Index 1
        self.stack.addWidget(self.forgot_screen) # Index 2
        self.stack.addWidget(self.home_screen)   # Index 3

        # Connect Signals
        self.login_screen.switch_to_signup.connect(lambda: self.stack.setCurrentIndex(1))
        self.login_screen.switch_to_forgot.connect(lambda: self.stack.setCurrentIndex(2))
        self.login_screen.login_success.connect(self.show_home)
        
        self.signup_screen.switch_to_login.connect(lambda: self.stack.setCurrentIndex(0))
        self.signup_screen.signup_success.connect(self.show_home)

        self.forgot_screen.switch_to_login.connect(lambda: self.stack.setCurrentIndex(0))
        self.home_screen.logout_requested.connect(self.handle_logout)

        self.load_stylesheet()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_home(self):
        self.stack.setCurrentIndex(3)
        self.showMaximized()

    def handle_logout(self):
        self.login_screen.clear_inputs()
        self.stack.setCurrentIndex(0)

    def load_stylesheet(self):
        style_path = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexaShieldApp()
    window.show()
    sys.exit(app.exec())