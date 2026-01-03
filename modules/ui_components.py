from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLineEdit, QToolButton, QGridLayout
)
from PyQt6.QtCore import Qt

class PasswordInput(QFrame):
    """Custom widget with an embedded eye icon to toggle visibility."""
    def __init__(self, placeholder="Password"):
        super().__init__()
        self.setObjectName("PasswordFrame")
        
        # Layout to hold input and button side-by-side
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(0)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_edit.setObjectName("PasswordLineEdit")
        self.layout.addWidget(self.line_edit)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("👁") # Unicode Eye Icon
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self.toggle_visibility)
        self.toggle_btn.setObjectName("VisibilityButton")
        self.layout.addWidget(self.toggle_btn)

    def toggle_visibility(self):
        mode = QLineEdit.EchoMode.Normal if self.toggle_btn.isChecked() else QLineEdit.EchoMode.Password
        self.line_edit.setEchoMode(mode)

    def text(self):
        return self.line_edit.text()

class AuthStyle(QWidget):
    """Base class for styling Login/Signup forms."""
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Container for the form to center it
        self.frame = QFrame()
        self.frame.setFixedWidth(400)
        self.frame.setObjectName("AuthFrame")
        self.frame_layout = QVBoxLayout()
        self.frame.setLayout(self.frame_layout)
        self.layout.addWidget(self.frame, 0, 0, Qt.AlignmentFlag.AlignCenter)