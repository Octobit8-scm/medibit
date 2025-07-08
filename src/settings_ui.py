from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget)
from PyQt5.QtCore import Qt

class SettingsUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Left: Settings buttons
        button_panel = QWidget()
        button_layout = QVBoxLayout(button_panel)
        button_layout.setSpacing(16)
        button_layout.setAlignment(Qt.AlignTop)
        self.notification_btn = QPushButton("Notification Settings")
        self.notification_btn.setMinimumHeight(50)
        button_layout.addWidget(self.notification_btn)
        self.pharmacy_btn = QPushButton("Pharmacy Details")
        self.pharmacy_btn.setMinimumHeight(50)
        button_layout.addWidget(self.pharmacy_btn)
        button_layout.addStretch()
        layout.addWidget(button_panel, 0)
        # Right: Settings panel area (QStackedWidget)
        self.settings_panel = QStackedWidget()
        layout.addWidget(self.settings_panel, 1) 