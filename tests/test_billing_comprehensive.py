import pytest
import datetime
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from src.billing_ui import BillingUi
from src.billing_service import BillingService
from src.db import add_bill, get_all_bills, clear_all_bills, get_pharmacy_details
from src.dialogs import AddMedicineDialog


@pytest.fixture(autouse=True)
def setup_billing():
    """Clear billing data before and after each test"""
    clear_all_bills()
    yield
    clear_all_bills()


@pytest.fixture
def sample_bills():
    """Create sample bills for testing"""
    bills = [
        {
            "timestamp": "2024-01-01 10:00:00",
            "total": 150.0,
            "items": [
                {"barcode": "BILL001", "name": "Aspirin", "quantity": 2, "price": 50.0, "subtotal": 100.0},
                {"barcode": "BILL002", "name": "Paracetamol", "quantity": 1, "price": 50.0, "subtotal": 50.0}
            ]
        },
        {
            "timestamp": "2024-01-02 11:30:00",
            "total": 432.0,
            "items": [
                {"barcode": "BILL003", "name": "PainRelief", "quantity": 2, "price": 200.0, "subtotal": 400.0, "discount": 20.0},
                {"barcode": "BILL004", "name": "Cough Syrup", "quantity": 1, "price": 80.0, "subtotal": 80.0, "discount": 8.0}
            ]
        }
    ]
    
    for bill in bills:
        add_bill(bill["timestamp"], bill["total"], bill["items"])
    
    return bills


@pytest.fixture
def mock_main_window():
    """Create a mock main window for UI tests"""
    return Mock()


@pytest.fixture
def billing_ui(mock_main_window):
    """Create a BillingUi instance for testing"""
    return BillingUi(mock_main_window)


@pytest.fixture
def billing_service():
    """Create a BillingService instance for testing"""
    return BillingService()


@pytest.fixture
def sample_customer():
    """Create sample customer data for testing"""
    return {
        "name": "John Doe",
        "age": 30,
        "gender": "Male",
        "phone": "1234567890",
        "email": "john.doe@example.com",
        "address": "123 Main Street, City, State"
    }


@pytest.fixture
def sample_billing_items():
    """Create sample billing items for testing"""
    return [
        {
            "barcode": "ITEM001",
            "name": "Test Medicine 1",
            "quantity": 2,
            "price": 100.0,
            "tax": 5.0,
            "discount": 10.0
        },
        {
            "barcode": "ITEM002",
            "name": "Test Medicine 2",
            "quantity": 1,
            "price": 50.0,
            "tax": 0.0,
            "discount": 0.0
        }
    ]


class TestBillingValidation:
    """Test billing validation functionality"""
    
    def test_validate_customer_info_valid_data(self, billing_ui, sample_customer):
        """Test validation with valid customer data"""
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        assert billing_ui.validate_customer_info() is True
    
    def test_validate_customer_info_empty_name(self, billing_ui, sample_customer):
        """Test validation with empty name"""
        billing_ui.customer_name.setText("")
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        assert billing_ui.validate_customer_info() is False
    
    def test_validate_customer_info_invalid_age(self, billing_ui, sample_customer):
        """Test validation with invalid age"""
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(0)  # Invalid age
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        assert billing_ui.validate_customer_info() is False
    
    def test_validate_customer_info_invalid_phone(self, billing_ui, sample_customer):
        """Test validation with invalid phone number"""
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText("123")  # Invalid phone
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        assert billing_ui.validate_customer_info() is False
    
    def test_validate_customer_info_invalid_email(self, billing_ui, sample_customer):
        """Test validation with invalid email"""
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText("invalid-email")  # Invalid email
        billing_ui.customer_address.setText(sample_customer["address"])
        
        assert billing_ui.validate_customer_info() is False
    
    def test_validate_customer_info_empty_address(self, billing_ui, sample_customer):
        """Test validation with empty address"""
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText("")
        
        assert billing_ui.validate_customer_info() is False
    
    def test_validate_billing_items_empty_table(self, billing_ui):
        """Test validation with empty billing table"""
        assert billing_ui.validate_billing_items() is False
    
    def test_validate_billing_items_valid_data(self, billing_ui, sample_billing_items):
        """Test validation with valid billing items"""
        # Add items to table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        assert billing_ui.validate_billing_items() is True
    
    def test_validate_billing_items_duplicate_barcode(self, billing_ui, sample_billing_items):
        """Test validation with duplicate barcodes"""
        # Add items with duplicate barcode
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem("DUPLICATE"))  # Same barcode
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        assert billing_ui.validate_billing_items() is False
    
    def test_validate_billing_items_invalid_quantity(self, billing_ui, sample_billing_items):
        """Test validation with invalid quantity"""
        billing_ui.billing_table.insertRow(0)
        billing_ui.billing_table.setItem(0, 0, QTableWidgetItem(sample_billing_items[0]["barcode"]))
        billing_ui.billing_table.setItem(0, 1, QTableWidgetItem(sample_billing_items[0]["name"]))
        billing_ui.billing_table.setItem(0, 2, QTableWidgetItem("0"))  # Invalid quantity
        billing_ui.billing_table.setItem(0, 3, QTableWidgetItem(str(sample_billing_items[0]["price"])))
        billing_ui.billing_table.setItem(0, 4, QTableWidgetItem(str(sample_billing_items[0]["tax"])))
        billing_ui.billing_table.setItem(0, 5, QTableWidgetItem(str(sample_billing_items[0]["discount"])))
        
        assert billing_ui.validate_billing_items() is False
    
    def test_validate_billing_items_negative_price(self, billing_ui, sample_billing_items):
        """Test validation with negative price"""
        billing_ui.billing_table.insertRow(0)
        billing_ui.billing_table.setItem(0, 0, QTableWidgetItem(sample_billing_items[0]["barcode"]))
        billing_ui.billing_table.setItem(0, 1, QTableWidgetItem(sample_billing_items[0]["name"]))
        billing_ui.billing_table.setItem(0, 2, QTableWidgetItem(str(sample_billing_items[0]["quantity"])))
        billing_ui.billing_table.setItem(0, 3, QTableWidgetItem("-50"))  # Negative price
        billing_ui.billing_table.setItem(0, 4, QTableWidgetItem(str(sample_billing_items[0]["tax"])))
        billing_ui.billing_table.setItem(0, 5, QTableWidgetItem(str(sample_billing_items[0]["discount"])))
        
        assert billing_ui.validate_billing_items() is False
    
    def test_validate_bill_comprehensive(self, billing_ui, sample_customer, sample_billing_items):
        """Test comprehensive bill validation"""
        # Set valid customer info
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        # Add valid billing items
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        assert billing_ui.validate_bill() is True


class TestBillingService:
    """Test billing service functionality"""
    
    def test_calculate_totals_basic(self, billing_service):
        """Test basic total calculation"""
        items = [
            {"barcode": "TEST001", "name": "Test Med", "quantity": 2, "price": 100.0, "tax": 0.0, "discount": 0.0}
        ]
        tax_percent = 10.0
        discount_percent = 5.0
        
        subtotal, tax_amount, discount_amount, total = billing_service.calculate_totals(items, tax_percent, discount_percent)
        
        assert subtotal == 200.0  # 2 * 100
        assert discount_amount == 10.0  # 5% of 200
        assert tax_amount == 19.0  # 10% of (200 - 10)
        assert total == 209.0  # (200 - 10) + 19
    
    def test_calculate_totals_zero_tax_discount(self, billing_service):
        """Test calculation with zero tax and discount"""
        items = [
            {"barcode": "TEST002", "name": "Test Med", "quantity": 1, "price": 50.0, "tax": 0.0, "discount": 0.0}
        ]
        tax_percent = 0.0
        discount_percent = 0.0
        
        subtotal, tax_amount, discount_amount, total = billing_service.calculate_totals(items, tax_percent, discount_percent)
        
        assert subtotal == 50.0
        assert discount_amount == 0.0
        assert tax_amount == 0.0
        assert total == 50.0
    
    def test_calculate_totals_multiple_items(self, billing_service):
        """Test calculation with multiple items"""
        items = [
            {"barcode": "TEST003", "name": "Med 1", "quantity": 2, "price": 100.0, "tax": 0.0, "discount": 0.0},
            {"barcode": "TEST004", "name": "Med 2", "quantity": 1, "price": 50.0, "tax": 0.0, "discount": 0.0}
        ]
        tax_percent = 15.0
        discount_percent = 10.0
        
        subtotal, tax_amount, discount_amount, total = billing_service.calculate_totals(items, tax_percent, discount_percent)
        
        assert subtotal == 250.0  # (2 * 100) + (1 * 50)
        assert discount_amount == 25.0  # 10% of 250
        assert tax_amount == 33.75  # 15% of (250 - 25)
        assert total == 258.75  # (250 - 25) + 33.75
    
    def test_create_bill_success(self, billing_service, sample_customer):
        """Test successful bill creation"""
        items = [
            {"barcode": "CREATE001", "name": "Create Test", "quantity": 1, "price": 100.0, "subtotal": 100.0}
        ]
        
        success, error, bill_id, items_list = billing_service.create_bill(items, sample_customer)
        
        assert success is True
        assert error is None
        assert bill_id is not None
        assert len(items_list) == 1
    
    def test_get_recent_bills(self, billing_service, sample_bills):
        """Test getting recent bills"""
        bills = billing_service.get_recent_bills(limit=5)
        
        assert isinstance(bills, list)
        assert len(bills) <= 5
        assert all(hasattr(bill, 'total') for bill in bills)
    
    def test_get_sales_data(self, billing_service, sample_bills):
        """Test getting sales data"""
        sales = billing_service.get_sales_data()
        
        assert isinstance(sales, list)
        # Sales data should include information about the bills
    
    def test_generate_receipt_success(self, billing_service):
        """Test successful receipt generation"""
        timestamp = datetime.datetime.now()
        items = [
            {"barcode": "RECEIPT001", "name": "Receipt Test", "quantity": 1, "price": 100.0, "subtotal": 100.0}
        ]
        total = 100.0
        details = {"name": "Test Pharmacy", "address": "Test Address", "phone": "1234567890"}
        
        receipt_path = billing_service.generate_receipt(timestamp, items, total, details)
        
        assert receipt_path is not None
        assert os.path.exists(receipt_path)
        
        # Clean up
        if os.path.exists(receipt_path):
            os.remove(receipt_path)
    
    def test_finalize_bill_success(self, billing_service, sample_customer, sample_billing_items):
        """Test successful bill finalization"""
        result = billing_service.finalize_bill(sample_billing_items, sample_customer, 10.0, 5.0)
        
        assert result['success'] is True
        assert result['error'] is None
        assert result['bill_id'] is not None
        assert 'totals' in result
    
    def test_save_draft_success(self, billing_service, sample_customer, sample_billing_items):
        """Test successful draft saving"""
        draft_data = {
            "customer": sample_customer,
            "items": sample_billing_items,
            "tax": 10.0,
            "discount": 5.0,
            "subtotal": 250.0,
            "total": 258.75
        }
        
        success, filename = billing_service.save_draft(draft_data, "test_draft")
        
        assert success is True
        assert filename is not None
        assert os.path.exists(filename)
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_load_draft_success(self, billing_service, sample_customer, sample_billing_items):
        """Test successful draft loading"""
        # First save a draft
        draft_data = {
            "customer": sample_customer,
            "items": sample_billing_items,
            "tax": 10.0,
            "discount": 5.0,
            "subtotal": 250.0,
            "total": 258.75
        }
        
        success, filename = billing_service.save_draft(draft_data, "test_draft")
        assert success is True
        
        # Then load it
        success, loaded_draft = billing_service.load_draft(filename)
        
        assert success is True
        assert loaded_draft is not None
        assert loaded_draft["customer"]["name"] == sample_customer["name"]
        assert len(loaded_draft["items"]) == len(sample_billing_items)
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
    
    def test_delete_draft_success(self, billing_service, sample_customer, sample_billing_items):
        """Test successful draft deletion"""
        # First save a draft
        draft_data = {
            "customer": sample_customer,
            "items": sample_billing_items,
            "tax": 10.0,
            "discount": 5.0,
            "subtotal": 250.0,
            "total": 258.75
        }
        
        success, filename = billing_service.save_draft(draft_data, "test_draft")
        assert success is True
        assert os.path.exists(filename)
        
        # Then delete it
        success, error = billing_service.delete_draft(filename)
        
        assert success is True
        assert error is None
        assert not os.path.exists(filename)
    
    def test_add_item_to_bill(self, billing_service, sample_billing_items):
        """Test adding item to bill"""
        bill_items = []
        medicine = {
            "barcode": "ADD001",
            "name": "Add Test",
            "price": 100.0,
            "quantity": 10
        }
        quantity = 2
        
        result = billing_service.add_item_to_bill(bill_items, medicine, quantity)
        
        assert result is True
        assert len(bill_items) == 1
        assert bill_items[0]["barcode"] == "ADD001"
        assert bill_items[0]["quantity"] == 2


class TestBillingUIComponents:
    """Test billing UI components"""
    
    def test_billing_ui_initialization(self, billing_ui):
        """Test billing UI initialization"""
        assert billing_ui.customer_name is not None
        assert billing_ui.customer_age is not None
        assert billing_ui.customer_gender is not None
        assert billing_ui.customer_phone is not None
        assert billing_ui.customer_email is not None
        assert billing_ui.customer_address is not None
        assert billing_ui.billing_table is not None
        assert billing_ui.recent_bills_list is not None
        assert billing_ui.tax_spin is not None
        assert billing_ui.discount_spin is not None
        assert billing_ui.subtotal_label is not None
        assert billing_ui.tax_label is not None
        assert billing_ui.discount_label is not None
        assert billing_ui.total_label is not None
    
    def test_get_billing_items(self, billing_ui, sample_billing_items):
        """Test extracting billing items from table"""
        # Add items to table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        items = billing_ui.get_billing_items()
        
        assert len(items) == len(sample_billing_items)
        assert items[0]["barcode"] == sample_billing_items[0]["barcode"]
        assert items[0]["name"] == sample_billing_items[0]["name"]
        assert items[0]["quantity"] == sample_billing_items[0]["quantity"]
        assert items[0]["price"] == sample_billing_items[0]["price"]
    
    def test_update_bill_summary(self, billing_ui, sample_billing_items):
        """Test bill summary update"""
        # Add items to table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # Set tax and discount
        billing_ui.tax_spin.setValue(10.0)
        billing_ui.discount_spin.setValue(5.0)
        
        billing_ui.update_bill_summary()
        
        # Check that labels are updated (they should contain non-zero values)
        assert "₹0.00" not in billing_ui.subtotal_label.text()
        assert "₹0.00" not in billing_ui.total_label.text()
    
    def test_clear_bill(self, billing_ui, sample_customer, sample_billing_items):
        """Test clearing the bill"""
        # Set customer info
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        # Add items to table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # Set tax and discount
        billing_ui.tax_spin.setValue(10.0)
        billing_ui.discount_spin.setValue(5.0)
        
        billing_ui.clear_bill()
        
        # Check that everything is cleared
        assert billing_ui.customer_name.text() == ""
        assert billing_ui.customer_age.value() == 25  # Default value
        assert billing_ui.customer_gender.currentIndex() == 0  # Default value
        assert billing_ui.customer_phone.text() == ""
        assert billing_ui.customer_email.text() == ""
        assert billing_ui.customer_address.text() == ""
        assert billing_ui.billing_table.rowCount() == 0
        assert billing_ui.tax_spin.value() == 0.0
        assert billing_ui.discount_spin.value() == 0.0
    
    def test_tax_discount_changed(self, billing_ui, sample_billing_items):
        """Test tax and discount change handling"""
        # Add items to table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # Change tax value
        billing_ui.tax_spin.setValue(15.0)
        
        # The summary should be updated automatically via the signal connection
        # We can verify this by checking that the tax label shows the new percentage
        assert "15.0%" in billing_ui.tax_label.text()
    
    def test_table_item_changed(self, billing_ui, sample_billing_items):
        """Test table item change handling"""
        # Add items to table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # Change a quantity
        billing_ui.billing_table.setItem(0, 2, QTableWidgetItem("5"))
        
        # The summary should be updated automatically via the signal connection
        # We can verify this by checking that the subtotal reflects the change
        items = billing_ui.get_billing_items()
        assert items[0]["quantity"] == 5


class TestBillingKeyboardShortcuts:
    """Test billing keyboard shortcuts"""
    
    def test_setup_shortcuts(self, billing_ui):
        """Test keyboard shortcuts setup"""
        assert hasattr(billing_ui, 'add_item_shortcut')
        assert hasattr(billing_ui, 'remove_item_shortcut')
        assert hasattr(billing_ui, 'finalize_shortcut')
        assert hasattr(billing_ui, 'save_draft_shortcut')
        assert hasattr(billing_ui, 'clear_bill_shortcut')
    
    def test_add_item_shortcut(self, billing_ui):
        """Test add item keyboard shortcut"""
        # Mock the main window method
        billing_ui.main_window.open_billing_add_medicine_dialog = Mock()
        
        billing_ui._on_add_item_shortcut()
        
        billing_ui.main_window.open_billing_add_medicine_dialog.assert_called_once()
    
    def test_remove_item_shortcut(self, billing_ui):
        """Test remove item keyboard shortcut"""
        # Mock the main window method
        billing_ui.main_window.remove_selected_billing_item = Mock()
        
        billing_ui._on_remove_item_shortcut()
        
        billing_ui.main_window.remove_selected_billing_item.assert_called_once()


class TestBillingEdgeCases:
    """Test billing edge cases and error handling"""
    
    def test_finalize_bill_without_main_window_method(self, billing_ui, sample_customer, sample_billing_items):
        """Test finalize bill when main window doesn't have the method"""
        # Set valid data
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # Remove the method from main window
        if hasattr(billing_ui.main_window, 'complete_sale'):
            delattr(billing_ui.main_window, 'complete_sale')
        
        billing_ui._on_finalize_bill()
        
        # Should handle gracefully without crashing
    
    def test_save_draft_without_main_window_method(self, billing_ui, sample_customer, sample_billing_items):
        """Test save draft when main window doesn't have the method"""
        # Set valid data
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # Remove the method from main window
        if hasattr(billing_ui.main_window, 'save_billing_draft'):
            delattr(billing_ui.main_window, 'save_billing_draft')
        
        billing_ui._on_save_draft()
        
        # Should handle gracefully without crashing
    
    def test_update_bill_summary_with_invalid_data(self, billing_ui):
        """Test bill summary update with invalid data"""
        # Add invalid item to table
        billing_ui.billing_table.insertRow(0)
        billing_ui.billing_table.setItem(0, 0, QTableWidgetItem("TEST"))
        billing_ui.billing_table.setItem(0, 1, QTableWidgetItem("Test"))
        billing_ui.billing_table.setItem(0, 2, QTableWidgetItem("invalid"))  # Invalid quantity
        billing_ui.billing_table.setItem(0, 3, QTableWidgetItem("invalid"))  # Invalid price
        billing_ui.billing_table.setItem(0, 4, QTableWidgetItem("0"))
        billing_ui.billing_table.setItem(0, 5, QTableWidgetItem("0"))
        
        # Should handle gracefully without crashing
        billing_ui.update_bill_summary()
        
        # Should set default values on error
        assert "₹0.00" in billing_ui.subtotal_label.text()
        assert "₹0.00" in billing_ui.total_label.text()


class TestBillingIntegration:
    """Test billing integration scenarios"""
    
    def test_complete_billing_workflow(self, billing_ui, billing_service, sample_customer, sample_billing_items):
        """Test complete billing workflow from start to finish"""
        # 1. Set customer information
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        # 2. Add items to billing table
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        # 3. Set tax and discount
        billing_ui.tax_spin.setValue(10.0)
        billing_ui.discount_spin.setValue(5.0)
        
        # 4. Update summary
        billing_ui.update_bill_summary()
        
        # 5. Validate bill
        assert billing_ui.validate_bill() is True
        
        # 6. Get billing items
        items = billing_ui.get_billing_items()
        assert len(items) == len(sample_billing_items)
        
        # 7. Test service integration
        result = billing_service.finalize_bill(items, sample_customer, 10.0, 5.0)
        assert result['success'] is True
    
    def test_draft_save_and_load_workflow(self, billing_ui, billing_service, sample_customer, sample_billing_items):
        """Test draft save and load workflow"""
        # 1. Set up bill data
        billing_ui.customer_name.setText(sample_customer["name"])
        billing_ui.customer_age.setValue(sample_customer["age"])
        billing_ui.customer_gender.setCurrentText(sample_customer["gender"])
        billing_ui.customer_phone.setText(sample_customer["phone"])
        billing_ui.customer_email.setText(sample_customer["email"])
        billing_ui.customer_address.setText(sample_customer["address"])
        
        for i, item in enumerate(sample_billing_items):
            billing_ui.billing_table.insertRow(i)
            billing_ui.billing_table.setItem(i, 0, QTableWidgetItem(item["barcode"]))
            billing_ui.billing_table.setItem(i, 1, QTableWidgetItem(item["name"]))
            billing_ui.billing_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            billing_ui.billing_table.setItem(i, 3, QTableWidgetItem(str(item["price"])))
            billing_ui.billing_table.setItem(i, 4, QTableWidgetItem(str(item["tax"])))
            billing_ui.billing_table.setItem(i, 5, QTableWidgetItem(str(item["discount"])))
        
        billing_ui.tax_spin.setValue(10.0)
        billing_ui.discount_spin.setValue(5.0)
        
        # 2. Save draft
        draft_data = {
            "customer": sample_customer,
            "items": billing_ui.get_billing_items(),
            "tax": billing_ui.tax_spin.value(),
            "discount": billing_ui.discount_spin.value(),
            "subtotal": 250.0,
            "total": 258.75
        }
        
        success, filename = billing_service.save_draft(draft_data, "test_workflow")
        assert success is True
        
        # 3. Load draft
        success, loaded_draft = billing_service.load_draft(filename)
        assert success is True
        assert loaded_draft["customer"]["name"] == sample_customer["name"]
        
        # 4. Clean up
        if os.path.exists(filename):
            os.remove(filename)


class TestBillingPerformance:
    """Test billing performance with large datasets"""
    
    def test_large_bill_calculation(self, billing_service):
        """Test calculation with large number of items"""
        # Create large number of items
        items = []
        for i in range(100):
            items.append({
                "barcode": f"PERF{i:03d}",
                "name": f"Performance Item {i}",
                "quantity": i + 1,
                "price": 10.0 + i,
                "tax": 0.0,
                "discount": 0.0
            })
        
        tax_percent = 15.0
        discount_percent = 10.0
        
        # Test calculation performance
        subtotal, tax_amount, discount_amount, total = billing_service.calculate_totals(items, tax_percent, discount_percent)
        
        assert subtotal > 0
        assert tax_amount > 0
        assert discount_amount > 0
        assert total > subtotal  # Should include tax
    
    def test_multiple_bills_creation(self, billing_service, sample_customer):
        """Test creating multiple bills"""
        for i in range(10):
            items = [
                {
                    "barcode": f"MULTI{i:03d}",
                    "name": f"Multi Test {i}",
                    "quantity": 1,
                    "price": 100.0,
                    "subtotal": 100.0
                }
            ]
            
            success, error, bill_id, items_list = billing_service.create_bill(items, sample_customer)
            assert success is True
            assert bill_id is not None
        
        # Check that all bills were created
        bills = billing_service.get_recent_bills(limit=20)
        assert len(bills) >= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 