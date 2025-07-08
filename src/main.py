import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from db import init_db  # Import init_db
from main_window import MainWindow
from splash_screen import MedibitSplashScreen

if __name__ == "__main__":
    init_db()  # Initialize the database
    app = QApplication(sys.argv)

    # Set the application icon to use the medibit logo
    try:
        import os

        from PyQt5.QtGui import QIcon

        # Try to use the existing ICO file first (preferred for Windows
        # taskbar)
        if os.path.exists("medibit.ico"):
            app_icon = QIcon("medibit.ico")
            # Set window icon for Windows taskbar
            app.setWindowIcon(app_icon)
        else:
            # Fallback to JPG if ICO doesn't exist
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QPixmap

            icon_pixmap = QPixmap("medibit.ico")
            if not icon_pixmap.isNull():
                # Scale the icon to a reasonable size for taskbar (32x32 pixels)
                icon_pixmap = icon_pixmap.scaled(
                    32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                app_icon = QIcon(icon_pixmap)
                app.setWindowIcon(app_icon)

    except Exception as e:
        print(f"Could not load icon: {e}")
        # Fallback to default icon if image loading fails
        pass

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
