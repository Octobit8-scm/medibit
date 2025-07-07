from db import add_order, get_all_orders

def test_add_order():
    add_order("2024-01-01 12:00", "order_test.pdf", [
        {"barcode": "ORDERTEST", "name": "OrderTest", "quantity": 2, "expiry": None, "manufacturer": "TestManu", "order_quantity": 2}
    ])
    orders = get_all_orders()
    assert any(order.file_path == "order_test.pdf" for order in orders) 