import pytest
from src.billing_service import BillingService
from src.db import clear_all_bills
import datetime

@pytest.fixture(autouse=True)
def setup_billing():
    clear_all_bills()
    yield
    clear_all_bills()

def test_create_bill_and_get_recent():
    service = BillingService()
    items = [{"barcode": "BILL1", "name": "MedB", "quantity": 2, "price": 50, "subtotal": 100}]
    customer = {"name": "Test Customer", "phone": "1234567890", "email": "test@example.com"}
    success, error, bill_id = service.create_bill(items, customer)
    assert success
    bills = service.get_recent_bills()
    assert any(bill.total == 100 for bill in bills)

def test_get_sales_data():
    service = BillingService()
    sales = service.get_sales_data()
    assert isinstance(sales, list)

def test_generate_receipt(tmp_path):
    service = BillingService()
    timestamp = datetime.datetime.now()
    items = [{"barcode": "BILL2", "name": "MedC", "quantity": 1, "price": 20, "subtotal": 20}]
    total = 20
    details = {"name": "TestPharm", "address": "Addr", "phone": "123"}
    path = service.generate_receipt(timestamp, items, total, details)
    assert path is not None 