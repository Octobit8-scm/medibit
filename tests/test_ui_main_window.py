import pytest
from PyQt5.QtWidgets import QApplication
from src.main_window import MainWindow

def test_main_window_launch(qtbot):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.isVisible() 