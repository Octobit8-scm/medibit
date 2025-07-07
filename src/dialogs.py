from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config import get_threshold
from db import (
    get_all_medicines,
    get_medicine_by_barcode,
    get_pharmacy_details,
    save_pharmacy_details,
    update_medicine,
    update_medicine_quantity,
    update_medicine_threshold,
)
from notifications import NotificationManager


class AddMedicineDialog(QDialog):
    def __init__(self, parent=None, barcode=None):
        super().__init__(parent)
        self.setWindowTitle("Add Medicine")
        self.setModal(True)
        self.setMinimumSize(420, 340)
        layout = QFormLayout(self)
        self.barcode = QLineEdit()
        if barcode:
            self.barcode.setText(barcode)
        self.name = QLineEdit()
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.expiry = QDateEdit()
        self.expiry.setCalendarPopup(True)
        self.expiry.setDate(QDate.currentDate())
        self.manufacturer = QLineEdit()
        self.price = QSpinBox()
        self.price.setRange(0, 100000)
        self.price.setPrefix("₹")
        self.threshold = QSpinBox()
        self.threshold.setRange(0, 10000)
        self.threshold.setValue(10)  # Default threshold
        self.threshold.setSuffix(" units")
        layout.addRow("Barcode:", self.barcode)
        layout.addRow("Name:", self.name)
        layout.addRow("Quantity:", self.quantity)
        layout.addRow("Threshold:", self.threshold)
        layout.addRow("Expiry:", self.expiry)
        layout.addRow("Manufacturer:", self.manufacturer)
        layout.addRow("Price:", self.price)

        # Add helpful note
        note_label = QLabel(
            "Note: If a medicine with this barcode already exists, the "
            "quantity will be added to the existing stock."
        )
        note_label.setStyleSheet(
            "color: #666; font-size: 11px; font-style: italic;"
        )
        note_label.setWordWrap(True)
        layout.addRow(note_label)

        self.buttonBox = QPushButton("Add")
        self.buttonBox.setMinimumHeight(40)  # Set height
        self.buttonBox.setMaximumHeight(50)  # Set maximum height
        self.buttonBox.clicked.connect(self.check_and_add)
        layout.addRow(self.buttonBox)

    def check_and_add(self):
        """Check if barcode exists and confirm before adding"""
        barcode = self.barcode.text().strip()
        if not barcode:
            QMessageBox.warning(self, "Input Error", "Barcode is required.")
            return

        # Check if medicine with this barcode already exists
        existing_medicine = get_medicine_by_barcode(barcode)

        if existing_medicine:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Barcode Already Exists",
                f"A medicine with barcode '{barcode}' already exists:\n\n"
                f"Name: {existing_medicine.name}\n"
                f"Current Quantity: {existing_medicine.quantity}\n\n"
                f"Do you want to add the new quantity to the existing medicine?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply == QMessageBox.Yes:
                self.accept()
            else:
                return
        else:
            self.accept()

    def get_data(self):
        return {
            "barcode": self.barcode.text().strip(),
            "name": self.name.text().strip(),
            "quantity": self.quantity.value(),
            "threshold": self.threshold.value(),
            "expiry": self.expiry.date().toPyDate(),
            "manufacturer": self.manufacturer.text().strip(),
            "price": self.price.value(),
        }


class OrderQuantityDialog(QDialog):
    def __init__(self, medicines, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Order Quantities")
        self.setModal(True)
        self.setMinimumSize(400, 300)
        self.medicines = medicines
        self.spins = {}
        layout = QFormLayout(self)
        for med in medicines:
            spin = QSpinBox()
            spin.setRange(1, 10000)
            spin.setValue(10)
            self.spins[med.barcode] = spin
            layout.addRow(f"{med.name} (Current: {med.quantity})", spin)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setMinimumHeight(40)  # Set height
        button_box.setMaximumHeight(50)  # Set maximum height
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_order_quantities(self):
        return {barcode: spin.value() for barcode, spin in self.spins.items()}


class NotificationSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notification Settings")
        self.setModal(True)
        self.setMinimumSize(540, 420)
        self.notification_manager = NotificationManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Email Settings
        email_group = QWidget()
        email_layout = QVBoxLayout(email_group)
        email_title = QLabel("Email Notifications")
        email_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1976d2;"
        )
        email_layout.addWidget(email_title)

        # Email enable checkbox
        self.email_enabled = QCheckBox("Enable Email Notifications")
        self.email_enabled.setChecked(
            self.notification_manager.config["email"]["enabled"]
        )
        email_layout.addWidget(self.email_enabled)

        # Email form
        email_form = QFormLayout()
        self.smtp_server = QLineEdit(
            self.notification_manager.config["email"]["smtp_server"]
        )
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(
            self.notification_manager.config["email"]["smtp_port"]
        )
        self.sender_email = QLineEdit(
            self.notification_manager.config["email"]["sender_email"]
        )
        self.sender_password = QLineEdit(
            self.notification_manager.config["email"]["sender_password"]
        )
        self.sender_password.setEchoMode(QLineEdit.Password)
        self.sender_password.setPlaceholderText(
            "Use App Password for Gmail (not regular password)"
        )
        self.recipient_emails = QLineEdit(
            ", ".join(
                self.notification_manager.config["email"]["recipient_emails"]
            )
        )
        self.recipient_emails.setPlaceholderText(
            "email1@example.com, email2@example.com"
        )

        # Add helpful note about Gmail App Passwords
        gmail_note = QLabel(
            "Note: For Gmail, you need to use an App Password instead of your "
            "regular password.\nGo to Google Account → Security → 2-Step Verification "
            "→ App passwords"
        )
        gmail_note.setStyleSheet(
            "color: #666; font-size: 11px; font-style: italic;"
        )
        gmail_note.setWordWrap(True)

        email_form.addRow("SMTP Server:", self.smtp_server)
        email_form.addRow("SMTP Port:", self.smtp_port)
        email_form.addRow("Sender Email:", self.sender_email)
        email_form.addRow("Sender Password:", self.sender_password)
        email_form.addRow("Recipient Emails:", self.recipient_emails)
        email_layout.addWidget(gmail_note)
        email_layout.addLayout(email_form)

        # WhatsApp Settings
        whatsapp_group = QWidget()
        whatsapp_layout = QVBoxLayout(whatsapp_group)
        whatsapp_title = QLabel("WhatsApp Notifications")
        whatsapp_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #25d366;"
        )
        whatsapp_layout.addWidget(whatsapp_title)

        # WhatsApp enable checkbox
        self.whatsapp_enabled = QCheckBox("Enable WhatsApp Notifications")
        self.whatsapp_enabled.setChecked(
            self.notification_manager.config["whatsapp"]["enabled"]
        )
        whatsapp_layout.addWidget(self.whatsapp_enabled)

        # WhatsApp form
        whatsapp_form = QFormLayout()
        self.whatsapp_api_key = QLineEdit(
            self.notification_manager.config["whatsapp"]["api_key"]
        )
        self.whatsapp_api_key.setPlaceholderText(
            "Account SID:Auth Token (for Twilio)"
        )
        self.whatsapp_phone_numbers = QLineEdit(
            ", ".join(
                self.notification_manager.config["whatsapp"]["phone_numbers"]
            )
        )
        self.whatsapp_phone_numbers.setPlaceholderText(
            "+1234567890, +0987654321"
        )

        whatsapp_form.addRow("API Key:", self.whatsapp_api_key)
        whatsapp_form.addRow("Phone Numbers:", self.whatsapp_phone_numbers)
        whatsapp_layout.addLayout(whatsapp_form)

        # Add helpful note about WhatsApp APIs
        whatsapp_note = QLabel(
            "Recommended: Twilio WhatsApp API\n"
            "• Sign up at: https://www.twilio.com/whatsapp\n"
            "• Use sandbox for testing\n"
            "• Format: Account SID:Auth Token"
        )
        whatsapp_note.setStyleSheet(
            "color: #666; font-size: 11px; font-style: italic;"
        )
        whatsapp_note.setWordWrap(True)
        whatsapp_layout.addWidget(whatsapp_note)

        # SMS Settings
        sms_group = QWidget()
        sms_layout = QVBoxLayout(sms_group)
        sms_title = QLabel("SMS Notifications")
        sms_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ff6b35;"
        )
        sms_layout.addWidget(sms_title)

        # SMS enable checkbox
        self.sms_enabled = QCheckBox("Enable SMS Notifications")
        self.sms_enabled.setChecked(
            self.notification_manager.config["sms"]["enabled"]
        )
        sms_layout.addWidget(self.sms_enabled)

        # SMS form
        sms_form = QFormLayout()
        self.sms_api_key = QLineEdit(
            self.notification_manager.config["sms"]["api_key"]
        )
        self.sms_api_key.setPlaceholderText("Account SID:Auth Token")
        self.sms_phone_numbers = QLineEdit(
            "+919923706784, +919876543210"
        )
        self.sms_phone_numbers.setPlaceholderText(
            "+919923706784, +919876543210"
        )

        sms_form.addRow("API Key:", self.sms_api_key)
        sms_form.addRow("Phone Numbers:", self.sms_phone_numbers)
        sms_layout.addLayout(sms_form)

        # Add helpful note about SMS APIs
        sms_note = QLabel(
            "Twilio SMS Setup:\n"
            "• Get Account SID & Auth Token from Twilio Console\n"
            "• Get a Twilio phone number for sending SMS\n"
            "• Update from_number in notifications.py\n"
            "• For trial: verify recipient numbers in Twilio Console"
        )
        sms_note.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        sms_note.setWordWrap(True)
        sms_layout.addWidget(sms_note)

        # Add all groups to main layout
        layout.addWidget(email_group)
        layout.addWidget(whatsapp_group)
        layout.addWidget(sms_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        test_btn = QPushButton("Test Notifications")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save_settings)
        test_btn.clicked.connect(self.test_notifications)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(test_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def save_settings(self):
        """Save notification settings"""
        try:
            # Update email settings
            self.notification_manager.update_config(
                "email", "enabled", self.email_enabled.isChecked()
            )
            self.notification_manager.update_config(
                "email", "smtp_server", self.smtp_server.text()
            )
            self.notification_manager.update_config(
                "email", "smtp_port", self.smtp_port.value()
            )
            self.notification_manager.update_config(
                "email", "sender_email", self.sender_email.text()
            )
            self.notification_manager.update_config(
                "email", "sender_password", self.sender_password.text()
            )

            recipient_emails = [
                email.strip()
                for email in self.recipient_emails.text().split(",")
                if email.strip()
            ]
            self.notification_manager.update_config(
                "email", "recipient_emails", recipient_emails
            )

            # Update WhatsApp settings
            self.notification_manager.update_config(
                "whatsapp", "enabled", self.whatsapp_enabled.isChecked()
            )
            self.notification_manager.update_config(
                "whatsapp", "api_key", self.whatsapp_api_key.text()
            )

            whatsapp_phones = [
                phone.strip()
                for phone in self.whatsapp_phone_numbers.text().split(",")
                if phone.strip()
            ]
            self.notification_manager.update_config(
                "whatsapp", "phone_numbers", whatsapp_phones
            )

            # Update SMS settings
            self.notification_manager.update_config(
                "sms", "enabled", self.sms_enabled.isChecked()
            )
            self.notification_manager.update_config(
                "sms", "api_key", self.sms_api_key.text()
            )

            sms_phones = [
                phone.strip()
                for phone in self.sms_phone_numbers.text().split(",")
                if phone.strip()
            ]
            self.notification_manager.update_config("sms", "phone_numbers", sms_phones)

            QMessageBox.information(
                self, "Success", "Notification settings saved successfully!"
            )
            self.accept()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save settings: {str(e)}")

    def test_notifications(self):
        """Test notification settings"""
        try:
            # Create a test medicine
            from db import Medicine

            test_medicine = Medicine(
                name="Test Medicine",
                barcode="TEST123",
                quantity=5,
                manufacturer="Test Manufacturer",
            )

            results = self.notification_manager.send_all_alerts([test_medicine])

            # Show results
            message = "Test notification results:\n\n"
            for channel, success, msg in results:
                status = "✅ Success" if success else "❌ Failed"
                message += f"{channel}: {status}\n{msg}\n\n"

            QMessageBox.information(self, "Test Results", message)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Test failed: {str(e)}")


class CustomerInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customer Information")
        self.setModal(True)
        self.setMinimumSize(400, 250)
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("WhatsApp number, e.g. +919999999999")
        self.email = QLineEdit()
        self.email.setPlaceholderText("customer@email.com")
        layout.addRow("Name:", self.name)
        layout.addRow("Phone:", self.phone)
        layout.addRow("Email:", self.email)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_data(self):
        return {
            "name": self.name.text().strip(),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
        }


class SupplierInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Supplier Information")
        self.setModal(True)
        self.setMinimumSize(400, 250)
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("WhatsApp number, e.g. +919999999999")
        self.email = QLineEdit()
        self.email.setPlaceholderText("supplier@email.com")
        layout.addRow("Name:", self.name)
        layout.addRow("Phone:", self.phone)
        layout.addRow("Email:", self.email)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_data(self):
        return {
            "name": self.name.text().strip(),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
        }


class ThresholdSettingDialog(QDialog):
    def __init__(self, medicine, parent=None):
        super().__init__(parent)
        self.medicine = medicine
        self.setWindowTitle("Set Threshold")
        self.setModal(True)
        self.setMinimumSize(400, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Medicine info
        info_group = QGroupBox("Medicine Information")
        info_layout = QFormLayout(info_group)

        name_label = QLabel(self.medicine.name)
        name_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        barcode_label = QLabel(self.medicine.barcode)
        current_stock_label = QLabel(str(self.medicine.quantity))
        current_threshold_label = QLabel(str(self.medicine.threshold))

        info_layout.addRow("Name:", name_label)
        info_layout.addRow("Barcode:", barcode_label)
        info_layout.addRow("Current Stock:", current_stock_label)
        info_layout.addRow("Current Threshold:", current_threshold_label)

        layout.addWidget(info_group)

        # Threshold setting
        threshold_group = QGroupBox("Set New Threshold")
        threshold_layout = QFormLayout(threshold_group)

        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setMinimum(0)
        self.threshold_spinbox.setMaximum(9999)
        self.threshold_spinbox.setValue(self.medicine.threshold)
        self.threshold_spinbox.setSuffix(" units")

        threshold_layout.addRow("New Threshold:", self.threshold_spinbox)

        # Add helpful note
        note_label = QLabel(
            "When stock falls below this threshold, you'll receive low stock alerts."
        )
        note_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        note_label.setWordWrap(True)
        threshold_layout.addRow(note_label)

        layout.addWidget(threshold_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Threshold")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save_threshold)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def save_threshold(self):
        try:
            new_threshold = self.threshold_spinbox.value()
            success, error = update_medicine_threshold(
                self.medicine.barcode, new_threshold
            )

            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Threshold updated to {new_threshold} units for {self.medicine.name}",
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Error", f"Failed to update threshold: {error}"
                )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update threshold: {str(e)}")


class BulkThresholdDialog(QDialog):
    def __init__(self, medicines, parent=None):
        super().__init__(parent)
        self.medicines = medicines
        self.setWindowTitle("Bulk Threshold Settings")
        self.setModal(True)
        self.setMinimumSize(540, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Set individual stock thresholds for each medicine. Double-click on a "
            "threshold value to edit it."
        )
        instructions.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Medicine", "Current Stock", "Current Threshold", "New Threshold"]
        )
        self.table.setRowCount(len(self.medicines))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Populate table
        for i, med in enumerate(self.medicines):
            # Medicine name
            name_item = QTableWidgetItem(f"{med.name} ({med.barcode})")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)

            # Current stock
            stock_item = QTableWidgetItem(str(med.quantity))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
            if med.quantity < getattr(med, "threshold", 10):
                stock_item.setBackground(
                    QColor(255, 200, 200)
                )  # Light red for low stock
            self.table.setItem(i, 1, stock_item)

            # Current threshold
            current_threshold_item = QTableWidgetItem(
                str(getattr(med, "threshold", 10))
            )
            current_threshold_item.setFlags(
                current_threshold_item.flags() & ~Qt.ItemIsEditable
            )
            self.table.setItem(i, 2, current_threshold_item)

            # New threshold (editable)
            new_threshold_item = QTableWidgetItem(str(getattr(med, "threshold", 10)))
            new_threshold_item.setFlags(new_threshold_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(i, 3, new_threshold_item)

        # Set column widths
        self.table.setColumnWidth(0, 200)  # Medicine name
        self.table.setColumnWidth(1, 100)  # Current stock
        self.table.setColumnWidth(2, 120)  # Current threshold
        self.table.setColumnWidth(3, 120)  # New threshold

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save All Thresholds")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save_all_thresholds)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def save_all_thresholds(self):
        """Save all threshold changes"""
        try:
            updated_count = 0
            errors = []

            for i, med in enumerate(self.medicines):
                new_threshold_item = self.table.item(i, 3)
                if new_threshold_item:
                    try:
                        new_threshold = int(new_threshold_item.text())
                        if new_threshold < 0:
                            errors.append(f"{med.name}: Threshold must be 0 or greater")
                            continue

                        success, error = update_medicine_threshold(
                            med.barcode, new_threshold
                        )
                        if success:
                            updated_count += 1
                        else:
                            errors.append(f"{med.name}: {error}")
                    except ValueError:
                        errors.append(f"{med.name}: Invalid threshold value")

            # Show results
            if errors:
                error_msg = "Some thresholds could not be updated:\n\n" + "\n".join(
                    errors
                )
                QMessageBox.warning(self, "Update Errors", error_msg)

            if updated_count > 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Updated thresholds for {updated_count} medicines.",
                )
                self.accept()
            elif not errors:
                QMessageBox.information(
                    self, "No Changes", "No thresholds were changed."
                )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update thresholds: {str(e)}")


class EditMedicineDialog(QDialog):
    def __init__(self, medicine, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Medicine")
        self.setModal(True)
        self.setMinimumSize(420, 340)
        self.medicine = medicine
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        # Medicine info (read-only)
        info_group = QGroupBox("Medicine Information")
        info_layout = QFormLayout(info_group)

        barcode_label = QLabel(self.medicine.barcode)
        barcode_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        info_layout.addRow("Barcode:", barcode_label)

        layout.addWidget(info_group)

        # Editable fields
        edit_group = QGroupBox("Edit Details")
        edit_layout = QFormLayout(edit_group)

        self.name = QLineEdit(self.medicine.name)
        self.quantity = QSpinBox()
        self.quantity.setRange(0, 100000)
        self.quantity.setValue(self.medicine.quantity)
        self.quantity.setSuffix(" units")

        self.expiry = QDateEdit()
        self.expiry.setCalendarPopup(True)
        if self.medicine.expiry:
            self.expiry.setDate(
                QDate.fromString(str(self.medicine.expiry), "yyyy-MM-dd")
            )
        else:
            self.expiry.setDate(QDate.currentDate())

        self.manufacturer = QLineEdit(self.medicine.manufacturer or "")
        self.price = QSpinBox()
        self.price.setRange(0, 100000)
        self.price.setValue(getattr(self.medicine, "price", 0))
        self.price.setPrefix("₹")

        self.threshold = QSpinBox()
        self.threshold.setRange(0, 10000)
        self.threshold.setValue(getattr(self.medicine, "threshold", 10))
        self.threshold.setSuffix(" units")

        edit_layout.addRow("Name:", self.name)
        edit_layout.addRow("Quantity:", self.quantity)
        edit_layout.addRow("Expiry:", self.expiry)
        edit_layout.addRow("Manufacturer:", self.manufacturer)
        edit_layout.addRow("Price:", self.price)
        edit_layout.addRow("Threshold:", self.threshold)

        layout.addWidget(edit_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save_changes)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

    def save_changes(self):
        try:
            # Validate required fields
            if not self.name.text().strip():
                QMessageBox.warning(
                    self, "Validation Error", "Medicine name is required."
                )
                return

            # Get updated data
            updated_data = {
                "name": self.name.text().strip(),
                "quantity": self.quantity.value(),
                "expiry": self.expiry.date().toPyDate(),
                "manufacturer": self.manufacturer.text().strip(),
                "price": self.price.value(),
                "threshold": self.threshold.value(),
            }

            # Update medicine
            success, error = update_medicine(
                self.medicine.barcode,
                updated_data["name"],
                updated_data["quantity"],
                updated_data["expiry"],
                updated_data["manufacturer"],
                updated_data["price"],
                updated_data["threshold"],
            )

            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Medicine '{updated_data['name']}' updated successfully!",
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self, "Error", f"Failed to update medicine: {error}"
                )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update medicine: {str(e)}")


class PharmacyDetailsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pharmacy Details")
        self.setModal(True)
        self.setMinimumSize(540, 420)
        self.init_ui()
        self.load_existing_details()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("Pharmacy Details")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1976d2; margin-bottom: 10px;"
        )
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Configure your pharmacy details that will appear on bills, orders, "
            "and other documents."
        )
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 15px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        # Pharmacy Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter pharmacy name")
        form_layout.addRow("Pharmacy Name*:", self.name_edit)

        # Address
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setPlaceholderText("Enter complete address")
        form_layout.addRow("Address*:", self.address_edit)

        # Phone
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone*:", self.phone_edit)

        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter email address")
        form_layout.addRow("Email*:", self.email_edit)

        # GST Number
        self.gst_edit = QLineEdit()
        self.gst_edit.setPlaceholderText("Enter GST number (optional)")
        form_layout.addRow("GST Number:", self.gst_edit)

        # License Number
        self.license_edit = QLineEdit()
        self.license_edit.setPlaceholderText("Enter license number (optional)")
        form_layout.addRow("License Number:", self.license_edit)

        # Website
        self.website_edit = QLineEdit()
        self.website_edit.setPlaceholderText("Enter website URL (optional)")
        form_layout.addRow("Website:", self.website_edit)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save Details")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self.save_details)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def load_existing_details(self):
        details = get_pharmacy_details()
        print(f"Loading pharmacy details in dialog: {details}")
        if details:
            self.name_edit.setText(details.name)
            self.address_edit.setPlainText(details.address)
            self.phone_edit.setText(details.phone)
            self.email_edit.setText(details.email)
            self.gst_edit.setText(details.gst_number or "")
            self.license_edit.setText(details.license_number or "")
            self.website_edit.setText(details.website or "")
            print(
                f"Loaded pharmacy details: {details.name}, {details.address}, {details.phone}, {details.email}"
            )
        else:
            print("No pharmacy details found, form will be empty")

    def save_details(self):
        name = self.name_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        gst_number = self.gst_edit.text().strip()
        license_number = self.license_edit.text().strip()
        website = self.website_edit.text().strip()

        # Validate required fields
        if not name:
            QMessageBox.warning(self, "Validation Error", "Pharmacy name is required.")
            return
        if not address:
            QMessageBox.warning(self, "Validation Error", "Address is required.")
            return
        if not phone:
            QMessageBox.warning(self, "Validation Error", "Phone number is required.")
            return
        if not email:
            QMessageBox.warning(self, "Validation Error", "Email is required.")
            return

        # Save to database
        print(f"Saving pharmacy details: {name}, {address}, {phone}, {email}")
        success, message = save_pharmacy_details(
            name, address, phone, email, gst_number, license_number, website
        )

        if success:
            print(f"Successfully saved pharmacy details: {message}")
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            print(f"Failed to save pharmacy details: {message}")
            QMessageBox.critical(
                self, "Error", f"Failed to save pharmacy details: {message}"
            )


class QuickAddStockDialog(QDialog):
    def __init__(self, medicines, parent=None):
        super().__init__(parent)
        self.medicines = medicines
        self.setWindowTitle("Quick Add Stock")
        self.setModal(True)
        self.setMinimumSize(540, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Quickly add stock to existing medicines. Enter quantities to add for "
            "each medicine."
        )
        instructions.setStyleSheet("color: #666; font-size: 12px; font-style: italic;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Medicine", "Current Stock", "Add Quantity", "New Total"]
        )
        self.table.setRowCount(len(self.medicines))
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Populate table
        for i, med in enumerate(self.medicines):
            # Medicine name
            name_item = QTableWidgetItem(f"{med.name} ({med.barcode})")
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)

            # Current stock
            stock_item = QTableWidgetItem(str(med.quantity))
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
            if med.quantity < getattr(med, "threshold", 10):
                stock_item.setBackground(
                    QColor(255, 200, 200)
                )  # Light red for low stock
            self.table.setItem(i, 1, stock_item)

            # Add quantity (editable)
            add_qty_item = QTableWidgetItem("0")
            add_qty_item.setFlags(add_qty_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(i, 2, add_qty_item)

            # New total (calculated)
            new_total_item = QTableWidgetItem(str(med.quantity))
            new_total_item.setFlags(new_total_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 3, new_total_item)

        # Set column widths
        self.table.setColumnWidth(0, 200)  # Medicine name
        self.table.setColumnWidth(1, 100)  # Current stock
        self.table.setColumnWidth(2, 100)  # Add quantity
        self.table.setColumnWidth(3, 100)  # New total

        # Connect cell changed signal to update totals
        self.table.itemChanged.connect(self.on_cell_changed)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Add Stock")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.add_stock)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def on_cell_changed(self, item):
        """Update the new total when add quantity changes"""
        if item.column() == 2:  # Add quantity column
            try:
                add_qty = int(item.text()) if item.text() else 0
                if add_qty < 0:
                    add_qty = 0
                    item.setText("0")

                row = item.row()
                current_stock = int(self.table.item(row, 1).text())
                new_total = current_stock + add_qty
                self.table.item(row, 3).setText(str(new_total))
            except ValueError:
                item.setText("0")
                self.table.item(row, 3).setText(self.table.item(row, 1).text())

    def add_stock(self):
        """Add stock to selected medicines"""
        try:
            updated_count = 0
            errors = []

            for i, med in enumerate(self.medicines):
                add_qty_item = self.table.item(i, 2)
                if add_qty_item:
                    try:
                        add_qty = int(add_qty_item.text()) if add_qty_item.text() else 0
                        if add_qty > 0:  # Only update if adding stock
                            new_total = med.quantity + add_qty

                            # Update medicine with new quantity (more efficient)
                            success, error = update_medicine_quantity(
                                med.barcode, new_total
                            )

                            if success:
                                updated_count += 1
                            else:
                                errors.append(f"{med.name}: {error}")
                    except ValueError:
                        errors.append(f"{med.name}: Invalid quantity")

            # Show results
            if errors:
                error_msg = "Some updates failed:\n\n" + "\n".join(errors)
                QMessageBox.warning(self, "Update Errors", error_msg)

            if updated_count > 0:
                QMessageBox.information(
                    self, "Success", f"Added stock to {updated_count} medicines."
                )
                self.accept()
            else:
                QMessageBox.information(
                    self,
                    "No Changes",
                    "No stock was added. Enter quantities greater than 0 to add stock.",
                )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add stock: {str(e)}")


class BillingAddMedicineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Medicine to Bill")
        self.setModal(True)
        self.setMinimumSize(540, 400)
        self.selected_medicine = None
        self.selected_quantity = 1
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Medicine table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Barcode", "Name", "Price"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Quantity selector
        qty_layout = QHBoxLayout()
        qty_label = QLabel("Quantity:")
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(1000)
        qty_layout.addWidget(qty_label)
        qty_layout.addWidget(self.qty_spin)
        layout.addLayout(qty_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add to Bill")
        self.add_btn.clicked.connect(self.accept_selection)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.medicines = get_all_medicines()
        self.populate_table(self.medicines)

    def populate_table(self, medicines):
        self.table.setRowCount(0)
        for med in medicines:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(med.barcode))
            self.table.setItem(row, 1, QTableWidgetItem(med.name))
            self.table.setItem(row, 2, QTableWidgetItem(f"₹{getattr(med, 'price', 0)}"))

    def filter_table(self, text):
        filtered = [
            m
            for m in self.medicines
            if text.lower() in m.name.lower() or text.lower() in m.barcode.lower()
        ]
        self.populate_table(filtered)

    def accept_selection(self):
        selected = self.table.currentRow()
        if selected >= 0:
            barcode = self.table.item(selected, 0).text()
            for med in self.medicines:
                if med.barcode == barcode:
                    self.selected_medicine = med
                    break
            self.selected_quantity = self.qty_spin.value()
            self.accept()

    def get_selected(self):
        return self.selected_medicine, self.selected_quantity
