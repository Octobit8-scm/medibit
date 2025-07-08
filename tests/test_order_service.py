import pytest
from src.order_service import OrderService
from src.db import clear_inventory, clear_all_bills
import datetime

@pytest.fixture(autouse=True)
def setup_orders():
    clear_inventory()
    clear_all_bills()
    yield
    clear_inventory()
    clear_all_bills()

def test_add_and_get_all_orders():
    service = OrderService()
    order_items = [{"barcode": "ORD1", "name": "MedO", "quantity": 5, "expiry": None, "manufacturer": "ManO", "order_quantity": 2}]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    order_id = int(datetime.datetime.now().timestamp())
    pdf_path = service.generate_order_pdf(order_items, order_id, timestamp)
    success, error = service.add(timestamp, pdf_path, order_items)
    assert success
    orders = service.get_all()
    assert any(order.file_path == pdf_path for order in orders)

def test_get_low_stock():
    service = OrderService()
    meds = service.get_low_stock()
    assert isinstance(meds, list) 