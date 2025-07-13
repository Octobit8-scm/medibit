import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from db import init_db  # Import init_db
from main_window import MainWindow
from splash_screen import MedibitSplashScreen
import logging
import sys
import traceback
import os

# Add global exception handler to log uncaught exceptions

def log_uncaught_exceptions(exctype, value, tb):
    logging.critical("Uncaught exception", exc_info=(exctype, value, tb))
    # Optionally, show a message box to the user
    try:
        from PyQt5.QtWidgets import QMessageBox
        msg = f"An unexpected error occurred:\n{value}\nSee log for details."
        QMessageBox.critical(None, "Application Error", msg)
    except Exception:
        pass

sys.excepthook = log_uncaught_exceptions

if __name__ == "__main__":
    init_db()  # Initialize the database
    app = QApplication(sys.argv)

    # Set app icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "medibit.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Show splash screen
    splash = MedibitSplashScreen()

    def launch_app():
        splash.close()
        # License check and dialog after splash, before main window
        if not MainWindow.check_license():
            MainWindow.prompt_license_dialog(parent=None)
        # Only create and show main window if license is valid
        if MainWindow.check_license():
            window = MainWindow()
            window.show()

    # Show main window after 2 seconds
    QTimer.singleShot(2000, launch_app)

    sys.exit(app.exec_())
