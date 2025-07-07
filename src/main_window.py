import csv
import datetime
import json
import logging
# Setup logging
import os
import os as _os
import subprocess
import sys
import tempfile
import webbrowser
from logging.handlers import RotatingFileHandler

import qtawesome as qta
from PyQt5.QtCore import QDate, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox,
                             QDateEdit, QDialog, QDialogButtonBox, QFileDialog,
                             QFormLayout, QFrame, QGroupBox, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QListView,
                             QListWidget, QListWidgetItem, QMainWindow, QMenu,
                             QMenuBar, QMessageBox, QPushButton, QScrollArea,
                             QSizePolicy, QSpinBox, QStackedWidget, QStatusBar,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget)

from barcode_scanner import BarcodeScannerDialog
from config import (get_installation_date, get_license_key, get_theme,
                    get_threshold, set_installation_date, set_license_key,
                    set_theme, set_threshold)
from db import (add_bill, add_medicine, add_order, clear_inventory,
                delete_medicine, get_all_bills, get_all_medicines,
                get_all_orders, get_low_stock_medicines, get_monthly_sales,
                get_pharmacy_details, save_pharmacy_details, update_medicine,
                update_medicine_quantity)
from dialogs import (AddMedicineDialog, BillingAddMedicineDialog,
                     BulkThresholdDialog, CustomerInfoDialog,
                     EditMedicineDialog, NotificationSettingsDialog,
                     OrderQuantityDialog, PharmacyDetailsDialog,
                     QuickAddStockDialog, SupplierInfoDialog,
                     ThresholdSettingDialog)
from license_utils import verify_license_key
from notifications import NotificationManager
from order_manager import OrderManager
from receipt_manager import ReceiptManager
from theme import get_stylesheet

log_dir = _os.path.join(_os.getcwd(), 'logs')
if not _os.path.exists(log_dir):
    _os.makedirs(log_dir)
log_file = _os.path.join(log_dir, 'medibit_app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=5)]
)
logger = logging.getLogger('medibit')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info('MainWindow initialized')
        self.setWindowTitle("Medibit")
        # Set the window icon to use the medibit logo
        try:
            import os

            # Try to use the existing ICO file first (preferred for Windows taskbar)
            if os.path.exists("medibit.ico"):
                self.setWindowIcon(QIcon("medibit.ico"))
            else:
                # Fallback to JPG if ICO doesn't exist
                icon_pixmap = QPixmap("public/images/medibit_logo.jpg")
                if not icon_pixmap.isNull():
                    # Scale the icon to a reasonable size for taskbar (32x32 pixels)
                    icon_pixmap = icon_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.setWindowIcon(QIcon(icon_pixmap))
        except:
            # Fallback to default icon if image loading fails
            pass
        self.resize(1000, 600)
        self.setMinimumSize(800, 500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.theme = get_theme()
        self.notification_manager = NotificationManager()  # Initialize notification manager
        self.receipt_manager = ReceiptManager()  # Add this line
        self._init_menubar()
        self.setStyleSheet(get_stylesheet())
        self.init_ui()
        self.showMaximized()
        # Status bar: only show developer name, no dynamic messages
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        dev_label = QLabel("Designed & Developed by Octobit8")
        dev_label.setStyleSheet("font-weight: bold; padding-right: 16px;")
        self.statusBar.addPermanentWidget(dev_label)

    def _init_menubar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        # Menu
        menu_menu = QMenu("Menu", self)
        # Add module access actions
        module_names = ["Inventory", "Billing", "Orders", "Alerts", "Sales", "Settings"]
        for idx, name in enumerate(module_names):
            action = QAction(name, self)
            action.triggered.connect(lambda checked, i=idx: self.display_page(i))
            menu_menu.addAction(action)
        # Add Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.handle_exit)
        menu_menu.addSeparator()
        menu_menu.addAction(exit_action)
        menubar.addMenu(menu_menu)
        # View
        view_menu = QMenu("View", self)
        light_action = QAction("Light Mode", self)
        dark_action = QAction("Dark Mode", self)
        light_action.triggered.connect(lambda: self.set_theme_from_menu('light'))
        dark_action.triggered.connect(lambda: self.set_theme_from_menu('dark'))
        view_menu.addAction(light_action)
        view_menu.addAction(dark_action)
        menubar.addMenu(view_menu)
        # About
        about_menu = QMenu("About", self)
        about_action = QAction("About Medibit", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)
        menubar.addMenu(about_menu)
        # License
        license_menu = QMenu("License", self)
        license_info_action = QAction("License Information", self)
        license_info_action.triggered.connect(self.show_license_info_dialog)
        license_menu.addAction(license_info_action)
        menubar.addMenu(license_menu)
        # Add Daily Sales Summary action to the Reports or Tools menu
        daily_sales_action = QAction("Send Daily Sales Summary", self)
        daily_sales_action.triggered.connect(self.send_daily_sales_summary)
        # Add to Reports or Tools menu (create if not present)
        reports_menu = self.menuBar().findChild(QMenu, "Reports")
        if not reports_menu:
            reports_menu = self.menuBar().addMenu("Reports")
        reports_menu.addAction(daily_sales_action)

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Pharmacy name above navbar
        self.pharmacy_name_label = QLabel('Pharmacy')
        self.pharmacy_name_label.setAlignment(Qt.AlignCenter)
        self.pharmacy_name_label.setStyleSheet(self.get_pharmacy_name_stylesheet())
        main_layout.addWidget(self.pharmacy_name_label)
        
        # Load pharmacy name from database
        self.update_pharmacy_name_label()

        # Top navigation bar (QHBoxLayout of QPushButtons)
        nav_bar_widget = QWidget()
        nav_bar_layout = QHBoxLayout(nav_bar_widget)
        nav_bar_layout.setContentsMargins(20, 10, 20, 10)
        nav_bar_layout.setSpacing(24)
        self.nav_buttons = []
        icon_color = '#FFFFFF' if get_theme() == 'dark' else '#000000'
        nav_items = [
            ("Inventory", qta.icon('fa5s.pills', color=icon_color)),
            ("Billing", qta.icon('fa5s.cash-register', color=icon_color)),
            ("Orders", qta.icon('fa5s.file-invoice', color=icon_color)),
            ("Alerts", qta.icon('fa5s.exclamation-triangle', color=icon_color)),
            ("Sales", qta.icon('fa5s.chart-line', color=icon_color)),
            ("Settings", qta.icon('fa5s.cog', color=icon_color)),
        ]
        for idx, (text, icon) in enumerate(nav_items):
            btn = QPushButton(icon, text)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.setMaximumHeight(50)
            btn.setMinimumWidth(150)
            btn.setIconSize(QSize(20, 20))
            btn.setStyleSheet(self.get_navbar_button_stylesheet())
            btn.clicked.connect(lambda checked, i=idx: self.display_page(i))
            nav_bar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        nav_bar_layout.addStretch()
        main_layout.addWidget(nav_bar_widget)

        # Stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create pages
        self.create_inventory_page()
        self.create_billing_page()
        self.create_orders_page()
        self.create_alerts_page()
        self.create_sales_page()
        self.create_settings_page()

        # Set initial page
        self.display_page(0)

    def update_navbar_highlight(self, index):
        """Update navbar button highlights"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def display_page(self, index):
        """Display the selected page"""
        self.stacked_widget.setCurrentIndex(index)
        self.update_navbar_highlight(index)

    def create_inventory_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
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
        search_label.setStyleSheet('font-size: 16px; margin-right: 8px;')
        header_layout.addWidget(search_label)
        self.inventory_search_box = QLineEdit()
        self.inventory_search_box.setPlaceholderText("Search by name, barcode, or manufacturer...")
        self.inventory_search_box.setFixedWidth(250)
        self.inventory_search_box.textChanged.connect(self.filter_inventory_table)
        header_layout.addWidget(self.inventory_search_box)

        # Inventory action buttons
        for btn in [
            ("Add Medicine", self.open_add_medicine_dialog),
            ("Scan Barcode", self.open_barcode_scanner),
            ("Generate Order", self.generate_order),
            ("Bulk Threshold Settings", lambda: self.show_inventory_panel("threshold")),
            ("Quick Add Stock", lambda: self.show_inventory_panel("quick_add")),
            ("Delete", self.delete_selected_inventory_row),
            ("Clear Inventory", self.clear_inventory),
        ]:
            b = QPushButton(btn[0])
            b.setMinimumHeight(36)
            b.clicked.connect(btn[1])
            header_layout.addWidget(b)

        layout.addLayout(header_layout)

        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Quantity", "Threshold", "Expiry", "Manufacturer", "Price"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.cellDoubleClicked.connect(self.on_inventory_cell_double_clicked)
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
        from dialogs import BulkThresholdDialog, QuickAddStockDialog
        self.bulk_threshold_widget = BulkThresholdDialog([], parent=self)
        self.quick_add_stock_widget = QuickAddStockDialog([], parent=self)
        self.inventory_panel.addWidget(self.bulk_threshold_widget)
        self.inventory_panel.addWidget(self.quick_add_stock_widget)
        self.inventory_panel.setCurrentIndex(-1)
        panel_frame.setVisible(False)
        self.all_medicines = []
        self.refresh_inventory_table()
        self.stacked_widget.addWidget(page)

    def create_billing_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Billing")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        for btn in [
            ("Add Medicine", self.open_billing_add_medicine_dialog),
            ("Scan Barcode", self.scan_billing_barcode),
            ("Complete Sale", self.complete_sale),
            ("Clear Bill", self.clear_bill),
        ]:
            b = QPushButton(btn[0])
            b.setMinimumHeight(40)
            b.clicked.connect(btn[1])
            header_layout.addWidget(b)
        layout.addLayout(header_layout)

        # Billing table
        self.billing_table = QTableWidget()
        self.billing_table.setColumnCount(5)
        self.billing_table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Quantity", "Price", "Total"
        ])
        self.billing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.billing_table.setAlternatingRowColors(True)
        self.billing_table.itemChanged.connect(self._on_billing_table_item_changed)
        self.billing_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.billing_table)

        # Info and summary layout
        info_summary_layout = QHBoxLayout()
        info_summary_layout.setSpacing(16)

        # Left: Customer info and bill summary (vertical)
        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(12)
        # Customer info
        customer_group = QGroupBox("Customer Information")
        customer_group.setMinimumWidth(350)
        customer_group.setStyleSheet("QGroupBox { padding: 12px 16px 12px 16px; margin-top: 8px; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px 0 8px; }")
        customer_layout = QFormLayout(customer_group)
        customer_layout.setContentsMargins(8, 8, 8, 8)
        customer_layout.setSpacing(10)
        self.customer_name = QLineEdit()
        self.customer_phone = QLineEdit()
        self.customer_email = QLineEdit()
        customer_layout.addRow("Name:", self.customer_name)
        customer_layout.addRow("Phone:", self.customer_phone)
        customer_layout.addRow("Email:", self.customer_email)
        left_vbox.addWidget(customer_group)
        # Bill summary below
        total_group = QGroupBox("Bill Summary")
        total_group.setMinimumWidth(220)
        total_group.setMaximumWidth(260)
        total_group.setStyleSheet("QGroupBox { padding: 12px 16px 12px 16px; margin-top: 8px; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px 0 8px; }")
        total_layout = QVBoxLayout(total_group)
        total_layout.setContentsMargins(8, 8, 8, 8)
        total_layout.setSpacing(10)
        self.total_label = QLabel("Total: ₹0.00")
        self.total_label.setStyleSheet(self.get_bill_summary_total_stylesheet())
        total_layout.addWidget(self.total_label)
        left_vbox.addWidget(total_group)
        left_vbox.addStretch()
        info_summary_layout.addLayout(left_vbox, 2)

        # Right: Recent Bills
        history_group = QGroupBox("Recent Bills")
        history_group.setStyleSheet("QGroupBox { padding: 12px 16px 12px 16px; margin-top: 8px; } QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 8px 0 8px; }")
        history_layout = QVBoxLayout(history_group)
        history_layout.setContentsMargins(8, 8, 8, 8)
        history_layout.setSpacing(10)
        self.billing_history_list = QListWidget()
        history_layout.addWidget(self.billing_history_list)
        info_summary_layout.addWidget(history_group, 1)

        layout.addLayout(info_summary_layout)
        self.billing_items = []
        self._refresh_billing_history()
        self.stacked_widget.addWidget(page)

    def create_orders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Orders Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        create_order_btn = QPushButton("Create Order")
        create_order_btn.setMinimumHeight(40)
        create_order_btn.clicked.connect(self.generate_order)
        header_layout.addWidget(create_order_btn)
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
        self.refresh_orders_table()
        self.stacked_widget.addWidget(page)

    def create_alerts_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Low Stock Alerts")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        send_alerts_btn = QPushButton("Send Alerts")
        send_alerts_btn.setMinimumHeight(40)
        send_alerts_btn.clicked.connect(self.send_low_stock_alerts)
        header_layout.addWidget(send_alerts_btn)
        layout.addLayout(header_layout)
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Medicine", "Current Stock", "Threshold", "Status", "Action"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.alerts_table)
        self.refresh_alerts_table()
        self.stacked_widget.addWidget(page)

    def create_sales_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Sales Reports")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        export_btn = QPushButton("Export CSV")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self._export_monthly_sales_csv)
        header_layout.addWidget(export_btn)
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
        self._refresh_monthly_sales()
        self.stacked_widget.addWidget(page)

    def create_settings_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Left: Settings buttons
        button_panel = QWidget()
        button_layout = QVBoxLayout(button_panel)
        button_layout.setSpacing(16)
        button_layout.setAlignment(Qt.AlignTop)
        notification_btn = QPushButton("Notification Settings")
        notification_btn.setMinimumHeight(50)
        notification_btn.clicked.connect(lambda: self.show_settings_panel("notification"))
        button_layout.addWidget(notification_btn)
        pharmacy_btn = QPushButton("Pharmacy Details")
        pharmacy_btn.setMinimumHeight(50)
        pharmacy_btn.clicked.connect(lambda: self.show_settings_panel("pharmacy"))
        button_layout.addWidget(pharmacy_btn)
        button_layout.addStretch()
        layout.addWidget(button_panel, 0)
        # Right: Settings panel area (QStackedWidget)
        self.settings_panel = QStackedWidget()
        layout.addWidget(self.settings_panel, 1)
        from dialogs import NotificationSettingsDialog, PharmacyDetailsDialog
        self.notification_settings_widget = NotificationSettingsDialog(parent=self)
        self.pharmacy_details_widget = PharmacyDetailsDialog(parent=self)
        self.settings_panel.addWidget(self.notification_settings_widget)
        self.settings_panel.addWidget(self.pharmacy_details_widget)
        self.settings_panel.setCurrentIndex(-1)
        self.stacked_widget.addWidget(page)

    def show_settings_panel(self, panel_name):
        """Show the selected settings panel in the settings page."""
        if panel_name == "notification":
            self.settings_panel.setCurrentIndex(0)
        elif panel_name == "pharmacy":
            self.settings_panel.setCurrentIndex(1)

    def show_inventory_panel(self, panel_name):
        """Show the selected inventory panel in the inventory page, always with up-to-date inventory."""
        from PyQt5.QtWidgets import QFrame

        from db import get_all_medicines
        from dialogs import BulkThresholdDialog, QuickAddStockDialog
        panel_frame = self.inventory_panel.parentWidget()
        if panel_name == "threshold":
            medicines = get_all_medicines()
            # Remove old widget and add a new one
            if self.inventory_panel.count() > 0:
                old_widget = self.inventory_panel.widget(0)
                self.inventory_panel.removeWidget(old_widget)
                old_widget.deleteLater()
            new_widget = BulkThresholdDialog(medicines, parent=self)
            self.inventory_panel.insertWidget(0, new_widget)
            self.inventory_panel.setCurrentIndex(0)
            panel_frame.setVisible(True)
        elif panel_name == "quick_add":
            medicines = get_all_medicines()
            # Remove old widget and add a new one
            if self.inventory_panel.count() > 1:
                old_widget = self.inventory_panel.widget(1)
                self.inventory_panel.removeWidget(old_widget)
                old_widget.deleteLater()
            new_widget = QuickAddStockDialog(medicines, parent=self)
            self.inventory_panel.insertWidget(1, new_widget)
            self.inventory_panel.setCurrentIndex(1)
            panel_frame.setVisible(True)
        else:
            panel_frame.setVisible(False)

    def refresh_inventory_table(self):
        """Refresh the inventory table with current data and update the all_medicines cache"""
        from db import get_all_medicines
        self.all_medicines = get_all_medicines()
        self.filter_inventory_table()

    def filter_inventory_table(self):
        """Filter the inventory table based on the search box text"""
        query = self.inventory_search_box.text().strip().lower() if hasattr(self, 'inventory_search_box') else ''
        filtered = []
        for med in self.all_medicines:
            if (
                query in med.name.lower() or
                query in med.barcode.lower() or
                (med.manufacturer and query in med.manufacturer.lower())
            ):
                filtered.append(med)
        self.inventory_table.setRowCount(len(filtered))
        for i, medicine in enumerate(filtered):
            self.inventory_table.setItem(i, 0, QTableWidgetItem(medicine.barcode))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(medicine.name))
            self.inventory_table.setItem(i, 2, QTableWidgetItem(str(medicine.quantity)))
            self.inventory_table.setItem(i, 3, QTableWidgetItem(str(getattr(medicine, 'threshold', 10))))
            self.inventory_table.setItem(i, 4, QTableWidgetItem(str(medicine.expiry) if medicine.expiry else "N/A"))
            self.inventory_table.setItem(i, 5, QTableWidgetItem(medicine.manufacturer or "N/A"))
            self.inventory_table.setItem(i, 6, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))

    def on_inventory_cell_double_clicked(self, row, column):
        """Handle double-click on inventory table"""
        barcode = self.inventory_table.item(row, 0).text()
        medicines = get_all_medicines()
        medicine = next((m for m in medicines if m.barcode == barcode), None)
        
        if medicine:
            dialog = EditMedicineDialog(medicine, self)
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_inventory_table()

    def open_add_medicine_dialog(self):
        """Open the add medicine dialog"""
        dialog = AddMedicineDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            success, error = add_medicine(
                data['barcode'], data['name'], data['quantity'],
                data['expiry'], data['manufacturer'], data['price'], data['threshold']
            )
            if success:
                self.refresh_inventory_table()
                QMessageBox.information(self, "Success", "Medicine added successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add medicine: {error}")

    def open_barcode_scanner(self):
        """Open the barcode scanner dialog"""
        dialog = BarcodeScannerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            barcode = dialog.get_barcode()
            if barcode:
                self.open_add_medicine_dialog(barcode)

    def generate_order(self):
        """Generate order for low stock medicines"""
        low_stock_medicines = get_low_stock_medicines()
        if not low_stock_medicines:
            QMessageBox.information(self, "No Orders Needed", "All medicines have sufficient stock.")
            return
        
        dialog = OrderQuantityDialog(low_stock_medicines, self)
        if dialog.exec_() == QDialog.Accepted:
            quantities = dialog.get_order_quantities()
            # Generate order logic here
            QMessageBox.information(self, "Order Generated", "Order has been generated successfully!")

    def set_theme_from_menu(self, theme):
        """Set theme from menu"""
        set_theme(theme)
        self.theme = theme
        self.setStyleSheet(get_stylesheet())
        # Update all text styles
        self.update_all_text_styles()

    def get_navbar_button_stylesheet(self):
        """Get navbar button stylesheet based on current theme"""
        if self.theme == 'dark':
            return '''
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                    color: #D4D4D4;
                }
                QPushButton:checked {
                    color: #ffd600;
                    background-color: #404040;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    color: #ffffff;
                    background-color: #505050;
                    border-radius: 4px;
                }
            '''
        else:
            return '''
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    border: none;
                    background: transparent;
                    color: #333333;
                }
                QPushButton:checked {
                    color: #1976d2;
                    background-color: #B3B3B3;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    color: #1976d2;
                    background-color: #F8F8F8;
                    border-radius: 4px;
                }
            '''

    def update_navbar_styles(self):
        """Update navbar button styles when theme changes"""
        for btn in self.nav_buttons:
            btn.setStyleSheet(self.get_navbar_button_stylesheet())

    def get_pharmacy_name_stylesheet(self):
        """Get pharmacy name stylesheet based on current theme"""
        if self.theme == 'dark':
            return 'font-size: 28px; font-weight: bold; color: #D4D4D4; margin: 18px 0 24px 0;'
        else:
            return 'font-size: 28px; font-weight: bold; color: #333333; margin: 18px 0 24px 0;'

    def get_page_title_stylesheet(self, accent_color=None):
        """Get page title stylesheet based on current theme with accent color"""
        if self.theme == 'dark':
            return 'font-size: 24px; font-weight: bold; color: #D4D4D4;'
        else:
            # Use blue accent for page titles in light mode
            return 'font-size: 24px; font-weight: bold; color: #1976d2;'

    def get_bill_summary_total_stylesheet(self):
        """Get stylesheet for the bill summary total label based on the current theme."""
        if self.theme == 'dark':
            return 'font-size: 18px; font-weight: bold; color: #D4D4D4;'
        else:
            return 'font-size: 18px; font-weight: bold; color: #1976d2;'

    def update_all_text_styles(self):
        """Update all text and button styles when theme changes"""
        # Update pharmacy name
        self.pharmacy_name_label.setStyleSheet(self.get_pharmacy_name_stylesheet())
        # Update navbar styles
        self.update_navbar_styles()
        # Update all page titles and buttons
        for i in range(self.stacked_widget.count()):
            page = self.stacked_widget.widget(i)
            self.apply_theme_to_buttons(page)
            # Update page title color
            for child in page.findChildren(QLabel):
                if child.text() in ["Inventory Management", "Billing", "Orders Management", "Low Stock Alerts", "Sales Reports", "Settings"]:
                    child.setStyleSheet(self.get_page_title_stylesheet(""))
                if child is getattr(self, 'total_label', None):
                    child.setStyleSheet(self.get_bill_summary_total_stylesheet())
        # Update icon colors for nav buttons
        icon_color = '#FFFFFF' if get_theme() == 'dark' else '#000000'
        nav_icons = [
            qta.icon('fa5s.pills', color=icon_color),
            qta.icon('fa5s.cash-register', color=icon_color),
            qta.icon('fa5s.file-invoice', color=icon_color),
            qta.icon('fa5s.exclamation-triangle', color=icon_color),
            qta.icon('fa5s.chart-line', color=icon_color),
            qta.icon('fa5s.cog', color=icon_color),
        ]
        for btn, icon in zip(self.nav_buttons, nav_icons):
            btn.setIcon(icon)

    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Medibit", 
                         "Medibit - Pharmacy Management System\n\n"
                         "Version 1.0\n"
                         "A comprehensive solution for pharmacy inventory and billing management.\n\n"
                         "Developed by Octobit8")

    def send_low_stock_alerts(self):
        """Send low stock alerts"""
        low_stock_medicines = get_low_stock_medicines()
        if not low_stock_medicines:
            QMessageBox.information(self, "No Alerts", "No medicines are below threshold.")
            return
        
        results = self.notification_manager.send_all_alerts(low_stock_medicines)
        
        # Show results
        message = "Alert results:\n\n"
        for channel, success, msg in results:
            status = "✅ Sent" if success else "❌ Failed"
            message += f"{channel}: {status}\n{msg}\n\n"
        
        QMessageBox.information(self, "Alert Results", message)

    def open_notification_settings(self):
        """Open notification settings dialog"""
        dialog = NotificationSettingsDialog(self)
        dialog.exec_()

    def update_pharmacy_name_label(self):
        """Update the pharmacy name label with the latest name from settings."""
        try:
            details = get_pharmacy_details()
            print("DEBUG: pharmacy details returned:", details)
            # Try both dict and object access
            if details:
                if isinstance(details, dict):
                    pharmacy_name = details.get('name', '').strip()
                else:
                    pharmacy_name = getattr(details, 'name', '').strip()
            else:
                pharmacy_name = ''
            print("DEBUG: pharmacy_name:", pharmacy_name)
            if not pharmacy_name:
                pharmacy_name = 'Pharmacy'
            self.pharmacy_name_label.setText(pharmacy_name)
            print("DEBUG: Set pharmacy name label to:", pharmacy_name)
        except Exception as e:
            print("DEBUG: Exception in update_pharmacy_name_label:", e)
            self.pharmacy_name_label.setText('Pharmacy')

    def open_pharmacy_details(self):
        """Open pharmacy details dialog"""
        dialog = PharmacyDetailsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_pharmacy_name_label()

    def open_bulk_threshold_dialog(self):
        """Open bulk threshold dialog"""
        medicines = get_all_medicines()
        if not medicines:
            QMessageBox.information(self, "No Medicines", "No medicines found in inventory.")
            return
        
        dialog = BulkThresholdDialog(medicines, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_inventory_table()

    def open_quick_add_stock_dialog(self):
        """Open quick add stock dialog"""
        medicines = get_all_medicines()
        if not medicines:
            QMessageBox.information(self, "No Medicines", "No medicines found in inventory.")
            return
        
        dialog = QuickAddStockDialog(medicines, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_inventory_table()

    # Billing methods
    def scan_billing_barcode(self):
        """Scan barcode for billing"""
        dialog = BarcodeScannerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            barcode = dialog.get_barcode()
            if barcode:
                self._add_billing_item(barcode)

    def _add_billing_item(self, barcode):
        """Add item to billing table by barcode"""
        # Look up medicine by barcode
        from db import get_medicine_by_barcode
        medicine = get_medicine_by_barcode(barcode)
        
        if not medicine:
            QMessageBox.warning(self, "Not Found", f"No medicine found with barcode: {barcode}")
            return
        
        # Check if already in billing table
        for i in range(self.billing_table.rowCount()):
            if self.billing_table.item(i, 0).text() == barcode:
                QMessageBox.information(self, "Already Added", f"{medicine.name} is already in the bill.")
                return
        
        # Add to billing table
        row = self.billing_table.rowCount()
        self.billing_table.insertRow(row)
        
        self.billing_table.setItem(row, 0, QTableWidgetItem(barcode))
        self.billing_table.setItem(row, 1, QTableWidgetItem(medicine.name))
        self.billing_table.setItem(row, 2, QTableWidgetItem("1"))
        self.billing_table.setItem(row, 3, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))
        self.billing_table.setItem(row, 4, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))
        
        self._refresh_billing_table()

    def _refresh_billing_table(self):
        """Refresh billing table totals"""
        total = 0
        for row in range(self.billing_table.rowCount()):
            try:
                quantity = int(self.billing_table.item(row, 2).text())
                price = float(self.billing_table.item(row, 3).text().replace('₹', ''))
                item_total = quantity * price
                self.billing_table.setItem(row, 4, QTableWidgetItem(f"₹{item_total:.2f}"))
                total += item_total
            except (ValueError, AttributeError):
                pass
        
        self.total_label.setText(f"Total: ₹{total:.2f}")

    def _on_billing_table_item_changed(self, item):
        """Handle billing table item changes"""
        # Only handle quantity column
        if item.column() == 2:
            try:
                quantity = int(item.text())
                if quantity < 0:
                    item.setText("0")
                    quantity = 0
                row = item.row()
                price_item = self.billing_table.item(row, 3)
                if price_item is None or not price_item.text():
                    price = 0.0
                else:
                    price = float(price_item.text().replace('₹', ''))
                total = quantity * price
                self.billing_table.setItem(row, 4, QTableWidgetItem(f"₹{total:.2f}"))
                self._refresh_billing_table()
            except ValueError:
                item.setText("0")

    def _refresh_billing_history(self):
        """Refresh billing history list"""
        # Clear layout
        for i in reversed(range(self.billing_history_list.count())):
            self.billing_history_list.takeItem(i)
        
        # Get recent bills
        bills = get_all_bills()
        for bill in bills[-10:]:  # Show last 10 bills
            item_text = f"Bill #{bill.id} - {bill.timestamp} - ₹{bill.total}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, bill.id)
            self.billing_history_list.addItem(item)

    def _refresh_monthly_sales(self):
        """Refresh monthly sales table"""
        sales_data = get_monthly_sales()
        self.sales_table.setRowCount(len(sales_data))
        
        for i, (month, total, count, avg) in enumerate(sales_data):
            self.sales_table.setItem(i, 0, QTableWidgetItem(month))
            # Convert total to float if it's a string
            try:
                total_float = float(total) if isinstance(total, str) else total
                self.sales_table.setItem(i, 1, QTableWidgetItem(f"₹{total_float:.2f}"))
            except (ValueError, TypeError):
                self.sales_table.setItem(i, 1, QTableWidgetItem(str(total)))
            
            self.sales_table.setItem(i, 2, QTableWidgetItem(str(count)))
            
            # Convert avg to float if it's a string
            try:
                avg_float = float(avg) if isinstance(avg, str) else avg
                self.sales_table.setItem(i, 3, QTableWidgetItem(f"₹{avg_float:.2f}"))
            except (ValueError, TypeError):
                self.sales_table.setItem(i, 3, QTableWidgetItem(str(avg)))

    def _export_monthly_sales_csv(self):
        """Export monthly sales to CSV"""
        try:
            sales_data = get_monthly_sales()
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Monthly Sales", "monthly_sales.csv", "CSV Files (*.csv)"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Month', 'Total Sales', 'Number of Bills', 'Average Bill'])
                    for month, total, count, avg in sales_data:
                        # Convert total and avg to float if they're strings
                        try:
                            total_float = float(total) if isinstance(total, str) else total
                            avg_float = float(avg) if isinstance(avg, str) else avg
                            writer.writerow([month, f"₹{total_float:.2f}", count, f"₹{avg_float:.2f}"])
                        except (ValueError, TypeError):
                            writer.writerow([month, str(total), count, str(avg)])
                
                QMessageBox.information(self, "Success", f"Sales data exported to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export sales data: {str(e)}")

    def complete_sale(self):
        """Complete the sale and generate receipt"""
        if self.billing_table.rowCount() == 0:
            QMessageBox.warning(self, "Empty Bill", "Please add items to the bill first.")
            return
        
        # Get customer info from inline fields
        customer_data = {
            'name': self.customer_name.text(),
            'phone': self.customer_phone.text(),
            'email': self.customer_email.text()
        }
        
        # Calculate total
        total = 0
        items = []
        for row in range(self.billing_table.rowCount()):
            barcode = self.billing_table.item(row, 0).text()
            name = self.billing_table.item(row, 1).text()
            quantity = int(self.billing_table.item(row, 2).text())
            price = float(self.billing_table.item(row, 3).text().replace('₹', ''))
            item_total = quantity * price
            
            items.append({
                'barcode': barcode,
                'name': name,
                'quantity': quantity,
                'price': price,
                'subtotal': item_total
            })
            total += item_total
        
        # Save bill to database
        timestamp = datetime.datetime.now()
        try:
            add_bill(timestamp, total, items)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save bill: {str(e)}")
            return
        
        # Update medicine quantities
        for item in items:
            from db import get_medicine_by_barcode, update_medicine_quantity
            medicine = get_medicine_by_barcode(item['barcode'])
            if medicine:
                new_quantity = medicine.quantity - item['quantity']
                if new_quantity < 0:
                    new_quantity = 0
                update_medicine_quantity(item['barcode'], new_quantity)
        
        # Generate receipt
        receipt_path = self._generate_receipt(timestamp, items, total)
        
        # Send receipt via WhatsApp and Email
        try:
            # Use timestamp as receipt_id for uniqueness
            receipt_id = timestamp.strftime('%Y%m%d_%H%M%S')
            customer_info = dict(customer_data)
            customer_info['items'] = items
            customer_info['total'] = total
            print("Sending receipt to customer:", customer_info)
            results = self.receipt_manager.send_receipt_to_customer(customer_info, items, total, timestamp, receipt_id)
            print("Receipt send results:", results)
            # Show results in a dialog
            result_msg = '\n'.join([f"{channel}: {'Success' if success else 'Failed'} - {msg}" for channel, success, msg in results])
            QMessageBox.information(self, "Receipt Notification", result_msg)
        except Exception as e:
            import traceback
            print("Exception during receipt notification:", traceback.format_exc())
            QMessageBox.warning(self, "Notification Error", f"Failed to send receipt notifications: {str(e)}")
        
        # Clear bill
        self.clear_bill()
        
        # Show success message
        QMessageBox.information(self, "Sale Complete", 
                              f"Sale completed successfully!\nTotal: ₹{total:.2f}")
        
        # Refresh tables
        self.refresh_inventory_table()
        self._refresh_billing_history()
        self._refresh_monthly_sales()

    def _generate_receipt(self, timestamp, items, total):
        """Generate receipt for the sale"""
        # Get pharmacy details
        details = get_pharmacy_details()
        pharmacy_name = details.name if details and hasattr(details, 'name') else 'Pharmacy'
        pharmacy_address = details.address if details and hasattr(details, 'address') else ''
        pharmacy_phone = details.phone if details and hasattr(details, 'phone') else ''
        
        # Create receipt content
        receipt_content = f"""
{pharmacy_name.upper()}
{pharmacy_address}
Phone: {pharmacy_phone}
Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
{'='*40}

Items:
"""
        
        for item in items:
            receipt_content += f"{item['name']}\n"
            receipt_content += f"  {item['quantity']} x ₹{item['price']:.2f} = ₹{item['subtotal']:.2f}\n"
        
        receipt_content += f"""
{'='*40}
Total: ₹{total:.2f}
{'='*40}

Thank you for your purchase!
"""
        
        # Save receipt to file
        receipt_dir = "receipts"
        if not os.path.exists(receipt_dir):
            os.makedirs(receipt_dir)
        
        receipt_filename = f"receipt_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        receipt_path = os.path.join(receipt_dir, receipt_filename)
        
        with open(receipt_path, 'w', encoding='utf-8') as f:
            f.write(receipt_content)
        
        return receipt_path

    def clear_bill(self):
        """Clear the current bill"""
        self.billing_table.setRowCount(0)
        self.customer_name.clear()
        self.customer_phone.clear()
        self.customer_email.clear()
        self.total_label.setText("Total: ₹0.00")

    def refresh_orders_table(self):
        """Refresh the orders table"""
        orders = get_all_orders()
        self.orders_table.setRowCount(len(orders))
        for i, order in enumerate(orders):
            self.orders_table.setItem(i, 0, QTableWidgetItem(str(order.id)))
            self.orders_table.setItem(i, 1, QTableWidgetItem(str(order.timestamp)))
            self.orders_table.setItem(i, 2, QTableWidgetItem(str(getattr(order, 'supplier', 'N/A'))))
            self.orders_table.setItem(i, 3, QTableWidgetItem(str(len(getattr(order, 'meds', [])))))
            self.orders_table.setItem(i, 4, QTableWidgetItem(str(getattr(order, 'total', 'N/A'))))
            self.orders_table.setItem(i, 5, QTableWidgetItem(str(getattr(order, 'status', 'N/A'))))

    def refresh_alerts_table(self):
        """Refresh the alerts table"""
        low_stock_medicines = get_low_stock_medicines()
        self.alerts_table.setRowCount(len(low_stock_medicines))
        
        for i, medicine in enumerate(low_stock_medicines):
            self.alerts_table.setItem(i, 0, QTableWidgetItem(medicine.name))
            self.alerts_table.setItem(i, 1, QTableWidgetItem(str(medicine.quantity)))
            self.alerts_table.setItem(i, 2, QTableWidgetItem(str(getattr(medicine, 'threshold', 10))))
            
            # Status
            if medicine.quantity == 0:
                status = "Out of Stock"
                status_color = QColor(255, 0, 0)  # Red
            else:
                status = "Low Stock"
                status_color = QColor(255, 165, 0)  # Orange
            
            status_item = QTableWidgetItem(status)
            status_item.setBackground(status_color)
            self.alerts_table.setItem(i, 3, status_item)
            
            # Action button
            action_btn = QPushButton("Set Threshold")
            action_btn.clicked.connect(lambda checked, med=medicine: self._open_threshold_dialog(med))
            self.alerts_table.setCellWidget(i, 4, action_btn)

    def _open_threshold_dialog(self, medicine):
        """Open threshold setting dialog for a specific medicine"""
        dialog = ThresholdSettingDialog(medicine, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_alerts_table()

    def get_button_stylesheet(self):
        """Get general button stylesheet based on current theme"""
        if self.theme == 'dark':
            return '''
                QPushButton {
                    background-color: #404040;
                    color: #D4D4D4;
                    border: 1px solid #606060;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #505050;
                    border-color: #707070;
                }
                QPushButton:pressed {
                    background-color: #303030;
                }
                QPushButton:disabled {
                    background-color: #2B2B2B;
                    color: #808080;
                    border-color: #404040;
                }
            '''
        else:
            return '''
                QPushButton {
                    background-color: #FFFFFF;
                    color: #333333;
                    border: 1px solid #B3B3B3;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F8F8F8;
                    color: #1976d2;
                    border-color: #1976d2;
                }
                QPushButton:pressed {
                    background-color: #B3B3B3;
                }
                QPushButton:disabled {
                    background-color: #F8F8F8;
                    color: #B3B3B3;
                }
            '''

    def apply_theme_to_buttons(self, parent_widget):
        """Recursively apply the theme-based button stylesheet to all QPushButton widgets in the given parent widget."""
        for child in parent_widget.findChildren(QPushButton):
            # Skip navbar buttons (they have their own style)
            if hasattr(self, 'nav_buttons') and child in self.nav_buttons:
                continue
            child.setStyleSheet(self.get_button_stylesheet())

    def open_billing_add_medicine_dialog(self):
        dialog = BillingAddMedicineDialog(self)
        if dialog.exec_() == dialog.Accepted:
            medicine, quantity = dialog.get_selected()
            if medicine and quantity:
                self._add_billing_item_manual(medicine, quantity)

    def _add_billing_item_manual(self, medicine, quantity):
        # Add the selected medicine to the billing table manually
        row = self.billing_table.rowCount()
        self.billing_table.insertRow(row)
        self.billing_table.setItem(row, 0, QTableWidgetItem(medicine.barcode))
        self.billing_table.setItem(row, 1, QTableWidgetItem(medicine.name))
        self.billing_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
        self.billing_table.setItem(row, 3, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))
        total = getattr(medicine, 'price', 0) * quantity
        self.billing_table.setItem(row, 4, QTableWidgetItem(f"₹{total:.2f}"))
        self._refresh_billing_table() 

    def handle_exit(self):
        # Check for unsaved data in all modules
        unsaved = []
        # Billing: unsaved items in billing table
        if hasattr(self, 'billing_table') and self.billing_table.rowCount() > 0:
            unsaved.append("Billing items")
        # Inventory: check for open add/edit dialogs or pending edits (customize as needed)
        if getattr(self, 'inventory_edit_in_progress', False):
            unsaved.append("Inventory edits")
        # Orders: check for open order dialogs or pending edits (customize as needed)
        if getattr(self, 'order_edit_in_progress', False):
            unsaved.append("Order edits")
        # Settings: check for unsaved config changes (customize as needed)
        if getattr(self, 'settings_edit_in_progress', False):
            unsaved.append("Settings changes")
        # Compose warning message
        if unsaved:
            msg = "There are unsaved changes in the following modules:\n- " + "\n- ".join(unsaved) + "\n\nAre you sure you want to exit? Unsaved data may be lost."
            reply = QMessageBox.warning(self, "Exit Warning", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        # Save all data
        self.save_all_data()
        QApplication.quit()

    def save_all_data(self):
        # Billing: Save or discard unsaved billing items
        if hasattr(self, 'billing_table') and self.billing_table.rowCount() > 0:
            self.save_billing_draft()
        else:
            self.clear_billing_table()

        # Inventory: Save or discard unsaved inventory edits
        if getattr(self, 'inventory_edit_in_progress', False):
            self.save_inventory_edits()
            self.inventory_edit_in_progress = False

        # Orders: Save or discard unsaved order edits
        if getattr(self, 'order_edit_in_progress', False):
            self.save_order_edits()
            self.order_edit_in_progress = False

        # Settings: Save or discard unsaved settings changes
        if getattr(self, 'settings_edit_in_progress', False):
            self.save_settings_changes()
            self.settings_edit_in_progress = False

    def save_billing_draft(self):
        # Save billing table as a draft bill to a JSON file
        if hasattr(self, 'billing_table'):
            draft = []
            for row in range(self.billing_table.rowCount()):
                item = {
                    'barcode': self.billing_table.item(row, 0).text() if self.billing_table.item(row, 0) else '',
                    'name': self.billing_table.item(row, 1).text() if self.billing_table.item(row, 1) else '',
                    'quantity': self.billing_table.item(row, 2).text() if self.billing_table.item(row, 2) else '',
                    'price': self.billing_table.item(row, 3).text() if self.billing_table.item(row, 3) else '',
                    'total': self.billing_table.item(row, 4).text() if self.billing_table.item(row, 4) else ''
                }
                draft.append(item)
            try:
                with open('billing_draft.json', 'w', encoding='utf-8') as f:
                    json.dump(draft, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Draft Saved", "Billing items have been saved as a draft bill (billing_draft.json).")
            except Exception as e:
                QMessageBox.warning(self, "Draft Save Failed", f"Failed to save draft: {str(e)}")

    def clear_billing_table(self):
        # Clear the billing table
        if hasattr(self, 'billing_table'):
            self.billing_table.setRowCount(0)
        # Optionally remove the draft file
        if os.path.exists('billing_draft.json'):
            os.remove('billing_draft.json')

    def save_inventory_edits(self):
        # Call inventory model/controller save method if present
        if hasattr(self, 'inventory_model') and hasattr(self.inventory_model, 'save_changes'):
            self.inventory_model.save_changes()
        self.inventory_edit_in_progress = False
        QMessageBox.information(self, "Inventory Saved", "Inventory edits have been saved.")

    def discard_inventory_edits(self):
        # Call inventory model/controller discard method if present
        if hasattr(self, 'inventory_model') and hasattr(self.inventory_model, 'discard_changes'):
            self.inventory_model.discard_changes()
        self.inventory_edit_in_progress = False
        QMessageBox.information(self, "Inventory Discarded", "Inventory edits have been discarded.")

    def save_order_edits(self):
        # Call order model/controller save method if present
        if hasattr(self, 'order_model') and hasattr(self.order_model, 'save_changes'):
            self.order_model.save_changes()
        self.order_edit_in_progress = False
        QMessageBox.information(self, "Orders Saved", "Order edits have been saved.")

    def discard_order_edits(self):
        # Call order model/controller discard method if present
        if hasattr(self, 'order_model') and hasattr(self.order_model, 'discard_changes'):
            self.order_model.discard_changes()
        self.order_edit_in_progress = False
        QMessageBox.information(self, "Orders Discarded", "Order edits have been discarded.")

    def save_settings_changes(self):
        # Call settings model/controller save method if present
        if hasattr(self, 'settings_model') and hasattr(self.settings_model, 'save_changes'):
            self.settings_model.save_changes()
        self.settings_edit_in_progress = False
        QMessageBox.information(self, "Settings Saved", "Settings changes have been saved.")

    def discard_settings_changes(self):
        # Call settings model/controller discard method if present
        if hasattr(self, 'settings_model') and hasattr(self.settings_model, 'discard_changes'):
            self.settings_model.discard_changes()
        self.settings_edit_in_progress = False
        QMessageBox.information(self, "Settings Discarded", "Settings changes have been discarded.")

    def show_license_info_dialog(self):
        from PyQt5.QtWidgets import (QDialog, QLabel, QMessageBox, QPushButton,
                                     QVBoxLayout)
        key = get_license_key()
        if not key:
            QMessageBox.warning(self, "No License", "No license key found.")
            return
        if key == 'TRIAL-000000000000':
            name = 'Trial User'
            install_date = get_installation_date()
            if install_date:
                install_dt = datetime.datetime.strptime(install_date, "%Y-%m-%d")
                days_used = (datetime.datetime.now() - install_dt).days
                days_left = max(0, 7 - days_used)
                exp = (install_dt + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            else:
                days_left = 'Unknown'
                exp = 'Unknown'
            info = f"License Type: Trial\nExpires: {exp}\nDays left: {days_left}"
        else:
            valid, data, err = verify_license_key(key)
            if not valid:
                info = f"Invalid license: {err}"
                name = 'Unknown'
                exp = 'Unknown'
                days_left = 'Unknown'
            else:
                name = data.get('name', 'Unknown')
                exp = data.get('exp', 'Unknown')
                if exp != 'Unknown':
                    exp_date = datetime.datetime.strptime(exp, '%Y-%m-%d').date()
                    days_left = (exp_date - datetime.datetime.now().date()).days
                else:
                    days_left = 'Unknown'
                info = f"Customer: {name}\nExpires: {exp}\nDays left: {days_left}"
        dialog = QDialog(self)
        dialog.setWindowTitle("License Information")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(info))
        update_btn = QPushButton("Update License Key")
        layout.addWidget(update_btn)
        def update_license():
            dialog.close()
            self.prompt_license_dialog(parent=self)
        update_btn.clicked.connect(update_license)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.setLayout(layout)
        dialog.exec_()

    @staticmethod
    def check_license():
        key = get_license_key()
        install_date = get_installation_date()
        if not key or not install_date:
            return False
        # Trial license logic
        if key == 'TRIAL-000000000000':
            try:
                install_dt = datetime.datetime.strptime(install_date, "%Y-%m-%d")
                days_used = (datetime.datetime.now() - install_dt).days
                if days_used > 7:
                    return False
                elif days_used >= 6:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "Trial Expiring", f"Your trial license will expire in {7 - days_used} day(s). Please activate a full license.")
            except Exception:
                return False
            return True
        # HMAC license key logic
        valid, data, err = verify_license_key(key)
        if not valid:
            from PyQt5.QtWidgets import QMessageBox
            if err == 'License expired':
                QMessageBox.critical(None, "License Expired", "Your license has expired. Please contact support.")
            else:
                QMessageBox.critical(None, "Invalid License", f"License error: {err}")
            return False
        # Optionally show customer info or expiry warning
        exp = data.get('exp')
        name = data.get('name')
        if exp:
            exp_date = datetime.datetime.strptime(exp, '%Y-%m-%d').date()
            days_left = (exp_date - datetime.datetime.now().date()).days
            if days_left <= 7:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(None, "License Expiring Soon", f"License for {name} expires in {days_left} day(s). Please renew.")
        return True

    @staticmethod
    def prompt_license_dialog(parent=None):
        import sys

        from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QLabel, QLineEdit,
                                     QMessageBox, QPushButton, QVBoxLayout)
        while True:
            dialog = QDialog(parent)
            dialog.setWindowTitle("License Key Required")
            dialog.setModal(True)
            layout = QVBoxLayout(dialog)
            label = QLabel("Enter your license key to activate Medibit.\n\nThe license is valid until the expiry date encoded in the key.\n\nTo try Medibit, enter: TRIAL-000000000000 (valid for 7 days)")
            layout.addWidget(label)
            key_input = QLineEdit()
            key_input.setMaxLength(256)
            key_input.setPlaceholderText("Enter license key (or TRIAL-000000000000)")
            layout.addWidget(key_input)
            btn_layout = QHBoxLayout()
            activate_btn = QPushButton("Activate")
            quit_btn = QPushButton("Quit")
            btn_layout.addWidget(activate_btn)
            btn_layout.addWidget(quit_btn)
            layout.addLayout(btn_layout)
            def try_activate():
                key = key_input.text().strip()
                if key == 'TRIAL-000000000000':
                    set_license_key(key)
                    if not get_installation_date():
                        set_installation_date(datetime.datetime.now().strftime("%Y-%m-%d"))
                    dialog.accept()
                    return
                # HMAC license key logic
                valid, data, err = verify_license_key(key)
                if not valid:
                    QMessageBox.critical(dialog, "Invalid License", f"License error: {err}")
                    return
                set_license_key(key)
                if not get_installation_date():
                    set_installation_date(datetime.datetime.now().strftime("%Y-%m-%d"))
                dialog.accept()
            def quit_app():
                dialog.done(2)  # Custom code for quit
            activate_btn.clicked.connect(try_activate)
            quit_btn.clicked.connect(quit_app)
            dialog.setLayout(layout)
            result = dialog.exec_()
            if result == QDialog.Accepted:
                if MainWindow.check_license():
                    break
                else:
                    QMessageBox.critical(dialog, "License Error", "License activation failed. Please try again.")
            elif result == 2:
                sys.exit(0)
            # If dialog closed in any other way, re-show dialog 

    def delete_selected_inventory_row(self):
        selected = self.inventory_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")
            return
        barcode = self.inventory_table.item(selected, 0).text()
        reply = QMessageBox.question(self, "Delete Medicine", f"Are you sure you want to delete the selected medicine (barcode: {barcode})?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, error = delete_medicine(barcode)
            if success:
                QMessageBox.information(self, "Deleted", "Medicine deleted successfully.")
                self.refresh_inventory_table()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete medicine: {error}")

    def clear_inventory(self):
        reply = QMessageBox.question(self, "Clear Inventory", "Are you sure you want to delete ALL medicines from inventory? This action cannot be undone.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, result = clear_inventory()
            if success:
                QMessageBox.information(self, "Inventory Cleared", f"All medicines deleted. ({result} items removed)")
                self.refresh_inventory_table()
            else:
                QMessageBox.critical(self, "Error", f"Failed to clear inventory: {result}") 

    def send_daily_sales_summary(self):
        import datetime

        from db import Bill
        from notifications import NotificationManager
        session = None
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(f'sqlite:///pharmacy_inventory.db', echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            bills = session.query(Bill).filter(Bill.timestamp.startswith(today)).all()
            total = sum(bill.total for bill in bills)
            count = len(bills)
            avg = total / count if count else 0
            bill_details = []
            for bill in bills:
                # Extract time from timestamp if possible
                time_str = bill.timestamp[11:16] if len(bill.timestamp) >= 16 else bill.timestamp
                bill_details.append({'time': time_str, 'total': bill.total})
            sales_summary = {'total': total, 'count': count, 'avg': avg}
            notif = NotificationManager()
            email_success, email_msg = notif.send_daily_sales_summary_email(sales_summary, bill_details)
            whatsapp_success, whatsapp_msg = notif.send_daily_sales_summary_whatsapp(sales_summary, bill_details)
            msg = f"Email: {email_msg}\nWhatsApp: {whatsapp_msg}"
            if email_success or whatsapp_success:
                QMessageBox.information(self, "Daily Sales Summary Sent", msg)
            else:
                QMessageBox.warning(self, "Daily Sales Summary Failed", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send daily sales summary: {str(e)}")
        finally:
            if session:
                session.close() 