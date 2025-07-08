from src.db import get_pharmacy_details, save_pharmacy_details


def test_save_and_get_pharmacy_details():
    # Test data
    test_name = "Test Pharmacy"
    test_address = "123 Test Street"
    test_phone = "+1234567890"
    test_email = "test@pharmacy.com"
    test_gst = "GST123456"
    test_license = "LIC123456"
    test_website = "www.testpharmacy.com"

    # Save pharmacy details
    success, message = save_pharmacy_details(
        test_name, test_address, test_phone, test_email, test_gst, test_license, test_website
    )
    assert success

    # Get pharmacy details
    details = get_pharmacy_details()
    assert details is not None
    assert details.name == test_name
    assert details.address == test_address
    assert details.phone == test_phone
    assert details.email == test_email
    assert details.gst_number == test_gst
    assert details.license_number == test_license
    assert details.website == test_website
