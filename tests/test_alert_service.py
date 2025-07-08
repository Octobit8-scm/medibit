import pytest
from src.alert_service import AlertService
from unittest.mock import patch


def test_get_low_stock():
    service = AlertService()
    meds = service.get_low_stock()
    assert isinstance(meds, list)

@patch('src.notifications.NotificationManager.send_email_alert', return_value=(True, 'Email sent'))
@patch('src.notifications.NotificationManager.send_whatsapp_alert', return_value=(True, 'WhatsApp sent'))
@patch('src.notifications.NotificationManager.send_sms_alert', return_value=(True, 'SMS sent'))
def test_send_all_alerts(mock_sms, mock_whatsapp, mock_email):
    service = AlertService()
    success, msg = service.send_all_alerts()
    assert isinstance(success, bool)
    assert isinstance(msg, str) 