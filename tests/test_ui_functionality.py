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
    from src.inventory_ui import InventoryUi
    window.inventory_ui = InventoryUi(window)
    window.inventory_ui.refresh_inventory_table()
    # Clear all filters and search box
    window.inventory_ui.clear_filters()
    window.inventory_ui.populate_manufacturer_filter()
    qtbot.wait(100)
    qtbot.mouseClick(window.nav_buttons[0], Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    # Check for medicine names as substrings in table items
    table = window.inventory_ui.inventory_table
    names_in_table = [table.item(row, 1).text() for row in range(table.rowCount()) if table.item(row, 1)]
    assert any("SampleMed1" in name for name in names_in_table)
    assert any("SampleMed2" in name for name in names_in_table)

def test_inventory_ui_expired_and_low_stock(app_and_window, sample_inventory):
    window, qtbot = app_and_window
    from src.inventory_ui import InventoryUi
    window.inventory_ui = InventoryUi(window)
    window.inventory_ui.refresh_inventory_table()
    qtbot.mouseClick(window.nav_buttons[0], Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    expired_found = low_stock_found = out_of_stock_found = False
    today = datetime.date.today()
    table = window.inventory_ui.inventory_table
    # Debug: print all rows
    for row in range(table.rowCount()):
        name = table.item(row, 1).text() if table.item(row, 1) else None
        expiry = table.item(row, 4).text() if table.item(row, 4) else None
        quantity = table.item(row, 2).text() if table.item(row, 2) else None
        print(f"[DEBUG] Row {row}: name={name}, quantity={quantity}, expiry={expiry}")
        if name and "PainRelief" in name and expiry:
            try:
                exp_date = datetime.datetime.strptime(expiry, "%Y-%m-%d").date()
                if exp_date < today:
                    expired_found = True
            except Exception:
                pass
        if name and "SampleMed2" in name and quantity == "1":
            low_stock_found = True
        if name and "LowStockMed" in name and quantity == "0":
            out_of_stock_found = True
    assert expired_found and low_stock_found and out_of_stock_found

def test_billing_ui_shows_sample_data(app_and_window, sample_billing):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[1], Qt.LeftButton)
    window.refresh_billing_history()
    qtbot.wait(100)
    assert window.billing_ui.recent_bills_list.count() > 0

def test_billing_ui_discounted_bill(app_and_window, sample_billing):
    window, qtbot = app_and_window
    qtbot.mouseClick(window.nav_buttons[1], Qt.LeftButton)
    window.refresh_billing_history()
    qtbot.wait(100)
    found_discount = False
    for i in range(window.billing_ui.recent_bills_list.count()):
        item = window.billing_ui.recent_bills_list.item(i)
        bill = item.data(Qt.UserRole)
        if hasattr(bill, 'items'):
            items = bill.items
            if callable(items):
                items = items()
            for line in items:
                if (
                    (getattr(line, 'name', None) in ["PainRelief", "Cough Syrup"]) and
                    (hasattr(line, 'discount') and getattr(line, 'discount', 0) > 0)
                ):
                    found_discount = True
    assert found_discount

def test_add_inventory_item(app_and_window, monkeypatch, sample_inventory):
    window, qtbot = app_and_window
    from src.inventory_ui import InventoryUi
    window.inventory_ui = InventoryUi(window)
    window.inventory_ui.refresh_inventory_table()
    # Clear inventory to ensure a clean state
    window.inventory_service.clear()
    window.inventory_ui.refresh_inventory_table()
    qtbot.mouseClick(window.nav_buttons[0], Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    # Clear all filters and search box
    window.inventory_ui.clear_filters()
    window.inventory_ui.populate_manufacturer_filter()
    qtbot.wait(100)
    import src.main_window as main_window_mod
    import src.inventory_ui as inventory_ui_mod
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
    monkeypatch.setattr(inventory_ui_mod, "AddMedicineDialog", FakeDialog)
    orig_add = window.inventory_service.add
    def debug_add(data):
        return orig_add(data)
    monkeypatch.setattr(window.inventory_service, 'add', debug_add)
    qtbot.mouseClick(window.inventory_ui.add_medicine_btn, Qt.LeftButton)
    window.refresh_inventory_table()
    qtbot.wait(100)
    found = False
    table = window.inventory_ui.inventory_table
    for row in range(table.rowCount()):
        name = table.item(row, 1).text() if table.item(row, 1) else None
        if name and "TestMed" in name:
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
    assert window.billing_ui.recent_bills_list.count() > 0 