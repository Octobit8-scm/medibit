import pytest
from unittest.mock import Mock
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from src.sales_ui import SalesUi, SaleDetailsDialog
from src.billing_service import BillingService
from src.db import add_bill, get_monthly_sales

@pytest.fixture
def mock_main_window():
    mw = Mock()
    mw.billing_service = BillingService()
    return mw

@pytest.fixture
def sales_ui(qtbot, mock_main_window):
    ui = SalesUi(mock_main_window)
    qtbot.addWidget(ui)
    return ui

@pytest.fixture
def sample_sale():
    class Item:
        name = "TestMed"
        quantity = 2
        price = 100.0
        subtotal = 200.0
    class Sale:
        id = 1
        customer = "John Doe"
        timestamp = "2024-01-01 10:00"
        total = 200.0
        items = [Item()]
    return Sale()

class TestSalesUi:
    def test_feedback_banner(self, sales_ui, qtbot):
        sales_ui.show_banner("Test Success", success=True)
        assert sales_ui.feedback_banner.isVisible()
        sales_ui.show_banner("Test Error", success=False)
        assert sales_ui.feedback_banner.isVisible()

    def test_loading_overlay(self, sales_ui, qtbot):
        sales_ui.show_loading("Loading...")
        assert sales_ui.loading_overlay.isVisible()
        sales_ui.hide_loading()
        assert not sales_ui.loading_overlay.isVisible()

    def test_pagination(self, sales_ui, qtbot, mock_main_window, sample_sale):
        # Add 25 sales to billing_service mock
        mock_main_window.billing_service.get_recent_bills = lambda n=1000: [sample_sale for _ in range(25)]
        sales_ui.load_sales_data()
        assert sales_ui.sales_table.rowCount() == sales_ui.page_size
        sales_ui.next_page()
        assert sales_ui.sales_table.rowCount() <= sales_ui.page_size
        sales_ui.prev_page()
        assert sales_ui.sales_table.rowCount() == sales_ui.page_size

    def test_accessibility(self, sales_ui):
        assert sales_ui.sales_table.accessibleName() == "Sales Table"
        assert sales_ui.sales_table.property("aria-role") == "table"
        assert sales_ui.prev_page_btn.accessibleName() == "Previous Page Button"
        assert sales_ui.next_page_btn.accessibleName() == "Next Page Button"

    def test_details_dialog(self, qtbot, sample_sale):
        dialog = SaleDetailsDialog(sample_sale)
        qtbot.addWidget(dialog)
        dialog.show()
        assert dialog.isVisible()
        dialog.accept()

    def test_context_menu(self, sales_ui, qtbot, mock_main_window, sample_sale):
        mock_main_window.billing_service.get_recent_bills = lambda n=1000: [sample_sale]
        sales_ui.load_sales_data()
        sales_ui.sales_table.setRowCount(1)
        sales_ui.sales_table.setItem(0, 0, QTableWidgetItem("1"))
        sales_ui.sales_table.selectRow(0)
        sales_ui.show_context_menu(sales_ui.sales_table.visualItemRect(sales_ui.sales_table.item(0, 0)).center())
        # No assertion, just ensure no crash

class TestBillingService:
    def test_get_monthly_sales(self):
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

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 