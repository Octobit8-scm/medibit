from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt

class OrdersUi(QWidget):
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
        title = QLabel("Orders Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.create_order_btn = QPushButton("Create Order")
        self.create_order_btn.setMinimumHeight(40)
        self.create_order_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.create_order_btn)
        layout.addLayout(header_layout)
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Supplier", "Items", "Total", "Status"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.orders_table) 