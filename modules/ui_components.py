import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLineEdit, QToolButton, QGridLayout, QPushButton,
    QLabel, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor

class PasswordInput(QFrame):
    """Custom widget with an embedded eye icon to toggle visibility."""
    def __init__(self, placeholder="Password"):
        super().__init__()
        self.setObjectName("PasswordFrame")
        
        # Layout to hold input and button side-by-side
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # Prevent double-padding conflict with QSS
        self.layout.setSpacing(5)

        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_edit.setObjectName("PasswordLineEdit")
        self.line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum) # Prevent input text squishing
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
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Top Bar for Theme Toggle
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 20, 20, 0)
        top_bar.addStretch()
        self.theme_toggle = QPushButton("☀️")
        self.theme_toggle.setFixedSize(40, 40)
        self.theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle.setObjectName("ThemeToggle")
        top_bar.addWidget(self.theme_toggle)
        self.main_layout.addLayout(top_bar)

        self.main_layout.addStretch()

        # Container for the form to center it
        self.frame = QFrame()
        self.frame.setFixedWidth(400)
        self.frame.setObjectName("AuthFrame")
        self.frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) # Prevent internal element squishing without scrollbars
        
        self.frame_layout = QVBoxLayout()
        self.frame_layout.setSpacing(12) 
        self.frame_layout.setContentsMargins(25, 25, 25, 25)
        self.frame.setLayout(self.frame_layout)
        
        # Secure horizontal centering
        h_center = QHBoxLayout()
        h_center.addStretch()
        h_center.addWidget(self.frame)
        h_center.addStretch()
        self.main_layout.addLayout(h_center)

        self.main_layout.addStretch()

class GlowingLogo(QWidget):
    """A reusable logo widget safely sized to guarantee no element overlapping."""
    def __init__(self, size=65, radius=12, parent=None):
        super().__init__(parent)
        
        # The padding container safely holds the shadow inside so it won't bleed
        padding = 15
        self.setFixedSize(size + (padding * 2), size + (padding * 2))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(0)
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(size, size)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "nexa.png")
        pixmap = QPixmap(logo_path)
        
        if not pixmap.isNull():
            scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Apply corner radius directly to image via QPainter
            rounded = QPixmap(size, size)
            rounded.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            path = QPainterPath()
            path.addRoundedRect(0, 0, size, size, radius, radius)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled)
            painter.end()
            
            self.logo_label.setPixmap(rounded)
        else:
            self.logo_label.setText("LOGO")

        # Soft, mild drop shadow on the inner label
        self.glow = QGraphicsDropShadowEffect(self.logo_label)
        self.glow.setBlurRadius(15) 
        self.glow.setColor(QColor(0, 120, 215, 120)) # Reduced opacity for a softer look
        self.glow.setOffset(0, 0)
        self.logo_label.setGraphicsEffect(self.glow)
        
        layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignCenter)