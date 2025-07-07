from src.db import get_monthly_sales


def test_get_monthly_sales():
    sales = get_monthly_sales()
    assert isinstance(sales, list)
    if sales:
        month, total, count, avg = sales[0]
        assert isinstance(month, str)
        assert isinstance(total, (int, float))
        assert isinstance(count, int)
        assert isinstance(avg, (int, float))
