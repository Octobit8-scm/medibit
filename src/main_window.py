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
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QDoubleSpinBox,
    QInputDialog,
)

from barcode_scanner import BarcodeScannerDialog
from dialogs import (
    AddMedicineDialog,
    BillingAddMedicineDialog,
    BulkThresholdDialog,
    CustomerInfoDialog,
    EditMedicineDialog,
    NotificationSettingsDialog,
    OrderQuantityDialog,
    PharmacyDetailsDialog,
    QuickAddStockDialog,
    SupplierInfoDialog,
    ThresholdSettingDialog,
)
from license_utils import verify_license_key
from order_service import OrderService
from receipt_manager import ReceiptManager
from theme import get_stylesheet
from billing_ui import BillingUi
from inventory_ui import InventoryUi
from orders_ui import OrdersUi
from alerts_ui import AlertsUi
from sales_ui import SalesUi
from settings_ui import SettingsUi
from inventory_service import InventoryService
from billing_service import BillingService
from db import (
    clear_all_bills,
)
from alert_service import AlertService
from settings_service import SettingsService
from config import get_theme
from notifications import NotificationManager

log_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "logs")
if not _os.path.exists(log_dir):
    _os.makedirs(log_dir)
log_file = _os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
logger = logging.getLogger("medibit")

# For drafts
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'drafts'), exist_ok=True)

class MainWindow(QMainWindow):
    """
    Main application window for the Medibit pharmacy management system.
    Handles UI setup, navigation, and delegates business logic to service classes.
    """
    def __init__(self) -> None:
        """
        Initialize the main window, set up UI, services, and status bar.
        """
        super().__init__()
        logger.info("MainWindow initialized")
        self.setWindowTitle("Medibit")
        # Set the window icon to use the medibit logo
        try:
            import os

            # Try to use the existing ICO file first (preferred for Windows
            # taskbar)
            if os.path.exists("medibit.ico"):
                self.setWindowIcon(QIcon("medibit.ico"))
            else:
                # Fallback to JPG if ICO doesn't exist
                icon_pixmap = QPixmap("public/images/medibit_logo.jpg")
                if not icon_pixmap.isNull():
                    # Scale the icon to a reasonable size for taskbar (32x32 pixels)
                    icon_pixmap = icon_pixmap.scaled(
                        32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.setWindowIcon(QIcon(icon_pixmap))
        except:
            # Fallback to default icon if image loading fails
            pass
        self.resize(1000, 600)
        self.setMinimumSize(800, 500)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.theme = get_theme()
        self.notification_manager = (
            NotificationManager()
        )  # Initialize notification manager
        self.receipt_manager = ReceiptManager()  # Add this line
        self.bulk_threshold_dialog = None
        self.quick_add_stock_dialog = None
        self.inventory_service = InventoryService()
        self.billing_service = BillingService()
        self.order_service = OrderService()
        self.alert_service = AlertService()
        self.settings_service = SettingsService()
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

    def _init_menubar(self) -> None:
        """
        Initialize the menu bar with navigation, view, about, license, and reports.
        """
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
        light_action.triggered.connect(lambda: self.set_theme_from_menu("light"))
        dark_action.triggered.connect(lambda: self.set_theme_from_menu("dark"))
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

    def init_ui(self) -> None:
        """
        Set up the main UI layout, navigation bar, and stacked widget pages.
        """
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Pharmacy name above navbar
        self.pharmacy_name_label = QLabel("Pharmacy")
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
        icon_color = "#FFFFFF" if get_theme() == "dark" else "#000000"
        nav_items = [
            ("Inventory", qta.icon("fa5s.pills", color=icon_color)),
            ("Billing", qta.icon("fa5s.cash-register", color=icon_color)),
            ("Orders", qta.icon("fa5s.file-invoice", color=icon_color)),
            ("Alerts", qta.icon("fa5s.exclamation-triangle", color=icon_color)),
            ("Sales", qta.icon("fa5s.chart-line", color=icon_color)),
            ("Settings", qta.icon("fa5s.cog", color=icon_color)),
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

    def update_navbar_highlight(self, index: int) -> None:
        """
        Update navbar button highlights.
        :param index: Index of the selected page
        """
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def display_page(self, index: int) -> None:
        """
        Display the selected page in the stacked widget.
        :param index: Index of the page to display
        """
        self.stacked_widget.setCurrentIndex(index)
        self.update_navbar_highlight(index)

    def create_inventory_page(self) -> None:
        """
        Create and set up the inventory page UI and connect signals.
        """
        self.inventory_ui = InventoryUi(self)
        # Connect buttons to MainWindow methods
        self.inventory_ui.add_medicine_btn.clicked.connect(self.open_add_medicine_dialog)
        self.inventory_ui.scan_barcode_btn.clicked.connect(self.open_barcode_scanner)
        self.inventory_ui.generate_order_btn.clicked.connect(self.generate_order)
        self.inventory_ui.bulk_threshold_btn.clicked.connect(lambda: self.show_inventory_panel("threshold"))
        self.inventory_ui.quick_add_stock_btn.clicked.connect(lambda: self.show_inventory_panel("quick_add"))
        self.inventory_ui.delete_btn.clicked.connect(self.delete_selected_inventory_row)
        self.inventory_ui.clear_inventory_btn.clicked.connect(self.clear_inventory)
        self.inventory_ui.inventory_search_box.textChanged.connect(self.filter_inventory_table)
        self.inventory_ui.inventory_table.cellDoubleClicked.connect(self.on_inventory_cell_double_clicked)
        self.stacked_widget.addWidget(self.inventory_ui)

    def create_billing_page(self) -> None:
        self.billing_ui = BillingUi(self)
        self.stacked_widget.addWidget(self.billing_ui)

    def create_orders_page(self) -> None:
        self.orders_ui = OrdersUi(self)
        self.stacked_widget.addWidget(self.orders_ui)

    def create_alerts_page(self) -> None:
        self.alerts_ui = AlertsUi(self)
        self.stacked_widget.addWidget(self.alerts_ui)

    def create_sales_page(self) -> None:
        self.sales_ui = SalesUi(self)
        self.stacked_widget.addWidget(self.sales_ui)

    def create_settings_page(self) -> None:
        self.settings_ui = SettingsUi(self)
        self.stacked_widget.addWidget(self.settings_ui)

    def view_or_download_bill(self) -> None:
        """
        View or download the selected bill from recent bills, or resume a draft.
        """
        selected_items = self.billing_history_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Bill Selected", "Please select a bill to view or download.")
            return
        selected_item = selected_items[0]
        data = selected_item.data(Qt.UserRole)
        # Resume draft if selected
        if isinstance(data, dict) and data.get('is_draft'):
            draft = data['draft']
            # Restore customer info
            self.customer_name.setText(draft['customer'].get('name', ''))
            self.customer_age.setValue(draft['customer'].get('age', 0))
            gender = draft['customer'].get('gender', 'Male')
            idx = self.customer_gender.findText(gender)
            self.customer_gender.setCurrentIndex(idx if idx != -1 else 0)
            self.customer_phone.setText(draft['customer'].get('phone', ''))
            self.customer_email.setText(draft['customer'].get('email', ''))
            self.customer_address.setText(draft['customer'].get('address', ''))
            # Restore billing table
            self.billing_table.setRowCount(0)
            for item in draft['items']:
                row = self.billing_table.rowCount()
                self.billing_table.insertRow(row)
                for col, key in enumerate(['barcode', 'name', 'quantity', 'price', 'tax', 'discount']):
                    self.billing_table.setItem(row, col, QTableWidgetItem(item.get(key, '')))
                self.billing_table.setItem(row, 6, QTableWidgetItem(""))  # Total will be recalculated
            self._refresh_billing_table()
            QMessageBox.information(self, "Draft Loaded", "Draft bill has been loaded. You can now resume billing.")
            return
        # Otherwise, handle as before
        bill = data
        if not bill:
            QMessageBox.warning(self, "Error", "Could not retrieve bill details.")
            return
        # If bill has a file_path, offer to open or save the PDF
        if hasattr(bill, 'file_path') and bill.file_path:
            from PyQt5.QtWidgets import QFileDialog
            import shutil
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Bill PDF", "bill.pdf", "PDF Files (*.pdf)")
            if save_path:
                try:
                    shutil.copyfile(bill.file_path, save_path)
                    QMessageBox.information(self, "Saved", f"Bill saved to {save_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not save file: {e}")
        else:
            QMessageBox.information(self, "No PDF Available", "No PDF file is available for this bill.")

    def show_settings_panel(self, panel_name: str) -> None:
        """
        Show the selected settings panel in the settings page.
        :param panel_name: Name of the settings panel to show
        """
        if panel_name == "notification":
            self.settings_ui.settings_panel.setCurrentIndex(0)
        elif panel_name == "pharmacy":
            self.settings_ui.settings_panel.setCurrentIndex(1)

    def show_inventory_panel(self, panel_name: str) -> None:
        """
        Show the selected inventory panel in the inventory page, always with up-to-date inventory.
        :param panel_name: Name of the inventory panel to show
        """
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
            new_widget = BulkThresholdDialog(medicines, self)
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
            new_widget = QuickAddStockDialog(medicines, self)
            self.inventory_panel.insertWidget(1, new_widget)
            self.inventory_panel.setCurrentIndex(1)
            panel_frame.setVisible(True)
        else:
            panel_frame.setVisible(False)

    def refresh_inventory_table(self) -> None:
        """
        Refresh the inventory table with current data and update the all_medicines cache.
        """
        self.all_medicines = self.inventory_service.get_all()
        self.filter_inventory_table()

    def filter_inventory_table(self) -> None:
        """
        Filter the inventory table based on the search box text.
        """
        query = (
            self.inventory_search_box.text().strip().lower()
            if hasattr(self, "inventory_search_box")
            else ""
        )
        filtered = self.inventory_service.search(query)
        self.inventory_table.setRowCount(len(filtered))
        for i, medicine in enumerate(filtered):
            self.inventory_table.setItem(i, 0, QTableWidgetItem(medicine.barcode))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(medicine.name))
            self.inventory_table.setItem(i, 2, QTableWidgetItem(str(medicine.quantity)))
            self.inventory_table.setItem(
                i, 3, QTableWidgetItem(str(getattr(medicine, "threshold", 10)))
            )
            self.inventory_table.setItem(
                i,
                4,
                QTableWidgetItem(str(medicine.expiry) if medicine.expiry else "N/A"),
            )
            self.inventory_table.setItem(
                i, 5, QTableWidgetItem(medicine.manufacturer or "N/A")
            )
            self.inventory_table.setItem(
                i, 6, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}")
            )

    def on_inventory_cell_double_clicked(self, row: int, column: int) -> None:
        """
        Handle double-click on inventory table.
        :param row: Row index
        :param column: Column index
        """
        barcode = self.inventory_table.item(row, 0).text()
        medicines = self.inventory_service.get_all()
        medicine = next((m for m in medicines if m.barcode == barcode), None)

        if medicine:
            dialog = EditMedicineDialog(medicine, self)
            if dialog.exec_() == QDialog.Accepted:
                # Save changes using service
                data = dialog.get_data()
                self.inventory_service.update(barcode, data)
                self.refresh_inventory_table()

    def open_add_medicine_dialog(self) -> None:
        """
        Open the add medicine dialog and add a new medicine if accepted.
        """
        dialog = AddMedicineDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            success, error = self.inventory_service.add(data)
            if success:
                self.refresh_inventory_table()
                QMessageBox.information(self, "Success", "Medicine added successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to add medicine: {error}")

    def open_barcode_scanner(self) -> None:
        """
        Open the barcode scanner dialog and add medicine by scanned barcode.
        """
        dialog = BarcodeScannerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            barcode = dialog.get_barcode()
            if barcode:
                self.open_add_medicine_dialog(barcode)

    def generate_order(self) -> None:
        """
        Generate an order for low stock medicines and save it if confirmed.
        """
        low_stock_medicines = self.order_service.get_low_stock()
        if not low_stock_medicines:
            QMessageBox.information(
                self, "No Orders Needed", "All medicines have sufficient stock."
            )
            return
        dialog = OrderQuantityDialog(low_stock_medicines, self)
        if dialog.exec_() == QDialog.Accepted:
            quantities = dialog.get_order_quantities()
            # Prepare order items based on selected quantities
            order_items = []
            for med in low_stock_medicines:
                qty = quantities.get(med.barcode, 0)
                if qty > 0:
                    order_items.append({
                        "barcode": med.barcode,
                        "name": med.name,
                        "quantity": med.quantity,
                        "expiry": med.expiry,
                        "manufacturer": med.manufacturer,
                        "order_quantity": qty,
                    })
            if order_items:
                import datetime
                timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                order_id = int(datetime.datetime.now().timestamp())  # simple unique ID
                pdf_path = self.order_service.generate_order_pdf(order_items, order_id, timestamp_str)
                success, error = self.order_service.add(timestamp_str, pdf_path, order_items)
                if success:
                    QMessageBox.information(self, "Order Generated", "Order has been generated and saved successfully!")
                    self.refresh_orders_table()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to save order: {error}")
            else:
                QMessageBox.warning(self, "No Items", "No order items were selected.")

    def set_theme_from_menu(self, theme: str) -> None:
        """
        Set the application theme from the menu.
        :param theme: Theme string ('light' or 'dark')
        """
        self.settings_service.set_theme(theme)
        self.theme = theme
        self.setStyleSheet(get_stylesheet())
        # Update all text styles
        self.update_all_text_styles()

    def get_navbar_button_stylesheet(self) -> str:
        """
        Get navbar button stylesheet based on current theme.
        :return: Stylesheet string
        """
        if self.theme == "dark":
            return """
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
            """
        else:
            return """
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
            """

    def update_navbar_styles(self) -> None:
        """
        Update navbar button styles when theme changes
        """
        for btn in self.nav_buttons:
            btn.setStyleSheet(self.get_navbar_button_stylesheet())

    def get_pharmacy_name_stylesheet(self) -> str:
        """
        Get pharmacy name stylesheet based on current theme.
        :return: Stylesheet string
        """
        if self.theme == "dark":
            return "font-size: 28px; font-weight: bold; color: #D4D4D4; margin: 18px 0 24px 0;"
        else:
            return "font-size: 28px; font-weight: bold; color: #333333; margin: 18px 0 24px 0;"

    def get_page_title_stylesheet(self, accent_color=None) -> str:
        """
        Get page title stylesheet based on current theme with accent color.
        :param accent_color: Optional accent color for the page title
        :return: Stylesheet string
        """
        if self.theme == "dark":
            return "font-size: 24px; font-weight: bold; color: #D4D4D4;"
        else:
            # Use blue accent for page titles in light mode
            return "font-size: 24px; font-weight: bold; color: #1976d2;"

    def get_bill_summary_total_stylesheet(self) -> str:
        """
        Get stylesheet for the bill summary total label based on the current theme.
        :return: Stylesheet string
        """
        if self.theme == "dark":
            return "font-size: 12px; font-weight: bold; color: #D4D4D4;"
        else:
            return "font-size: 12px; font-weight: bold; color: #1976d2;"

    def get_section_title_stylesheet(self) -> str:
        """
        Get section title stylesheet: same color as page title, 16px, bold.
        :return: Stylesheet string
        """
        if self.theme == "dark":
            return "font-size: 16px; font-weight: bold; color: #D4D4D4;"
        else:
            return "font-size: 16px; font-weight: bold; color: #1976d2;"

    def update_all_text_styles(self) -> None:
        """
        Update all text and button styles when theme changes
        """
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
                if child.text() in [
                    "Inventory Management",
                    "Billing",
                    "Orders Management",
                    "Low Stock Alerts",
                    "Sales Reports",
                    "Settings",
                ]:
                    child.setStyleSheet(self.get_page_title_stylesheet(""))
                if child is getattr(self, "total_label", None):
                    child.setStyleSheet(self.get_bill_summary_total_stylesheet())
        # Update icon colors for nav buttons
        icon_color = "#FFFFFF" if get_theme() == "dark" else "#000000"
        nav_icons = [
            qta.icon("fa5s.pills", color=icon_color),
            qta.icon("fa5s.cash-register", color=icon_color),
            qta.icon("fa5s.file-invoice", color=icon_color),
            qta.icon("fa5s.exclamation-triangle", color=icon_color),
            qta.icon("fa5s.chart-line", color=icon_color),
            qta.icon("fa5s.cog", color=icon_color),
        ]
        for btn, icon in zip(self.nav_buttons, nav_icons):
            btn.setIcon(icon)

    def show_about_dialog(self) -> None:
        """
        Show about dialog
        """
        QMessageBox.about(
            self,
            "About Medibit",
            "Medibit - Pharmacy Management System\n\n"
            "Version 1.0\n"
            "A comprehensive solution for pharmacy inventory and billing management.\n\n"
            "Developed by Octobit8",
        )

    def send_low_stock_alerts(self) -> None:
        """
        Send low stock alerts
        """
        success, msg = self.alert_service.send_all_alerts()
        if success:
            QMessageBox.information(self, "Alerts Sent", msg)
        else:
            QMessageBox.warning(self, "Alerts Failed", msg)

    def open_notification_settings(self) -> None:
        dialog = NotificationSettingsDialog(self)
        dialog.exec_()

    def update_pharmacy_name_label(self) -> None:
        """
        Update the pharmacy name label with the latest name from settings.
        """
        try:
            details = get_pharmacy_details()
            if details:
                if isinstance(details, dict):
                    pharmacy_name = details.get("name", "").strip()
                else:
                    pharmacy_name = getattr(details, "name", "").strip()
            else:
                pharmacy_name = ""
            if not pharmacy_name:
                pharmacy_name = "Pharmacy"
            self.pharmacy_name_label.setText(pharmacy_name)
        except Exception as e:
            self.pharmacy_name_label.setText("Pharmacy")

    def open_pharmacy_details(self) -> None:
        dialog = PharmacyDetailsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_pharmacy_name_label()

    def open_bulk_threshold_dialog(self) -> None:
        """
        Open bulk threshold dialog
        """
        medicines = get_all_medicines()
        if not medicines:
            QMessageBox.information(
                self, "No Medicines", "No medicines found in inventory."
            )
            return

        self.bulk_threshold_dialog = BulkThresholdDialog(medicines, self)
        self.bulk_threshold_dialog.exec_()
        self.bulk_threshold_dialog = None
        self.refresh_inventory_table()

    def open_quick_add_stock_dialog(self) -> None:
        """
        Open quick add stock dialog
        """
        medicines = get_all_medicines()
        if not medicines:
            QMessageBox.information(
                self, "No Medicines", "No medicines found in inventory."
            )
            return

        self.quick_add_stock_dialog = QuickAddStockDialog(medicines, self)
        if self.quick_add_stock_dialog.exec_() == QDialog.Accepted:
            self.refresh_inventory_table()
        self.quick_add_stock_dialog = None

    # Billing methods
    def scan_billing_barcode(self) -> None:
        """
        Scan barcode for billing
        """
        dialog = BarcodeScannerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            barcode = dialog.get_barcode()
            if barcode:
                self._add_billing_item(barcode)

    def _add_billing_item(self, barcode: str) -> None:
        """
        Add item to billing table by barcode
        :param barcode: Barcode of the medicine to add
        """
        # Look up medicine by barcode
        from db import get_medicine_by_barcode

        medicine = get_medicine_by_barcode(barcode)

        if not medicine:
            QMessageBox.warning(
                self, "Not Found", f"No medicine found with barcode: {barcode}"
            )
            return

        # Check if already in billing table
        for i in range(self.billing_table.rowCount()):
            if self.billing_table.item(i, 0).text() == barcode:
                QMessageBox.information(
                    self, "Already Added", f"{medicine.name} is already in the bill."
                )
                return

        # Add to billing table
        row = self.billing_table.rowCount()
        self.billing_table.insertRow(row)

        self.billing_table.setItem(row, 0, QTableWidgetItem(barcode))
        self.billing_table.setItem(row, 1, QTableWidgetItem(medicine.name))
        self.billing_table.setItem(row, 2, QTableWidgetItem("1"))
        self.billing_table.setItem(row, 3, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))
        self.billing_table.setItem(row, 4, QTableWidgetItem("0"))  # Tax
        self.billing_table.setItem(row, 5, QTableWidgetItem("0"))  # Discount
        self.billing_table.setItem(row, 6, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))

        self._refresh_billing_table()

    def _refresh_billing_table(self) -> None:
        """
        Refresh billing table totals and bill summary, applying discounts and tax.
        """
        subtotal = 0
        for row in range(self.billing_table.rowCount()):
            try:
                qty_item = self.billing_table.item(row, 2)
                quantity = int(qty_item.text()) if qty_item and qty_item.text() and qty_item.text().isdigit() else 0
                price_item = self.billing_table.item(row, 3)
                price_text = price_item.text().replace("₹", "") if price_item and price_item.text() else "0"
                price = float(price_text) if price_text.replace('.', '', 1).isdigit() else 0.0
                discount_item = self.billing_table.item(row, 5)
                discount_text = discount_item.text() if discount_item and discount_item.text() else "0"
                try:
                    discount = float(discount_text)
                except ValueError:
                    discount = 0.0
                item_total = max(0, (price - discount)) * quantity
                self.billing_table.setItem(row, 6, QTableWidgetItem(f"₹{item_total:.2f}"))
                subtotal += item_total
            except Exception:
                self.billing_table.setItem(row, 6, QTableWidgetItem("₹0.00"))
        # Apply tax to subtotal
        tax_percent = self.tax_spin.value() if hasattr(self, 'tax_spin') else 0
        tax_amount = subtotal * (tax_percent / 100)
        total = subtotal + tax_amount
        self.total_label.setText(f"Total: ₹{total:.2f} (Tax: ₹{tax_amount:.2f})")

    def _on_billing_table_item_changed(self, item: QTableWidgetItem) -> None:
        # Recalculate totals if quantity, price, or discount changes
        if item.column() in [2, 3, 5]:
            self._refresh_billing_table()

    def _refresh_billing_history(self) -> None:
        """
        Refresh billing history list
        """
        # Clear layout
        for i in reversed(range(self.billing_history_list.count())):
            self.billing_history_list.takeItem(i)

        # Add all drafts if exist
        import os, json, re
        if os.path.exists('drafts'):
            for fname in sorted(os.listdir('drafts')):
                if re.match(r'draft_bill_.*\.json$', fname) or re.match(r'draft_bill_.*\.json$', fname):
                    path = os.path.join('drafts', fname)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            draft = json.load(f)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON draft {path}: {e}")
                        QMessageBox.warning(self, "Draft Error", f"Could not load draft {fname}: Invalid file format.")
                        continue
                    except Exception as e:
                        logger.error(f"Failed to read draft {path}: {e}")
                        QMessageBox.warning(self, "Draft Error", f"Could not load draft {fname}: {e}")
                        continue
                    label = f"Draft Bill: {fname.replace('draft_bill_', '').replace('.json', '')}"
                    item = QListWidgetItem(label)
                    item.setData(Qt.UserRole, {'is_draft': True, 'draft': draft, 'draft_path': path})
                    self.billing_history_list.addItem(item)

        # Get recent bills
        bills = self.billing_service.get_recent_bills(10)
        for bill in bills:
            item_text = f"Bill #{bill.id} - {bill.timestamp} - ₹{bill.total}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, bill)  # Store the full bill object
            self.billing_history_list.addItem(item)

    def _refresh_monthly_sales(self) -> None:
        """
        Refresh monthly sales table
        """
        sales_data = self.billing_service.get_sales_data()
        self.sales_ui.sales_table.setRowCount(len(sales_data))

        for i, (month, total, count, avg) in enumerate(sales_data):
            self.sales_ui.sales_table.setItem(i, 0, QTableWidgetItem(month))
            try:
                total_float = float(total)
                self.sales_ui.sales_table.setItem(i, 1, QTableWidgetItem(f"₹{total_float:.2f}"))
            except Exception:
                self.sales_ui.sales_table.setItem(i, 1, QTableWidgetItem(str(total)))
            self.sales_ui.sales_table.setItem(i, 2, QTableWidgetItem(str(count)))
            try:
                avg_float = float(avg)
                self.sales_ui.sales_table.setItem(i, 3, QTableWidgetItem(f"₹{avg_float:.2f}"))
            except Exception:
                self.sales_ui.sales_table.setItem(i, 3, QTableWidgetItem(str(avg)))

    def _export_monthly_sales_csv(self) -> None:
        """
        Export monthly sales to CSV
        """
        try:
            sales_data = self.billing_service.get_sales_data()
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Monthly Sales", "monthly_sales.csv", "CSV Files (*.csv)"
            )
            if not filename:
                return
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    ["Month", "Total Sales", "Number of Bills", "Average Bill"]
                )
                for month, total, count, avg in sales_data:
                    try:
                        total_float = (
                            float(total) if isinstance(total, str) else total
                        )
                        avg_float = float(avg) if isinstance(avg, str) else avg
                        writer.writerow(
                            [
                                month,
                                f"₹{total_float:.2f}",
                                count,
                                f"₹{avg_float:.2f}",
                            ]
                        )
                    except (ValueError, TypeError):
                        writer.writerow([month, str(total), count, str(avg)])
            QMessageBox.information(
                self, "Success", f"Sales data exported to {filename}"
            )
        except Exception as e:
            logger.error(f"Failed to export sales data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to export sales data: {str(e)}")

    def complete_sale(self) -> None:
        """
        Complete the sale and generate receipt
        """
        if self.billing_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Empty Bill", "Please add items to the bill first."
            )
            return

        # Get customer info from inline fields
        customer_data = {
            "name": self.customer_name.text(),
            "phone": self.customer_phone.text(),
            "email": self.customer_email.text(),
        }

        # Calculate total and items
        total = 0
        items = []
        for row in range(self.billing_table.rowCount()):
            barcode = self.billing_table.item(row, 0).text()
            name = self.billing_table.item(row, 1).text()
            quantity = int(self.billing_table.item(row, 2).text())
            price = float(self.billing_table.item(row, 3).text().replace("₹", ""))
            item_total = quantity * price
            items.append(
                {
                    "barcode": barcode,
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "subtotal": item_total,
                }
            )
            total += item_total

        # Save bill and update inventory using service
        success, error, _ = self.billing_service.create_bill(items, customer_data)
        if not success:
            QMessageBox.warning(self, "Error", f"Failed to save bill: {error}")
            return

        # Generate receipt
        details = get_pharmacy_details()
        timestamp = datetime.datetime.now()
        receipt_path = self.billing_service.generate_receipt(timestamp, items, total, details)

        # Send receipt via WhatsApp and Email
        try:
            # Use timestamp as receipt_id for uniqueness
            receipt_id = timestamp.strftime("%Y%m%d_%H%M%S")
            customer_info = dict(customer_data)
            customer_info["items"] = items
            customer_info["total"] = total
            print("Sending receipt to customer:", customer_info)
            results = self.receipt_manager.send_receipt_to_customer(
                customer_info, items, total, timestamp, receipt_id
            )
            print("Receipt send results:", results)
            # Show results in a dialog
            result_msg = "\n".join(
                [
                    f"{channel}: {'Success' if success else 'Failed'} - {msg}"
                    for channel, success, msg in results
                ]
            )
            QMessageBox.information(self, "Receipt Notification", result_msg)
        except Exception as e:
            print("Exception during receipt notification:", traceback.format_exc())
            QMessageBox.warning(
                self,
                "Notification Error",
                f"Failed to send receipt notifications: {str(e)}",
            )

        # Clear bill
        self.clear_bill()

        # Show success message
        QMessageBox.information(
            self, "Sale Complete", f"Sale completed successfully!\nTotal: ₹{total:.2f}"
        )

        # Refresh tables
        self.refresh_inventory_table()
        self._refresh_billing_history()
        self._refresh_monthly_sales()

    def _generate_receipt(self, timestamp: datetime.datetime, items: list, total: float) -> None:
        """
        Generate receipt for the sale
        """
        # Deprecated: now handled by BillingService
        return None

    def clear_bill(self) -> None:
        """
        Clear the current bill
        """
        self.billing_table.setRowCount(0)
        self.customer_name.clear()
        self.customer_phone.clear()
        self.customer_email.clear()
        self.customer_address.clear()
        self.customer_age.clear()
        self.customer_gender.setCurrentIndex(0)
        self.total_label.setText("Total: ₹0.00")

    def refresh_orders_table(self) -> None:
        """
        Refresh the orders table
        """
        orders = self.order_service.get_all()
        self.orders_ui.orders_table.setRowCount(len(orders))
        for i, order in enumerate(orders):
            self.orders_ui.orders_table.setItem(i, 0, QTableWidgetItem(str(order.id)))
            self.orders_ui.orders_table.setItem(i, 1, QTableWidgetItem(str(order.timestamp)))
            self.orders_ui.orders_table.setItem(
                i, 2, QTableWidgetItem(str(getattr(order, "supplier", "N/A")))
            )
            self.orders_ui.orders_table.setItem(
                i, 3, QTableWidgetItem(str(len(getattr(order, "meds", []))))
            )
            self.orders_ui.orders_table.setItem(
                i, 4, QTableWidgetItem(str(getattr(order, "status", "N/A")))
            )

    def refresh_alerts_table(self) -> None:
        """
        Refresh the alerts table
        """
        low_stock_medicines = self.order_service.get_low_stock()
        self.alerts_ui.alerts_table.setRowCount(len(low_stock_medicines))

        for i, medicine in enumerate(low_stock_medicines):
            self.alerts_ui.alerts_table.setItem(i, 0, QTableWidgetItem(medicine.name))
            self.alerts_ui.alerts_table.setItem(i, 1, QTableWidgetItem(str(medicine.quantity)))
            self.alerts_ui.alerts_table.setItem(
                i, 2, QTableWidgetItem(str(getattr(medicine, "threshold", 10)))
            )

            # Status
            if medicine.quantity == 0:
                status = "Out of Stock"
                status_color = QColor(255, 0, 0)  # Red
            else:
                status = "Low Stock"
                status_color = QColor(255, 165, 0)  # Orange

            status_item = QTableWidgetItem(status)
            status_item.setBackground(status_color)
            self.alerts_ui.alerts_table.setItem(i, 3, status_item)

            # Action button
            action_btn = QPushButton("Set Threshold")
            action_btn.clicked.connect(
                lambda checked, med=medicine: self._open_threshold_dialog(med)
            )
            self.alerts_ui.alerts_table.setCellWidget(i, 4, action_btn)

    def _open_threshold_dialog(self, medicine: dict) -> None:
        """
        Open threshold setting dialog for a specific medicine
        :param medicine: Medicine dictionary
        """
        dialog = ThresholdSettingDialog(medicine, self)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_alerts_table()

    def get_button_stylesheet(self) -> str:
        """
        Get general button stylesheet based on current theme, with push animation.
        :return: Stylesheet string
        """
        if self.theme == "dark":
            return """
                QPushButton {
                    background-color: #404040;
                    color: #D4D4D4;
                    border: 1px solid #606060;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    transition: all 0.1s;
                }
                QPushButton:hover {
                    background-color: #505050;
                    border-color: #707070;
                }
                QPushButton:pressed {
                    background-color: #303030;
                    transform: scale(0.97);
                }
                QPushButton:disabled {
                    background-color: #2B2B2B;
                    color: #808080;
                    border-color: #404040;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #FFFFFF;
                    color: #333333;
                    border: 1px solid #B3B3B3;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    transition: all 0.1s;
                }
                QPushButton:hover {
                    background-color: #F8F8F8;
                    color: #1976d2;
                    border-color: #1976d2;
                }
                QPushButton:pressed {
                    background-color: #B3B3B3;
                    transform: scale(0.97);
                }
                QPushButton:disabled {
                    background-color: #F8F8F8;
                    color: #B3B3B3;
                }
            """

    def apply_theme_to_buttons(self, parent_widget: QWidget) -> None:
        """
        Recursively apply the theme-based button stylesheet to all QPushButton widgets in the given parent widget.
        :param parent_widget: Parent widget to apply styles to
        """
        for child in parent_widget.findChildren(QPushButton):
            # Skip navbar buttons (they have their own style)
            if hasattr(self, "nav_buttons") and child in self.nav_buttons:
                continue
            child.setStyleSheet(self.get_button_stylesheet())

    def open_billing_add_medicine_dialog(self) -> None:
        dialog = BillingAddMedicineDialog(self)
        if dialog.exec_() == dialog.Accepted:
            medicine, quantity = dialog.get_selected()
            if medicine and quantity:
                self._add_billing_item_manual(medicine, quantity)

    def _add_billing_item_manual(self, medicine: dict, quantity: int) -> None:
        # Add the selected medicine to the billing table manually
        row = self.billing_table.rowCount()
        self.billing_table.insertRow(row)
        self.billing_table.setItem(row, 0, QTableWidgetItem(medicine.get('barcode', '')))
        self.billing_table.setItem(row, 1, QTableWidgetItem(medicine.get('name', '')))
        self.billing_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
        self.billing_table.setItem(row, 3, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))
        self.billing_table.setItem(row, 4, QTableWidgetItem("0"))  # Tax
        self.billing_table.setItem(row, 5, QTableWidgetItem("0"))  # Discount
        self.billing_table.setItem(row, 6, QTableWidgetItem(f"₹{getattr(medicine, 'price', 0)}"))
        total = getattr(medicine, "price", 0) * quantity
        self.billing_table.setItem(row, 6, QTableWidgetItem(f"₹{total:.2f}"))
        self._refresh_billing_table()

    def handle_exit(self) -> None:
        # Check for unsaved data in all modules
        unsaved = []
        # Billing: unsaved items in billing table
        if hasattr(self, "billing_table") and self.billing_table.rowCount() > 0:
            unsaved.append("Billing items")
        # Inventory: check for open add/edit dialogs or pending edits (customize as needed)
        if getattr(self, "inventory_edit_in_progress", False):
            unsaved.append("Inventory edits")
        # Orders: check for open order dialogs or pending edits (customize as needed)
        if getattr(self, "order_edit_in_progress", False):
            unsaved.append("Order edits")
        # Settings: check for unsaved config changes (customize as needed)
        if getattr(self, "settings_edit_in_progress", False):
            unsaved.append("Settings changes")
        # Compose warning message
        if unsaved:
            msg = (
                "There are unsaved changes in the following modules:\n- "
                + "\n- ".join(unsaved)
                + "\n\nAre you sure you want to exit? Unsaved data may be lost."
            )
            reply = QMessageBox.warning(
                self,
                "Exit Warning",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        # Save all data
        self.save_all_data()
        QApplication.quit()

    def save_all_data(self) -> None:
        # Billing: Save or discard unsaved billing items
        if hasattr(self, "billing_table") and self.billing_table.rowCount() > 0:
            self.save_billing_draft()
        else:
            self.clear_billing_table()

        # Inventory: Save or discard unsaved inventory edits
        if getattr(self, "inventory_edit_in_progress", False):
            self.save_inventory_edits()
            self.inventory_edit_in_progress = False

        # Orders: Save or discard unsaved order edits
        if getattr(self, "order_edit_in_progress", False):
            self.save_order_edits()
            self.order_edit_in_progress = False

        # Settings: Save or discard unsaved settings changes
        if getattr(self, "settings_edit_in_progress", False):
            self.save_settings_changes()
            self.settings_edit_in_progress = False

    def save_billing_draft(self) -> None:
        """
        Save the current bill as a draft to a local JSON file (multiple drafts supported, custom name).
        """
        import json, os, datetime
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        if not os.path.exists('drafts'):
            os.makedirs('drafts')
        # Prompt for custom name
        name, ok = QInputDialog.getText(self, "Draft Name", "Enter a name for this draft:")
        if not ok or not name.strip():
            QMessageBox.warning(self, "No Name", "Draft not saved: name is required.")
            return
        safe_name = "_".join(name.strip().split())
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f'drafts/draft_bill_{safe_name}_{timestamp}.json'
        draft = {
            'customer': {
                'name': self.customer_name.text(),
                'age': self.customer_age.value(),
                'gender': self.customer_gender.currentText(),
                'phone': self.customer_phone.text(),
                'email': self.customer_email.text(),
                'address': self.customer_address.text(),
            },
            'items': []
        }
        for row in range(self.billing_table.rowCount()):
            item = {
                'barcode': self.billing_table.item(row, 0).text() if self.billing_table.item(row, 0) else '',
                'name': self.billing_table.item(row, 1).text() if self.billing_table.item(row, 1) else '',
                'quantity': self.billing_table.item(row, 2).text() if self.billing_table.item(row, 2) else '',
                'price': self.billing_table.item(row, 3).text() if self.billing_table.item(row, 3) else '',
                'tax': self.billing_table.item(row, 4).text() if self.billing_table.item(row, 4) else '',
                'discount': self.billing_table.item(row, 5).text() if self.billing_table.item(row, 5) else '',
            }
            draft['items'].append(item)
        try:
            with open(draft_filename, 'w', encoding='utf-8') as f:
                json.dump(draft, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Draft Saved", f"Current bill has been saved as a draft: {draft_filename}")
            self._refresh_billing_history()
        except Exception as e:
            logger.error(f"Failed to save draft {draft_filename}: {e}")
            QMessageBox.warning(self, "Draft Error", f"Could not save draft: {e}")

    def clear_billing_table(self) -> None:
        # Clear the billing table
        if hasattr(self, "billing_table"):
            self.billing_table.setRowCount(0)
        # Optionally remove the draft file
        if os.path.exists("billing_draft.json"):
            try:
                os.remove("billing_draft.json")
            except Exception as e:
                logger.error(f"Failed to delete billing_draft.json: {e}")
                QMessageBox.warning(self, "Delete Error", f"Could not delete billing draft: {e}")

    def save_inventory_edits(self) -> None:
        # Call inventory model/controller save method if present
        if hasattr(self, "inventory_model") and hasattr(
            self.inventory_model, "save_changes"
        ):
            self.inventory_model.save_changes()
        self.inventory_edit_in_progress = False
        QMessageBox.information(
            self, "Inventory Saved", "Inventory edits have been saved."
        )

    def discard_inventory_edits(self) -> None:
        # Call inventory model/controller discard method if present
        if hasattr(self, "inventory_model") and hasattr(
            self.inventory_model, "discard_changes"
        ):
            self.inventory_model.discard_changes()
        self.inventory_edit_in_progress = False
        QMessageBox.information(
            self, "Inventory Discarded", "Inventory edits have been discarded."
        )

    def save_order_edits(self) -> None:
        # Call order model/controller save method if present
        if hasattr(self, "order_model") and hasattr(self.order_model, "save_changes"):
            self.order_model.save_changes()
        self.order_edit_in_progress = False
        QMessageBox.information(self, "Orders Saved", "Order edits have been saved.")

    def discard_order_edits(self) -> None:
        # Call order model/controller discard method if present
        if hasattr(self, "order_model") and hasattr(
            self.order_model, "discard_changes"
        ):
            self.order_model.discard_changes()
        self.order_edit_in_progress = False
        QMessageBox.information(
            self, "Orders Discarded", "Order edits have been discarded."
        )

    def save_settings_changes(self) -> None:
        # Call settings model/controller save method if present
        if hasattr(self, "settings_model") and hasattr(
            self.settings_model, "save_changes"
        ):
            self.settings_model.save_changes()
        self.settings_edit_in_progress = False
        QMessageBox.information(
            self, "Settings Saved", "Settings changes have been saved."
        )

    def discard_settings_changes(self) -> None:
        # Call settings model/controller discard method if present
        if hasattr(self, "settings_model") and hasattr(
            self.settings_model, "discard_changes"
        ):
            self.settings_model.discard_changes()
        self.settings_edit_in_progress = False
        QMessageBox.information(
            self, "Settings Discarded", "Settings changes have been discarded."
        )

    def show_license_info_dialog(self) -> None:
        from PyQt5.QtWidgets import (
            QDialog,
            QLabel,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        key = self.settings_service.get_license_key()
        if not key:
            QMessageBox.warning(self, "No License", "No license key found.")
            return
        if key == "TRIAL-000000000000":
            name = "Trial User"
            install_date = self.settings_service.get_installation_date()
            if install_date:
                install_dt = datetime.datetime.strptime(install_date, "%Y-%m-%d")
                days_used = (datetime.datetime.now() - install_dt).days
                days_left = max(0, 7 - days_used)
                exp = (install_dt + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            else:
                days_left = "Unknown"
                exp = "Unknown"
            info = f"License Type: Trial\nExpires: {exp}\nDays left: {days_left}"
        else:
            valid, data, err = verify_license_key(key)
            if not valid:
                info = f"Invalid license: {err}"
                name = "Unknown"
                exp = "Unknown"
                days_left = "Unknown"
            else:
                name = data.get("name", "Unknown")
                exp = data.get("exp", "Unknown")
                if exp != "Unknown":
                    exp_date = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
                    days_left = (exp_date - datetime.datetime.now().date()).days
                else:
                    days_left = "Unknown"
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
    def check_license() -> bool:
        settings_service = SettingsService()
        key = settings_service.get_license_key()
        install_date = settings_service.get_installation_date()
        if not key or not install_date:
            return False
        # Trial license logic
        if key == "TRIAL-000000000000":
            try:
                install_dt = datetime.datetime.strptime(install_date, "%Y-%m-%d")
                days_used = (datetime.datetime.now() - install_dt).days
                if days_used > 7:
                    return False
                elif days_used >= 6:
                    from PyQt5.QtWidgets import QMessageBox

                    QMessageBox.warning(
                        None,
                        "Trial Expiring",
                        f"Your trial license will expire in {7 - days_used} day(s). Please activate a full license.",
                    )
            except Exception:
                return False
            return True
        # HMAC license key logic
        valid, data, err = verify_license_key(key)
        if not valid:
            from PyQt5.QtWidgets import QMessageBox

            if err == "License expired":
                QMessageBox.critical(
                    None,
                    "License Expired",
                    "Your license has expired. Please contact support.",
                )
            else:
                QMessageBox.critical(None, "Invalid License", f"License error: {err}")
            return False
        # Optionally show customer info or expiry warning
        exp = data.get("exp")
        name = data.get("name")
        if exp:
            exp_date = datetime.datetime.strptime(exp, "%Y-%m-%d").date()
            days_left = (exp_date - datetime.datetime.now().date()).days
            if days_left <= 7:
                from PyQt5.QtWidgets import QMessageBox

                QMessageBox.warning(
                    None,
                    "License Expiring Soon",
                    f"License for {name} expires in {days_left} day(s). Please renew.",
                )
        return True

    @staticmethod
    def prompt_license_dialog(parent=None) -> None:
        import sys

        from PyQt5.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        while True:
            dialog = QDialog(parent)
            dialog.setWindowTitle("License Key Required")
            dialog.setModal(True)
            layout = QVBoxLayout(dialog)
            label = QLabel(
                "Enter your license key to activate Medibit.\n\nThe license is valid until the expiry date encoded in the key.\n\nTo try Medibit, enter: TRIAL-000000000000 (valid for 7 days)"
            )
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
                if key == "TRIAL-000000000000":
                    settings_service = SettingsService()
                    settings_service.set_license_key(key)
                    if not settings_service.get_installation_date():
                        settings_service.set_installation_date(
                            datetime.datetime.now().strftime("%Y-%m-%d")
                        )
                    dialog.accept()
                    return
                # HMAC license key logic
                valid, data, err = verify_license_key(key)
                if not valid:
                    QMessageBox.critical(
                        dialog, "Invalid License", f"License error: {err}"
                    )
                    return
                settings_service.set_license_key(key)
                if not settings_service.get_installation_date():
                    settings_service.set_installation_date(datetime.datetime.now().strftime("%Y-%m-%d"))
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
                    QMessageBox.critical(
                        dialog,
                        "License Error",
                        "License activation failed. Please try again.",
                    )
            elif result == 2:
                sys.exit(0)
            # If dialog closed in any other way, re-show dialog

    def delete_selected_inventory_row(self) -> None:
        selected = self.inventory_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")
            return
        barcode = self.inventory_table.item(selected, 0).text()
        reply = QMessageBox.question(
            self,
            "Delete Medicine",
            f"Are you sure you want to delete the selected medicine (barcode: {barcode})?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            success, error = self.inventory_service.delete(barcode)
            if success:
                QMessageBox.information(
                    self, "Deleted", "Medicine deleted successfully."
                )
                self.refresh_inventory_table()
                # Refresh open dialogs if present
                if self.bulk_threshold_dialog is not None:
                    self.bulk_threshold_dialog.reload_data()
                if self.quick_add_stock_dialog is not None:
                    self.quick_add_stock_dialog.reload_data()
            else:
                QMessageBox.critical(
                    self, "Error", f"Failed to delete medicine: {error}"
                )

    def clear_inventory(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear Inventory",
            "Are you sure you want to delete ALL medicines from inventory? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            success, result = self.inventory_service.clear()
            if success:
                QMessageBox.information(
                    self,
                    "Inventory Cleared",
                    f"All medicines deleted. ({result} items removed)",
                )
                self.refresh_inventory_table()
                # Refresh open dialogs if present
                if self.bulk_threshold_dialog is not None:
                    self.bulk_threshold_dialog.reload_data()
                if self.quick_add_stock_dialog is not None:
                    self.quick_add_stock_dialog.reload_data()
            else:
                QMessageBox.critical(
                    self, "Error", f"Failed to clear inventory: {result}"
                )

    def send_daily_sales_summary(self) -> None:
        import datetime

        from db import Bill
        from notifications import NotificationManager

        session = None
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker

            engine = create_engine(f"sqlite:///pharmacy_inventory.db", echo=False)
            Session = sessionmaker(bind=engine)
            session = Session()
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            bills = session.query(Bill).filter(Bill.timestamp.startswith(today)).all()
            total = sum(bill.total for bill in bills)
            count = len(bills)
            avg = total / count if count else 0
            bill_details = []
            for bill in bills:
                # Extract time from timestamp if possible
                time_str = (
                    bill.timestamp[11:16]
                    if len(bill.timestamp) >= 16
                    else bill.timestamp
                )
                bill_details.append({"time": time_str, "total": bill.total})
            sales_summary = {"total": total, "count": count, "avg": avg}
            notif = NotificationManager()
            email_success, email_msg = notif.send_daily_sales_summary_email(
                sales_summary, bill_details
            )
            whatsapp_success, whatsapp_msg = notif.send_daily_sales_summary_whatsapp(
                sales_summary, bill_details
            )
            msg = f"Email: {email_msg}\nWhatsApp: {whatsapp_msg}"
            if email_success or whatsapp_success:
                QMessageBox.information(self, "Daily Sales Summary Sent", msg)
            else:
                QMessageBox.warning(self, "Daily Sales Summary Failed", msg)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to send daily sales summary: {str(e)}"
            )
        finally:
            if session:
                session.close()

    def clear_billing_history(self) -> None:
        """
        Clear all recent bills from the history (does not delete drafts).
        """
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Clear History", "Are you sure you want to clear all recent bills? This cannot be undone.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Assuming get_all_bills() returns a list of bill objects and you have a function to delete bills
            clear_all_bills()
            self._refresh_billing_history()
            QMessageBox.information(self, "History Cleared", "All recent bills have been cleared.")

    def delete_selected_draft(self) -> None:
        """
        Delete the selected draft file from the drafts directory.
        """
        from PyQt5.QtWidgets import QMessageBox
        selected_items = self.billing_history_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a draft to delete.")
            return
        selected_item = selected_items[0]
        data = selected_item.data(Qt.UserRole)
        if not (isinstance(data, dict) and data.get('is_draft') and data.get('draft_path')):
            QMessageBox.warning(self, "Not a Draft", "Please select a draft bill to delete.")
            return
        import os
        try:
            os.remove(data['draft_path'])
            QMessageBox.information(self, "Draft Deleted", "Draft has been deleted.")
            self._refresh_billing_history()
        except Exception as e:
            QMessageBox.warning(self, "Delete Failed", f"Could not delete draft: {e}")

    @property
    def inventory_table(self):
        """
        Property to access the inventory table widget for compatibility with tests and legacy code.
        """
        return self.inventory_ui.inventory_table

    def refresh_billing_history(self):
        """
        Public method to refresh billing history, for use by BillingUi and tests.
        """
        self._refresh_billing_history()
