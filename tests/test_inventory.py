import pytest
from src.db import add_medicine, get_all_medicines, delete_medicine, clear_inventory

def test_add_and_delete_medicine():
    barcode = "TEST123"
    add_medicine(barcode, "TestMed", 10, None, "TestManu", 100, 5)
    meds = get_all_medicines()
    assert any(m.barcode == barcode for m in meds)
    delete_medicine(barcode)
    meds = get_all_medicines()
    assert not any(m.barcode == barcode for m in meds)

def test_clear_inventory():
    add_medicine("TEST456", "TestMed2", 5, None, "TestManu2", 50, 2)
    clear_inventory()
    meds = get_all_medicines()
    assert len(meds) == 0 