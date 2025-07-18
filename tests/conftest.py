import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import pytest
import datetime

from src.db import init_db, clear_inventory, add_medicine, clear_all_bills, add_bill, save_pharmacy_details, add_order
from src.settings_service import SettingsService
from src.license_utils import generate_license_key

import pytest
from PyQt5.QtWidgets import QMessageBox, QDialog, QFileDialog, QColorDialog, QInputDialog, QMenu
from PyQt5.QtGui import QColor

@pytest.fixture(autouse=True)
def patch_messageboxes_and_dialogs(monkeypatch):
    # Patch QMessageBox methods to auto-accept
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)

    # Patch exec_ for all QDialog subclasses to auto-accept
    original_exec = QDialog.exec_
    def auto_accept(self, *a, **k):
        return QDialog.Accepted
    monkeypatch.setattr(QDialog, "exec_", auto_accept)
    
    # Patch QFileDialog to auto-return values
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("test.xlsx", "Excel Files (*.xlsx)"))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("output.pdf", "PDF Files (*.pdf)"))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: "test_dir")
    
    # Patch QColorDialog to auto-return a color
    monkeypatch.setattr(QColorDialog, "getColor", lambda *a, **k: QColor(255, 255, 255))
    
    # Patch QInputDialog to auto-return text
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("TestInput", True))

    # Patch custom dialogs in orders and sales to auto-accept and return default data
    import src.dialogs as dialogs_mod
    class FakeSupplierInfoDialog:
        def exec_(self):
            return QDialog.Accepted
        def get_data(self):
            return {"email": "supplier@example.com", "phone": "1234567890"}
    class FakeOrderQuantityDialog:
        def exec_(self):
            return QDialog.Accepted
        def get_order_quantities(self):
            return {"TESTBARCODE": 10}
    monkeypatch.setattr(dialogs_mod, "SupplierInfoDialog", FakeSupplierInfoDialog)
    monkeypatch.setattr(dialogs_mod, "OrderQuantityDialog", FakeOrderQuantityDialog)
    # Add more custom dialog patches here as needed

    # Patch QMenu.exec_ to auto-trigger the first action
    def fake_qmenu_exec(self, *args, **kwargs):
        actions = self.actions()
        if actions:
            actions[0].trigger()
            return actions[0]
        return None
    monkeypatch.setattr(QMenu, "exec_", fake_qmenu_exec)

    yield
    # Optionally restore original exec_ if needed
    monkeypatch.setattr(QDialog, "exec_", original_exec)


@pytest.fixture(autouse=True)
def setup_database():
    """Automatically initialize the database before each test"""
    init_db()
    yield
    # Cleanup could be added here if needed

@pytest.fixture(autouse=True)
def activate_license():
    settings_service = SettingsService()
    # Use a unique test email for identification
    test_email = "testuser@example.com"
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    key = generate_license_key(test_email, expiry)
    settings_service.set_license_key(key)
    settings_service.set_installation_date(datetime.datetime.now().strftime("%Y-%m-%d"))

def pytest_configure():
    # Optionally, global setup for all tests
    pass

@pytest.fixture
def sample_inventory():
    clear_inventory()
    today = datetime.date.today()
    expired = today.replace(year=today.year - 1)
    add_medicine("SAMP001", "SampleMed1", 10, today, "SampleManu", 100, 5)
    add_medicine("SAMP002", "SampleMed2", 1, today, "SampleManu", 50, 2)  # Low stock
    add_medicine("SAMP003", "PainRelief", 20, expired, "HealthCorp", 200, 10)  # Expired
    add_medicine("SAMP004", "Cough Syrup", 15, today, "PharmaPlus", 80, 3)
    add_medicine("SAMP005", "AntibioticX", 8, expired, "BioMed", 300, 4)  # Expired
    add_medicine("SAMP006", "LowStockMed", 0, today, "ShortageInc", 60, 2)  # Out of stock

@pytest.fixture
def sample_billing():
    clear_all_bills()
    add_bill("2024-01-01 10:00:00", 150, [
        {"barcode": "SAMP001", "name": "SampleMed1", "quantity": 2, "price": 50, "subtotal": 100},
        {"barcode": "SAMP002", "name": "SampleMed2", "quantity": 1, "price": 50, "subtotal": 50}
    ])
    add_bill("2024-01-02 11:30:00", 432, [
        {"barcode": "SAMP003", "name": "PainRelief", "quantity": 2, "price": 200, "subtotal": 400, "discount": 20},
        {"barcode": "SAMP004", "name": "Cough Syrup", "quantity": 1, "price": 80, "subtotal": 80, "discount": 8}
    ])

@pytest.fixture
def sample_orders():
    clear_inventory()
    today = datetime.date.today()
    expired = today.replace(year=today.year - 1)
    add_order("2024-01-01 12:00:00", "orders/sample_order1.pdf", [
        {"barcode": "SAMP001", "name": "SampleMed1", "quantity": 2, "expiry": today, "manufacturer": "SampleManu"},
        {"barcode": "SAMP003", "name": "PainRelief", "quantity": 1, "expiry": expired, "manufacturer": "HealthCorp"}
    ])
    add_order("2024-01-03 15:45:00", "orders/sample_order2.pdf", [
        {"barcode": "SAMP004", "name": "Cough Syrup", "quantity": 3, "expiry": today, "manufacturer": "PharmaPlus"},
        {"barcode": "SAMP006", "name": "LowStockMed", "quantity": 1, "expiry": today, "manufacturer": "ShortageInc"}
    ])

@pytest.fixture
def sample_settings():
    save_pharmacy_details("TestPharmacy", "Addr", "123", "test@pharm.com", "GST", "LIC", "www.test.com")
