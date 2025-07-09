import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QInputDialog, QTableWidgetItem
from src.main_window import MainWindow
import datetime

@pytest.fixture
def app_and_window(qtbot):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    return window, qtbot

def test_navigation(app_and_window):
    window, qtbot = app_and_window
    for i, btn in enumerate(window.nav_buttons):
        qtbot.mouseClick(btn, Qt.LeftButton)
        assert window.stacked_widget.currentIndex() == i

def test_inventory_ui_shows_sample_data(app_and_window, sample_inventory):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[0], Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    found1 = found2 = False
    for row in range(window.inventory_ui.inventory_table.rowCount()):
        name = window.inventory_ui.inventory_table.item(row, 1)
        if name and name.text() == "SampleMed1":
            found1 = True
        if name and name.text() == "SampleMed2":
            found2 = True
    assert found1 and found2

def test_inventory_ui_expired_and_low_stock(app_and_window, sample_inventory):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[0], Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    expired_found = low_stock_found = out_of_stock_found = False
    today = datetime.date.today()
    for row in range(window.inventory_ui.inventory_table.rowCount()):
        name = window.inventory_ui.inventory_table.item(row, 1)
        expiry = window.inventory_ui.inventory_table.item(row, 4)
        quantity = window.inventory_ui.inventory_table.item(row, 2)
        if name and name.text() == "PainRelief" and expiry and expiry.text():
            try:
                exp_date = datetime.datetime.strptime(expiry.text(), "%Y-%m-%d").date()
                if exp_date < today:
                    expired_found = True
            except Exception:
                pass
        if name and name.text() == "SampleMed2" and quantity and quantity.text() == "1":
            low_stock_found = True
        if name and name.text() == "LowStockMed" and quantity and quantity.text() == "0":
            out_of_stock_found = True
    assert expired_found and low_stock_found and out_of_stock_found

def test_billing_ui_shows_sample_data(app_and_window, sample_billing):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[1], Qt.LeftButton)
    window.refresh_billing_history()
    qtbot.wait(100)
    assert window.billing_ui.billing_history_list.count() > 0

def test_billing_ui_discounted_bill(app_and_window, sample_billing):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[1], Qt.LeftButton)
    window.refresh_billing_history()
    qtbot.wait(100)
    found_discount = False
    for i in range(window.billing_ui.billing_history_list.count()):
        item = window.billing_ui.billing_history_list.item(i)
        bill = item.data(Qt.UserRole)
        if hasattr(bill, 'items'):
            print(f'Bill {i} items:')
            for line in bill.items:
                print('  name:', getattr(line, 'name', None), 'discount:', getattr(line, 'discount', None))
                if (
                    (getattr(line, 'name', None) in ["PainRelief", "Cough Syrup"]) and
                    (hasattr(line, 'discount') and getattr(line, 'discount', 0) > 0)
                ):
                    found_discount = True
    assert found_discount

def test_add_inventory_item(app_and_window, monkeypatch, sample_inventory):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[0], Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)

    # Patch AddMedicineDialog in main_window's namespace
    import src.main_window as main_window_mod

    class FakeDialog:
        def __init__(self, *args, **kwargs):
            pass
        def exec_(self):
            return 1  # QDialog.Accepted
        def get_data(self):
            return {
                "name": "TestMed",
                "barcode": "TEST123",
                "quantity": 10,
                "price": 50,
                "manufacturer": "TestManu",
                "expiry": datetime.date(2025, 1, 1),
                "threshold": 5
            }

    monkeypatch.setattr(main_window_mod, "AddMedicineDialog", FakeDialog)

    # Patch inventory_service.add to print arguments and return value
    orig_add = window.inventory_service.add
    def debug_add(data):
        print('inventory_service.add called with:', data)
        result = orig_add(data)
        print('inventory_service.add returned:', result)
        return result
    monkeypatch.setattr(window.inventory_service, 'add', debug_add)

    qtbot.mouseClick(window.inventory_ui.add_medicine_btn, Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    print('Inventory table items:')
    for row in range(window.inventory_ui.inventory_table.rowCount()):
        item = window.inventory_ui.inventory_table.item(row, 1)
        print(f'Row {row}:', item.text() if item else None)
    found = False
    for row in range(window.inventory_ui.inventory_table.rowCount()):
        if window.inventory_ui.inventory_table.item(row, 1) and window.inventory_ui.inventory_table.item(row, 1).text() == "TestMed":
            found = True
    assert found

def test_billing_add_item_and_save_draft(app_and_window, monkeypatch, sample_billing):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[1], Qt.LeftButton)
    window.refresh_billing_history()
    qtbot.wait(100)
    table = window.billing_ui.billing_table
    table.insertRow(0)
    table.setItem(0, 0, QTableWidgetItem("TEST123"))
    table.setItem(0, 1, QTableWidgetItem("TestMed"))
    table.setItem(0, 2, QTableWidgetItem("1"))
    table.setItem(0, 3, QTableWidgetItem("50"))
    table.setItem(0, 4, QTableWidgetItem("0"))
    table.setItem(0, 5, QTableWidgetItem("0"))
    def fake_getText(*args, **kwargs):
        return ("TestDraft", True)
    monkeypatch.setattr(QInputDialog, "getText", fake_getText)
    qtbot.mouseClick(window.billing_ui.save_draft_btn, Qt.LeftButton)
    qtbot.wait(100)
    assert window.billing_ui.billing_history_list.count() > 0 