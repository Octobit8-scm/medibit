from config import get_theme


def get_stylesheet() -> str:
    """Get the appropriate stylesheet based on current theme"""
    theme = get_theme()

    if theme == "dark":
        return get_dark_stylesheet()
    else:
        return get_light_stylesheet()


def get_dark_stylesheet() -> str:
    """Dark theme stylesheet: white text, black/white icons only, no table highlight or borders"""
    return """
    QMainWindow, QWidget {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QFrame {
        background-color: transparent;
        border: 1px solid #444444;
        border-radius: 6px;
    }
    QTableWidget, QListWidget, QTreeWidget {
        background-color: transparent;
        color: #FFFFFF;
        border: none;
        selection-background-color: #2B2B2B;
        selection-color: #FFFFFF;
    }
    QTableWidget::item {
        background-color: transparent;
        border: none;
        selection-background-color: #2B2B2B;
        selection-color: #FFFFFF;
    }
    QListWidget::item {
        background-color: transparent;
        color: #FFFFFF;
        border: none;
    }
    QDialog, QMessageBox {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QMenuBar {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QMenuBar::item {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QMenu {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QMenu::item {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QPushButton, QLabel, QStatusBar, QTabBar::tab, QTabWidget::pane, QGroupBox, QGroupBox::title, QCheckBox {
        color: #FFFFFF;
        background-color: transparent;
    }
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QDateEdit {
        color: #FFFFFF;
        background-color: transparent;
        border: 1px solid #888;
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: #2B2B2B;
        selection-color: #FFFFFF;
    }
    QPushButton {
        background-color: #404040;
        color: #FFFFFF;
        border: 1px solid #606060;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:disabled {
        color: #808080;
    }
    QHeaderView::section {
        background-color: #404040;
        color: #FFFFFF;
        border: none;
    }
    QLabel {
        color: #FFFFFF;
    }
    QStatusBar {
        color: #FFFFFF;
    }
    /* Remove all accent and non-white text colors */
    """


def get_light_stylesheet() -> str:
    """Light theme stylesheet: black text, black/white icons only"""
    return """
    QMainWindow, QWidget {
        background-color: #FFFFFF;
        color: #000000;
    }
    QFrame {
        background-color: transparent;
        border: 1px solid #CCCCCC;
        border-radius: 6px;
    }
    QTableWidget, QListWidget, QTreeWidget {
        background-color: transparent;
        color: #000000;
    }
    QTableWidget::item {
        background-color: transparent;
        border: none;
    }
    QListWidget::item {
        background-color: transparent;
        color: #000000;
        border: none;
    }
    QDialog, QMessageBox {
        background-color: #FFFFFF;
        color: #000000;
    }
    QMenuBar {
        background-color: #FFFFFF;
        color: #000000;
    }
    QMenuBar::item {
        background-color: #FFFFFF;
        color: #000000;
    }
    QMenu {
        background-color: #FFFFFF;
        color: #000000;
    }
    QMenu::item {
        background-color: #FFFFFF;
        color: #000000;
    }
    QPushButton, QLabel, QStatusBar, QTabBar::tab, QTabWidget::pane, QGroupBox, QGroupBox::title, QCheckBox {
        color: #000000;
        background-color: transparent;
    }
    QLineEdit, QSpinBox, QComboBox, QTextEdit, QDateEdit {
        color: #000000;
        background-color: transparent;
        border: 1px solid #B3B3B3;
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: #FFFFFF;
        selection-color: #000000;
    }
    QPushButton {
        background-color: #FFFFFF;
        color: #000000;
        border: 1px solid #B3B3B3;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:disabled {
        color: #666666;
    }
    QHeaderView::section {
        background-color: #FFFFFF;
        color: #000000;
    }
    QLabel {
        color: #000000;
    }
    QStatusBar {
        color: #000000;
    }
    /* Remove all accent and non-black text colors */
    """
