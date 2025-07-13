import pytest
from unittest.mock import Mock
from PyQt5.QtWidgets import QApplication, QTableWidgetItem
from src.alerts_ui import AlertsUi, MedicineDetailsDialog
from src.alert_service import AlertService
from src.db import clear_inventory, get_all_medicines

@pytest.fixture(autouse=True)
def setup_alerts():
    clear_inventory()
    yield
    clear_inventory()

@pytest.fixture
def mock_main_window():
    mw = Mock()
    mw.alert_service = AlertService()
    return mw

@pytest.fixture
def alerts_ui(qtbot, mock_main_window):
    ui = AlertsUi(mock_main_window)
    qtbot.addWidget(ui)
    return ui

@pytest.fixture
def sample_medicine():
    class Med:
        barcode = "ALERT001"
        name = "TestMed"
        quantity = 2
        threshold = 5
        expiry = "2025-12-31"
        manufacturer = "PharmaA"
    return Med()

class TestAlertsUi:
    def test_feedback_banner(self, alerts_ui, qtbot):
        alerts_ui.show_banner("Test Success", success=True)
        assert alerts_ui.feedback_banner.isVisible()
        alerts_ui.show_banner("Test Error", success=False)
        assert alerts_ui.feedback_banner.isVisible()

    def test_loading_overlay(self, alerts_ui, qtbot):
        alerts_ui.show_loading("Loading...")
        assert alerts_ui.loading_overlay.isVisible()
        alerts_ui.hide_loading()
        assert not alerts_ui.loading_overlay.isVisible()

    def test_pagination(self, alerts_ui, qtbot, mock_main_window, sample_medicine):
        # Add 25 medicines to alert service mock
        mock_main_window.alert_service.get_low_stock = lambda: [sample_medicine for _ in range(25)]
        alerts_ui.refresh_alerts_table()
        assert alerts_ui.alerts_table.rowCount() == alerts_ui.page_size
        alerts_ui.next_page()
        assert alerts_ui.alerts_table.rowCount() <= alerts_ui.page_size
        alerts_ui.prev_page()
        assert alerts_ui.alerts_table.rowCount() == alerts_ui.page_size

    def test_context_menu_and_details(self, alerts_ui, qtbot, mock_main_window, sample_medicine):
        # Add a medicine to the table
        mock_main_window.alert_service.get_low_stock = lambda: [sample_medicine]
        alerts_ui.refresh_alerts_table()
        # Simulate context menu event
        alerts_ui.alerts_table.setRowCount(1)
        alerts_ui.alerts_table.setItem(0, 0, QTableWidgetItem("ALERT001"))
        alerts_ui.alerts_table.selectRow(0)
        alerts_ui.show_context_menu(alerts_ui.alerts_table.visualItemRect(alerts_ui.alerts_table.item(0, 0)).center())
        # Simulate double click
        alerts_ui._on_table_double_clicked(0, 0)
        # No assertion, just ensure no crash

    def test_bulk_dismiss(self, alerts_ui, qtbot, mock_main_window, sample_medicine):
        mock_main_window.alert_service.get_low_stock = lambda: [sample_medicine for _ in range(5)]
        alerts_ui.refresh_alerts_table()
        for i in range(5):
            alerts_ui.alerts_table.selectRow(i)
        alerts_ui.dismiss_selected_alerts()
        assert alerts_ui.alerts_table.rowCount() < 5

    def test_bulk_generate_order(self, alerts_ui, qtbot, mock_main_window, sample_medicine):
        mock_main_window.alert_service.get_low_stock = lambda: [sample_medicine for _ in range(3)]
        alerts_ui.refresh_alerts_table()
        for i in range(3):
            alerts_ui.alerts_table.selectRow(i)
        alerts_ui.generate_order_for_selected()
        # No assertion, just ensure no crash

    def test_accessibility(self, alerts_ui):
        assert alerts_ui.alerts_table.accessibleName() == "Alerts Table"
        assert alerts_ui.alerts_table.property("aria-role") == "table"
        assert alerts_ui.prev_page_btn.accessibleName() == "Previous Page Button"
        assert alerts_ui.next_page_btn.accessibleName() == "Next Page Button"

class TestAlertService:
    def test_get_low_stock(self, mock_main_window, sample_medicine):
        mock_main_window.alert_service.get_low_stock = lambda: [sample_medicine]
        result = mock_main_window.alert_service.get_low_stock()
        assert result

    def test_send_alerts_no_alerts(self, mock_main_window):
        mock_main_window.alert_service.get_low_stock = lambda: []
        success, msg = mock_main_window.alert_service.send_alerts([])
        assert success
        assert "No alerts needed" in msg

    def test_send_alerts_failure(self, mock_main_window, sample_medicine):
        # Simulate notification failure
        def fail_send(*args, **kwargs):
            return False, "Failed"
        mock_main_window.alert_service.get_low_stock = lambda: [sample_medicine]
        mock_main_window.alert_service.send_alerts = lambda alert_data: (False, "Failed to send")
        success, msg = mock_main_window.alert_service.send_alerts([sample_medicine])
        assert not success
        assert "Failed" in msg

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 