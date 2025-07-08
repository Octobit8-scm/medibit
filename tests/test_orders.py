from src.db import add_order, get_all_orders


def test_add_order():
    medicines = [
        {
            "barcode": "ORDERTEST",
            "name": "OrderTest",
            "quantity": 10,
            "expiry": "2024-12-31",
            "manufacturer": "TestManu",
            "order_quantity": 5,
        }
    ]
    add_order("2024-01-01 10:00", "test_order.pdf", medicines)
    orders = get_all_orders()
    assert len(orders) > 0
