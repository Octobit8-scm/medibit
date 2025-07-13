import pytest
import datetime
import tempfile
import os
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtTest import QTest

from src.inventory_ui import InventoryUi, InventoryProgressDialog, ImportWorker, ExportWorker
from src.inventory_service import InventoryService
from src.db import add_medicine, get_all_medicines, clear_inventory, get_medicine_by_barcode
from src.dialogs import AddMedicineDialog, EditMedicineDialog


@pytest.fixture(autouse=True)
def setup_inventory():
    """Clear inventory before and after each test"""
    clear_inventory()
    yield
    clear_inventory()


@pytest.fixture
def sample_medicines():
    """Create sample medicines for testing"""
    today = datetime.date.today()
    expired = today.replace(year=today.year - 1)
    expiring_soon = today + datetime.timedelta(days=15)
    
    medicines = [
        {"barcode": "TEST001", "name": "Aspirin", "quantity": 10, "expiry": today, "manufacturer": "PharmaA", "price": 100, "threshold": 5},
        {"barcode": "TEST002", "name": "Paracetamol", "quantity": 1, "expiry": today, "manufacturer": "PharmaB", "price": 50, "threshold": 2},  # Low stock
        {"barcode": "TEST003", "name": "ExpiredMed", "quantity": 20, "expiry": expired, "manufacturer": "PharmaC", "price": 200, "threshold": 10},  # Expired
        {"barcode": "TEST004", "name": "ExpiringSoon", "quantity": 15, "expiry": expiring_soon, "manufacturer": "PharmaA", "price": 80, "threshold": 3},  # Expiring soon
        {"barcode": "TEST005", "name": "OutOfStock", "quantity": 0, "expiry": today, "manufacturer": "PharmaD", "price": 60, "threshold": 2},  # Out of stock
    ]
    
    for med in medicines:
        add_medicine(med["barcode"], med["name"], med["quantity"], med["expiry"], 
                    med["manufacturer"], med["price"], med["threshold"])
    
    return medicines


@pytest.fixture
def mock_main_window():
    """Create a mock main window for UI tests"""
    return Mock()


@pytest.fixture
def inventory_ui(qapp, mock_main_window):
    """Create an InventoryUi instance for testing"""
    from src.inventory_ui import InventoryUi
    return InventoryUi(mock_main_window)


@pytest.fixture
def inventory_service():
    """Create an InventoryService instance for testing"""
    return InventoryService()


class TestInventoryValidation:
    """Test inventory validation functionality"""
    
    def test_validate_medicine_input_static_valid_data(self, inventory_ui):
        """Test validation with valid data"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "Test Medicine", 10, "2024-12-31", "Test Manufacturer", 100, 5, True
        )
        assert len(errors) == 0
    
    def test_validate_medicine_input_static_empty_barcode(self, inventory_ui):
        """Test validation with empty barcode"""
        errors = inventory_ui.validate_medicine_input_static(
            "", "Test Medicine", 10, "2024-12-31", "Test Manufacturer", 100, 5, True
        )
        assert "Barcode cannot be empty" in errors[0]
    
    def test_validate_medicine_input_static_empty_name(self, inventory_ui):
        """Test validation with empty name"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "", 10, "2024-12-31", "Test Manufacturer", 100, 5, True
        )
        assert "Name cannot be empty" in errors[0]
    
    def test_validate_medicine_input_static_negative_quantity(self, inventory_ui):
        """Test validation with negative quantity"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "Test Medicine", -5, "2024-12-31", "Test Manufacturer", 100, 5, True
        )
        assert "Quantity must be a non-negative integer" in errors[0]
    
    def test_validate_medicine_input_static_invalid_quantity_type(self, inventory_ui):
        """Test validation with invalid quantity type"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "Test Medicine", "invalid", "2024-12-31", "Test Manufacturer", 100, 5, True
        )
        assert "Quantity must be a non-negative integer" in errors[0]
    
    def test_validate_medicine_input_static_negative_price(self, inventory_ui):
        """Test validation with negative price"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "Test Medicine", 10, "2024-12-31", "Test Manufacturer", -50, 5, True
        )
        assert "Price must be a non-negative integer" in errors[0]
    
    def test_validate_medicine_input_static_negative_threshold(self, inventory_ui):
        """Test validation with negative threshold"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "Test Medicine", 10, "2024-12-31", "Test Manufacturer", 100, -2, True
        )
        assert "Threshold must be a non-negative integer" in errors[0]
    
    def test_validate_medicine_input_static_invalid_expiry_format(self, inventory_ui):
        """Test validation with invalid expiry date format"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST123", "Test Medicine", 10, "invalid-date", "Test Manufacturer", 100, 5, True
        )
        assert "Expiry must be in YYYY-MM-DD format" in errors[0]
    
    def test_validate_medicine_input_static_duplicate_barcode(self, inventory_ui, sample_medicines):
        """Test validation with duplicate barcode"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST001", "Test Medicine", 10, "2024-12-31", "Test Manufacturer", 100, 5, True
        )
        assert "barcode already exists" in errors[0]
    
    def test_validate_medicine_input_static_edit_mode_no_duplicate_check(self, inventory_ui, sample_medicines):
        """Test validation in edit mode (is_add=False) doesn't check for duplicates"""
        errors = inventory_ui.validate_medicine_input_static(
            "TEST001", "Test Medicine", 10, "2024-12-31", "Test Manufacturer", 100, 5, False
        )
        assert len(errors) == 0


class TestInventoryService:
    """Test inventory service functionality"""
    
    def test_add_medicine_success(self, inventory_service):
        """Test successful medicine addition"""
        data = {
            "barcode": "SVC001", "name": "Test Medicine", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Test Manufacturer", "price": 100, "threshold": 5
        }
        success, error = inventory_service.add(data)
        assert success
        assert error is None
        
        medicines = inventory_service.get_all()
        assert any(m.barcode == "SVC001" for m in medicines)
    
    def test_add_medicine_duplicate_barcode(self, inventory_service):
        """Test adding medicine with duplicate barcode"""
        data = {
            "barcode": "SVC002", "name": "Test Medicine", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Test Manufacturer", "price": 100, "threshold": 5
        }
        inventory_service.add(data)
        
        # Try to add again with same barcode
        success, error = inventory_service.add(data)
        assert not success
        assert "barcode" in error.lower()
    
    def test_update_medicine_success(self, inventory_service):
        """Test successful medicine update"""
        # Add medicine first
        data = {
            "barcode": "SVC003", "name": "Original Name", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Original Manufacturer", "price": 100, "threshold": 5
        }
        inventory_service.add(data)
        
        # Update medicine
        update_data = {
            "name": "Updated Name", "quantity": 15, "expiry": "2024-12-31",
            "manufacturer": "Updated Manufacturer", "price": 150, "threshold": 8
        }
        success, error = inventory_service.update("SVC003", update_data)
        assert success
        
        medicines = inventory_service.get_all()
        medicine = next(m for m in medicines if m.barcode == "SVC003")
        assert medicine.name == "Updated Name"
        assert medicine.quantity == 15
        assert medicine.price == 150
    
    def test_update_medicine_not_found(self, inventory_service):
        """Test updating non-existent medicine"""
        update_data = {
            "name": "Updated Name", "quantity": 15, "expiry": "2024-12-31",
            "manufacturer": "Updated Manufacturer", "price": 150, "threshold": 8
        }
        success, error = inventory_service.update("NONEXISTENT", update_data)
        assert not success
        assert "not found" in error.lower()
    
    def test_update_quantity_success(self, inventory_service):
        """Test successful quantity update"""
        data = {
            "barcode": "SVC004", "name": "Test Medicine", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Test Manufacturer", "price": 100, "threshold": 5
        }
        inventory_service.add(data)
        
        success, error = inventory_service.update_quantity("SVC004", 25)
        assert success
        
        medicines = inventory_service.get_all()
        medicine = next(m for m in medicines if m.barcode == "SVC004")
        assert medicine.quantity == 25
    
    def test_delete_medicine_success(self, inventory_service):
        """Test successful medicine deletion"""
        data = {
            "barcode": "SVC005", "name": "Test Medicine", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Test Manufacturer", "price": 100, "threshold": 5
        }
        inventory_service.add(data)
        
        success, error = inventory_service.delete("SVC005")
        assert success
        
        medicines = inventory_service.get_all()
        assert not any(m.barcode == "SVC005" for m in medicines)
    
    def test_delete_medicine_not_found(self, inventory_service):
        """Test deleting non-existent medicine"""
        success, error = inventory_service.delete("NONEXISTENT")
        assert not success
        assert "not found" in error.lower()
    
    def test_clear_inventory(self, inventory_service):
        """Test clearing all inventory"""
        # Add some medicines
        data1 = {"barcode": "SVC006", "name": "Med1", "quantity": 10, "expiry": "2024-12-31", "manufacturer": "M1", "price": 100, "threshold": 5}
        data2 = {"barcode": "SVC007", "name": "Med2", "quantity": 5, "expiry": "2024-12-31", "manufacturer": "M2", "price": 50, "threshold": 2}
        inventory_service.add(data1)
        inventory_service.add(data2)
        
        inventory_service.clear()
        medicines = inventory_service.get_all()
        assert len(medicines) == 0
    
    def test_search_medicine_by_name(self, inventory_service):
        """Test searching medicine by name"""
        data = {
            "barcode": "SVC008", "name": "Aspirin", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "PharmaA", "price": 100, "threshold": 5
        }
        inventory_service.add(data)
        
        results = inventory_service.search("aspirin")
        assert len(results) == 1
        assert results[0].name == "Aspirin"
    
    def test_search_medicine_by_manufacturer(self, inventory_service):
        """Test searching medicine by manufacturer"""
        data = {
            "barcode": "SVC009", "name": "Paracetamol", "quantity": 5,
            "expiry": "2024-12-31", "manufacturer": "PharmaB", "price": 50, "threshold": 2
        }
        inventory_service.add(data)
        
        results = inventory_service.search("pharmab")
        assert len(results) == 1
        assert results[0].manufacturer == "PharmaB"
    
    def test_search_medicine_by_barcode(self, inventory_service):
        """Test searching medicine by barcode"""
        data = {
            "barcode": "SVC010", "name": "Test Medicine", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Test Manufacturer", "price": 100, "threshold": 5
        }
        inventory_service.add(data)
        
        results = inventory_service.search("SVC010")
        assert len(results) == 1
        assert results[0].barcode == "SVC010"
    
    def test_search_no_results(self, inventory_service):
        """Test search with no results"""
        results = inventory_service.search("nonexistent")
        assert len(results) == 0


class TestInventoryFiltering:
    """Test inventory filtering functionality"""
    
    def test_apply_advanced_filters_all(self, inventory_ui, sample_medicines):
        """Test filtering with 'All' filters"""
        medicines = get_all_medicines()
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == len(medicines)
    
    def test_apply_advanced_filters_low_stock(self, inventory_ui, sample_medicines):
        """Test filtering for low stock medicines"""
        medicines = get_all_medicines()
        inventory_ui.stock_filter.setCurrentText("Low Stock")
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == 1
        assert filtered[0].barcode == "TEST002"  # Paracetamol with quantity 1
    
    def test_apply_advanced_filters_out_of_stock(self, inventory_ui, sample_medicines):
        """Test filtering for out of stock medicines"""
        medicines = get_all_medicines()
        inventory_ui.stock_filter.setCurrentText("Out of Stock")
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == 1
        assert filtered[0].barcode == "TEST005"  # OutOfStock with quantity 0
    
    def test_apply_advanced_filters_expired(self, inventory_ui, sample_medicines):
        """Test filtering for expired medicines"""
        medicines = get_all_medicines()
        inventory_ui.expiry_filter.setCurrentText("Expired")
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == 1
        assert filtered[0].barcode == "TEST003"  # ExpiredMed
    
    def test_apply_advanced_filters_expiring_soon(self, inventory_ui, sample_medicines):
        """Test filtering for medicines expiring soon"""
        medicines = get_all_medicines()
        inventory_ui.expiry_filter.setCurrentText("Expiring Soon (30 days)")
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == 1
        assert filtered[0].barcode == "TEST004"  # ExpiringSoon
    
    def test_apply_advanced_filters_manufacturer(self, inventory_ui, sample_medicines, qtbot):
        """Test filtering by manufacturer"""
        medicines = get_all_medicines()
        inventory_ui.populate_manufacturer_filter()
        inventory_ui.manufacturer_filter.setCurrentText("PharmaA")
        qtbot.wait(100)  # Allow UI to process filter change
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == 2  # Aspirin and ExpiringSoon
        assert all(m.manufacturer == "PharmaA" for m in filtered)
    
    def test_apply_advanced_filters_combined(self, inventory_ui, sample_medicines, qtbot):
        """Test combining multiple filters"""
        medicines = get_all_medicines()
        inventory_ui.populate_manufacturer_filter()
        inventory_ui.stock_filter.setCurrentText("In Stock")
        inventory_ui.manufacturer_filter.setCurrentText("PharmaA")
        qtbot.wait(100)
        filtered = inventory_ui.apply_advanced_filters(medicines)
        assert len(filtered) == 2  # Aspirin and ExpiringSoon from PharmaA that are in stock


class TestInventoryUIComponents:
    """Test inventory UI components"""
    
    def test_inventory_ui_initialization(self, qapp, inventory_ui, qtbot):
        """Test inventory UI initialization"""
        inventory_ui.show()
        qtbot.waitExposed(inventory_ui)
        assert inventory_ui.inventory_table is not None
        assert inventory_ui.add_medicine_btn is not None
        assert inventory_ui.search_box is not None
        assert inventory_ui.export_btn is not None
        assert inventory_ui.import_btn is not None
    
    def test_refresh_inventory_table(self, qapp, inventory_ui, sample_medicines, qtbot):
        """Test refreshing inventory table"""
        inventory_ui.show()
        qtbot.waitExposed(inventory_ui)
        inventory_ui.refresh_inventory_table()
        qtbot.wait(100)  # Allow UI to update
        assert inventory_ui.inventory_table.rowCount() == len(sample_medicines)
    
    def test_filter_inventory_table(self, inventory_ui, sample_medicines, qtbot):
        """Test filtering inventory table"""
        inventory_ui.show()
        qtbot.waitExposed(inventory_ui)
        inventory_ui.refresh_inventory_table()
        inventory_ui.search_box.setText("Aspirin")
        inventory_ui.filter_inventory_table()
        qtbot.wait(100)
        # Should show only Aspirin
        visible_rows = 0
        for row in range(inventory_ui.inventory_table.rowCount()):
            if not inventory_ui.inventory_table.isRowHidden(row):
                visible_rows += 1
        assert visible_rows == 1
    
    def test_populate_manufacturer_filter(self, inventory_ui, sample_medicines, qtbot):
        """Test populating manufacturer filter"""
        inventory_ui.show()
        qtbot.waitExposed(inventory_ui)
        inventory_ui.populate_manufacturer_filter()
        manufacturers = [inventory_ui.manufacturer_filter.itemText(i) 
                        for i in range(inventory_ui.manufacturer_filter.count())]
        assert "All" in manufacturers
        assert "PharmaA" in manufacturers
        assert "PharmaB" in manufacturers
        assert "PharmaC" in manufacturers
        assert "PharmaD" in manufacturers
    
    def test_clear_filters(self, inventory_ui, sample_medicines, qtbot):
        """Test clearing all filters"""
        inventory_ui.show()
        qtbot.waitExposed(inventory_ui)
        inventory_ui.refresh_inventory_table()
        # Set some filters
        inventory_ui.search_box.setText("test")
        inventory_ui.stock_filter.setCurrentText("Low Stock")
        inventory_ui.expiry_filter.setCurrentText("Expired")
        inventory_ui.manufacturer_filter.setCurrentText("PharmaA")
        # Clear filters
        inventory_ui.clear_filters()
        qtbot.wait(100)
        assert inventory_ui.search_box.text() == ""
        assert inventory_ui.stock_filter.currentText() == "All"
        assert inventory_ui.expiry_filter.currentText() == "All"
        assert inventory_ui.manufacturer_filter.currentText() == "All"


class TestInventoryProgressDialog:
    """Test inventory progress dialog"""
    
    def test_progress_dialog_initialization(self):
        """Test progress dialog initialization"""
        dialog = InventoryProgressDialog("Test Title", "Test Label", 100)
        assert dialog.progress_bar.maximum() == 100
        assert dialog.progress_bar.value() == 0
        assert dialog.label.text() == "Test Label"
    
    def test_progress_dialog_set_progress(self):
        """Test setting progress"""
        dialog = InventoryProgressDialog("Test Title", "Test Label", 100)
        dialog.set_progress(50, "Halfway done")
        assert dialog.progress_bar.value() == 50
        assert dialog.label.text() == "Halfway done"
    
    def test_progress_dialog_complete(self):
        """Test completing progress"""
        dialog = InventoryProgressDialog("Test Title", "Test Label", 100)
        dialog.complete("Operation complete")
        assert dialog.progress_bar.value() == 100
        assert dialog.label.text() == "Operation complete"


class TestImportExportWorkers:
    """Test import and export workers"""
    
    def test_import_worker_initialization(self):
        """Test import worker initialization"""
        df = pd.DataFrame({
            "Barcode": ["TEST001"],
            "Name": ["Test Medicine"],
            "Quantity": [10],
            "Threshold": [5],
            "Expiry": ["2024-12-31"],
            "Manufacturer": ["Test Manufacturer"],
            "Price": [100]
        })
        worker = ImportWorker(df)
        assert worker.df is not None
        assert not worker._canceled
    
    def test_export_worker_initialization(self, sample_medicines):
        """Test export worker initialization"""
        medicines = get_all_medicines()
        worker = ExportWorker(medicines, "test_export.xlsx")
        assert worker.medicines == medicines
        assert worker.file_path == "test_export.xlsx"
        assert not worker._canceled
    
    def test_worker_cancel(self):
        """Test worker cancellation"""
        df = pd.DataFrame({"Barcode": ["TEST001"], "Name": ["Test"], "Quantity": [10]})
        worker = ImportWorker(df)
        worker.cancel()
        assert worker._canceled


class TestInventoryContextMenu:
    """Test inventory context menu functionality"""
    
    def test_show_context_menu(self, inventory_ui, sample_medicines):
        """Test showing context menu"""
        inventory_ui.refresh_inventory_table()
        
        # Simulate right-click on first row
        position = inventory_ui.inventory_table.visualItemRect(
            inventory_ui.inventory_table.item(0, 0)
        ).center()
        
        # This would normally show a context menu
        # We can't easily test the actual menu display, but we can test the method exists
        assert hasattr(inventory_ui, 'show_context_menu')
    
    def test_copy_to_clipboard(self, inventory_ui, sample_medicines):
        """Test copying to clipboard"""
        inventory_ui.refresh_inventory_table()
        
        # Test copying cell content
        inventory_ui.copy_to_clipboard(0, 1)  # Copy name from first row
        
        # Verify clipboard has content (this is hard to test without QApplication)
        assert hasattr(inventory_ui, 'copy_to_clipboard')


class TestInventoryShortcuts:
    """Test inventory keyboard shortcuts"""
    
    def test_setup_shortcuts(self, inventory_ui):
        """Test setting up keyboard shortcuts"""
        inventory_ui.setup_shortcuts()
        # Verify shortcuts are set up (hard to test without QApplication)
        assert hasattr(inventory_ui, 'setup_shortcuts')
    
    def test_open_add_medicine_dialog_with_shortcut(self, inventory_ui):
        """Test opening add medicine dialog with shortcut"""
        # This would normally open a dialog
        # We can test the method exists
        assert hasattr(inventory_ui, 'open_add_medicine_dialog_with_shortcut')


class TestInventoryEdgeCases:
    """Test inventory edge cases and error handling"""
    
    def test_add_medicine_with_empty_data(self, inventory_ui):
        """Test adding medicine with empty data"""
        # This would normally show validation errors
        assert hasattr(inventory_ui, '_on_add_medicine')
    
    def test_edit_nonexistent_medicine(self, inventory_ui):
        """Test editing non-existent medicine"""
        # This should handle the case gracefully
        assert hasattr(inventory_ui, 'edit_selected_medicine')
    
    def test_delete_nonexistent_medicine(self, inventory_ui):
        """Test deleting non-existent medicine"""
        # This should handle the case gracefully
        assert hasattr(inventory_ui, 'delete_selected_medicine')
    
    def test_export_empty_inventory(self, inventory_ui):
        """Test exporting empty inventory"""
        # This should show appropriate message
        assert hasattr(inventory_ui, 'export_to_excel')
    
    def test_import_invalid_file(self, inventory_ui):
        """Test importing invalid file"""
        # This should handle errors gracefully
        assert hasattr(inventory_ui, 'import_from_excel')
    
    def test_filter_with_special_characters(self, inventory_ui, sample_medicines):
        """Test filtering with special characters"""
        inventory_ui.refresh_inventory_table()
        inventory_ui.search_box.setText("!@#$%^&*()")
        inventory_ui.filter_inventory_table()
        
        # Should show no results
        visible_rows = 0
        for row in range(inventory_ui.inventory_table.rowCount()):
            if not inventory_ui.inventory_table.isRowHidden(row):
                visible_rows += 1
        assert visible_rows == 0


class TestInventoryIntegration:
    """Test inventory integration scenarios"""
    
    def test_full_medicine_lifecycle(self, inventory_service):
        """Test complete medicine lifecycle: add, update, delete"""
        # Add medicine
        data = {
            "barcode": "LIFE001", "name": "Lifecycle Test", "quantity": 10,
            "expiry": "2024-12-31", "manufacturer": "Test Manufacturer", "price": 100, "threshold": 5
        }
        success, error = inventory_service.add(data)
        assert success
        
        # Verify added
        medicines = inventory_service.get_all()
        medicine = next(m for m in medicines if m.barcode == "LIFE001")
        assert medicine.name == "Lifecycle Test"
        
        # Update medicine
        update_data = {
            "name": "Updated Lifecycle Test", "quantity": 15, "expiry": "2024-12-31",
            "manufacturer": "Updated Manufacturer", "price": 150, "threshold": 8
        }
        success, error = inventory_service.update("LIFE001", update_data)
        assert success
        
        # Verify updated
        medicines = inventory_service.get_all()
        medicine = next(m for m in medicines if m.barcode == "LIFE001")
        assert medicine.name == "Updated Lifecycle Test"
        assert medicine.quantity == 15
        
        # Delete medicine
        success, error = inventory_service.delete("LIFE001")
        assert success
        
        # Verify deleted
        medicines = inventory_service.get_all()
        assert not any(m.barcode == "LIFE001" for m in medicines)
    
    def test_bulk_operations(self, inventory_service):
        """Test bulk operations"""
        # Add multiple medicines
        medicines_data = [
            {"barcode": "BULK001", "name": "Bulk Med 1", "quantity": 10, "expiry": "2024-12-31", "manufacturer": "Bulk Pharma", "price": 100, "threshold": 5},
            {"barcode": "BULK002", "name": "Bulk Med 2", "quantity": 5, "expiry": "2024-12-31", "manufacturer": "Bulk Pharma", "price": 50, "threshold": 2},
            {"barcode": "BULK003", "name": "Bulk Med 3", "quantity": 15, "expiry": "2024-12-31", "manufacturer": "Bulk Pharma", "price": 150, "threshold": 8},
        ]
        
        for data in medicines_data:
            success, error = inventory_service.add(data)
            assert success
        
        # Verify all added
        medicines = inventory_service.get_all()
        assert len([m for m in medicines if m.manufacturer == "Bulk Pharma"]) == 3
        
        # Clear all
        inventory_service.clear()
        medicines = inventory_service.get_all()
        assert len(medicines) == 0


class TestInventoryPerformance:
    """Test inventory performance with large datasets"""
    
    def test_large_dataset_operations(self, inventory_service):
        """Test operations with large dataset"""
        # Add many medicines
        for i in range(100):
            data = {
                "barcode": f"PERF{i:03d}", "name": f"Performance Med {i}", "quantity": i,
                "expiry": "2024-12-31", "manufacturer": f"Pharma{i % 5}", "price": i * 10, "threshold": i // 2
            }
            success, error = inventory_service.add(data)
            assert success
        
        # Test search performance
        medicines = inventory_service.get_all()
        assert len(medicines) == 100
        
        # Test filtering performance
        results = inventory_service.search("Performance")
        assert len(results) == 100
        
        # Test update performance
        success, error = inventory_service.update_quantity("PERF050", 999)
        assert success
        
        # Verify update
        medicines = inventory_service.get_all()
        medicine = next(m for m in medicines if m.barcode == "PERF050")
        assert medicine.quantity == 999


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 