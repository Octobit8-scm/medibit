from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QStackedWidget, QFileDialog, QMessageBox, QProgressDialog, QComboBox, QMenu, QShortcut)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QKeySequence, QColor
import pandas as pd
import datetime
from db import add_medicine, get_medicine_by_barcode, update_medicine, get_all_medicines
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from db import get_pharmacy_details
import json
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QProgressDialog, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel
import logging
import psutil, os
import tempfile
import threading
from theme import theme_manager, create_animated_button
from dialogs import AddMedicineDialog

logger = logging.getLogger("medibit")

def log_memory_usage(tag=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)
    logging.info(f"Memory usage {tag}: {mem:.2f} MB")

class InventoryProgressDialog(QDialog):
    def __init__(self, title, label_text, maximum, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 200)
        self.setStyleSheet(theme_manager.get_dialog_stylesheet())
        layout = QVBoxLayout(self)
        self.label = QLabel(label_text)
        self.label.setStyleSheet("font-size: 15px; margin-bottom: 8px;")
        self.label.setToolTip("Progress label for inventory operation.")
        self.label.setAccessibleName("Inventory Progress Label")
        layout.addWidget(self.label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("height: 32px; font-size: 18px;")
        self.progress_bar.setToolTip("Shows progress of import/export operation.")
        self.progress_bar.setAccessibleName("Inventory Progress Bar")
        layout.addWidget(self.progress_bar)
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.setToolTip("Cancel the ongoing operation.")
        self.cancel_btn.setAccessibleName("Inventory Progress Cancel Button")
        self.cancel_btn.clicked.connect(self.reject)
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setEnabled(False)
        self.ok_btn.setFixedWidth(100)
        self.ok_btn.setToolTip("Acknowledge completion of operation.")
        self.ok_btn.setAccessibleName("Inventory Progress OK Button")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)
    def set_progress(self, value, label_text=None):
        self.progress_bar.setValue(value)
        if label_text:
            self.label.setText(label_text)
        QApplication.processEvents()
    def complete(self, done_label="Operation complete."):
        self.ok_btn.setEnabled(True)
        self.cancel_btn.hide()
        self.label.setText(done_label)
        QApplication.processEvents()

class ImportWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(int, int, int, list, list, list)
    canceled = pyqtSignal()

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        imported, updated, errors = 0, 0, 0
        imported_barcodes, updated_barcodes, error_details = [], [], []
        row_count = len(self.df)
        try:
            log_memory_usage("import worker start")
            for idx, row in self.df.iterrows():
                if self._cancel:
                    self.canceled.emit()
                    for handler in logging.root.handlers:
                        handler.flush()
                    return
                if idx % 20 == 0 or idx == row_count - 1:
                    log_memory_usage(f"import row {idx}")
                self.progress.emit(idx, f"Processing row {idx+1} of {row_count}...")
                try:
                    barcode = str(row["Barcode"]).strip()
                    name = str(row["Name"]).strip()
                    quantity = row["Quantity"]
                    threshold = row["Threshold"] if "Threshold" in row and not pd.isna(row["Threshold"]) else 10
                    expiry = row["Expiry"] if "Expiry" in row and not pd.isna(row["Expiry"]) else None
                    manufacturer = str(row["Manufacturer"]) if "Manufacturer" in row and not pd.isna(row["Manufacturer"]) else ""
                    price = row["Price"] if "Price" in row and not pd.isna(row["Price"]) else 0
                    # Use InventoryService for DB access
                    from inventory_service import InventoryService
                    service = InventoryService()
                    validation_errors = InventoryUi.validate_medicine_input_static(barcode, name, quantity, expiry, manufacturer, price, threshold, is_add=(service.get_all() and not any(m.barcode == barcode for m in service.get_all())))
                    if validation_errors:
                        errors += 1
                        error_details.append(f"Row {idx+2} (Barcode: {barcode}): {'; '.join(validation_errors)}")
                        continue
                    # Convert expiry to Python date object if needed
                    if expiry:
                        import datetime
                        if isinstance(expiry, str):
                            try:
                                expiry = datetime.datetime.strptime(expiry, "%Y-%m-%d").date()
                            except Exception:
                                expiry = None
                        elif hasattr(expiry, 'to_pydatetime'):
                            expiry = expiry.to_pydatetime().date()
                        elif isinstance(expiry, datetime.datetime):
                            expiry = expiry.date()
                        elif not isinstance(expiry, datetime.date):
                            expiry = None
                    existing = [m for m in service.get_all() if m.barcode == barcode]
                    if existing:
                        success, msg = service.update(barcode, {
                            "name": name,
                            "quantity": int(quantity),
                            "expiry": expiry,
                            "manufacturer": manufacturer,
                            "price": int(price),
                            "threshold": int(threshold)
                        })
                        if success:
                            updated += 1
                            updated_barcodes.append(barcode)
                        else:
                            errors += 1
                            error_details.append(f"Row {idx+2} (Barcode: {barcode}): {msg}")
                    else:
                        result = service.add({
                            "barcode": barcode,
                            "name": name,
                            "quantity": int(quantity),
                            "expiry": expiry,
                            "manufacturer": manufacturer,
                            "price": int(price),
                            "threshold": int(threshold)
                        })
                        if result[0]:
                            imported += 1
                            imported_barcodes.append(barcode)
                        else:
                            errors += 1
                            error_details.append(f"Row {idx+2} (Barcode: {barcode}): {result[1]}")
                except Exception as e:
                    errors += 1
                    error_details.append(f"Row {idx+2} (Barcode: {row.get('Barcode', 'N/A')}): {e}")
            log_memory_usage("import worker complete")
            self.progress.emit(row_count, "Import complete.")
            self.finished.emit(imported, updated, errors, imported_barcodes, updated_barcodes, error_details)
        except Exception as e:
            logging.critical("Fatal error in import worker", exc_info=True)
            for handler in logging.root.handlers:
                handler.flush()
            self.canceled.emit()
        except BaseException as e:
            logging.critical("Non-standard fatal error in import worker", exc_info=True)
            for handler in logging.root.handlers:
                handler.flush()
            self.canceled.emit()
        for handler in logging.root.handlers:
            handler.flush()

class ExportWorker(QObject):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    canceled = pyqtSignal()

    def __init__(self, medicines, file_path):
        super().__init__()
        self.medicines = medicines
        self.file_path = file_path
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            data = []
            row_count = len(self.medicines)
            for idx, med in enumerate(self.medicines):
                if self._cancel:
                    self.canceled.emit()
                    return
                # Build dict for each medicine
                data.append({
                    'Barcode': med.barcode,
                    'Name': med.name,
                    'Quantity': med.quantity,
                    'Threshold': med.threshold,
                    'Expiry': str(med.expiry),
                    'Manufacturer': med.manufacturer,
                    'Price': med.price
                })
                # Throttle progress updates: every 500 rows and last row
                if idx % 500 == 0 or idx == row_count - 1:
                    self.progress.emit(idx, f"Processing row {idx+1} of {row_count}...")
            self.progress.emit(row_count, "Export complete.")
            # Write DataFrame to Excel directly
            df = pd.DataFrame(data)
            df.to_excel(self.file_path, index=False)
            logging.info(f"[WORKER] Excel file written: {self.file_path}")
            self.finished.emit(self.file_path)
        except Exception as exc:
            logging.critical("[WORKER] Exception during export", exc_info=True)
            self.error.emit(str(exc))
        except BaseException as exc:
            logging.critical(f"Non-standard fatal error in ExportWorker: {exc}", exc_info=True)
            self.error.emit(str(exc))
        for handler in logging.root.handlers:
            handler.flush()

class InventoryUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        logger.info("InventoryUi initialized")
        self.init_ui()
        # Connect validation to add/edit actions
        # Only connect the button once
        try:
            self.add_medicine_btn.clicked.disconnect()
        except Exception:
            pass
        self.add_medicine_btn.clicked.connect(self._on_add_medicine)
        # If you have edit button, connect similarly

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        title.setToolTip("Section: Inventory Management")
        title.setAccessibleName("Inventory Management Title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Header buttons
        self.add_medicine_btn = create_animated_button("Add Medicine", self)
        self.add_medicine_btn.setMinimumHeight(40)
        self.add_medicine_btn.setToolTip("Add a new medicine to the inventory.")
        self.add_medicine_btn.setAccessibleName("Add Medicine Button")
        
        self.scan_barcode_btn = create_animated_button("Scan Barcode", self)
        self.scan_barcode_btn.setMinimumHeight(40)
        self.scan_barcode_btn.setToolTip("Scan barcode to quickly add medicine.")
        self.scan_barcode_btn.setAccessibleName("Scan Barcode Button")
        self.scan_barcode_btn.clicked.connect(self._on_scan_barcode)
        
        header_layout.addWidget(self.add_medicine_btn)
        header_layout.addWidget(self.scan_barcode_btn)
        layout.addLayout(header_layout)
        # Search and Filter Section
        search_frame = QFrame()
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 12, 12, 12)
        search_layout.setSpacing(10)
        
        # Search title and basic search
        search_header = QHBoxLayout()
        search_title = QLabel("Search & Filter")
        search_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        search_title.setToolTip("Section: Search and Filter")
        search_title.setAccessibleName("Search Filter Title")
        search_header.addWidget(search_title)
        search_header.addStretch()
        
        # Basic search row
        basic_search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold;")
        basic_search_layout.addWidget(search_label)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by barcode, name, or manufacturer...")
        self.search_box.setToolTip("Search medicines by barcode, name, or manufacturer.")
        self.search_box.setAccessibleName("Search Box")
        self.search_box.textChanged.connect(self.filter_inventory)
        basic_search_layout.addWidget(self.search_box)
        
        # Action buttons
        self.export_btn = create_animated_button("Export", self)
        self.export_btn.setToolTip("Export inventory data to Excel file.")
        self.export_btn.setAccessibleName("Export Button")
        self.export_btn.clicked.connect(self.export_to_excel)
        basic_search_layout.addWidget(self.export_btn)
        
        self.import_btn = create_animated_button("Import", self)
        self.import_btn.setToolTip("Import inventory data from Excel file.")
        self.import_btn.setAccessibleName("Import Button")
        self.import_btn.clicked.connect(self.import_from_excel)
        basic_search_layout.addWidget(self.import_btn)
        
        search_layout.addLayout(search_header)
        search_layout.addLayout(basic_search_layout)
        
        # Advanced filters row
        filter_layout = QHBoxLayout()
        
        # Stock status filter
        stock_label = QLabel("Stock Status:")
        stock_label.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(stock_label)
        self.stock_filter = QComboBox()
        self.stock_filter.addItems(["All", "Low Stock", "Out of Stock", "In Stock"])
        self.stock_filter.setToolTip("Filter by stock status.")
        self.stock_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.stock_filter)
        
        # Expiry filter
        expiry_label = QLabel("Expiry:")
        expiry_label.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(expiry_label)
        self.expiry_filter = QComboBox()
        self.expiry_filter.addItems(["All", "Expired", "Expiring Soon (30 days)", "Valid"])
        self.expiry_filter.setToolTip("Filter by expiry status.")
        self.expiry_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.expiry_filter)
        
        # Manufacturer filter
        manufacturer_label = QLabel("Manufacturer:")
        manufacturer_label.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(manufacturer_label)
        self.manufacturer_filter = QComboBox()
        self.manufacturer_filter.addItems(["All"])
        self.manufacturer_filter.setToolTip("Filter by manufacturer.")
        self.manufacturer_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.manufacturer_filter)
        
        # Clear filters button
        self.clear_filters_btn = QPushButton("Clear Filters")
        self.clear_filters_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.clear_filters_btn.setToolTip("Clear all applied filters.")
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(self.clear_filters_btn)
        
        filter_layout.addStretch()
        search_layout.addLayout(filter_layout)
        layout.addWidget(search_frame)
        # Inventory Table
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)
        table_title = QLabel("Inventory Items")
        table_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        table_title.setToolTip("Section: Inventory Items")
        table_title.setAccessibleName("Inventory Items Title")
        table_layout.addWidget(table_title)
        self.inventory_table = QTableWidget(0, 7)
        self.inventory_table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Quantity", "Threshold", "Expiry", "Manufacturer", "Price"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.inventory_table.setToolTip("Table showing all medicines in inventory.")
        self.inventory_table.setAccessibleName("Inventory Table")
        self.inventory_table.itemSelectionChanged.connect(self.on_item_selected)
        
        # Enable sorting
        self.inventory_table.setSortingEnabled(True)
        self.inventory_table.horizontalHeader().setSectionsClickable(True)
        
        # Connect sorting signal
        self.inventory_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        # Enable context menu
        self.inventory_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.inventory_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        # Initialize inventory service
        from inventory_service import InventoryService
        self.inventory_service = InventoryService()
        # Table and buttons layout (horizontal)
        table_and_buttons_layout = QHBoxLayout()
        
        # Table takes most of the space
        table_and_buttons_layout.addWidget(self.inventory_table, stretch=4)
        
        # Vertical button column on the right
        button_column = QVBoxLayout()
        button_column.setSpacing(8)
        button_column.setContentsMargins(16, 0, 0, 0)
        
        # Action buttons in vertical column
        self.edit_medicine_btn = create_animated_button("Edit Selected", self)
        self.edit_medicine_btn.setMinimumHeight(36)
        self.edit_medicine_btn.setToolTip("Edit the selected medicine.")
        self.edit_medicine_btn.setAccessibleName("Edit Selected Button")
        self.edit_medicine_btn.clicked.connect(self.edit_selected_medicine)
        
        self.delete_medicine_btn = create_animated_button("Delete Selected", self)
        self.delete_medicine_btn.setMinimumHeight(36)
        self.delete_medicine_btn.setToolTip("Delete the selected medicine.")
        self.delete_medicine_btn.setAccessibleName("Delete Selected Button")
        self.delete_medicine_btn.clicked.connect(self.delete_selected_medicine)
        
        self.generate_order_btn = create_animated_button("Generate Order", self)
        self.generate_order_btn.setMinimumHeight(36)
        self.generate_order_btn.setToolTip("Generate order for low stock medicines.")
        self.generate_order_btn.setAccessibleName("Generate Order Button")
        self.generate_order_btn.clicked.connect(self._on_generate_order)
        
        self.clear_inventory_btn = create_animated_button("Clear Inventory", self)
        self.clear_inventory_btn.setMinimumHeight(36)
        self.clear_inventory_btn.setToolTip("Clear all inventory data (use with caution).")
        self.clear_inventory_btn.setAccessibleName("Clear Inventory Button")
        self.clear_inventory_btn.clicked.connect(self._on_clear_inventory)
        
        # Add buttons to vertical column
        button_column.addWidget(self.edit_medicine_btn)
        button_column.addWidget(self.delete_medicine_btn)
        button_column.addWidget(self.generate_order_btn)
        button_column.addWidget(self.clear_inventory_btn)
        button_column.addStretch()  # Push buttons to top
        
        # Add button column to the right of table
        table_and_buttons_layout.addLayout(button_column, stretch=1)
        
        table_layout.addLayout(table_and_buttons_layout)
        layout.addWidget(table_frame)
        

        # Load initial data
        self.load_inventory()

    def refresh_inventory_table(self):
        medicines = self.inventory_service.get_all()
        self.filter_inventory_table()

    def filter_inventory_table(self):
        query = self.search_box.text().strip().lower()
        filtered = self.inventory_service.search(query)
        
        # Apply advanced filters
        filtered = self.apply_advanced_filters(filtered)
        
        # Performance optimization: Disable sorting during bulk update
        self.inventory_table.setSortingEnabled(False)
        
        # Batch update table
        self.inventory_table.clearContents()
        self.inventory_table.setRowCount(len(filtered))
        
        # Use blockSignals for better performance
        self.inventory_table.blockSignals(True)
        
        from datetime import date
        
        for i, med in enumerate(filtered):
            # Barcode
            self.inventory_table.setItem(i, 0, QTableWidgetItem(med.barcode))
            
            # Name with status indicators
            name_text = med.name
            if hasattr(med, 'threshold') and med.quantity <= med.threshold:
                name_text += " 🔴"  # Low stock indicator
            if med.expiry and med.expiry <= date.today():
                name_text += " ⚠️"  # Expired indicator
            elif med.expiry and (med.expiry - date.today()).days <= 30:
                name_text += " 🟡"  # Expiring soon indicator
            
            name_item = QTableWidgetItem(name_text)
            self.inventory_table.setItem(i, 1, name_item)
            
            # Quantity with color coding
            quantity_item = QTableWidgetItem(str(med.quantity))
            quantity_item.setTextAlignment(Qt.AlignCenter)
            if hasattr(med, 'threshold') and med.quantity <= med.threshold:
                quantity_item.setBackground(QColor(255, 200, 200))  # Light red for low stock
            self.inventory_table.setItem(i, 2, quantity_item)
            
            # Threshold
            threshold_item = QTableWidgetItem(str(getattr(med, 'threshold', 10)))
            threshold_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_table.setItem(i, 3, threshold_item)
            
            # Expiry with color coding
            expiry_text = str(med.expiry) if med.expiry else "N/A"
            expiry_item = QTableWidgetItem(expiry_text)
            expiry_item.setTextAlignment(Qt.AlignCenter)
            if med.expiry:
                if med.expiry <= date.today():
                    expiry_item.setBackground(QColor(255, 150, 150))  # Red for expired
                elif (med.expiry - date.today()).days <= 30:
                    expiry_item.setBackground(QColor(255, 255, 150))  # Yellow for expiring soon
            self.inventory_table.setItem(i, 4, expiry_item)
            
            # Manufacturer
            self.inventory_table.setItem(i, 5, QTableWidgetItem(med.manufacturer or "N/A"))
            
            # Price
            price_item = QTableWidgetItem(f"₹{getattr(med, 'price', 0)}")
            price_item.setTextAlignment(Qt.AlignCenter)
            self.inventory_table.setItem(i, 6, price_item)
        
        # Re-enable signals and sorting
        self.inventory_table.blockSignals(False)
        self.inventory_table.setSortingEnabled(True)
        
        self.inventory_table.viewport().update()
        self.inventory_table.repaint()
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
    
    def apply_advanced_filters(self, medicines):
        """Apply advanced filters to the medicine list."""
        from datetime import date
        
        filtered = medicines
        
        # Stock status filter
        stock_filter = self.stock_filter.currentText()
        if stock_filter == "Low Stock":
            filtered = [m for m in filtered if hasattr(m, 'threshold') and m.quantity <= m.threshold]
        elif stock_filter == "Out of Stock":
            filtered = [m for m in filtered if m.quantity == 0]
        elif stock_filter == "In Stock":
            filtered = [m for m in filtered if m.quantity > 0]
        
        # Expiry filter
        expiry_filter = self.expiry_filter.currentText()
        if expiry_filter == "Expired":
            filtered = [m for m in filtered if m.expiry and m.expiry <= date.today()]
        elif expiry_filter == "Expiring Soon (30 days)":
            filtered = [m for m in filtered if m.expiry and (m.expiry - date.today()).days <= 30 and m.expiry > date.today()]
        elif expiry_filter == "Valid":
            filtered = [m for m in filtered if m.expiry and m.expiry > date.today()]
        
        # Manufacturer filter
        manufacturer_filter = self.manufacturer_filter.currentText()
        if manufacturer_filter != "All":
            filtered = [m for m in filtered if m.manufacturer == manufacturer_filter]
        
        return filtered

    @staticmethod
    def validate_medicine_input_static(barcode, name, quantity, expiry, manufacturer, price, threshold, is_add=True):
        errors = []
        if not barcode or not str(barcode).strip():
            errors.append("Barcode cannot be empty.")
        if not name or not str(name).strip():
            errors.append("Name cannot be empty.")
        try:
            quantity = int(quantity)
            if quantity < 0:
                errors.append("Quantity must be a non-negative integer.")
        except Exception:
            errors.append("Quantity must be a non-negative integer.")
        try:
            price = int(price)
            if price < 0:
                errors.append("Price must be a non-negative integer.")
        except Exception:
            errors.append("Price must be a non-negative integer.")
        try:
            threshold = int(threshold)
            if threshold < 0:
                errors.append("Threshold must be a non-negative integer.")
        except Exception:
            errors.append("Threshold must be a non-negative integer.")
        # Optionally, validate expiry date format
        if expiry:
            import datetime
            try:
                if isinstance(expiry, str):
                    datetime.datetime.strptime(expiry, "%Y-%m-%d")
            except Exception:
                errors.append("Expiry must be in YYYY-MM-DD format or empty.")
        # Check for duplicate barcode on add
        if is_add:
            from db import get_medicine_by_barcode
            if get_medicine_by_barcode(barcode):
                errors.append("A medicine with this barcode already exists.")
        return errors

    def _on_add_medicine(self):
        logger.info("Add Medicine button clicked.")
        try:
            dialog = AddMedicineDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                med_data = dialog.get_data()
                logger.debug(f"Adding medicine: {med_data}")
                
                # Enhanced validation
                errors = self.validate_medicine_input_static(
                    med_data['barcode'], med_data['name'], med_data['quantity'], 
                    med_data['expiry'], med_data['manufacturer'], med_data['price'], 
                    med_data['threshold'], is_add=True
                )
                
                if errors:
                    logger.warning(f"Validation failed for new medicine: {errors}")
                    QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                    return
                
                # Additional business logic validation
                if med_data['quantity'] < 0:
                    QMessageBox.warning(self, "Validation Error", "Quantity cannot be negative.")
                    return
                
                if med_data['price'] < 0:
                    QMessageBox.warning(self, "Validation Error", "Price cannot be negative.")
                    return
                
                # Proceed with add
                result = self.inventory_service.add(med_data)
                if not result[0]:
                    logger.error(f"Failed to add medicine: {result[1]}")
                    QMessageBox.warning(self, "Add Failed", result[1])
                    return  # Exit early on failure
                else:
                    self.refresh_inventory_table()
                    self.populate_manufacturer_filter()  # Update manufacturer filter
                    logger.info("Medicine added successfully.")
                    QMessageBox.information(self, "Success", "Medicine added successfully!")
                    return  # Exit after success
        except Exception as e:
            logger.error(f"Exception in add medicine: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An error occurred while adding medicine: {e}")

    def import_from_excel(self):
        try:
            log_memory_usage("main thread before import")
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
            if not file_path:
                return
            required_columns = ["Barcode", "Name", "Quantity"]
            optional_columns = {"Threshold": 10, "Expiry": None, "Manufacturer": "", "Price": 0}
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to read Excel file:\n{e}")
                return
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                QMessageBox.critical(self, "Import Error", f"Missing required columns: {', '.join(missing)}")
                return
            row_count = len(df)
            progress = InventoryProgressDialog("Importing Inventory", f"Processing row 0 of {row_count}...", row_count, self)
            worker = ImportWorker(df)
            thread = QThread()
            worker.moveToThread(thread)
            worker.progress.connect(lambda idx, text: progress.set_progress(idx, text))
            worker.finished.connect(lambda imported, updated, errors, imported_barcodes, updated_barcodes, error_details: self._on_import_finished(progress, thread, imported, updated, errors, imported_barcodes, updated_barcodes, error_details))
            worker.canceled.connect(lambda: self._on_import_canceled(progress, thread))
            progress.cancel_btn.clicked.connect(worker.cancel)
            thread.started.connect(worker.run)
            thread.start()
            progress.exec_()
            log_memory_usage("main thread after starting import thread")
        except Exception as e:
            logging.critical("Fatal error in main thread import trigger", exc_info=True)
            for handler in logging.root.handlers:
                handler.flush()
            QMessageBox.critical(self, "Import Error", f"A fatal error occurred during import. See log for details.\n{e}")
        except BaseException as e:
            logging.critical("Non-standard fatal error in main thread import trigger", exc_info=True)
            for handler in logging.root.handlers:
                handler.flush()
            QMessageBox.critical(self, "Import Error", f"A non-standard fatal error occurred during import. See log for details.\n{e}")

    def _on_import_finished(self, progress, thread, imported, updated, errors, imported_barcodes, updated_barcodes, error_details):
        progress.complete("Import complete.")
        thread.quit()
        thread.wait()
        self.refresh_inventory_table()
        count = len(self.inventory_service.get_all())
        summary = f"Imported: {imported}\nUpdated: {updated}\nErrors: {errors}\nTotal medicines in DB: {count}\n"
        summary += f"\nImported Barcodes (first 10): {imported_barcodes[:10]}"
        summary += f"\nUpdated Barcodes (first 10): {updated_barcodes[:10]}"
        if errors:
            summary += f"\n\nError Details (first 10):\n" + '\n'.join(error_details[:10])
        QMessageBox.information(self, "Import Complete", summary)

    def _on_import_canceled(self, progress, thread):
        progress.complete("Import canceled.")
        thread.quit()
        thread.wait()

    def export_to_excel(self):
        try:
            log_memory_usage("main thread before export")
            logging.info("Starting export_to_excel operation.")
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Inventory Export", "inventory_export.xlsx", "Excel Files (*.xlsx)")
            if not file_path:
                return
            medicines = self.inventory_service.get_all()
            if not medicines:
                logging.info("No inventory data to export.")
                QMessageBox.information(self, "Export", "No inventory data to export.")
                return
            row_count = len(medicines)
            logging.info(f"Exporting {row_count} medicines.")
            progress = InventoryProgressDialog("Exporting Inventory", f"Processing row 0 of {row_count}...", row_count, self)
            self._export_thread = QThread()
            self._export_worker = ExportWorker(medicines, file_path)
            self._export_worker.moveToThread(self._export_thread)
            self._export_worker.progress.connect(lambda idx, text: (logging.info(f"Export progress: {text}"), progress.set_progress(idx, text)))
            self._export_worker.finished.connect(self._on_export_finished)
            self._export_worker.error.connect(self._on_export_error)
            self._export_worker.canceled.connect(self._on_export_canceled)
            progress.cancel_btn.clicked.connect(self._export_worker.cancel)
            self._export_thread.started.connect(self._export_worker.run)
            self._export_thread.start()
            self._export_progress = progress
            progress.exec_()
            log_memory_usage("main thread after starting export thread")
        except Exception as e:
            logging.critical("Fatal error in main thread export trigger", exc_info=True)
            for handler in logging.root.handlers:
                handler.flush()
            QMessageBox.critical(self, "Export Error", f"A fatal error occurred during export. See log for details.\n{e}")
        except BaseException as e:
            logging.critical("Non-standard fatal error in main thread export trigger", exc_info=True)
            for handler in logging.root.handlers:
                handler.flush()
            QMessageBox.critical(self, "Export Error", f"A non-standard fatal error occurred during export. See log for details.\n{e}")

    def _on_export_finished(self, file_path):
        self._export_progress.complete("Export complete.")
        self._export_thread.quit()
        self._export_thread.wait()
        self._export_worker.deleteLater()
        self._export_thread.deleteLater()
        QMessageBox.information(self, "Export Complete", f"Inventory exported to file: {file_path}")

    def _on_export_error(self, error_msg):
        self._export_progress.complete("Export failed.")
        self._export_thread.quit()
        self._export_thread.wait()
        self._export_worker.deleteLater()
        self._export_thread.deleteLater()
        QMessageBox.critical(self, "Export Error", f"Export failed: {error_msg}")

    def _on_export_canceled(self):
        progress = self._export_progress
        thread = self._export_thread
        logging.info("Export operation canceled by user.")
        progress.complete("Export canceled.")
        thread.quit()
        thread.wait()
        self._export_worker.deleteLater()
        self._export_thread.deleteLater()
        self._export_worker = None
        self._export_thread = None
        self._export_progress = None

    def send_inventory_email(self, file_path):
        # Load SMTP config from order_manager config
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            email_cfg = config.get('email', {})
        except Exception as e:
            return False, f"Failed to load email config: {e}"
        if not email_cfg.get('enabled'):
            return False, "Email notifications are disabled in config."
        pharmacy = get_pharmacy_details()
        if not pharmacy or not pharmacy.email:
            return False, "Pharmacy email not configured."
        try:
            msg = MIMEMultipart()
            msg['From'] = email_cfg['sender_email']
            msg['To'] = pharmacy.email
            msg['Subject'] = "Pharmacy Inventory Export"
            body = f"Dear {pharmacy.name},\n\nPlease find attached the latest inventory export from your Medibit system.\n\nBest regards,\nMedibit Team"
            msg.attach(MIMEText(body, 'plain'))
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename=inventory_export.xlsx",
            )
            msg.attach(part)
            server = smtplib.SMTP(email_cfg['smtp_server'], email_cfg['smtp_port'])
            server.starttls()
            server.login(email_cfg['sender_email'], email_cfg['sender_password'])
            server.send_message(msg)
            server.quit()
            return True, "Email sent"
        except Exception as e:
            return False, str(e) 

    def edit_selected_medicine(self):
        """Edit the selected medicine in the table."""
        logger.info("Edit Selected Medicine button clicked.")
        current_row = self.inventory_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a medicine to edit.")
            return
        
        # Get the barcode of the selected medicine
        barcode_item = self.inventory_table.item(current_row, 0)
        if not barcode_item:
            QMessageBox.warning(self, "Error", "Could not get medicine barcode.")
            return
        
        barcode = barcode_item.text()
        logger.debug(f"Editing medicine with barcode: {barcode}")
        
        # Get the medicine object from the service
        medicines = self.inventory_service.get_all()
        medicine = next((m for m in medicines if m.barcode == barcode), None)
        
        if not medicine:
            QMessageBox.warning(self, "Error", "Could not find medicine in database.")
            return
        
        # Open edit dialog
        from dialogs import EditMedicineDialog
        dialog = EditMedicineDialog(medicine, self)
        if dialog.exec_() == QDialog.Accepted:
            # Get updated data and save using service
            updated_data = dialog.get_data()
            result = self.inventory_service.update(barcode, updated_data)
            if result[0]:
                logger.info(f"Medicine updated successfully: {barcode}")
                self.refresh_inventory_table()
                QMessageBox.information(self, "Success", "Medicine updated successfully!")
            else:
                logger.error(f"Failed to update medicine: {result[1]}")
                QMessageBox.warning(self, "Update Failed", result[1])

    def delete_selected_medicine(self):
        """Delete the selected medicine from the table."""
        logger.info("Delete Selected Medicine button clicked.")
        current_row = self.inventory_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a medicine to delete.")
            return
        
        # Get the barcode of the selected medicine
        barcode_item = self.inventory_table.item(current_row, 0)
        if not barcode_item:
            QMessageBox.warning(self, "Error", "Could not get medicine barcode.")
            return
        
        barcode = barcode_item.text()
        logger.debug(f"Deleting medicine with barcode: {barcode}")
        
        # Confirm deletion
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete medicine with barcode {barcode}?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                result = self.inventory_service.delete(barcode)
                if result[0]:
                    logger.info(f"Medicine deleted: {barcode}")
                    self.refresh_inventory_table()
                    QMessageBox.information(self, "Success", "Medicine deleted successfully.")
                else:
                    logger.error(f"Failed to delete medicine: {result[1]}")
                    QMessageBox.warning(self, "Delete Failed", result[1])
            except Exception as e:
                logger.error(f"Exception while deleting medicine: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"An error occurred while deleting the medicine: {e}")

    def on_item_selected(self):
        """Handle item selection in the inventory table."""
        current_row = self.inventory_table.currentRow()
        if current_row >= 0:
            logger.debug(f"Medicine selected at row: {current_row}")
        else:
            logger.debug("No medicine selected")

    def load_inventory(self):
        """Load and display inventory data."""
        logger.info("Loading inventory data.")
        try:
            self.refresh_inventory_table()
            self.populate_manufacturer_filter()
            logger.info("Inventory data loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load inventory: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load inventory data: {e}")

    def filter_inventory(self):
        """Filter inventory based on search text."""
        logger.debug("Filtering inventory.")
        self.filter_inventory_table()
    
    def on_header_clicked(self, logical_index):
        """Handle header click for custom sorting."""
        logger.debug(f"Header clicked: column {logical_index}")
        # The built-in sorting will handle most cases, but we can add custom logic here if needed
        self.filter_inventory_table()  # Refresh to maintain status indicators
    
    def apply_filters(self):
        """Apply all active filters to the inventory table."""
        logger.debug("Applying filters")
        self.filter_inventory_table()
    
    def clear_filters(self):
        """Clear all applied filters."""
        logger.debug("Clearing all filters")
        self.stock_filter.setCurrentText("All")
        self.expiry_filter.setCurrentText("All")
        self.manufacturer_filter.setCurrentText("All")
        self.search_box.clear()
        self.filter_inventory_table()
    
    def populate_manufacturer_filter(self):
        """Populate manufacturer filter with unique manufacturers."""
        try:
            medicines = self.inventory_service.get_all()
            manufacturers = set()
            for medicine in medicines:
                if medicine.manufacturer:
                    manufacturers.add(medicine.manufacturer)
            
            current_text = self.manufacturer_filter.currentText()
            self.manufacturer_filter.clear()
            self.manufacturer_filter.addItems(["All"] + sorted(list(manufacturers)))
            
            # Restore selection if it still exists
            if current_text in [self.manufacturer_filter.itemText(i) for i in range(self.manufacturer_filter.count())]:
                self.manufacturer_filter.setCurrentText(current_text)
        except Exception as e:
            logger.error(f"Error populating manufacturer filter: {e}")
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for inventory actions."""
        # Add Medicine shortcut (Ctrl+N)
        self.add_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.add_shortcut.activated.connect(self.open_add_medicine_dialog_with_shortcut)
        
        # Edit shortcut (Ctrl+E)
        edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_shortcut.activated.connect(self.edit_selected_medicine)
        
        # Delete shortcut (Delete key)
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self.delete_selected_medicine)
        
        # Search shortcut (Ctrl+F)
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(lambda: self.search_box.setFocus())
        
        # Refresh shortcut (F5)
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_inventory_table)
        
        # Export shortcut (Ctrl+Shift+E)
        export_shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        export_shortcut.activated.connect(self.export_to_excel)
    
    def open_add_medicine_dialog_with_shortcut(self):
        # Temporarily disable the shortcut while dialog is open
        self.add_shortcut.setEnabled(False)
        try:
            self._on_add_medicine()
        finally:
            self.add_shortcut.setEnabled(True)

    def show_context_menu(self, position):
        """Show context menu for inventory table."""
        current_row = self.inventory_table.currentRow()
        if current_row < 0:
            return
        
        context_menu = QMenu(self)
        
        # Add actions
        edit_action = context_menu.addAction("Edit Medicine")
        edit_action.setShortcut("Ctrl+E")
        edit_action.triggered.connect(self.edit_selected_medicine)
        
        delete_action = context_menu.addAction("Delete Medicine")
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected_medicine)
        
        context_menu.addSeparator()
        
        # Copy actions
        copy_barcode_action = context_menu.addAction("Copy Barcode")
        copy_barcode_action.triggered.connect(lambda: self.copy_to_clipboard(current_row, 0))
        
        copy_name_action = context_menu.addAction("Copy Name")
        copy_name_action.triggered.connect(lambda: self.copy_to_clipboard(current_row, 1))
        
        context_menu.addSeparator()
        
        # View details action
        view_details_action = context_menu.addAction("View Details")
        view_details_action.triggered.connect(lambda: self.view_medicine_details(current_row))
        
        # Show menu at cursor position
        context_menu.exec_(self.inventory_table.mapToGlobal(position))
    
    def copy_to_clipboard(self, row, column):
        """Copy cell content to clipboard."""
        try:
            item = self.inventory_table.item(row, column)
            if item:
                clipboard = QApplication.clipboard()
                clipboard.setText(item.text())
                logger.debug(f"Copied to clipboard: {item.text()}")
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
    
    def view_medicine_details(self, row):
        """View detailed information about the selected medicine."""
        try:
            barcode_item = self.inventory_table.item(row, 0)
            if not barcode_item:
                return
            
            barcode = barcode_item.text()
            medicines = self.inventory_service.get_all()
            medicine = next((m for m in medicines if m.barcode == barcode), None)
            
            if medicine:
                details = f"""
Medicine Details:
Barcode: {medicine.barcode}
Name: {medicine.name}
Quantity: {medicine.quantity}
Threshold: {getattr(medicine, 'threshold', 'N/A')}
Expiry: {medicine.expiry or 'N/A'}
Manufacturer: {medicine.manufacturer or 'N/A'}
Price: ₹{getattr(medicine, 'price', 0)}
                """
                QMessageBox.information(self, "Medicine Details", details.strip())
        except Exception as e:
            logger.error(f"Error viewing medicine details: {e}")
            QMessageBox.warning(self, "Error", f"Could not load medicine details: {e}")
    
    def _on_scan_barcode(self):
        """Handle barcode scanning."""
        logger.info("Scan Barcode button clicked.")
        # For now, show a message that this will be implemented
        QMessageBox.information(self, "Barcode Scanner", 
                               "Barcode scanning functionality will be implemented with hardware integration.")
    

    
    def _on_generate_order(self):
        """Generate order for low stock medicines."""
        logger.info("Generate Order button clicked.")
        try:
            # Get low stock medicines
            medicines = self.inventory_service.get_all()
            low_stock_medicines = [m for m in medicines if m.quantity <= getattr(m, 'threshold', 10)]
            
            if not low_stock_medicines:
                QMessageBox.information(self, "No Low Stock", "No medicines are currently low on stock.")
                return
            
            # Show confirmation with list of low stock medicines
            medicine_list = "\n".join([f"• {m.name} (Current: {m.quantity}, Threshold: {getattr(m, 'threshold', 10)})" 
                                     for m in low_stock_medicines[:10]])  # Show first 10
            if len(low_stock_medicines) > 10:
                medicine_list += f"\n... and {len(low_stock_medicines) - 10} more"
            
            reply = QMessageBox.question(self, "Generate Order", 
                                        f"Generate order for {len(low_stock_medicines)} low stock medicines?\n\n{medicine_list}",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # TODO: Implement order generation logic
                QMessageBox.information(self, "Order Generation", 
                                       f"Order generation for {len(low_stock_medicines)} medicines will be implemented.")
        except Exception as e:
            logger.error(f"Error generating order: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to generate order: {e}")
    
    def _on_clear_inventory(self):
        """Clear all inventory data."""
        logger.info("Clear Inventory button clicked.")
        
        # Show warning confirmation
        reply = QMessageBox.warning(self, "Clear Inventory", 
                                   "This will permanently delete ALL inventory data. This action cannot be undone.\n\n"
                                   "Are you absolutely sure you want to continue?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Double confirmation
            reply2 = QMessageBox.critical(self, "Final Confirmation", 
                                         "This is your final warning. All inventory data will be permanently deleted.\n\n"
                                         "Type 'DELETE' to confirm:",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply2 == QMessageBox.Yes:
                try:
                    result = self.inventory_service.clear()
                    if result[0]:
                        logger.info("Inventory cleared successfully.")
                        self.refresh_inventory_table()
                        QMessageBox.information(self, "Success", "Inventory cleared successfully!")
                    else:
                        logger.error(f"Failed to clear inventory: {result[1]}")
                        QMessageBox.warning(self, "Clear Failed", result[1])
                except Exception as e:
                    logger.error(f"Error clearing inventory: {e}", exc_info=True)
                    QMessageBox.critical(self, "Error", f"Failed to clear inventory: {e}") 