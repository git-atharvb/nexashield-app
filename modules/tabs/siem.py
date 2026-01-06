import sys
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from subtabs.overview import OverviewWidget
from subtabs.files import FilesWidget
from subtabs.settings import SettingsWidget
from subtabs.about import AboutWidget
from subtabs.help import HelpWidget
from subtabs.contact import ContactWidget

class SIEMDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Main Layout (Horizontal: Sidebar + Content)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("SIEMSidebar")
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            #SIEMSidebar {
                background-color: #252526;
                border-right: 1px solid #333;
            }
            QPushButton {
                text-align: left;
                padding: 12px 20px;
                border: none;
                color: #ccc;
                font-size: 14px;
                background-color: transparent;
                border-left: 3px solid transparent;
            }
            QPushButton:hover {
                background-color: #2a2d2e;
                color: white;
            }
            QPushButton:checked {
                background-color: #1e1e1e;
                color: #0078d7;
                font-weight: bold;
                border-left: 3px solid #0078d7;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(5)

        # Sidebar Title
        title_lbl = QLabel("SIEM Controls")
        title_lbl.setStyleSheet("color: #666; font-weight: bold; padding-left: 20px; margin-bottom: 10px; text-transform: uppercase; font-size: 11px;")
        sidebar_layout.addWidget(title_lbl)

        # Menu Buttons
        self.menu_buttons = []
        menus = [
            ("📊 Overview", 0),
            ("📂 Files", 1),
            ("⚙️ Settings", 2),
            ("ℹ️ About", 3),
            ("❓ Help", 4),
            ("📞 Contact", 5)
        ]

        for text, idx in menus:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.switch_view(i))
            sidebar_layout.addWidget(btn)
            self.menu_buttons.append(btn)

        sidebar_layout.addStretch()
        
        # --- Right Content Area ---
        self.content_area = QStackedWidget()
        
        # Add sub-modules
        self.content_area.addWidget(OverviewWidget())
        self.content_area.addWidget(FilesWidget())
        self.content_area.addWidget(SettingsWidget())
        self.content_area.addWidget(AboutWidget())
        self.content_area.addWidget(HelpWidget())
        self.content_area.addWidget(ContactWidget())

        # Add to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)

        # Select first tab
        self.switch_view(0)

    def switch_view(self, index):
        self.content_area.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)