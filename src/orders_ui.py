from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QDialog, QLineEdit, QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox, QGroupBox, QSpacerItem, QComboBox)
from PyQt5.QtCore import Qt
from dialogs import SupplierInfoDialog
from order_manager import OrderManager
from PyQt5.QtWidgets import QMessageBox
from db import get_order_items, get_all_orders, update_order_status, get_all_medicines

class InventoryLookupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Medicine from Inventory")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        layout = QVBoxLayout(self)
        from PyQt5.QtWidgets import QLineEdit
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by barcode, name, or manufacturer...")
        self.search_box.textChanged.connect(self.filter_inventory)
        layout.addWidget(self.search_box)
        table_group = QGroupBox("Inventory Medicines")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget(0, 5)
        self.table.setMinimumHeight(250)
        self.table.setHorizontalHeaderLabels(["Barcode", "Name", "Expiry", "Manufacturer", "Quantity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.table)
        layout.addWidget(table_group)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        layout = QVBoxLayout(self)
        form_group = QGroupBox("Order Details")
        form = QFormLayout(form_group)
        self.supplier_name = QLineEdit()
        form.addRow("Supplier Name:", self.supplier_name)
        layout.addWidget(form_group)
        meds_group = QGroupBox("Order Medicines")
        meds_layout = QVBoxLayout(meds_group)
        self.meds_table = QTableWidget(0, 6)
        self.meds_table.setMinimumHeight(220)
        self.meds_table.setHorizontalHeaderLabels(["Barcode", "Name", "Quantity", "Expiry", "Manufacturer", "Order Qty"])
        self.meds_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        meds_layout.addWidget(self.meds_table)
        btn_row_layout = QHBoxLayout()
        btn_add_row = QPushButton("Add Medicine")
        btn_add_row.clicked.connect(self.add_row)
        btn_add_inventory = QPushButton("Add from Inventory")
        btn_add_inventory.clicked.connect(self.add_from_inventory)
        btn_remove_row = QPushButton("Remove Selected Row")
        btn_remove_row.clicked.connect(self.remove_selected_row)
        btn_row_layout.addWidget(btn_add_row)
        btn_row_layout.addWidget(btn_add_inventory)
        btn_row_layout.addWidget(btn_remove_row)
        btn_row_layout.addStretch()
        meds_layout.addLayout(btn_row_layout)
        layout.addWidget(meds_group)
        layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
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
        from PyQt5.QtWidgets import QMessageBox
        supplier, meds = self.get_data()
        if not supplier:
            QMessageBox.warning(self, "Validation Error", "Supplier name is required.")
            return
        if not meds:
            QMessageBox.warning(self, "Validation Error", "At least one medicine is required.")
            return
        for idx, med in enumerate(meds):
            if not all([med['barcode'], med['name'], med['expiry'], med['manufacturer']]):
                QMessageBox.warning(self, "Validation Error", f"All fields are required for medicine row {idx+1}.")
                return
            if med['quantity'] <= 0 or med['order_quantity'] <= 0:
                QMessageBox.warning(self, "Validation Error", f"Quantities must be positive integers for medicine row {idx+1}.")
                return
        self.accept()

class OrdersUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.get_button_stylesheet = main_window.get_button_stylesheet
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Completed"])
        self.status_filter.setFixedWidth(120)
        self.status_filter.currentIndexChanged.connect(self.refresh_orders_table)
        from PyQt5.QtWidgets import QLineEdit
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by supplier, medicine, or order ID...")
        self.search_box.textChanged.connect(self.refresh_orders_table)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(24, 24, 24, 24)
        left_layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Orders Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.create_order_btn = QPushButton("Create Order")
        self.create_order_btn.setMinimumHeight(40)
        self.create_order_btn.setStyleSheet(self.get_button_stylesheet())
        self.create_order_btn.clicked.connect(self.open_create_order_dialog)
        header_layout.addWidget(self.create_order_btn)
        self.send_order_btn = QPushButton("Send Order")
        self.send_order_btn.setMinimumHeight(40)
        self.send_order_btn.setStyleSheet(self.get_button_stylesheet())
        self.send_order_btn.clicked.connect(self.send_order_to_supplier)
        header_layout.addWidget(self.send_order_btn)
        left_layout.addLayout(header_layout)
        # Filter/Search Row
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Status:"))
        filter_row.addWidget(self.status_filter)
        filter_row.addSpacing(20)
        filter_row.addWidget(QLabel("Search:"))
        filter_row.addWidget(self.search_box)
        filter_row.addStretch()
        left_layout.addLayout(filter_row)
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Supplier", "Items", "Total", "Status"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.setAlternatingRowColors(False)
        self.orders_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setSelectionMode(QTableWidget.SingleSelection)
        self.orders_table.itemSelectionChanged.connect(self.update_action_buttons)
        left_layout.addWidget(self.orders_table)
        left_layout.addStretch()
        layout.addLayout(left_layout, 4)
        # Action buttons on the right
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 24, 24, 24)
        right_layout.setSpacing(16)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setStyleSheet(self.get_button_stylesheet())
        self.edit_btn.setMinimumHeight(40)
        self.edit_btn.clicked.connect(self.edit_selected_order)
        right_layout.addWidget(self.edit_btn)
        self.confirm_btn = QPushButton("Confirm Delivery")
        self.confirm_btn.setStyleSheet(self.get_button_stylesheet())
        self.confirm_btn.setMinimumHeight(40)
        self.confirm_btn.clicked.connect(self.confirm_selected_order)
        right_layout.addWidget(self.confirm_btn)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet(self.get_button_stylesheet())
        self.delete_btn.setMinimumHeight(40)
        self.delete_btn.clicked.connect(self.delete_selected_order)
        right_layout.addWidget(self.delete_btn)
        self.pdf_btn = QPushButton("Download/View PDF")
        self.pdf_btn.setStyleSheet(self.get_button_stylesheet())
        self.pdf_btn.setMinimumHeight(40)
        self.pdf_btn.clicked.connect(self.download_selected_order_pdf)
        right_layout.addWidget(self.pdf_btn)
        right_layout.addStretch()
        layout.addLayout(right_layout, 1)
        self.setLayout(layout)
        self.refresh_orders_table()
        self.update_action_buttons()

    def open_create_order_dialog(self):
        dialog = CreateOrderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            supplier, meds = dialog.get_data()
            if not supplier or not meds:
                QMessageBox.warning(self, "Missing Data", "Supplier and at least one medicine are required.")
                return
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # For now, PDF path is empty; can be generated later
            pdf_path = ""
            # Call service to add order
            success, error = self.main_window.order_service.add(timestamp, pdf_path, meds)
            if success:
                QMessageBox.information(self, "Order Created", "Order has been created successfully.")
                self.refresh_orders_table()
            else:
                QMessageBox.warning(self, "Error", f"Failed to create order: {error}")

    def send_order_to_supplier(self):
        selected = self.orders_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Order Selected", "Please select an order to send.")
            return
        order_id = self.orders_table.item(selected, 0).text()
        order_date = self.orders_table.item(selected, 1).text()
        supplier_name = self.orders_table.item(selected, 2).text()
        # You may need to fetch order_items from your data model, here we use a placeholder
        order_items = self.get_order_items_for_order(order_id)
        dialog = SupplierInfoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            supplier_info = dialog.get_data()
            # Add order_id and timestamp to supplier_info for PDF and notifications
            supplier_info['order_id'] = order_id
            supplier_info['order_date'] = order_date
            manager = OrderManager()
            results = manager.send_order_to_supplier(supplier_info, order_items, order_id, order_date)
            msg = '\n'.join([f"{channel}: {'Success' if success else 'Failed'} - {message}" for channel, success, message in results])
            QMessageBox.information(self, "Send Order Result", msg)

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
        self.orders_table.setRowCount(len(orders))
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Supplier", "Items", "Total", "Status"
        ])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.timestamp))
            supplier = order.meds[0].manufacturer if order.meds else ""
            self.orders_table.setItem(row, 2, QTableWidgetItem(supplier))
            items = ", ".join([med.name for med in order.meds])
            self.orders_table.setItem(row, 3, QTableWidgetItem(items))
            total = sum([med.order_quantity or 0 for med in order.meds])
            self.orders_table.setItem(row, 4, QTableWidgetItem(str(total)))
            self.orders_table.setItem(row, 5, QTableWidgetItem(order.status))

    def get_selected_order_id(self):
        selected = self.orders_table.selectedItems()
        if not selected:
            return None
        row = self.orders_table.currentRow()
        return int(self.orders_table.item(row, 0).text())

    def update_action_buttons(self):
        order_id = self.get_selected_order_id()
        if order_id is None:
            self.edit_btn.setEnabled(False)
            self.confirm_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.pdf_btn.setEnabled(False)
            return
        orders = get_all_orders()
        order = next((o for o in orders if o.id == order_id), None)
        if not order:
            self.edit_btn.setEnabled(False)
            self.confirm_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.pdf_btn.setEnabled(False)
            return
        self.pdf_btn.setEnabled(True)
        if order.status == "pending":
            self.edit_btn.setEnabled(True)
            self.confirm_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.edit_btn.setEnabled(False)
            self.confirm_btn.setEnabled(False)
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
        if order_id:
            self.delete_order(order_id)

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