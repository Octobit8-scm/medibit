from db import save_pharmacy_details, get_pharmacy_details

def test_save_and_get_pharmacy_details():
    name = "Test Pharmacy"
    address = "123 Test St"
    phone = "+1234567890"
    email = "test@pharmacy.com"
    gst = "GST123"
    lic = "LIC123"
    website = "www.testpharmacy.com"
    success, msg = save_pharmacy_details(name, address, phone, email, gst, lic, website)
    assert success
    details = get_pharmacy_details()
    assert details.name == name
    assert details.address == address
    assert details.phone == phone
    assert details.email == email
    assert details.gst_number == gst
    assert details.license_number == lic
    assert details.website == website 