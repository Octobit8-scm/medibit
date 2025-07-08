from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QHeaderView, QSizePolicy, QStackedWidget)
from PyQt5.QtCore import Qt

class InventoryUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.theme = main_window.theme
        self.get_button_stylesheet = main_window.get_button_stylesheet
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        # Search box
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-size: 16px; margin-right: 8px;")
        header_layout.addWidget(search_label)
        self.inventory_search_box = QLineEdit()
        self.inventory_search_box.setPlaceholderText("Search by name, barcode, or manufacturer...")
        self.inventory_search_box.setFixedWidth(250)
        header_layout.addWidget(self.inventory_search_box)
        # Inventory action buttons (callbacks to be connected in main_window)
        self.add_medicine_btn = QPushButton("Add Medicine")
        self.add_medicine_btn.setMinimumHeight(36)
        self.add_medicine_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.add_medicine_btn)
        self.scan_barcode_btn = QPushButton("Scan Barcode")
        self.scan_barcode_btn.setMinimumHeight(36)
        self.scan_barcode_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.scan_barcode_btn)
        self.generate_order_btn = QPushButton("Generate Order")
        self.generate_order_btn.setMinimumHeight(36)
        self.generate_order_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.generate_order_btn)
        self.bulk_threshold_btn = QPushButton("Bulk Threshold Settings")
        self.bulk_threshold_btn.setMinimumHeight(36)
        self.bulk_threshold_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.bulk_threshold_btn)
        self.quick_add_stock_btn = QPushButton("Quick Add Stock")
        self.quick_add_stock_btn.setMinimumHeight(36)
        self.quick_add_stock_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.quick_add_stock_btn)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.delete_btn)
        self.clear_inventory_btn = QPushButton("Clear Inventory")
        self.clear_inventory_btn.setMinimumHeight(36)
        self.clear_inventory_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.clear_inventory_btn)
        layout.addLayout(header_layout)
        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Quantity", "Threshold", "Expiry", "Manufacturer", "Price"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setAlternatingRowColors(False)
        self.inventory_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.inventory_table, stretch=1)
        # Inline inventory panel area
        panel_frame = QFrame()
        panel_frame.setFrameShape(QFrame.StyledPanel)
        panel_frame.setFrameShadow(QFrame.Raised)
        panel_layout = QVBoxLayout(panel_frame)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        self.inventory_panel = QStackedWidget()
        panel_layout.addWidget(self.inventory_panel)
        layout.addWidget(panel_frame) 