from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QSpinBox, QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QDoubleSpinBox, QListWidget, QListWidgetItem, QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt
import re
from theme import theme_manager
import logging
logger = logging.getLogger("medibit")
from theme import create_animated_button

class BillingUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Reference to MainWindow for callbacks
        logger.info("BillingUi initialized")
        self.init_ui()
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        # Connect validation to finalize/save actions
        self.finalize_bill_btn.clicked.connect(self._on_finalize_bill)
        self.save_draft_btn.clicked.connect(self._on_save_draft)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # --- Customer Information Section ---
        customer_info_frame = QFrame()
        customer_layout = QGridLayout(customer_info_frame)
        customer_layout.setContentsMargins(12, 12, 12, 12)
        customer_layout.setSpacing(10)
        # Title
        customer_title = QLabel("Customer Information")
        customer_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        customer_title.setToolTip("Section: Customer Information")
        customer_title.setAccessibleName("Customer Information Title")
        customer_layout.addWidget(customer_title, 0, 0, 1, 4)
        # Name & Age
        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Enter customer name")
        self.customer_name.setToolTip("Enter the customer's full name.")
        self.customer_name.setAccessibleName("Customer Name Field")
        customer_layout.addWidget(QLabel("Name:"), 1, 0)
        customer_layout.addWidget(self.customer_name, 1, 1)
        self.customer_age = QSpinBox()
        self.customer_age.setRange(1, 120)
        self.customer_age.setValue(25)
        self.customer_age.setToolTip("Enter the customer's age.")
        self.customer_age.setAccessibleName("Customer Age Field")
        customer_layout.addWidget(QLabel("Age:"), 1, 2)
        customer_layout.addWidget(self.customer_age, 1, 3)
        # Gender & Phone
        self.customer_gender = QComboBox()
        self.customer_gender.addItems(["Male", "Female", "Other"])
        self.customer_gender.setToolTip("Select the customer's gender.")
        self.customer_gender.setAccessibleName("Customer Gender Field")
        customer_layout.addWidget(QLabel("Gender:"), 2, 0)
        customer_layout.addWidget(self.customer_gender, 2, 1)
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("Enter phone number")
        self.customer_phone.setToolTip("Enter the customer's phone number.")
        self.customer_phone.setAccessibleName("Customer Phone Field")
        customer_layout.addWidget(QLabel("Phone:"), 2, 2)
        customer_layout.addWidget(self.customer_phone, 2, 3)
        # Email & Address
        self.customer_email = QLineEdit()
        self.customer_email.setPlaceholderText("Enter email address")
        self.customer_email.setToolTip("Enter the customer's email address.")
        self.customer_email.setAccessibleName("Customer Email Field")
        customer_layout.addWidget(QLabel("Email:"), 3, 0)
        customer_layout.addWidget(self.customer_email, 3, 1)
        self.customer_address = QLineEdit()
        self.customer_address.setPlaceholderText("Enter address")
        self.customer_address.setToolTip("Enter the customer's address.")
        self.customer_address.setAccessibleName("Customer Address Field")
        customer_layout.addWidget(QLabel("Address:"), 3, 2)
        customer_layout.addWidget(self.customer_address, 3, 3)
        layout.addWidget(customer_info_frame)
        # --- Billing Table Section ---
        billing_frame = QFrame()
        billing_layout = QVBoxLayout(billing_frame)
        billing_layout.setContentsMargins(12, 12, 12, 12)
        billing_layout.setSpacing(10)
        # Title
        billing_title = QLabel("Billing Items")
        billing_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        billing_title.setToolTip("Section: Billing Items")
        billing_title.setAccessibleName("Billing Items Title")
        billing_layout.addWidget(billing_title)
        # Table
        self.billing_table = QTableWidget(0, 6)
        self.billing_table.setHorizontalHeaderLabels(["Barcode", "Name", "Quantity", "Price", "Tax", "Discount"])
        self.billing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.billing_table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.billing_table.setToolTip("Table showing all items in the current bill.")
        self.billing_table.setAccessibleName("Billing Items Table")
        # Connect table changes to summary updates
        self.billing_table.itemChanged.connect(self._on_table_item_changed)
        billing_layout.addWidget(self.billing_table)
        # Buttons
        btn_layout = QHBoxLayout()
        self.add_item_btn = create_animated_button("Add Item", self)
        self.add_item_btn.setToolTip("Add a new item to the bill.")
        self.add_item_btn.setAccessibleName("Add Item Button")
        # Note: Button connections will be handled by MainWindow
        self.remove_item_btn = create_animated_button("Remove Item", self)
        self.remove_item_btn.setToolTip("Remove the selected item from the bill.")
        self.remove_item_btn.setAccessibleName("Remove Item Button")
        # Note: Button connections will be handled by MainWindow
        btn_layout.addWidget(self.add_item_btn)
        btn_layout.addWidget(self.remove_item_btn)
        btn_layout.addStretch()
        billing_layout.addLayout(btn_layout)
        
        # --- Billing Table and Recent Bills Side by Side ---
        table_and_recent_layout = QHBoxLayout()
        table_and_recent_layout.setSpacing(16)
        
        # Left side: Billing Table
        table_and_recent_layout.addWidget(billing_frame, stretch=2)
        
        # Right side: Recent Bills & Drafts
        recent_frame = QFrame()
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setContentsMargins(12, 12, 12, 12)
        recent_layout.setSpacing(10)
        
        # Title
        recent_title = QLabel("Recent Bills & Drafts")
        recent_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        recent_title.setToolTip("Section: Recent Bills and Drafts")
        recent_title.setAccessibleName("Recent Bills Drafts Title")
        recent_layout.addWidget(recent_title)
        
        # List
        self.recent_bills_list = QListWidget()
        self.recent_bills_list.setStyleSheet(theme_manager.get_table_stylesheet())
        self.recent_bills_list.setToolTip("List of recent bills and saved drafts.")
        self.recent_bills_list.setAccessibleName("Recent Bills List")
        recent_layout.addWidget(self.recent_bills_list)
        
        # Buttons
        recent_btn_layout = QHBoxLayout()
        self.download_pdf_btn = create_animated_button("Download PDF", self)
        self.download_pdf_btn.setToolTip("Download the selected bill as PDF.")
        self.download_pdf_btn.setAccessibleName("Download PDF Button")
        # Note: Button connections will be handled by MainWindow
        
        self.delete_draft_btn = create_animated_button("Delete Draft", self)
        self.delete_draft_btn.setToolTip("Delete the selected draft.")
        self.delete_draft_btn.setAccessibleName("Delete Draft Button")
        # Note: Button connections will be handled by MainWindow
        
        recent_btn_layout.addWidget(self.download_pdf_btn)
        recent_btn_layout.addWidget(self.delete_draft_btn)
        recent_btn_layout.addStretch()
        recent_layout.addLayout(recent_btn_layout)
        
        # Add recent frame to the right side
        table_and_recent_layout.addWidget(recent_frame, stretch=1)
        
        # Add the combined layout to main layout
        layout.addLayout(table_and_recent_layout)
        # --- Bill Summary Section ---
        summary_frame = QFrame()
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(10)
        # Title
        summary_title = QLabel("Bill Summary")
        summary_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        summary_title.setToolTip("Section: Bill Summary")
        summary_title.setAccessibleName("Bill Summary Title")
        summary_layout.addWidget(summary_title)
        # Summary details
        summary_details_layout = QGridLayout()
        
        # Tax and Discount Input Row
        tax_discount_layout = QHBoxLayout()
        
        # Tax percentage input
        tax_label = QLabel("Tax %:")
        tax_label.setStyleSheet("font-weight: bold;")
        tax_discount_layout.addWidget(tax_label)
        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setRange(0.0, 100.0)
        self.tax_spin.setValue(0.0)
        self.tax_spin.setSuffix("%")
        self.tax_spin.setDecimals(2)
        self.tax_spin.setToolTip("Enter tax percentage to apply to the bill.")
        self.tax_spin.setAccessibleName("Tax Percentage Input")
        self.tax_spin.valueChanged.connect(self._on_tax_discount_changed)
        tax_discount_layout.addWidget(self.tax_spin)
        
        tax_discount_layout.addSpacing(20)
        
        # Discount percentage input
        discount_label = QLabel("Discount %:")
        discount_label.setStyleSheet("font-weight: bold;")
        tax_discount_layout.addWidget(discount_label)
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0.0, 100.0)
        self.discount_spin.setValue(0.0)
        self.discount_spin.setSuffix("%")
        self.discount_spin.setDecimals(2)
        self.discount_spin.setToolTip("Enter discount percentage to apply to the bill.")
        self.discount_spin.setAccessibleName("Discount Percentage Input")
        self.discount_spin.valueChanged.connect(self._on_tax_discount_changed)
        tax_discount_layout.addWidget(self.discount_spin)
        
        tax_discount_layout.addStretch()
        summary_details_layout.addLayout(tax_discount_layout, 0, 0, 1, 2)
        
        # Summary labels
        self.subtotal_label = QLabel("Subtotal: ₹0.00")
        self.subtotal_label.setToolTip("Subtotal amount before tax and discount.")
        self.subtotal_label.setAccessibleName("Subtotal Label")
        summary_details_layout.addWidget(self.subtotal_label, 1, 0)
        
        self.tax_label = QLabel("Tax (0%): ₹0.00")
        self.tax_label.setToolTip("Tax amount based on the tax percentage.")
        self.tax_label.setAccessibleName("Tax Label")
        summary_details_layout.addWidget(self.tax_label, 1, 1)
        
        self.discount_label = QLabel("Discount (0%): ₹0.00")
        self.discount_label.setToolTip("Discount amount based on the discount percentage.")
        self.discount_label.setAccessibleName("Discount Label")
        summary_details_layout.addWidget(self.discount_label, 2, 0)
        
        self.total_label = QLabel("Total: ₹0.00")
        self.total_label.setStyleSheet(theme_manager.get_bill_summary_total_stylesheet())
        self.total_label.setToolTip("Total amount including tax and discount.")
        self.total_label.setAccessibleName("Total Label")
        summary_details_layout.addWidget(self.total_label, 2, 1)
        summary_layout.addLayout(summary_details_layout)
        # Action buttons
        action_btn_layout = QHBoxLayout()
        self.save_draft_btn = create_animated_button("Save Draft", self)
        self.save_draft_btn.setToolTip("Save the current bill as a draft.")
        self.save_draft_btn.setAccessibleName("Save Draft Button")
        # Note: Button connections will be handled by MainWindow
        self.finalize_bill_btn = create_animated_button("Finalize Bill", self)
        self.finalize_bill_btn.setToolTip("Finalize and complete the bill.")
        self.finalize_bill_btn.setAccessibleName("Finalize Bill Button")
        # Note: Button connections will be handled by MainWindow
        self.print_bill_btn = create_animated_button("Print Bill", self)
        self.print_bill_btn.setToolTip("Print the current bill.")
        self.print_bill_btn.setAccessibleName("Print Bill Button")
        # Note: Button connections will be handled by MainWindow
        self.clear_bill_btn = create_animated_button("Clear Bill", self)
        self.clear_bill_btn.setToolTip("Clear all items and customer information.")
        self.clear_bill_btn.setAccessibleName("Clear Bill Button")
        self.clear_bill_btn.clicked.connect(self.clear_bill)
        action_btn_layout.addWidget(self.save_draft_btn)
        action_btn_layout.addWidget(self.finalize_bill_btn)
        action_btn_layout.addWidget(self.print_bill_btn)
        action_btn_layout.addWidget(self.clear_bill_btn)
        action_btn_layout.addStretch()
        summary_layout.addLayout(action_btn_layout)
        layout.addWidget(summary_frame)

    def validate_customer_info(self):
        """Validate customer information fields"""
        name = self.customer_name.text().strip()
        age = self.customer_age.value()
        phone = self.customer_phone.text().strip()
        email = self.customer_email.text().strip()
        address = self.customer_address.text().strip()
        # Name
        if not name:
            QMessageBox.warning(self, "Validation Error", "Customer name is required to finalize the bill.")
            return False
        # Age
        if age < 1:
            QMessageBox.warning(self, "Validation Error", "Customer age must be greater than 0.")
            return False
        # Phone (must be at least 10 digits and numeric)
        if not (phone.isdigit() and len(phone) >= 10):
            QMessageBox.warning(self, "Validation Error", "Customer phone must be at least 10 digits and numeric.")
            return False
        # Email (must contain '@' and '.')
        if '@' not in email or '.' not in email:
            QMessageBox.warning(self, "Validation Error", "Customer email must be valid (contain '@' and '.').")
            return False
        # Address
        if not address:
            QMessageBox.warning(self, "Validation Error", "Customer address is required.")
            return False
        return True

    def validate_billing_items(self):
        """Validate billing items for completeness and correctness"""
        logger.debug("Validating billing items...")
        
        # Check if billing table has any items
        if self.billing_table.rowCount() == 0:
            logger.warning("Validation failed: No items in bill.")
            QMessageBox.warning(self, "Validation Error", "Please add at least one item to the bill.")
            return False
        
        # Check each item for validity
        barcodes = set()
        for row in range(self.billing_table.rowCount()):
            barcode = self.billing_table.item(row, 0).text().strip()
            name = self.billing_table.item(row, 1).text().strip()
            quantity = self.billing_table.item(row, 2).text().strip()
            price = self.billing_table.item(row, 3).text().strip()
            
            # Check for duplicate barcodes
            if barcode in barcodes:
                logger.warning(f"Validation failed: Duplicate barcode {barcode}.")
                QMessageBox.warning(self, "Validation Error", f"Duplicate barcode found: {barcode}")
                return False
            barcodes.add(barcode)
            
            # Check for empty required fields
            if not barcode or not name:
                logger.warning("Validation failed: Empty barcode or name.")
                QMessageBox.warning(self, "Validation Error", "All items must have barcode and name.")
                return False
            
            # Check for valid quantity
            try:
                qty = int(quantity)
                if qty <= 0:
                    logger.warning(f"Validation failed: Invalid quantity {qty}.")
                    QMessageBox.warning(self, "Validation Error", f"Quantity must be greater than 0 for item: {name}")
                    return False
            except ValueError:
                logger.warning(f"Validation failed: Invalid quantity format {quantity}.")
                QMessageBox.warning(self, "Validation Error", f"Invalid quantity format for item: {name}")
                return False
            
            # Check for valid price
            try:
                prc = float(price)
                if prc < 0:
                    logger.warning(f"Validation failed: Negative price {prc}.")
                    QMessageBox.warning(self, "Validation Error", f"Price cannot be negative for item: {name}")
                    return False
            except ValueError:
                logger.warning(f"Validation failed: Invalid price format {price}.")
                QMessageBox.warning(self, "Validation Error", f"Invalid price format for item: {name}")
                return False
        
        logger.info("Billing items validated successfully.")
        return True

    def validate_bill(self):
        """Validate both customer info and billing items"""
        logger.debug("Validating complete bill...")
        
        # Validate customer information
        if not self.validate_customer_info():
            return False
        
        # Validate billing items
        if not self.validate_billing_items():
            return False
        
        logger.info("Complete bill validation successful.")
        return True

    def _on_tax_discount_changed(self):
        """Handle tax or discount percentage changes"""
        logger.debug("Tax or discount percentage changed, recalculating totals.")
        self.update_bill_summary()

    def get_billing_items(self):
        """Extract billing items from the table"""
        items = []
        for row in range(self.billing_table.rowCount()):
            barcode = self.billing_table.item(row, 0).text().strip()
            name = self.billing_table.item(row, 1).text().strip()
            quantity = self.billing_table.item(row, 2).text().strip()
            price = self.billing_table.item(row, 3).text().strip()
            tax = self.billing_table.item(row, 4).text().strip() if self.billing_table.item(row, 4) else "0"
            discount = self.billing_table.item(row, 5).text().strip() if self.billing_table.item(row, 5) else "0"
            
            if barcode and name and quantity and price:
                try:
                    items.append({
                        'barcode': barcode,
                        'name': name,
                        'quantity': int(quantity),
                        'price': float(price),
                        'tax': float(tax) if tax else 0.0,
                        'discount': float(discount) if discount else 0.0
                    })
                except ValueError:
                    logger.warning(f"Invalid numeric value in row {row}")
                    continue
        return items

    def update_bill_summary(self):
        """Calculate and update the bill summary using the billing service"""
        try:
            from billing_service import BillingService
            
            # Get items from table
            items = self.get_billing_items()
            
            # Get tax and discount percentages
            tax_percent = self.tax_spin.value()
            discount_percent = self.discount_spin.value()
            
            # Calculate subtotal
            subtotal = sum(item['price'] * item['quantity'] for item in items)
            
            # Use billing service for calculation
            billing_service = BillingService()
            subtotal_calc, tax_amount, discount_amount, total = billing_service.calculate_totals(
                items, tax_percent, discount_percent
            )
            
            # Update labels
            self.subtotal_label.setText(f"Subtotal: ₹{subtotal:.2f}")
            self.tax_label.setText(f"Tax ({tax_percent:.1f}%): ₹{tax_amount:.2f}")
            self.discount_label.setText(f"Discount ({discount_percent:.1f}%): ₹{discount_amount:.2f}")
            self.total_label.setText(f"Total: ₹{total:.2f}")
            
            logger.debug(f"Bill summary updated: subtotal={subtotal:.2f}, tax={tax_amount:.2f}, discount={discount_amount:.2f}, total={total:.2f}")
            
        except Exception as e:
            logger.error(f"Error updating bill summary: {e}", exc_info=True)
            # Set default values on error
            self.subtotal_label.setText("Subtotal: ₹0.00")
            self.tax_label.setText("Tax (0%): ₹0.00")
            self.discount_label.setText("Discount (0%): ₹0.00")
            self.total_label.setText("Total: ₹0.00")

    def refresh_billing_table(self):
        """Refresh the billing table and update summary"""
        logger.debug("Refreshing billing table and updating summary.")
        self.update_bill_summary()

    def clear_bill(self):
        """Clear the current bill"""
        logger.info("Clearing current bill.")
        
        # Clear customer info
        self.customer_name.clear()
        self.customer_age.setValue(25)
        self.customer_gender.setCurrentIndex(0)
        self.customer_phone.clear()
        self.customer_email.clear()
        self.customer_address.clear()
        
        # Clear billing table
        self.billing_table.setRowCount(0)
        
        # Reset tax and discount
        self.tax_spin.setValue(0.0)
        self.discount_spin.setValue(0.0)
        
        # Update summary
        self.update_bill_summary()
        
        logger.info("Bill cleared successfully.")

    def show_success_message(self, message):
        """Show a success message to the user"""
        QMessageBox.information(self, "Success", message)
        logger.info(f"Success message shown: {message}")

    def show_error_message(self, message):
        """Show an error message to the user"""
        QMessageBox.critical(self, "Error", message)
        logger.error(f"Error message shown: {message}")

    def _on_finalize_bill(self):
        """Handle finalize bill button click with comprehensive validation"""
        logger.info("Finalize bill button clicked.")
        self.finalize_bill_btn.setEnabled(False)  # Disable to prevent double-trigger
        try:
            if not self.validate_bill():
                return  # Validation failed, error message already shown
            # Call the main window's finalize bill method
            if hasattr(self.main_window, 'complete_sale'):
                result = self.main_window.complete_sale()
                if result and result.get('success'):
                    self.show_success_message("Bill finalized successfully!")
                    self.clear_bill()  # Clear the bill after successful finalization
                else:
                    error_msg = result.get('error', 'Unknown error occurred') if result else 'Unable to finalize bill'
                    self.show_error_message(f"Failed to finalize bill: {error_msg}")
            else:
                logger.error("Main window does not have complete_sale method")
                self.show_error_message("Unable to finalize bill. Please try again.")
        finally:
            self.finalize_bill_btn.setEnabled(True)  # Always re-enable after operation

    def _on_save_draft(self):
        """Handle save draft button click with comprehensive validation"""
        logger.info("Save draft button clicked.")
        
        if not self.validate_bill():
            return  # Validation failed, error message already shown
        
        # Call the main window's save draft method
        if hasattr(self.main_window, 'save_billing_draft'):
            result = self.main_window.save_billing_draft()
            if result and result.get('success'):
                self.show_success_message("Draft saved successfully!")
            else:
                error_msg = result.get('error', 'Unknown error occurred') if result else 'Unable to save draft'
                self.show_error_message(f"Failed to save draft: {error_msg}")
        else:
            logger.error("Main window does not have save_billing_draft method")
            self.show_error_message("Unable to save draft. Please try again.")

    def _on_table_item_changed(self, item):
        """Handle changes to billing table items"""
        logger.debug(f"Table item changed at row {item.row()}, column {item.column()}")
        # Update the bill summary when any item changes
        self.update_bill_summary()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts for billing operations"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Add item shortcut (Ctrl+A)
        self.add_item_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.add_item_shortcut.activated.connect(self._on_add_item_shortcut)
        
        # Remove item shortcut (Delete)
        self.remove_item_shortcut = QShortcut(QKeySequence("Delete"), self)
        self.remove_item_shortcut.activated.connect(self._on_remove_item_shortcut)
        
        # Finalize bill shortcut (Ctrl+F)
        self.finalize_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.finalize_shortcut.activated.connect(self._on_finalize_bill)
        
        # Save draft shortcut (Ctrl+S)
        self.save_draft_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_draft_shortcut.activated.connect(self._on_save_draft)
        
        # Clear bill shortcut (Ctrl+Shift+C)
        self.clear_bill_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.clear_bill_shortcut.activated.connect(self.clear_bill)
        
        logger.info("Billing keyboard shortcuts setup completed.")

    def _on_add_item_shortcut(self):
        """Handle add item keyboard shortcut"""
        logger.debug("Add item shortcut activated.")
        if hasattr(self.main_window, 'open_billing_add_medicine_dialog'):
            self.main_window.open_billing_add_medicine_dialog()
        else:
            logger.warning("Main window does not have open_billing_add_medicine_dialog method")

    def _on_remove_item_shortcut(self):
        """Handle remove item keyboard shortcut"""
        logger.debug("Remove item shortcut activated.")
        if hasattr(self.main_window, 'remove_selected_billing_item'):
            self.main_window.remove_selected_billing_item()
        else:
            logger.warning("Main window does not have remove_selected_billing_item method") 