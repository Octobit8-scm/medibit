from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QDialog, QLineEdit, QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox, QGroupBox, QSpacerItem, QComboBox, QFrame, QStackedLayout, QProgressDialog, QFrame, QMenu)
from PyQt5.QtCore import Qt
from dialogs import SupplierInfoDialog
from order_manager import OrderManager
from PyQt5.QtWidgets import QMessageBox
from db import get_order_items, get_all_orders, update_order_status, get_all_medicines
from theme import theme_manager
import logging
logger = logging.getLogger("medibit")
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from theme import create_animated_button

class InventoryLookupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Medicine from Inventory")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self.setStyleSheet(theme_manager.get_dialog_stylesheet())
        layout = QVBoxLayout(self)
        from PyQt5.QtWidgets import QLineEdit
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by barcode, name, or manufacturer...")
        self.search_box.textChanged.connect(self.filter_inventory)
        self.search_box.setToolTip("Search medicines in inventory.")
        self.search_box.setAccessibleName("Inventory Search Box")
        layout.addWidget(self.search_box)
        table_group = QGroupBox("Inventory Medicines")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 5)
        self.table.setMinimumHeight(250)
        self.table.setHorizontalHeaderLabels(["Barcode", "Name", "Expiry", "Manufacturer", "Quantity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.table.setToolTip("Table showing available medicines from inventory.")
        self.table.setAccessibleName("Inventory Lookup Table")
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        btns = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout.addWidget(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.all_medicines = []
        self.load_inventory()
    def load_inventory(self):
        medicines = get_all_medicines()
        self.all_medicines = [
            {
                'barcode': str(med.barcode),
                'name': med.name,
                'expiry': str(med.expiry),
                'manufacturer': med.manufacturer,
                'quantity': int(med.quantity) if hasattr(med, 'quantity') else 0,
            }
            for med in medicines
        ]
        self.show_medicines(self.all_medicines)
    def show_medicines(self, medicines):
        self.table.setRowCount(len(medicines))
        for row, med in enumerate(medicines):
            self.table.setItem(row, 0, QTableWidgetItem(med['barcode']))
            self.table.setItem(row, 1, QTableWidgetItem(med['name']))
            self.table.setItem(row, 2, QTableWidgetItem(med['expiry']))
            self.table.setItem(row, 3, QTableWidgetItem(med['manufacturer']))
            self.table.setItem(row, 4, QTableWidgetItem(str(med['quantity'])))
    def filter_inventory(self, text):
        text = text.lower().strip()
        if not text:
            filtered = self.all_medicines
        else:
            filtered = [med for med in self.all_medicines if text in med['barcode'].lower() or text in med['name'].lower() or text in med['manufacturer'].lower()]
        self.show_medicines(filtered)
    def get_selected_medicine(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return {
            'barcode': self.table.item(row, 0).text(),
            'name': self.table.item(row, 1).text(),
            'expiry': self.table.item(row, 2).text(),
            'manufacturer': self.table.item(row, 3).text(),
            'quantity': int(self.table.item(row, 4).text()) if self.table.item(row, 4) and self.table.item(row, 4).text().isdigit() else 0,
        }

class CreateOrderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Order")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setStyleSheet(theme_manager.get_dialog_stylesheet())
        layout = QVBoxLayout(self)
        form_group = QGroupBox("Order Details")
        form = QFormLayout(form_group)
        self.supplier_name = QLineEdit()
        self.supplier_name.setToolTip("Enter the supplier's name.")
        self.supplier_name.setAccessibleName("Supplier Name Field")
        self.supplier_name.setFocusPolicy(Qt.StrongFocus)
        form.addRow("Supplier Name:", self.supplier_name)
        layout.addWidget(form_group)
        meds_group = QGroupBox("Order Medicines")
        meds_layout = QVBoxLayout(meds_group)
        self.meds_table = QTableWidget(0, 6)
        self.meds_table.setMinimumHeight(220)
        self.meds_table.setHorizontalHeaderLabels(["Barcode", "Name", "Quantity", "Expiry", "Manufacturer", "Order Qty"])
        self.meds_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.meds_table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.meds_table.setToolTip("Table listing all medicines in the order.")
        self.meds_table.setAccessibleName("Order Medicines Table")
        self.meds_table.setProperty("aria-role", "table")
        self.meds_table.setFocusPolicy(Qt.StrongFocus)
        meds_layout.addWidget(self.meds_table)
        btn_row_layout = QHBoxLayout()
        btn_add_row = QPushButton("Add Medicine")
        btn_add_row.setStyleSheet(theme_manager.get_button_stylesheet())
        btn_add_row.setToolTip("Add a new medicine row to the order.")
        btn_add_row.setAccessibleName("Add Medicine Row Button")
        btn_add_row.clicked.connect(self.add_row)
        btn_add_inventory = QPushButton("Add from Inventory")
        btn_add_inventory.setStyleSheet(theme_manager.get_button_stylesheet())
        btn_add_inventory.setToolTip("Add medicine from inventory to the order.")
        btn_add_inventory.setAccessibleName("Add from Inventory Button")
        btn_add_inventory.clicked.connect(self.add_from_inventory)
        btn_remove_row = QPushButton("Remove Selected Row")
        btn_remove_row.setStyleSheet(theme_manager.get_button_stylesheet())
        btn_remove_row.setToolTip("Remove the selected medicine row from the order.")
        btn_remove_row.setAccessibleName("Remove Selected Row Button")
        btn_remove_row.clicked.connect(self.remove_selected_row)
        btn_row_layout.addWidget(btn_add_row)
        btn_row_layout.addWidget(btn_add_inventory)
        btn_row_layout.addWidget(btn_remove_row)
        btn_row_layout.addStretch()
        meds_layout.addLayout(btn_row_layout)
        layout.addWidget(meds_group)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("OK")
        btns.button(QDialogButtonBox.Cancel).setText("Cancel")
        btns.button(QDialogButtonBox.Ok).setMinimumWidth(100)
        btns.button(QDialogButtonBox.Cancel).setMinimumWidth(100)
        btns.setCenterButtons(True)
        layout.addWidget(btns)
        btns.accepted.connect(self.validate_and_accept)
        btns.rejected.connect(self.reject)
    def add_row(self):
        row = self.meds_table.rowCount()
        self.meds_table.insertRow(row)
        for col in range(6):
            item = QTableWidgetItem("")
            if col in (2, 5):  # Quantity, Order Qty
                item.setText("1")
            self.meds_table.setItem(row, col, item)
        self.meds_table.setCurrentCell(row, 0)
    def add_from_inventory(self):
        dialog = InventoryLookupDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            med = dialog.get_selected_medicine()
            if med:
                # Prevent duplicate barcodes
                for row in range(self.meds_table.rowCount()):
                    if self.meds_table.item(row, 0) and self.meds_table.item(row, 0).text() == med['barcode']:
                        QMessageBox.warning(self, "Duplicate Medicine", f"Medicine with barcode {med['barcode']} is already in the order.")
                        return
                row = self.meds_table.rowCount()
                self.meds_table.insertRow(row)
                self.meds_table.setItem(row, 0, QTableWidgetItem(med['barcode']))
                self.meds_table.setItem(row, 1, QTableWidgetItem(med['name']))
                qty_item = QTableWidgetItem("1")
                self.meds_table.setItem(row, 2, qty_item)
                self.meds_table.setItem(row, 3, QTableWidgetItem(med['expiry']))
                self.meds_table.setItem(row, 4, QTableWidgetItem(med['manufacturer']))
                order_qty_item = QTableWidgetItem("1")
                self.meds_table.setItem(row, 5, order_qty_item)
                self.meds_table.setCurrentCell(row, 2)
    def remove_selected_row(self):
        row = self.meds_table.currentRow()
        if row >= 0:
            self.meds_table.removeRow(row)
    def get_data(self):
        supplier = self.supplier_name.text().strip()
        meds = []
        for row in range(self.meds_table.rowCount()):
            med = {
                'barcode': self.meds_table.item(row, 0).text() if self.meds_table.item(row, 0) else '',
                'name': self.meds_table.item(row, 1).text() if self.meds_table.item(row, 1) else '',
                'quantity': int(self.meds_table.item(row, 2).text()) if self.meds_table.item(row, 2) and self.meds_table.item(row, 2).text().isdigit() else 0,
                'expiry': self.meds_table.item(row, 3).text() if self.meds_table.item(row, 3) else '',
                'manufacturer': self.meds_table.item(row, 4).text() if self.meds_table.item(row, 4) else '',
                'order_quantity': int(self.meds_table.item(row, 5).text()) if self.meds_table.item(row, 5) and self.meds_table.item(row, 5).text().isdigit() else 0,
            }
            meds.append(med)
        return supplier, meds
    def validate_and_accept(self):
        supplier, meds = self.get_data()
        errors = []
        if not supplier:
            errors.append("Supplier name is required.")
        if not meds:
            errors.append("At least one medicine is required.")
        seen_barcodes = set()
        for idx, med in enumerate(meds):
            if not all([med['barcode'], med['name'], med['expiry'], med['manufacturer']]):
                errors.append(f"All fields are required for medicine row {idx+1}.")
            if med['quantity'] <= 0 or med['order_quantity'] <= 0:
                errors.append(f"Quantities must be positive integers for medicine row {idx+1}.")
            if med['barcode'] in seen_barcodes:
                errors.append(f"Duplicate medicine barcode {med['barcode']} in row {idx+1}.")
            seen_barcodes.add(med['barcode'])
        if errors:
            logger.warning(f"Order validation failed: {errors}")
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return
        logger.info("Order validated successfully.")
        self.accept()

class OrderDetailsDialog(QDialog):
    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Order Details - ID {order.id}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setStyleSheet(theme_manager.get_dialog_stylesheet())
        layout = QVBoxLayout(self)
        # Order metadata
        meta_group = QGroupBox("Order Metadata")
        meta_layout = QFormLayout(meta_group)
        meta_layout.addRow("Order ID:", QLabel(str(order.id)))
        meta_layout.addRow("Date:", QLabel(order.timestamp))
        meta_layout.addRow("Status:", QLabel(order.status))
        meta_layout.addRow("PDF Path:", QLabel(order.file_path))
        layout.addWidget(meta_group)
        # Supplier info (from first medicine)
        if order.meds:
            supplier = order.meds[0].manufacturer or ""
        else:
            supplier = ""
        supplier_group = QGroupBox("Supplier Info")
        supplier_layout = QFormLayout(supplier_group)
        supplier_layout.addRow("Supplier:", QLabel(supplier))
        layout.addWidget(supplier_group)
        # Medicines table
        meds_group = QGroupBox("Medicines")
        meds_layout = QVBoxLayout(meds_group)
        table = QTableWidget(len(order.meds), 6)
        table.setHorizontalHeaderLabels(["Barcode", "Name", "Quantity", "Expiry", "Manufacturer", "Order Qty"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, med in enumerate(order.meds):
            table.setItem(row, 0, QTableWidgetItem(str(med.barcode)))
            table.setItem(row, 1, QTableWidgetItem(med.name))
            table.setItem(row, 2, QTableWidgetItem(str(med.quantity)))
            table.setItem(row, 3, QTableWidgetItem(str(med.expiry)))
            table.setItem(row, 4, QTableWidgetItem(med.manufacturer))
            table.setItem(row, 5, QTableWidgetItem(str(med.order_quantity or 0)))
        meds_layout.addWidget(table)
        layout.addWidget(meds_group)
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.button(QDialogButtonBox.Ok).setText("Close")
        btns.button(QDialogButtonBox.Ok).setMinimumWidth(100)
        btns.setCenterButtons(True)
        layout.addWidget(btns)
        btns.accepted.connect(self.accept)
        self.setAccessibleName("Order Details Dialog")
        self.setFocusPolicy(Qt.StrongFocus)

class OrdersUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.page_size = 20
        self.current_page = 0
        self.main_window = main_window
        logger.info("OrdersUi initialized")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Feedback banner
        self.feedback_banner = QLabel("")
        self.feedback_banner.setStyleSheet("padding: 8px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        self.feedback_banner.setVisible(False)
        layout.addWidget(self.feedback_banner)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Order Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        title.setToolTip("Section: Order Management")
        title.setAccessibleName("Order Management Title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.create_order_btn = create_animated_button("Create Order", self)
        self.create_order_btn.setMinimumHeight(40)
        self.create_order_btn.setToolTip("Create a new order for medicines. (Ctrl+N)")
        self.create_order_btn.setAccessibleName("Create Order Button")
        self.create_order_btn.setFocusPolicy(Qt.StrongFocus)
        self.create_order_btn.clicked.connect(self.open_create_order_dialog)
        header_layout.addWidget(self.create_order_btn)
        layout.addLayout(header_layout)
        # Status Filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Status:")
        filter_label.setToolTip("Filter orders by status.")
        filter_label.setAccessibleName("Order Status Filter Label")
        filter_layout.addWidget(filter_label)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Completed"])
        self.status_filter.setCurrentIndex(0)
        self.status_filter.setToolTip("Select order status to filter.")
        self.status_filter.setAccessibleName("Order Status Filter ComboBox")
        self.status_filter.setFocusPolicy(Qt.StrongFocus)
        self.status_filter.currentTextChanged.connect(self.refresh_orders_table)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        # Search Box (if present)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by barcode, name, or manufacturer...")
        self.search_box.textChanged.connect(self.refresh_orders_table)
        self.search_box.setToolTip("Search medicines in inventory.")
        self.search_box.setAccessibleName("Inventory Search Box")
        layout.addWidget(self.search_box)
        # Orders Table
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)
        table_title = QLabel("Orders")
        table_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        table_title.setToolTip("Section: Orders")
        table_title.setAccessibleName("Orders Title")
        table_layout.addWidget(table_title)
        self.orders_table = QTableWidget(0, 6)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setSelectionMode(QTableWidget.MultiSelection)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Supplier", "Items", "Total", "Status"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.orders_table.setToolTip("Table showing all orders.")
        self.orders_table.setAccessibleName("Orders Table")
        self.orders_table.setProperty("aria-role", "table")
        self.orders_table.setFocusPolicy(Qt.StrongFocus)
        self.orders_table.setTabKeyNavigation(True)
        self.orders_table.itemSelectionChanged.connect(self.update_action_buttons)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.show_context_menu)
        table_layout.addWidget(self.orders_table)
        # Table action buttons
        table_btn_layout = QHBoxLayout()
        self.view_order_btn = create_animated_button("View Order", self)
        self.view_order_btn.setToolTip("View details of the selected order.")
        self.view_order_btn.setAccessibleName("View Order Button")
        self.view_order_btn.setFocusPolicy(Qt.StrongFocus)
        # Note: view_order method doesn't exist, will be handled by MainWindow
        self.delete_order_btn = create_animated_button("Delete Order", self)
        self.delete_order_btn.setToolTip("Delete the selected order.")
        self.delete_order_btn.setAccessibleName("Delete Order Button")
        self.delete_order_btn.setFocusPolicy(Qt.StrongFocus)
        self.delete_order_btn.clicked.connect(self.delete_selected_order)
        self.delete_selected_btn = create_animated_button("Delete Selected", self)
        self.delete_selected_btn.setToolTip("Delete all selected orders. (Del)")
        self.delete_selected_btn.setAccessibleName("Delete Selected Orders Button")
        self.delete_selected_btn.setFocusPolicy(Qt.StrongFocus)
        self.delete_selected_btn.clicked.connect(self.delete_selected_orders)
        table_btn_layout.addWidget(self.view_order_btn)
        table_btn_layout.addWidget(self.delete_order_btn)
        table_btn_layout.addWidget(self.delete_selected_btn)
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        layout.addWidget(table_frame)
        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton("Previous")
        self.prev_page_btn.setAccessibleName("Previous Page Button")
        self.prev_page_btn.setFocusPolicy(Qt.StrongFocus)
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.next_page_btn = QPushButton("Next")
        self.next_page_btn.setAccessibleName("Next Page Button")
        self.next_page_btn.setFocusPolicy(Qt.StrongFocus)
        self.next_page_btn.clicked.connect(self.next_page)
        self.page_label = QLabel("")
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_btn)
        layout.addLayout(pagination_layout)
        # Load initial data
        self.refresh_orders_table()
        # Loading overlay
        self.loading_overlay = QProgressDialog("Please wait...", None, 0, 0, self)
        self.loading_overlay.setWindowModality(Qt.WindowModal)
        self.loading_overlay.setCancelButton(None)
        self.loading_overlay.setWindowTitle("Loading")
        self.loading_overlay.setMinimumDuration(0)
        self.loading_overlay.close()
        # Add shortcuts
        self.shortcut_create = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_create.activated.connect(self.open_create_order_dialog)
        self.shortcut_delete = QShortcut(QKeySequence("Delete"), self)
        self.shortcut_delete.activated.connect(self.delete_selected_orders)
        self.shortcut_confirm = QShortcut(QKeySequence("Ctrl+D"), self)
        self.shortcut_confirm.activated.connect(self.confirm_selected_order)
        self.shortcut_edit = QShortcut(QKeySequence("Ctrl+E"), self)
        self.shortcut_edit.activated.connect(self.edit_selected_order)
        self.orders_table.cellDoubleClicked.connect(self._on_table_double_clicked)

    def show_loading(self, message="Loading..."):
        self.loading_overlay.setLabelText(message)
        self.loading_overlay.setValue(0)
        self.loading_overlay.show()
        QApplication.processEvents()

    def hide_loading(self):
        self.loading_overlay.hide()
        QApplication.processEvents()

    def show_banner(self, message, success=True):
        color = "#43a047" if success else "#e53935"
        self.feedback_banner.setStyleSheet(f"background: {color}; color: white; padding: 8px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        self.feedback_banner.setText(message)
        self.feedback_banner.setVisible(True)
        QTimer.singleShot(3000, lambda: self.feedback_banner.setVisible(False))

    def open_create_order_dialog(self):
        dialog = CreateOrderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            supplier, meds = dialog.get_data()
            if not supplier or not meds:
                self.show_banner("Supplier and at least one medicine are required.", success=False)
                return
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # For now, PDF path is empty; can be generated later
            pdf_path = ""
            self.show_loading("Creating order...")
            try:
                success, error = self.main_window.order_service.add(timestamp, pdf_path, meds)
                if success:
                    self.show_banner("Order has been created successfully.", success=True)
                    self.refresh_orders_table()
                else:
                    self.show_banner(f"Failed to create order: {error}", success=False)
            finally:
                self.hide_loading()

    def send_order_to_supplier(self):
        selected = self.orders_table.currentRow()
        if selected < 0:
            self.show_banner("Please select an order to send.", success=False)
            return
        order_id = self.orders_table.item(selected, 0).text()
        order_date = self.orders_table.item(selected, 1).text()
        supplier_name = self.orders_table.item(selected, 2).text()
        order_items = self.get_order_items_for_order(order_id)
        dialog = SupplierInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            supplier_info = dialog.get_data()
            if not supplier_info.get('email') and not supplier_info.get('phone'):
                self.show_banner("Supplier email or phone is required to send the order.", success=False)
                return
            supplier_info['order_id'] = order_id
            supplier_info['order_date'] = order_date
            manager = OrderManager()
            self.show_loading("Sending order to supplier...")
            try:
                results = manager.send_order_to_supplier(supplier_info, order_items, order_id, order_date)
                msg = '\n'.join([f"{channel}: {'Success' if success else 'Failed'} - {message}" for channel, success, message in results])
                self.show_banner(msg, success=all(success for _, success, _ in results))
            finally:
                self.hide_loading()

    def get_order_items_for_order(self, order_id):
        try:
            order_id_int = int(order_id)
        except Exception:
            return []
        items = get_order_items(order_id_int)
        # Convert OrderMedicine objects to dicts as expected by the PDF/email logic
        result = []
        for item in items:
            result.append({
                'barcode': item.barcode,
                'name': item.name,
                'quantity': item.quantity,
                'expiry': item.expiry,
                'manufacturer': item.manufacturer,
                'order_quantity': item.order_quantity,
            })
        return result

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_orders_table()
    def next_page(self):
        self.current_page += 1
        self.refresh_orders_table()
    def refresh_orders_table(self):
        orders = get_all_orders()
        # Apply status filter
        status = self.status_filter.currentText().lower()
        if status != "all":
            orders = [o for o in orders if o.status.lower() == status]
        # Apply search filter
        text = self.search_box.text().lower().strip()
        if text:
            def order_matches(o):
                if text in str(o.id).lower():
                    return True
                if any(text in (med.name or '').lower() for med in o.meds):
                    return True
                if any(text in (med.manufacturer or '').lower() for med in o.meds):
                    return True
                if any(text in (med.barcode or '').lower() for med in o.meds):
                    return True
                return False
            orders = [o for o in orders if order_matches(o)]
        # Pagination
        total_orders = len(orders)
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_orders = orders[start:end]
        self.orders_table.setRowCount(len(paged_orders))
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Supplier", "Items", "Total", "Status"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, order in enumerate(paged_orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.timestamp))
            supplier = order.meds[0].manufacturer if order.meds else ""
            self.orders_table.setItem(row, 2, QTableWidgetItem(supplier))
            items = ", ".join([med.name for med in order.meds])
            self.orders_table.setItem(row, 3, QTableWidgetItem(items))
            total = sum([med.order_quantity or 0 for med in order.meds])
            self.orders_table.setItem(row, 4, QTableWidgetItem(str(total)))
            self.orders_table.setItem(row, 5, QTableWidgetItem(order.status))
        # Update pagination label and button states
        total_pages = max(1, (total_orders + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled((self.current_page + 1) * self.page_size < total_orders)

    def get_selected_order_id(self):
        selected = self.orders_table.selectedItems()
        if not selected:
            return None
        row = self.orders_table.currentRow()
        return int(self.orders_table.item(row, 0).text())

    def get_selected_order_ids(self):
        selected_rows = set(idx.row() for idx in self.orders_table.selectedIndexes())
        order_ids = []
        for row in selected_rows:
            item = self.orders_table.item(row, 0)
            if item:
                order_ids.append(item.text())
        return order_ids

    def delete_selected_orders(self):
        order_ids = self.get_selected_order_ids()
        if not order_ids:
            self.show_banner("No orders selected.", success=False)
            return
        self.show_loading("Deleting selected orders...")
        failed = []
        for order_id in order_ids:
            success, error = self.main_window.order_service.delete(order_id)
            if not success:
                failed.append((order_id, error))
        self.hide_loading()
        if not failed:
            self.show_banner("All selected orders deleted successfully.", success=True)
        else:
            msg = "Failed to delete: " + ", ".join(f"{oid} ({err})" for oid, err in failed)
            self.show_banner(msg, success=False)
        self.refresh_orders_table()

    def update_action_buttons(self):
        order_id = self.get_selected_order_id()
        if order_id is None:
            if hasattr(self, 'edit_btn'):
                self.edit_btn.setEnabled(False)
            if hasattr(self, 'confirm_btn'):
                self.confirm_btn.setEnabled(False)
            if hasattr(self, 'delete_btn'):
                self.delete_btn.setEnabled(False)
            if hasattr(self, 'pdf_btn'):
                self.pdf_btn.setEnabled(False)
            return
        orders = get_all_orders()
        order = next((o for o in orders if o.id == order_id), None)
        if not order:
            if hasattr(self, 'edit_btn'):
                self.edit_btn.setEnabled(False)
            if hasattr(self, 'confirm_btn'):
                self.confirm_btn.setEnabled(False)
            if hasattr(self, 'delete_btn'):
                self.delete_btn.setEnabled(False)
            if hasattr(self, 'pdf_btn'):
                self.pdf_btn.setEnabled(False)
            return
        if hasattr(self, 'pdf_btn'):
            self.pdf_btn.setEnabled(True)
        if order.status == "pending":
            if hasattr(self, 'edit_btn'):
                self.edit_btn.setEnabled(True)
            if hasattr(self, 'confirm_btn'):
                self.confirm_btn.setEnabled(True)
            if hasattr(self, 'delete_btn'):
                self.delete_btn.setEnabled(True)
        else:
            if hasattr(self, 'edit_btn'):
                self.edit_btn.setEnabled(False)
            if hasattr(self, 'confirm_btn'):
                self.confirm_btn.setEnabled(False)
            if hasattr(self, 'delete_btn'):
                self.delete_btn.setEnabled(False)

    def edit_selected_order(self):
        order_id = self.get_selected_order_id()
        if order_id:
            self.edit_order(order_id)

    def confirm_selected_order(self):
        order_id = self.get_selected_order_id()
        if order_id:
            self.confirm_delivery(order_id)

    def delete_selected_order(self):
        order_id = self.get_selected_order_id()
        if order_id is None:
            self.show_banner("No order selected.", success=False)
            return
        self.show_loading("Deleting order...")
        try:
            success, error = self.main_window.order_service.delete(order_id)
            if success:
                self.show_banner("Order deleted successfully.", success=True)
                self.refresh_orders_table()
            else:
                self.show_banner(f"Failed to delete order: {error}", success=False)
        finally:
            self.hide_loading()

    def download_selected_order_pdf(self):
        order_id = self.get_selected_order_id()
        if order_id:
            self.download_order_pdf(order_id)

    def confirm_delivery(self, order_id):
        if update_order_status(order_id, "completed"):
            QMessageBox.information(self, "Order Completed", f"Order {order_id} marked as completed.")
            self.refresh_orders_table()
        else:
            QMessageBox.warning(self, "Error", f"Failed to update order {order_id}.")

    def edit_order(self, order_id):
        # Fetch order and its medicines
        orders = get_all_orders()
        order = next((o for o in orders if o.id == order_id), None)
        if not order:
            QMessageBox.warning(self, "Error", f"Order {order_id} not found.")
            return
        # Prepare data for dialog
        supplier = order.meds[0].manufacturer if order.meds else ""
        meds = []
        for med in order.meds:
            meds.append({
                'barcode': med.barcode,
                'name': med.name,
                'quantity': med.quantity,
                'expiry': med.expiry,
                'manufacturer': med.manufacturer,
                'order_quantity': med.order_quantity or 1,
            })
        dialog = CreateOrderDialog(self)
        dialog.supplier_name.setText(supplier)
        dialog.meds_table.setRowCount(0)
        for med in meds:
            row = dialog.meds_table.rowCount()
            dialog.meds_table.insertRow(row)
            dialog.meds_table.setItem(row, 0, QTableWidgetItem(str(med['barcode'])))
            dialog.meds_table.setItem(row, 1, QTableWidgetItem(med['name']))
            dialog.meds_table.setItem(row, 2, QTableWidgetItem(str(med['quantity'])))
            dialog.meds_table.setItem(row, 3, QTableWidgetItem(str(med['expiry'])))
            dialog.meds_table.setItem(row, 4, QTableWidgetItem(med['manufacturer']))
            dialog.meds_table.setItem(row, 5, QTableWidgetItem(str(med['order_quantity'])))
        if dialog.exec_() == QDialog.Accepted:
            new_supplier, new_meds = dialog.get_data()
            # Call service to update order
            success, error = self.main_window.order_service.update(order_id, new_supplier, new_meds)
            if success:
                QMessageBox.information(self, "Order Updated", "Order has been updated successfully.")
                self.refresh_orders_table()
            else:
                QMessageBox.warning(self, "Error", f"Failed to update order: {error}")

    def delete_order(self, order_id):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Delete Order", f"Are you sure you want to delete order {order_id}? This cannot be undone.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, error = self.main_window.order_service.delete(order_id)
            if success:
                QMessageBox.information(self, "Order Deleted", f"Order {order_id} has been deleted.")
                self.refresh_orders_table()
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete order: {error}")

    def download_order_pdf(self, order_id):
        import os
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        orders = get_all_orders()
        order = next((o for o in orders if o.id == order_id), None)
        if not order:
            QMessageBox.warning(self, "Error", f"Order {order_id} not found.")
            return
        pdf_path = getattr(order, 'file_path', None)
        if pdf_path and os.path.exists(pdf_path):
            pdf_filename = os.path.basename(pdf_path)
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Order PDF", pdf_filename, "PDF Files (*.pdf)")
            if save_path:
                try:
                    import shutil
                    shutil.copyfile(pdf_path, save_path)
                    QMessageBox.information(self, "Saved", f"Order PDF saved to {save_path}")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not save file: {e}")
        else:
            reply = QMessageBox.question(self, "No PDF", "No PDF file is available for this order. Generate it now?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Generate PDF using service
                order_items = []
                for med in order.meds:
                    order_items.append({
                        'barcode': med.barcode,
                        'name': med.name,
                        'quantity': med.quantity,
                        'expiry': med.expiry,
                        'manufacturer': med.manufacturer,
                        'order_quantity': med.order_quantity or 1,
                    })
                from datetime import datetime
                timestamp = order.timestamp if hasattr(order, 'timestamp') else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                supplier_info = {'name': order.meds[0].manufacturer if order.meds else ''}
                pdf_path = self.main_window.order_service.generate_order_pdf(order_items, order.id, timestamp, supplier_info)
                from db import update_order_file_path
                update_order_file_path(order.id, pdf_path)
                if pdf_path and os.path.exists(pdf_path):
                    open_reply = QMessageBox.question(self, "PDF Generated", "Order PDF has been generated. Do you want to open it now?", QMessageBox.Yes | QMessageBox.No)
                    if open_reply == QMessageBox.Yes:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
                    # Offer to save the new PDF
                    pdf_filename = os.path.basename(pdf_path)
                    save_path, _ = QFileDialog.getSaveFileName(self, "Save Order PDF", pdf_filename, "PDF Files (*.pdf)")
                    if save_path:
                        try:
                            import shutil
                            shutil.copyfile(pdf_path, save_path)
                            QMessageBox.information(self, "Saved", f"Order PDF saved to {save_path}")
                        except Exception as e:
                            QMessageBox.warning(self, "Error", f"Could not save file: {e}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to generate PDF file.")

    def show_context_menu(self, pos):
        menu = QMenu(self)
        view_action = menu.addAction("View Details")
        edit_action = menu.addAction("Edit Order")
        confirm_action = menu.addAction("Confirm Delivery")
        delete_action = menu.addAction("Delete Order")
        action = menu.exec_(self.orders_table.viewport().mapToGlobal(pos))
        row = self.orders_table.currentRow()
        if row < 0:
            return
        order_id = self.orders_table.item(row, 0).text()
        if action == view_action:
            self.view_order_details(order_id)
        elif action == edit_action:
            self.edit_order(int(order_id))
        elif action == confirm_action:
            self.confirm_delivery(int(order_id))
        elif action == delete_action:
            self.delete_order(int(order_id))

    def view_order_details(self, order_id):
        from db import get_all_orders
        orders = get_all_orders()
        order = next((o for o in orders if str(o.id) == str(order_id)), None)
        if not order:
            QMessageBox.warning(self, "Error", f"Order {order_id} not found.")
            return
        dialog = OrderDetailsDialog(order, self)
        dialog.exec_()

    def _on_table_double_clicked(self, row, col):
        order_id = self.orders_table.item(row, 0).text()
        self.view_order_details(order_id) 