import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget
)
from PyQt6.QtGui import QIcon
from database import DatabaseManager
from login import LoginWindow
from signup import SignupWindow
from forgot_password import ForgotPasswordWindow
from home import HomeWindow

# MAIN APPLICATION CONTROLLER

class NexaShieldApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark_mode = True
        self.setWindowTitle("NexaShield Cybersecurity Suite")
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        self.setWindowIcon(QIcon(icon_path))

        self.center()
        self.setMinimumSize(600, 600)

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

        # Theme Toggles
        self.login_screen.theme_toggle.clicked.connect(self.toggle_theme)
        self.signup_screen.theme_toggle.clicked.connect(self.toggle_theme)
        self.forgot_screen.theme_toggle.clicked.connect(self.toggle_theme)
        self.home_screen.theme_toggle.clicked.connect(self.toggle_theme)

        self.load_stylesheet()

    def center(self):
        w, h = 600, 600
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width() - w) // 2
        y = screen.y() + (screen.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def show_home(self, username):
        self.setWindowTitle(f"NexaShield Cybersecurity Suite : Welcome {username}")
        self.stack.setCurrentIndex(3)
        self.showMaximized()

    def handle_logout(self):
        self.setWindowTitle("NexaShield Cybersecurity Suite")
        self.login_screen.clear_inputs()
        self.stack.setCurrentIndex(0)
        self.showNormal()
        self.resize(600, 600)
        self.center()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        icon = "☀️" if self.is_dark_mode else "🌙"
        
        # Update icons on all screens
        self.login_screen.theme_toggle.setText(icon)
        self.signup_screen.theme_toggle.setText(icon)
        self.forgot_screen.theme_toggle.setText(icon)
        self.home_screen.theme_toggle.setText(icon)
        
        self.load_stylesheet()

    def load_stylesheet(self):
        style_path = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                qss = f.read()
                
                if not self.is_dark_mode:
                    # Dynamic Light Mode Patching
                    qss = qss.replace("#2b2b2b", "#f5f5f5")  # Main BG
                    qss = qss.replace("#333", "#ffffff")     # Panels/Frames
                    qss = qss.replace("#222", "#e8e8e8")     # Inputs
                    qss = qss.replace("#202020", "#e0e0e0")  # Navbar
                    qss = qss.replace("color: white;", "color: #333;")
                    qss = qss.replace("color: #fff;", "color: #333;")
                    qss = qss.replace("color: #aaa;", "color: #555;")

                self.setStyleSheet(qss)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexaShieldApp()
    window.show()
    sys.exit(app.exec())