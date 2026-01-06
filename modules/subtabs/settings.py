from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("⚙️ SIEM Settings")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)