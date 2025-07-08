import pytest
from src.settings_service import SettingsService
from src.db import save_pharmacy_details, get_pharmacy_details


def test_theme_and_license():
    service = SettingsService()
    service.set_theme('dark')
    assert service.get_theme() == 'dark'
    service.set_license_key('TESTKEY')
    assert service.get_license_key() == 'TESTKEY'
    service.set_installation_date('2024-01-01')
    assert service.get_installation_date() == '2024-01-01'

def test_pharmacy_details():
    service = SettingsService()
    details = {
        'name': 'PharmTest',
        'address': 'Addr',
        'phone': '123',
        'email': 'test@pharm.com',
        'gst_number': 'GST',
        'license_number': 'LIC',
        'website': 'www.test.com',
    }
    service.save_pharmacy_details(details)
    pd = service.get_pharmacy_details()
    assert pd.name == 'PharmTest'
    assert pd.address == 'Addr'
    assert pd.phone == '123'
    assert pd.email == 'test@pharm.com'
    assert pd.gst_number == 'GST'
    assert pd.license_number == 'LIC'
    assert pd.website == 'www.test.com'

def test_notification_settings():
    service = SettingsService()
    config = service.get_notification_settings()
    config['email']['enabled'] = True
    service.save_notification_settings(config)
    new_config = service.get_notification_settings()
    assert new_config['email']['enabled'] is True 