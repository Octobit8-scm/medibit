import logging
import os as _os
from logging.handlers import RotatingFileHandler

import cv2
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout
from pyzbar.pyzbar import decode

# Logging is configured in main_window.py
barcode_logger = logging.getLogger("medibit.barcode")


class BarcodeScannerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Barcode")
        self.setModal(True)
        self.barcode = None
        self.capture = cv2.VideoCapture(0)
        # Set higher resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Initializing camera...")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(40)  # Set height
        self.cancel_btn.setMaximumHeight(50)  # Set maximum height
        self.cancel_btn.setMinimumWidth(80)  # Decreased from 100 to 80
        self.cancel_btn.setIconSize(QSize(20, 20))  # Set icon size
        self.cancel_btn.clicked.connect(self.reject)
        self.layout.addWidget(self.cancel_btn)
        self.timer.start(30)
        self.start_time = None
        self.timeout_ms = 10000  # 10 seconds
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.handle_timeout)
        self.timeout_timer.start(self.timeout_ms)

    def next_frame(self):
        ret, frame = self.capture.read()
        if not ret:
            self.label.setText("Failed to access camera.")
            return
        barcodes = decode(frame)
        if barcodes:
            self.barcode = barcodes[0].data.decode("utf-8")
            self.timer.stop()
            self.timeout_timer.stop()
            self.capture.release()
            self.accept()
            return
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(
            QPixmap.fromImage(qt_image).scaled(600, 400, Qt.KeepAspectRatio)
        )

    def handle_timeout(self):
        self.timer.stop()
        if self.capture.isOpened():
            self.capture.release()
        QMessageBox.information(
            self,
            "No Barcode Detected",
            "No barcode was detected after 10 seconds. Please try again.",
        )
        self.reject()

    def get_barcode(self):
        return self.barcode

    def closeEvent(self, event):
        self.timer.stop()
        self.timeout_timer.stop()
        if self.capture.isOpened():
            self.capture.release()
        event.accept()
