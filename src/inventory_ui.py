from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QStackedWidget, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
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
        self.all_medicines = get_all_medicines()
        self.filter_inventory_table()

    def filter_inventory_table(self):
        query = self.inventory_search_box.text().strip().lower()
        medicines = self.all_medicines
        if not query:
            filtered = medicines
        else:
            filtered = [
                m for m in medicines
                if query == (m.name or '').lower()
                or query == (m.barcode or '').lower()
                or query == (m.manufacturer or '').lower()
            ]
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

    def import_from_excel(self):
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
        imported, updated, errors = 0, 0, 0
        imported_barcodes, updated_barcodes, error_details = [], [], []
        for idx, row in df.iterrows():
            try:
                barcode = str(row["Barcode"]).strip()
                name = str(row["Name"]).strip()
                quantity = int(row["Quantity"])
                threshold = int(row["Threshold"]) if "Threshold" in row and not pd.isna(row["Threshold"]) else 10
                expiry = row["Expiry"] if "Expiry" in row and not pd.isna(row["Expiry"]) else None
                # Convert expiry to Python date object if needed
                if expiry:
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
                manufacturer = str(row["Manufacturer"]) if "Manufacturer" in row and not pd.isna(row["Manufacturer"]) else ""
                price = int(row["Price"]) if "Price" in row and not pd.isna(row["Price"]) else 0
                existing = get_medicine_by_barcode(barcode)
                if existing:
                    success, msg = update_medicine(barcode, name, quantity, expiry, manufacturer, price, threshold)
                    if success:
                        updated += 1
                        updated_barcodes.append(barcode)
                    else:
                        errors += 1
                        error_details.append(f"Row {idx+2} (Barcode: {barcode}): {msg}")
                else:
                    result = add_medicine(barcode, name, quantity, expiry, manufacturer, price, threshold)
                    if result[0]:
                        imported += 1
                        imported_barcodes.append(barcode)
                    else:
                        errors += 1
                        error_details.append(f"Row {idx+2} (Barcode: {barcode}): {result[1]}")
            except Exception as e:
                errors += 1
                error_details.append(f"Row {idx+2} (Barcode: {row.get('Barcode', 'N/A')}): {e}")
        self.refresh_inventory_table()
        count = len(get_all_medicines())
        summary = f"Imported: {imported}\nUpdated: {updated}\nErrors: {errors}\nTotal medicines in DB: {count}\n"
        summary += f"\nImported Barcodes (first 10): {imported_barcodes[:10]}"
        summary += f"\nUpdated Barcodes (first 10): {updated_barcodes[:10]}"
        if errors:
            summary += f"\n\nError Details (first 10):\n" + '\n'.join(error_details[:10])
        QMessageBox.information(self, "Import Complete", summary)

    def export_to_excel(self):
        medicines = get_all_medicines()
        if not medicines:
            QMessageBox.information(self, "Export", "No inventory data to export.")
            return
        data = []
        for med in medicines:
            data.append({
                'Barcode': med.barcode,
                'Name': med.name,
                'Quantity': med.quantity,
                'Threshold': getattr(med, 'threshold', 10),
                'Expiry': str(med.expiry) if med.expiry else '',
                'Manufacturer': med.manufacturer or '',
                'Price': getattr(med, 'price', 0),
            })
        df = pd.DataFrame(data)
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Inventory Excel", "inventory_export.xlsx", "Excel Files (*.xlsx)")
        if not file_path:
            return
        try:
            df.to_excel(file_path, index=False)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save Excel file:\n{e}")
            return
        # Send email to pharmacy
        result, msg = self.send_inventory_email(file_path)
        if result:
            QMessageBox.information(self, "Export Complete", f"Inventory exported and sent to pharmacy email.\nFile: {file_path}")
        else:
            QMessageBox.critical(self, "Email Error", f"Failed to send email: {msg}")
        self.refresh_inventory_table()

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