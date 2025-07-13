from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QComboBox, QColorDialog, QLabel, QMessageBox, QFileDialog, QFormLayout, QLineEdit)
from PyQt5.QtCore import Qt
from dialogs import NotificationSettingsWidget, PharmacyDetailsWidget
import shutil, os
from PyQt5.QtGui import QLinearGradient, QBrush, QColor, QPalette
import re
from theme import theme_manager
import logging
logger = logging.getLogger("medibit")

class ThemeSettingsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        title = QLabel("Theme & Appearance")
        title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        title.setToolTip("Section: Theme and Appearance")
        title.setAccessibleName("Theme Appearance Title")
        layout.addWidget(title)
        desc = QLabel("Customize the application's appearance.")
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 15px;")
        desc.setWordWrap(True)
        desc.setToolTip("Description of theme and appearance settings.")
        desc.setAccessibleName("Theme Appearance Description")
        layout.addWidget(desc)
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setToolTip("Select light or dark mode for the application.")
        self.theme_combo.setAccessibleName("Theme ComboBox")
        current_theme = getattr(self.main_window, 'theme', 'light').capitalize()
        idx = self.theme_combo.findText(current_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        # Accent color
        accent_layout = QHBoxLayout()
        accent_label = QLabel("Accent Color:")
        self.accent_btn = QPushButton("Choose Color")
        self.accent_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.accent_btn.setToolTip("Choose the accent color for the application.")
        self.accent_btn.setAccessibleName("Accent Color Button")
        self.accent_btn.clicked.connect(self.choose_accent_color)
        self.accent_display = QLabel()
        self.accent_display.setFixedSize(32, 20)
        self.accent_display.setStyleSheet("background: #1976d2; border: 1px solid #888;")
        self.accent_display.setToolTip("Displays the selected accent color.")
        self.accent_display.setAccessibleName("Accent Color Display")
        accent_layout.addWidget(accent_label)
        accent_layout.addWidget(self.accent_btn)
        accent_layout.addWidget(self.accent_display)
        accent_layout.addStretch()
        layout.addLayout(accent_layout)
        # Gradient selection
        gradient_layout = QHBoxLayout()
        gradient_label = QLabel("Background Gradient:")
        self.gradient_combo = QComboBox()
        self.gradient_combo.addItems([
            "None",
            "Blue to White",
            "Purple to Pink",
            "Green to Blue",
            "Grey to Black"
        ])
        self.gradient_combo.setToolTip("Select a background gradient for the application.")
        self.gradient_combo.setAccessibleName("Gradient ComboBox")
        self.gradient_combo.currentIndexChanged.connect(self.update_gradient_preview)
        gradient_layout.addWidget(gradient_label)
        gradient_layout.addWidget(self.gradient_combo)
        layout.addLayout(gradient_layout)
        # Gradient preview
        self.gradient_preview = QLabel()
        self.gradient_preview.setFixedSize(120, 32)
        self.gradient_preview.setStyleSheet("border: 1px solid #888;")
        self.gradient_preview.setToolTip("Preview of the selected background gradient.")
        self.gradient_preview.setAccessibleName("Gradient Preview Label")
        layout.addWidget(self.gradient_preview)
        self.update_gradient_preview()
        # Save button
        self.save_btn = QPushButton("Apply Theme")
        self.save_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.save_btn.setToolTip("Apply the selected theme and appearance settings.")
        self.save_btn.setAccessibleName("Apply Theme Button")
        self.save_btn.clicked.connect(self.save_theme)
        layout.addWidget(self.save_btn)
        layout.addStretch()
        self.selected_accent = '#1976d2'
        self.selected_gradient = 'None'

    def choose_accent_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_accent = color.name()
            self.accent_display.setStyleSheet(f"background: {self.selected_accent}; border: 1px solid #888;")

    def update_gradient_preview(self):
        gradient = self.gradient_combo.currentText()
        self.selected_gradient = gradient
        if gradient == "Blue to White":
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #ffffff);"
        elif gradient == "Purple to Pink":
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8e24aa, stop:1 #ff4081);"
        elif gradient == "Green to Blue":
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #43cea2, stop:1 #185a9d);"
        elif gradient == "Grey to Black":
            style = "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0e0e0, stop:1 #212121);"
        else:
            style = "background: #fff;"
        self.gradient_preview.setStyleSheet(f"border: 1px solid #888; {style}")

    def save_theme(self):
        logger.info("Apply Theme button clicked.")
        theme = self.theme_combo.currentText().lower()
        accent = self.selected_accent
        gradient = self.selected_gradient
        # Save to settings_service if available
        if hasattr(self.main_window, 'settings_service'):
            self.main_window.settings_service.set_theme(theme)
            self.main_window.settings_service.set_accent_color(accent)
            self.main_window.settings_service.set_gradient(gradient)
        # Apply theme and gradient immediately if possible
        if hasattr(self.main_window, 'set_theme_from_menu'):
            self.main_window.set_theme_from_menu(theme)
        self.apply_gradient_to_app(gradient)
        QMessageBox.information(self, "Theme Applied", f"Theme: {theme.capitalize()}\nAccent: {accent}\nGradient: {gradient}")
        logger.info("Theme applied successfully.")

    def apply_gradient_to_app(self, gradient):
        # Apply the gradient to the main window or app
        if gradient == "Blue to White":
            style = "QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976d2, stop:1 #ffffff); }"
        elif gradient == "Purple to Pink":
            style = "QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8e24aa, stop:1 #ff4081); }"
        elif gradient == "Green to Blue":
            style = "QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #43cea2, stop:1 #185a9d); }"
        elif gradient == "Grey to Black":
            style = "QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e0e0e0, stop:1 #212121); }"
        else:
            style = ""
        if style:
            self.main_window.setStyleSheet(style)
        else:
            # Always reapply the theme stylesheet if no gradient is selected
            if hasattr(self.main_window, 'set_theme_from_menu'):
                self.main_window.set_theme_from_menu(self.theme_combo.currentText().lower())

class BackupSettingsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        title = QLabel("Backup & Restore")
        title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        title.setToolTip("Section: Backup and Restore")
        title.setAccessibleName("Backup Restore Title")
        layout.addWidget(title)
        desc = QLabel("Backup your data or restore from a previous backup. Only admins should use restore.")
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 15px;")
        desc.setWordWrap(True)
        desc.setToolTip("Description of backup and restore settings.")
        desc.setAccessibleName("Backup Restore Description")
        layout.addWidget(desc)
        # Backup button
        self.backup_btn = QPushButton("Backup Data")
        self.backup_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.backup_btn.setToolTip("Backup the current application data.")
        self.backup_btn.setAccessibleName("Backup Data Button")
        self.backup_btn.clicked.connect(self.backup_data)
        layout.addWidget(self.backup_btn)
        # Restore button
        self.restore_btn = QPushButton("Restore Data")
        self.restore_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.restore_btn.setToolTip("Restore data from a previously saved backup file.")
        self.restore_btn.setAccessibleName("Restore Data Button")
        self.restore_btn.clicked.connect(self.restore_data)
        layout.addWidget(self.restore_btn)
        layout.addStretch()

    def backup_data(self):
        logger.info("Backup Data button clicked.")
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'medibit.db')
        if not os.path.exists(db_path):
            QMessageBox.warning(self, "Backup Failed", "Database file not found.")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Backup Database", "medibit_backup.db", "Database Files (*.db)")
        if filename:
            try:
                shutil.copy2(db_path, filename)
                QMessageBox.information(self, "Backup Complete", f"Backup saved to: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Backup Failed", str(e))
        logger.info("Data backup completed.")

    def restore_data(self):
        logger.info("Restore Data button clicked.")
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database', 'medibit.db')
        filename, _ = QFileDialog.getOpenFileName(self, "Restore Database", "", "Database Files (*.db)")
        if filename:
            try:
                shutil.copy2(filename, db_path)
                QMessageBox.information(self, "Restore Complete", "Database restored successfully. Please restart the application.")
            except Exception as e:
                QMessageBox.critical(self, "Restore Failed", str(e))
        logger.info("Data restore completed.")

class LicenseSettingsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        title = QLabel("License Activation")
        title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        title.setToolTip("Section: License Activation")
        title.setAccessibleName("License Activation Title")
        layout.addWidget(title)
        desc = QLabel("View your license status or activate your product.")
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 15px;")
        desc.setWordWrap(True)
        desc.setToolTip("Description of license activation settings.")
        desc.setAccessibleName("License Activation Description")
        layout.addWidget(desc)
        # License status
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        self.status_label.setToolTip("Current status of your application license.")
        self.status_label.setAccessibleName("License Status Label")
        layout.addWidget(self.status_label)
        self.refresh_status()
        # License key entry
        form_layout = QFormLayout()
        self.license_key_edit = QLineEdit()
        self.license_key_edit.setPlaceholderText("Enter license key")
        self.license_key_edit.setToolTip("Enter your license key to activate the application.")
        self.license_key_edit.setAccessibleName("License Key Edit")
        form_layout.addRow("License Key:", self.license_key_edit)
        layout.addLayout(form_layout)
        # Activate button
        self.activate_btn = QPushButton("Activate License")
        self.activate_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.activate_btn.setToolTip("Activate the application using the provided license key.")
        self.activate_btn.setAccessibleName("Activate License Button")
        self.activate_btn.clicked.connect(self.activate_license)
        layout.addWidget(self.activate_btn)
        layout.addStretch()

    def refresh_status(self):
        # Try to get license status from main_window or settings_service
        status = "Unknown"
        if hasattr(self.main_window, 'check_license'):
            status = "Activated" if self.main_window.check_license() else "Not Activated"
        elif hasattr(self.main_window, 'settings_service') and hasattr(self.main_window.settings_service, 'is_activated'):
            status = "Activated" if self.main_window.settings_service.is_activated() else "Not Activated"
        self.status_label.setText(f"License Status: {status}")

    def activate_license(self):
        logger.info("Activate License button clicked.")
        key = self.license_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Validation Error", "Please enter a license key.")
            return
        # Add basic format check (e.g., length or pattern)
        if len(key) < 8:
            QMessageBox.warning(self, "Validation Error", "License key must be at least 8 characters.")
            return
        # Try to activate via main_window or settings_service
        success = False
        msg = ""
        if hasattr(self.main_window, 'settings_service') and hasattr(self.main_window.settings_service, 'activate_license'):
            try:
                success, msg = self.main_window.settings_service.activate_license(key)
            except Exception as e:
                msg = str(e)
        elif hasattr(self.main_window, 'activate_license'):
            try:
                success, msg = self.main_window.activate_license(key)
            except Exception as e:
                msg = str(e)
        if success:
            QMessageBox.information(self, "Success", msg or "License activated successfully.")
            self.refresh_status()
        else:
            QMessageBox.critical(self, "Activation Failed", msg or "Failed to activate license.")
        logger.info("License activation attempted.")

class IntegrationSettingsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        title = QLabel("Integration Settings")
        title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        title.setToolTip("Section: Integration Settings")
        title.setAccessibleName("Integration Settings Title")
        layout.addWidget(title)
        desc = QLabel("Configure API keys and integration settings for Email, WhatsApp, and SMS notifications.")
        desc.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 15px;")
        desc.setWordWrap(True)
        desc.setToolTip("Description of integration settings for notifications.")
        desc.setAccessibleName("Integration Settings Description")
        layout.addWidget(desc)
        form_layout = QFormLayout()
        # Email
        self.email_api_key = QLineEdit()
        self.email_api_key.setPlaceholderText("SMTP password or App Password")
        self.email_api_key.setToolTip("Enter the SMTP password or App Password for sending emails.")
        self.email_api_key.setAccessibleName("Email API Key Edit")
        form_layout.addRow("Email SMTP/App Password:", self.email_api_key)
        # WhatsApp
        self.whatsapp_api_key = QLineEdit()
        self.whatsapp_api_key.setPlaceholderText("Twilio Account SID:Auth Token")
        self.whatsapp_api_key.setToolTip("Enter your Twilio Account SID and Auth Token for WhatsApp notifications.")
        self.whatsapp_api_key.setAccessibleName("WhatsApp API Key Edit")
        form_layout.addRow("WhatsApp API Key:", self.whatsapp_api_key)
        # SMS
        self.sms_api_key = QLineEdit()
        self.sms_api_key.setPlaceholderText("Twilio Account SID:Auth Token")
        self.sms_api_key.setToolTip("Enter your Twilio Account SID and Auth Token for SMS notifications.")
        self.sms_api_key.setAccessibleName("SMS API Key Edit")
        form_layout.addRow("SMS API Key:", self.sms_api_key)
        layout.addLayout(form_layout)
        self.save_btn = QPushButton("Save Integration Settings")
        self.save_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.save_btn.setToolTip("Save the current integration settings.")
        self.save_btn.setAccessibleName("Save Integration Settings Button")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)
        layout.addStretch()
        # Load current values if available
        self.load_current_settings()

    def load_current_settings(self):
        # Try to load from main_window or settings_service
        nm = getattr(self.main_window, 'notification_manager', None)
        if not nm and hasattr(self.main_window, 'settings_service'):
            nm = getattr(self.main_window.settings_service, 'notification_manager', None)
        if nm:
            self.email_api_key.setText(nm.config['email'].get('sender_password', ''))
            self.whatsapp_api_key.setText(nm.config['whatsapp'].get('api_key', ''))
            self.sms_api_key.setText(nm.config['sms'].get('api_key', ''))

    def save_settings(self):
        logger.info("Save Integration Settings button clicked.")
        email_key = self.email_api_key.text().strip()
        whatsapp_key = self.whatsapp_api_key.text().strip()
        sms_key = self.sms_api_key.text().strip()
        errors = []
        if not email_key:
            errors.append("Email SMTP/App Password is required.")
        if not whatsapp_key:
            errors.append("WhatsApp API Key is required.")
        if not sms_key:
            errors.append("SMS API Key is required.")
        # Add basic format checks (e.g., length or pattern)
        if email_key and len(email_key) < 6:
            errors.append("Email SMTP/App Password must be at least 6 characters.")
        if whatsapp_key and ':' not in whatsapp_key:
            errors.append("WhatsApp API Key must be in the format 'SID:AuthToken'.")
        if sms_key and ':' not in sms_key:
            errors.append("SMS API Key must be in the format 'SID:AuthToken'.")
        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return
        # Try to save to notification_manager if available
        nm = getattr(self.main_window, 'notification_manager', None)
        if not nm and hasattr(self.main_window, 'settings_service'):
            nm = getattr(self.main_window.settings_service, 'notification_manager', None)
        if nm:
            nm.update_config('email', 'sender_password', self.email_api_key.text().strip())
            nm.update_config('whatsapp', 'api_key', self.whatsapp_api_key.text().strip())
            nm.update_config('sms', 'api_key', self.sms_api_key.text().strip())
            QMessageBox.information(self, "Success", "Integration settings saved.")
        else:
            QMessageBox.warning(self, "Not Saved", "Could not find notification manager to save settings.")
        logger.info("Integration settings saved.")

class SettingsUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        logger.info("SettingsUi initialized")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Left: Settings buttons
        button_panel = QWidget()
        button_layout = QVBoxLayout(button_panel)
        button_layout.setSpacing(16)
        button_layout.setAlignment(Qt.AlignTop)
        self.notification_btn = QPushButton("Notification Settings")
        self.notification_btn.setMinimumHeight(50)
        self.notification_btn.setToolTip("Open Notification Settings.")
        self.notification_btn.setAccessibleName("Notification Settings Button")
        button_layout.addWidget(self.notification_btn)
        self.pharmacy_btn = QPushButton("Pharmacy Details")
        self.pharmacy_btn.setMinimumHeight(50)
        self.pharmacy_btn.setToolTip("Open Pharmacy Details Settings.")
        self.pharmacy_btn.setAccessibleName("Pharmacy Details Button")
        button_layout.addWidget(self.pharmacy_btn)
        self.theme_btn = QPushButton("Theme / Appearance")
        self.theme_btn.setMinimumHeight(50)
        self.theme_btn.setToolTip("Open Theme and Appearance Settings.")
        self.theme_btn.setAccessibleName("Theme Appearance Button")
        button_layout.addWidget(self.theme_btn)
        self.backup_btn = QPushButton("Backup & Restore")
        self.backup_btn.setMinimumHeight(50)
        self.backup_btn.setToolTip("Open Backup and Restore Settings.")
        self.backup_btn.setAccessibleName("Backup Restore Button")
        button_layout.addWidget(self.backup_btn)
        self.license_btn = QPushButton("License Activation")
        self.license_btn.setMinimumHeight(50)
        self.license_btn.setToolTip("Open License Activation Settings.")
        self.license_btn.setAccessibleName("License Activation Button")
        button_layout.addWidget(self.license_btn)
        self.integration_btn = QPushButton("Integration Settings")
        self.integration_btn.setMinimumHeight(50)
        self.integration_btn.setToolTip("Open Integration Settings for Email, WhatsApp, and SMS.")
        self.integration_btn.setAccessibleName("Integration Settings Button")
        button_layout.addWidget(self.integration_btn)
        button_layout.addStretch()
        layout.addWidget(button_panel, 0)
        # Right: Settings panel area (QStackedWidget)
        self.settings_panel = QStackedWidget()
        self.notification_widget = NotificationSettingsWidget(self)
        self.pharmacy_widget = PharmacyDetailsWidget(self.main_window)
        # Connect details_saved signal to a robust slot
        self.pharmacy_widget.details_saved.connect(self._on_pharmacy_details_saved)
        self.theme_widget = ThemeSettingsWidget(self.main_window)
        self.backup_widget = BackupSettingsWidget(self.main_window)
        self.license_widget = LicenseSettingsWidget(self.main_window)
        self.integration_widget = IntegrationSettingsWidget(self.main_window)
        self.settings_panel.addWidget(self.notification_widget)
        self.settings_panel.addWidget(self.pharmacy_widget)
        self.settings_panel.addWidget(self.theme_widget)
        self.settings_panel.addWidget(self.backup_widget)
        self.settings_panel.addWidget(self.license_widget)
        self.settings_panel.addWidget(self.integration_widget)
        layout.addWidget(self.settings_panel, 1)
        # Connect buttons to switch panels
        self.notification_btn.clicked.connect(lambda: self.settings_panel.setCurrentIndex(0))
        self.pharmacy_btn.clicked.connect(lambda: self.settings_panel.setCurrentIndex(1))
        self.theme_btn.clicked.connect(lambda: self.settings_panel.setCurrentIndex(2))
        self.backup_btn.clicked.connect(lambda: self.settings_panel.setCurrentIndex(3))
        self.license_btn.clicked.connect(lambda: self.settings_panel.setCurrentIndex(4))
        self.integration_btn.clicked.connect(lambda: self.settings_panel.setCurrentIndex(5))
        # Connect details_saved signal to main window label update
        if hasattr(self.main_window, 'update_pharmacy_name_label'):
            self.pharmacy_widget.details_saved.connect(self.main_window.update_pharmacy_name_label) 

    def _on_pharmacy_details_saved(self):
        main_window = self.pharmacy_widget._main_window_ref()
        if main_window and hasattr(main_window, 'update_pharmacy_name_label'):
            main_window.update_pharmacy_name_label() 