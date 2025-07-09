from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QSizePolicy, QMessageBox, QTableWidgetItem)
from PyQt5.QtCore import Qt

class AlertsUi(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.get_button_stylesheet = main_window.get_button_stylesheet
        self.init_ui()
        self.refresh_alerts_table()
        self.send_alerts_btn.clicked.connect(self.send_alerts)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Low Stock Alerts")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-right: 24px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.send_alerts_btn = QPushButton("Send Alerts")
        self.send_alerts_btn.setMinimumHeight(40)
        self.send_alerts_btn.setStyleSheet(self.get_button_stylesheet())
        header_layout.addWidget(self.send_alerts_btn)
        layout.addLayout(header_layout)
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Medicine", "Current Stock", "Threshold", "Status", "Action"
        ])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.alerts_table)

    def refresh_alerts_table(self):
        self.alerts_table.setRowCount(0)
        low_stock = self.main_window.alert_service.get_low_stock()
        for med in low_stock:
            row = self.alerts_table.rowCount()
            self.alerts_table.insertRow(row)
            self.alerts_table.setItem(row, 0, QTableWidgetItem(med.name))
            self.alerts_table.setItem(row, 1, QTableWidgetItem(str(med.quantity)))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(str(med.threshold)))
            status = "Low" if med.quantity < med.threshold else "OK"
            self.alerts_table.setItem(row, 3, QTableWidgetItem(status))
            self.alerts_table.setItem(row, 4, QTableWidgetItem('-'))

    def send_alerts(self):
        success, msg = self.main_window.alert_service.send_all_alerts()
        if success:
            QMessageBox.information(self, "Alerts Sent", msg)
        else:
            QMessageBox.warning(self, "Send Failed", msg) 