from src.db import add_bill, get_all_bills

def test_add_bill():
    add_bill("2024-01-01 10:00", 500, [
        {"barcode": "BILLTEST", "name": "BillTest", "price": 100, "quantity": 5, "subtotal": 500}
    ])
    bills = get_all_bills()
    assert any(bill.total == 500 for bill in bills) 