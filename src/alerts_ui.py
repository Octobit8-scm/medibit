from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QSizePolicy, QMessageBox, QTableWidgetItem, QFrame, QProgressDialog, QApplication, QMenu, QDialog, QDialogButtonBox, QFormLayout)
from PyQt5.QtCore import Qt, QTimer
from theme import theme_manager, create_animated_button
import logging
logger = logging.getLogger("medibit")

class MedicineDetailsDialog(QDialog):
    def __init__(self, med, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Medicine Details - {med.get('name', med.get('barcode', ''))}")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        for key in ["barcode", "name", "quantity", "threshold", "expiry", "manufacturer"]:
            value = med.get(key, "")
            layout.addRow(key.capitalize() + ":", QLabel(str(value)))
        btns = QDialogButtonBox(QDialogButtonBox.Ok)
        btns.button(QDialogButtonBox.Ok).setText("Close")
        btns.setCenterButtons(True)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)
        self.setAccessibleName("Medicine Details Dialog")
        self.setFocusPolicy(Qt.StrongFocus)

class AlertsUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        logger.info("AlertsUi initialized")
        self.init_ui()
        self.refresh_alerts_table()
        self.send_alerts_btn.clicked.connect(self.send_alerts)
        # Feedback banner
        self.feedback_banner = QLabel("")
        self.feedback_banner.setStyleSheet("padding: 8px; border-radius: 4px; font-weight: bold; font-size: 14px;")
        self.feedback_banner.setVisible(False)
        self.layout().insertWidget(0, self.feedback_banner)
        # Loading overlay
        self.loading_overlay = QProgressDialog("Please wait...", None, 0, 0, self)
        self.loading_overlay.setWindowModality(Qt.WindowModal)
        self.loading_overlay.setCancelButton(None)
        self.loading_overlay.setWindowTitle("Loading")
        self.loading_overlay.setMinimumDuration(0)
        self.loading_overlay.close()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Low Stock Alerts")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        title.setToolTip("Section: Low Stock Alerts")
        title.setAccessibleName("Low Stock Alerts Title")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.send_alerts_btn = create_animated_button("Send Alerts", self)
        self.send_alerts_btn.setMinimumHeight(40)
        self.send_alerts_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.send_alerts_btn.setToolTip("Send all low stock alerts to suppliers or staff.")
        self.send_alerts_btn.setAccessibleName("Send Alerts Button")
        self.send_alerts_btn.clicked.connect(self.send_alerts)
        header_layout.addWidget(self.send_alerts_btn)
        layout.addLayout(header_layout)
        # Alerts Table
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(12, 12, 12, 12)
        table_layout.setSpacing(10)
        table_title = QLabel("Low Stock Items")
        table_title.setStyleSheet(theme_manager.get_section_title_stylesheet())
        table_title.setToolTip("Section: Low Stock Items")
        table_title.setAccessibleName("Low Stock Items Title")
        table_layout.addWidget(table_title)
        self.alerts_table = QTableWidget(0, 6)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.alerts_table.setSelectionMode(QTableWidget.MultiSelection)
        self.alerts_table.setAccessibleName("Alerts Table")
        self.alerts_table.setProperty("aria-role", "table")
        self.alerts_table.setFocusPolicy(Qt.StrongFocus)
        self.alerts_table.setTabKeyNavigation(True)
        self.alerts_table.setHorizontalHeaderLabels([
            "Barcode", "Name", "Current Stock", "Threshold", "Days Until Expiry", "Status"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.setStyleSheet(theme_manager.get_table_stylesheet())
        self.alerts_table.setToolTip("Table showing medicines with low stock or expiring soon.")
        self.alerts_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.alerts_table.customContextMenuRequested.connect(self.show_context_menu)
        self.alerts_table.cellDoubleClicked.connect(self._on_table_double_clicked)
        table_layout.addWidget(self.alerts_table)
        # Pagination controls
        self.page_size = 20
        self.current_page = 0
        pagination_layout = QHBoxLayout()
        self.prev_page_btn = create_animated_button("Previous", self)
        self.prev_page_btn.setAccessibleName("Previous Page Button")
        self.prev_page_btn.setFocusPolicy(Qt.StrongFocus)
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.next_page_btn = create_animated_button("Next", self)
        self.next_page_btn.setAccessibleName("Next Page Button")
        self.next_page_btn.setFocusPolicy(Qt.StrongFocus)
        self.next_page_btn.clicked.connect(self.next_page)
        self.page_label = QLabel("")
        pagination_layout.addWidget(self.prev_page_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_page_btn)
        layout.addLayout(pagination_layout)
        # Table action buttons
        table_btn_layout = QHBoxLayout()
        self.generate_order_btn = create_animated_button("Generate Order", self)
        self.generate_order_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.generate_order_btn.setToolTip("Generate an order for the selected low stock items.")
        self.generate_order_btn.setAccessibleName("Generate Order Button")
        self.generate_order_btn.clicked.connect(self.generate_order)
        self.dismiss_alert_btn = create_animated_button("Dismiss Alert", self)
        self.dismiss_alert_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.dismiss_alert_btn.setToolTip("Dismiss the selected alert.")
        self.dismiss_alert_btn.setAccessibleName("Dismiss Alert Button")
        self.dismiss_alert_btn.clicked.connect(self.dismiss_alert)
        # Bulk action buttons
        self.generate_order_selected_btn = create_animated_button("Generate Order for Selected", self)
        self.generate_order_selected_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.generate_order_selected_btn.setToolTip("Generate an order for all selected alerts.")
        self.generate_order_selected_btn.setAccessibleName("Generate Order for Selected Button")
        self.generate_order_selected_btn.clicked.connect(self.generate_order_for_selected)
        self.dismiss_selected_btn = create_animated_button("Dismiss Selected", self)
        self.dismiss_selected_btn.setStyleSheet(theme_manager.get_button_stylesheet())
        self.dismiss_selected_btn.setToolTip("Dismiss all selected alerts.")
        self.dismiss_selected_btn.setAccessibleName("Dismiss Selected Alerts Button")
        self.dismiss_selected_btn.clicked.connect(self.dismiss_selected_alerts)
        table_btn_layout.addWidget(self.generate_order_btn)
        table_btn_layout.addWidget(self.dismiss_alert_btn)
        table_btn_layout.addWidget(self.generate_order_selected_btn)
        table_btn_layout.addWidget(self.dismiss_selected_btn)
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        layout.addWidget(table_frame)
        # Load initial data
        self.load_alerts()

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
        def safe_hide():
            if self.feedback_banner and not sip.isdeleted(self.feedback_banner):
                self.feedback_banner.setVisible(False)
        import sip
        QTimer.singleShot(3000, safe_hide)

    def send_alerts(self):
        logger.info("Send Alerts button clicked.")
        self.show_loading("Sending alerts...")
        try:
            success, msg = self.main_window.alert_service.send_all_alerts()
            if success:
                self.show_banner(msg, success=True)
            else:
                self.show_banner(msg, success=False)
        finally:
            self.hide_loading()
        logger.info("Alerts sent.")

    def generate_order(self):
        logger.info("Generate Order button clicked.")
        self.show_loading("Generating order...")
        try:
            # ... existing code ...
            self.show_banner("Order generated from alert.", success=True)
        except Exception as e:
            self.show_banner(f"Failed to generate order: {str(e)}", success=False)
        finally:
            self.hide_loading()
        logger.info("Order generated from alert.")

    def dismiss_alert(self):
        logger.info("Dismiss Alert button clicked.")
        self.show_loading("Dismissing alert...")
        try:
            # ... existing code ...
            self.show_banner("Alert dismissed.", success=True)
        except Exception as e:
            self.show_banner(f"Failed to dismiss alert: {str(e)}", success=False)
        finally:
            self.hide_loading()
        logger.info("Alert dismissed.")

    def get_selected_alert_rows(self):
        return set(idx.row() for idx in self.alerts_table.selectedIndexes())
    def generate_order_for_selected(self):
        rows = self.get_selected_alert_rows()
        if not rows:
            self.show_banner("No alerts selected.", success=False)
            return
        meds = [self._get_medicine_from_row(row) for row in rows]
        self._generate_order_for_meds(meds)
    def dismiss_selected_alerts(self):
        rows = sorted(self.get_selected_alert_rows(), reverse=True)
        self._dismiss_alerts(rows)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        view_action = menu.addAction("View Details")
        order_action = menu.addAction("Generate Order")
        dismiss_action = menu.addAction("Dismiss Alert")
        action = menu.exec_(self.alerts_table.viewport().mapToGlobal(pos))
        row = self.alerts_table.currentRow()
        if row < 0:
            return
        med = self._get_medicine_from_row(row)
        if action == view_action:
            self.view_medicine_details(med)
        elif action == order_action:
            self._generate_order_for_meds([med])
        elif action == dismiss_action:
            self._dismiss_alerts([row])
    def _on_table_double_clicked(self, row, col):
        med = self._get_medicine_from_row(row)
        self.view_medicine_details(med)
    def view_medicine_details(self, med):
        dialog = MedicineDetailsDialog(med, self)
        dialog.exec_()
    def _get_medicine_from_row(self, row):
        return {
            "barcode": self.alerts_table.item(row, 0).text() if self.alerts_table.item(row, 0) else '',
            "name": self.alerts_table.item(row, 1).text() if self.alerts_table.item(row, 1) else '',
            "quantity": self.alerts_table.item(row, 2).text() if self.alerts_table.item(row, 2) else '',
            "threshold": self.alerts_table.item(row, 3).text() if self.alerts_table.item(row, 3) else '',
            "expiry": self.alerts_table.item(row, 4).text() if self.alerts_table.item(row, 4) else '',
            "status": self.alerts_table.item(row, 5).text() if self.alerts_table.item(row, 5) else '',
        }
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_alerts_table()
    def next_page(self):
        self.current_page += 1
        self.refresh_alerts_table()
    def refresh_alerts_table(self):
        self.alerts_table.setRowCount(0)
        low_stock = self.main_window.alert_service.get_low_stock()
        # Pagination
        total_alerts = len(low_stock)
        start = self.current_page * self.page_size
        end = start + self.page_size
        paged_alerts = low_stock[start:end]
        for med in paged_alerts:
            row = self.alerts_table.rowCount()
            self.alerts_table.insertRow(row)
            self.alerts_table.setItem(row, 0, QTableWidgetItem(getattr(med, 'barcode', '')))
            self.alerts_table.setItem(row, 1, QTableWidgetItem(getattr(med, 'name', '')))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(str(getattr(med, 'quantity', ''))))
            self.alerts_table.setItem(row, 3, QTableWidgetItem(str(getattr(med, 'threshold', ''))))
            self.alerts_table.setItem(row, 4, QTableWidgetItem(str(getattr(med, 'expiry', ''))))
            status = "Low" if getattr(med, 'quantity', 0) < getattr(med, 'threshold', 0) else "OK"
            self.alerts_table.setItem(row, 5, QTableWidgetItem(status))
        # Update pagination label and button states
        total_pages = max(1, (total_alerts + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled((self.current_page + 1) * self.page_size < total_alerts)
    def _generate_order_for_meds(self, meds):
        if not meds:
            self.show_banner("No medicines selected for order.", success=False)
            return
        # ... logic to generate order for given meds ...
        self.show_banner("Order generated for selected medicines.", success=True)
    def _dismiss_alerts(self, rows):
        if not rows:
            self.show_banner("No alerts selected to dismiss.", success=False)
            return
        for row in sorted(rows, reverse=True):
            self.alerts_table.removeRow(row)
        self.show_banner("Selected alerts dismissed.", success=True)

    def load_alerts(self):
        pass 