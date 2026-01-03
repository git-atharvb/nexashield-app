from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class SIEMDashboard(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        
        # Placeholder content
        label = QLabel("SIEM Dashboard Content")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(label)