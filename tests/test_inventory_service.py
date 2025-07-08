import pytest
from src.inventory_service import InventoryService
from src.db import clear_inventory

@pytest.fixture(autouse=True)
def setup_inventory():
    clear_inventory()
    yield
    clear_inventory()

def test_add_and_get_all():
    service = InventoryService()
    data = {"barcode": "SVC1", "name": "Med1", "quantity": 10, "expiry": None, "manufacturer": "M1", "price": 100, "threshold": 5}
    success, error = service.add(data)
    assert success
    meds = service.get_all()
    assert any(m.barcode == "SVC1" for m in meds)

def test_duplicate_barcode():
    service = InventoryService()
    data = {"barcode": "SVC2", "name": "Med2", "quantity": 5, "expiry": None, "manufacturer": "M2", "price": 50, "threshold": 2}
    service.add(data)
    success, error = service.add(data)
    assert not success
    assert "barcode" in error.lower()

def test_update_and_update_quantity():
    service = InventoryService()
    data = {"barcode": "SVC3", "name": "Med3", "quantity": 8, "expiry": None, "manufacturer": "M3", "price": 80, "threshold": 3}
    service.add(data)
    update_data = {"name": "Med3-upd", "quantity": 12, "expiry": None, "manufacturer": "M3", "price": 90, "threshold": 4}
    success, error = service.update("SVC3", update_data)
    assert success
    meds = service.get_all()
    med = next(m for m in meds if m.barcode == "SVC3")
    assert med.name == "Med3-upd"
    success, error = service.update_quantity("SVC3", 20)
    assert success
    meds = service.get_all()
    med = next(m for m in meds if m.barcode == "SVC3")
    assert med.quantity == 20

def test_delete_and_clear():
    service = InventoryService()
    data = {"barcode": "SVC4", "name": "Med4", "quantity": 6, "expiry": None, "manufacturer": "M4", "price": 60, "threshold": 2}
    service.add(data)
    success, error = service.delete("SVC4")
    assert success
    meds = service.get_all()
    assert not any(m.barcode == "SVC4" for m in meds)
    # Test clear
    service.add({"barcode": "SVC5", "name": "Med5", "quantity": 3, "expiry": None, "manufacturer": "M5", "price": 30, "threshold": 1})
    service.clear()
    meds = service.get_all()
    assert len(meds) == 0

def test_search():
    service = InventoryService()
    service.add({"barcode": "SVC6", "name": "Aspirin", "quantity": 10, "expiry": None, "manufacturer": "PharmaA", "price": 10, "threshold": 1})
    service.add({"barcode": "SVC7", "name": "Paracetamol", "quantity": 5, "expiry": None, "manufacturer": "PharmaB", "price": 20, "threshold": 1})
    results = service.search("aspirin")
    assert any(m.name == "Aspirin" for m in results)
    results = service.search("pharmab")
    assert any(m.manufacturer == "PharmaB" for m in results) 