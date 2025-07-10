from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QStackedWidget, QFileDialog, QMessageBox, QProgressDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
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
        layout = QVBoxLayout(self)
        self.label = QLabel(label_text)
        self.label.setStyleSheet("font-size: 15px; margin-bottom: 8px;")
        layout.addWidget(self.label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("height: 32px; font-size: 18px;")
        layout.addWidget(self.progress_bar)
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setEnabled(False)
        self.ok_btn.setFixedWidth(100)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
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
        self.theme = main_window.theme
        self.get_button_stylesheet = main_window.get_button_stylesheet
        from inventory_service import InventoryService
        self.inventory_service = InventoryService()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header (title + search)
        header_layout = QHBoxLayout()
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        # Remove the 'Search:' label
        # search_label = QLabel("Search:")
        # search_label.setStyleSheet("font-size: 16px; margin-right: 8px;")
        # header_layout.addWidget(search_label)
        self.inventory_search_box = QLineEdit()
        self.inventory_search_box.setPlaceholderText("Search by name, barcode, or manufacturer...")
        self.inventory_search_box.setFixedWidth(250)
        header_layout.addWidget(self.inventory_search_box)
        # Add Search button
        self.search_button = QPushButton("Search")
        self.search_button.setFixedHeight(36)
        self.search_button.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.search_button)
        self.search_button.clicked.connect(self.filter_inventory_table)
        self.inventory_search_box.returnPressed.connect(self.filter_inventory_table)
        # Debug: Confirm signal connection
        print('Connected search box to filter_inventory_table')
        layout.addLayout(header_layout)
        # Main content: table + buttons on right
        main_layout = QHBoxLayout()
        # Inventory table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Quantity", "Threshold", "Expiry", "Manufacturer", "Price"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setAlternatingRowColors(False)
        self.inventory_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.inventory_table, stretch=1)
        # Button column
        button_col = QVBoxLayout()
        self.add_medicine_btn = QPushButton("Add Medicine")
        self.add_medicine_btn.setMinimumHeight(36)
        self.add_medicine_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.add_medicine_btn)
        self.scan_barcode_btn = QPushButton("Scan Barcode")
        self.scan_barcode_btn.setMinimumHeight(36)
        self.scan_barcode_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.scan_barcode_btn)
        self.generate_order_btn = QPushButton("Generate Order")
        self.generate_order_btn.setMinimumHeight(36)
        self.generate_order_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.generate_order_btn)
        self.bulk_threshold_btn = QPushButton("Bulk Threshold Settings")
        self.bulk_threshold_btn.setMinimumHeight(36)
        self.bulk_threshold_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.bulk_threshold_btn)
        self.quick_add_stock_btn = QPushButton("Quick Add Stock")
        self.quick_add_stock_btn.setMinimumHeight(36)
        self.quick_add_stock_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.quick_add_stock_btn)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(36)
        self.delete_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.delete_btn)
        self.clear_inventory_btn = QPushButton("Clear Inventory")
        self.clear_inventory_btn.setMinimumHeight(36)
        self.clear_inventory_btn.setStyleSheet(self.get_button_stylesheet())
        button_col.addWidget(self.clear_inventory_btn)
        self.import_excel_btn = QPushButton("Import from Excel")
        self.import_excel_btn.setMinimumHeight(36)
        self.import_excel_btn.setStyleSheet(self.get_button_stylesheet())
        self.import_excel_btn.clicked.connect(self.import_from_excel)
        button_col.addWidget(self.import_excel_btn)
        self.export_excel_btn = QPushButton("Export to Excel")
        self.export_excel_btn.setMinimumHeight(36)
        self.export_excel_btn.setStyleSheet(self.get_button_stylesheet())
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        button_col.addWidget(self.export_excel_btn)
        button_col.addStretch()
        main_layout.addLayout(button_col)
        layout.addLayout(main_layout)
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
        self.refresh_inventory_table()
        # self.filter_inventory_table()  # Remove this line

    def refresh_inventory_table(self):
        medicines = self.inventory_service.get_all()
        self.filter_inventory_table()

    def filter_inventory_table(self):
        query = self.inventory_search_box.text().strip().lower()
        filtered = self.inventory_service.search(query)
        # Debug print
        print(f'[DEBUG] Query: "{query}", Matches: {len(filtered)}')
        for m in filtered[:5]:
            print(f'[DEBUG] Match: {m.name}')
        self.inventory_table.clearContents()
        self.inventory_table.setRowCount(0)
        self.inventory_table.setRowCount(len(filtered))
        for i, med in enumerate(filtered):
            self.inventory_table.setItem(i, 0, QTableWidgetItem(med.barcode))
            self.inventory_table.setItem(i, 1, QTableWidgetItem(med.name))
            self.inventory_table.setItem(i, 2, QTableWidgetItem(str(med.quantity)))
            self.inventory_table.setItem(i, 3, QTableWidgetItem(str(getattr(med, 'threshold', 10))))
            self.inventory_table.setItem(i, 4, QTableWidgetItem(str(med.expiry) if med.expiry else "N/A"))
            self.inventory_table.setItem(i, 5, QTableWidgetItem(med.manufacturer or "N/A"))
            self.inventory_table.setItem(i, 6, QTableWidgetItem(f"₹{getattr(med, 'price', 0)}"))
        self.inventory_table.viewport().update()
        self.inventory_table.repaint()
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()

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