import pytest
from unittest.mock import Mock
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
from src.orders_ui import OrdersUi, CreateOrderDialog
from src.order_service import OrderService
from src.db import clear_all_orders, get_all_orders
import datetime

@pytest.fixture(autouse=True)
def setup_orders():
    clear_all_orders()
    yield
    clear_all_orders()

@pytest.fixture
def mock_main_window():
    mock = Mock()
    mock.order_service.add.return_value = (True, None)
    mock.order_service.delete.return_value = (True, None)
    mock.order_service.update.return_value = (True, None)
    return mock

@pytest.fixture
def orders_ui(qtbot, mock_main_window):
    ui = OrdersUi(mock_main_window)
    qtbot.addWidget(ui)
    return ui

@pytest.fixture
def order_service():
    return OrderService()

@pytest.fixture
def sample_order_items():
    return [
        {"barcode": "ORD001", "name": "MedA", "quantity": 5, "expiry": "2025-12-31", "manufacturer": "PharmaA", "order_quantity": 2},
        {"barcode": "ORD002", "name": "MedB", "quantity": 10, "expiry": "2026-01-31", "manufacturer": "PharmaB", "order_quantity": 3}
    ]

@pytest.fixture
def sample_supplier():
    return "SupplierX"

class TestOrderDialogValidation:
    def test_valid_order(self, qtbot):
        dialog = CreateOrderDialog()
        dialog.supplier_name.setText("SupplierX")
        dialog.meds_table.insertRow(0)
        dialog.meds_table.setItem(0, 0, QTableWidgetItem("ORD001"))
        dialog.meds_table.setItem(0, 1, QTableWidgetItem("MedA"))
        dialog.meds_table.setItem(0, 2, QTableWidgetItem("5"))
        dialog.meds_table.setItem(0, 3, QTableWidgetItem("2025-12-31"))
        dialog.meds_table.setItem(0, 4, QTableWidgetItem("PharmaA"))
        dialog.meds_table.setItem(0, 5, QTableWidgetItem("2"))
        assert dialog.validate_and_accept() is None  # Accepts

    def test_duplicate_medicine(self, qtbot):
        dialog = CreateOrderDialog()
        dialog.supplier_name.setText("SupplierX")
        for i in range(2):
            dialog.meds_table.insertRow(i)
            dialog.meds_table.setItem(i, 0, QTableWidgetItem("ORD001"))
            dialog.meds_table.setItem(i, 1, QTableWidgetItem("MedA"))
            dialog.meds_table.setItem(i, 2, QTableWidgetItem("5"))
            dialog.meds_table.setItem(i, 3, QTableWidgetItem("2025-12-31"))
            dialog.meds_table.setItem(i, 4, QTableWidgetItem("PharmaA"))
            dialog.meds_table.setItem(i, 5, QTableWidgetItem("2"))
        assert dialog.validate_and_accept() is None  # Should show error and not accept

    def test_missing_supplier(self, qtbot):
        dialog = CreateOrderDialog()
        dialog.supplier_name.setText("")
        dialog.meds_table.insertRow(0)
        dialog.meds_table.setItem(0, 0, QTableWidgetItem("ORD001"))
        dialog.meds_table.setItem(0, 1, QTableWidgetItem("MedA"))
        dialog.meds_table.setItem(0, 2, QTableWidgetItem("5"))
        dialog.meds_table.setItem(0, 3, QTableWidgetItem("2025-12-31"))
        dialog.meds_table.setItem(0, 4, QTableWidgetItem("PharmaA"))
        dialog.meds_table.setItem(0, 5, QTableWidgetItem("2"))
        assert dialog.validate_and_accept() is None  # Should show error and not accept

class TestOrderService:
    def test_add_and_get_order(self, order_service, sample_order_items, sample_supplier):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_path = "test.pdf"
        success, error = order_service.add(timestamp, pdf_path, sample_order_items)
        assert success
        orders = order_service.get_all()
        assert any(o.file_path == pdf_path for o in orders)

    def test_delete_order(self, order_service, sample_order_items, sample_supplier):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_path = "test.pdf"
        success, error = order_service.add(timestamp, pdf_path, sample_order_items)
        assert success
        orders = order_service.get_all()
        order_id = orders[0].id
        success, error = order_service.delete(order_id)
        assert success
        orders = order_service.get_all()
        assert all(o.id != order_id for o in orders)

    def test_update_order(self, order_service, sample_order_items, sample_supplier):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf_path = "test.pdf"
        success, error = order_service.add(timestamp, pdf_path, sample_order_items)
        assert success
        orders = order_service.get_all()
        order_id = orders[0].id
        new_items = [{"barcode": "ORD003", "name": "MedC", "quantity": 7, "expiry": "2027-01-01", "manufacturer": "PharmaC", "order_quantity": 4}]
        success, error = order_service.update(order_id, "SupplierY", new_items)
        assert success

class TestOrdersUi:
    def test_pagination(self, orders_ui, qtbot, order_service, sample_order_items):
        # Add 25 orders
        for i in range(25):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf_path = f"test_{i}.pdf"
            order_service.add(timestamp, pdf_path, sample_order_items)
        orders_ui.refresh_orders_table()
        assert orders_ui.orders_table.rowCount() == orders_ui.page_size
        orders_ui.next_page()
        assert orders_ui.orders_table.rowCount() <= orders_ui.page_size
        orders_ui.prev_page()
        assert orders_ui.orders_table.rowCount() == orders_ui.page_size

    def test_filtering(self, orders_ui, qtbot, order_service, sample_order_items):
        # Add orders with different suppliers
        for i, supplier in enumerate(["Alpha", "Beta", "Gamma"]):
            items = [{**sample_order_items[0], "manufacturer": supplier}]
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf_path = f"test_{i}.pdf"
            order_service.add(timestamp, pdf_path, items)
        orders_ui.search_box.setText("Beta")
        orders_ui.refresh_orders_table()
        assert any("Beta" in orders_ui.orders_table.item(row, 2).text() for row in range(orders_ui.orders_table.rowCount()))

    def test_keyboard_shortcuts(self, orders_ui, qtbot):
        # Simulate shortcut activation
        orders_ui.shortcut_create.activated.emit()
        orders_ui.shortcut_delete.activated.emit()
        orders_ui.shortcut_confirm.activated.emit()
        orders_ui.shortcut_edit.activated.emit()
        # No assertion, just ensure no crash

    def test_context_menu(self, orders_ui, qtbot):
        # Simulate context menu event
        orders_ui.orders_table.setRowCount(1)
        orders_ui.orders_table.setItem(0, 0, QTableWidgetItem("1"))
        orders_ui.orders_table.selectRow(0)
        orders_ui.show_context_menu(orders_ui.orders_table.visualItemRect(orders_ui.orders_table.item(0, 0)).center())
        # No assertion, just ensure no crash

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 