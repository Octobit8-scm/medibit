from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QSplashScreen


class MedibitSplashScreen(QSplashScreen):
    def __init__(self):
        # Load the actual medibit logo image
        try:
            original_pixmap = QPixmap("medibit_logo.jpg")
            if not original_pixmap.isNull():
                # Scale the image to a reasonable splash screen size
                splash_pixmap = original_pixmap.scaled(
                    400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            else:
                # Fallback to text-based design if image loading fails
                splash_pixmap = self.create_text_based_splash()
        except:
            # Fallback to text-based design if image file not found
            splash_pixmap = self.create_text_based_splash()

        super().__init__(splash_pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()

    def create_text_based_splash(self):
        # Fallback text-based splash screen
        splash_pixmap = QPixmap(400, 300)
        splash_pixmap.fill(QColor("#1976d2"))  # Blue background

        # Create a simple text-based logo
        painter = QPainter(splash_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw medibit text
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(splash_pixmap.rect(), Qt.AlignCenter, "Medibit")

        # Draw subtitle
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#e3f2fd")))
        painter.drawText(
            splash_pixmap.rect().adjusted(0, 50, 0, 0),
            Qt.AlignCenter,
            "Pharmacy Management System",
        )

        # Draw version
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#bbdefb")))
        painter.drawText(
            splash_pixmap.rect().adjusted(0, 80, 0, 0), Qt.AlignCenter, "Version 1.0"
        )

        # Draw loading text
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(
            splash_pixmap.rect().adjusted(0, 120, 0, 0), Qt.AlignCenter, "Loading..."
        )

        painter.end()
        return splash_pixmap
