from config import get_theme

def get_stylesheet():
    """Get the appropriate stylesheet based on current theme"""
    theme = get_theme()
    
    if theme == 'dark':
        return get_dark_stylesheet()
    else:
        return get_light_stylesheet()

def get_dark_stylesheet():
    """Dark theme stylesheet: white text, black/white icons only"""
    return """
    QMainWindow, QWidget {
        background-color: #2B2B2B;
        color: #FFFFFF;
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
    QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QTableWidget, QListWidget, QTreeWidget, QHeaderView::section, QLabel, QStatusBar, QTabBar::tab, QTabWidget::pane, QGroupBox, QGroupBox::title, QCheckBox {
        color: #FFFFFF;
        background-color: transparent;
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
    QTableWidget, QListWidget, QTreeWidget {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QHeaderView::section {
        background-color: #404040;
        color: #FFFFFF;
    }
    QLabel {
        color: #FFFFFF;
    }
    QStatusBar {
        color: #FFFFFF;
    }
    /* Remove all accent and non-white text colors */
    """

def get_light_stylesheet():
    """Light theme stylesheet: black text, black/white icons only"""
    return """
    QMainWindow, QWidget {
        background-color: #FFFFFF;
        color: #000000;
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
    QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QTableWidget, QListWidget, QTreeWidget, QHeaderView::section, QLabel, QStatusBar, QTabBar::tab, QTabWidget::pane, QGroupBox, QGroupBox::title, QCheckBox {
        color: #000000;
        background-color: transparent;
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
    QTableWidget, QListWidget, QTreeWidget {
        background-color: #FFFFFF;
        color: #000000;
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