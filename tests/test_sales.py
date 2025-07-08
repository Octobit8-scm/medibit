from src.db import add_bill, get_monthly_sales


def test_get_monthly_sales():
    # Add a test bill
    add_bill(
        "2024-01-01 10:00",
        500,
        [
            {
                "barcode": "SALESTEST",
                "name": "SalesTest",
                "price": 100,
                "quantity": 5,
                "subtotal": 500,
            }
        ],
    )

    sales = get_monthly_sales()
    assert len(sales) > 0
