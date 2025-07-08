from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt

class SalesUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.get_button_stylesheet = main_window.get_button_stylesheet
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Sales Reports")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.export_btn)
        layout.addLayout(header_layout)
        # Monthly sales table
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels([
            "Month", "Total Sales", "Number of Bills", "Average Bill"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.sales_table) 