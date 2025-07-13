import pytest
from src.notifications import NotificationManager
from unittest.mock import patch, MagicMock
import logging
import sys
import os

# For UI tests
from PyQt5.QtWidgets import QApplication
import pytestqt
from src.dialogs import NotificationSettingsDialog

@pytest.fixture
def notif_manager():
    notif = NotificationManager()
    notif.config['email'].update({
        'enabled': True,
        'smtp_server': 'smtp.test.com',
        'smtp_port': 587,
        'sender_email': 'test@test.com',
        'sender_password': 'pass',
        'recipient_emails': ['a@test.com', 'b@test.com']
    })
    notif.config['whatsapp'].update({
        'enabled': True,
        'api_key': 'sid:token',
        'phone_numbers': ['+1234567890']
    })
    notif.config['sms'].update({
        'enabled': True,
        'api_key': 'sid:token',
        'phone_numbers': ['+1234567890']
    })
    return notif

def test_notification_config_load_and_save():
    notif = NotificationManager()
    notif.update_config("email", "enabled", True)
    assert notif.config["email"]["enabled"] is True

@patch('smtplib.SMTP')
@patch('requests.post')
def test_send_all_alerts_success(mock_post, mock_smtp, notif_manager, caplog):
    # Mock SMTP
    smtp_instance = MagicMock()
    mock_smtp.return_value = smtp_instance
    # Mock requests
    mock_post.return_value.status_code = 200
    # Dummy medicine
    class DummyMed:
        name = 'TestMed'
        barcode = '123'
        quantity = 5
        manufacturer = 'TestManu'
    meds = [DummyMed()]
    with caplog.at_level(logging.INFO):
        results = notif_manager.send_all_alerts(meds)
        assert all(success for _, success, _ in results)
        # Check audit log entries
        assert any('[Audit] Email:' in r for r in caplog.text.splitlines())
        assert any('[Audit] WhatsApp:' in r for r in caplog.text.splitlines())
        assert any('[Audit] SMS:' in r for r in caplog.text.splitlines())

@patch('smtplib.SMTP', side_effect=Exception('SMTP error'))
@patch('requests.post', side_effect=Exception('Network error'))
def test_send_all_alerts_failure(mock_post, mock_smtp, notif_manager, caplog):
    class DummyMed:
        name = 'TestMed'
        barcode = '123'
        quantity = 5
        manufacturer = 'TestManu'
    meds = [DummyMed()]
    notif_manager.config['email']['enabled'] = True
    notif_manager.config['whatsapp']['enabled'] = True
    notif_manager.config['sms']['enabled'] = True
    with caplog.at_level(logging.ERROR):
        results = notif_manager.send_all_alerts(meds)
        assert all(not success for _, success, _ in results)
        assert 'SMTP error' in caplog.text or 'Network error' in caplog.text

@patch('smtplib.SMTP')
def test_send_email_disabled(mock_smtp, notif_manager, caplog):
    notif_manager.config['email']['enabled'] = False
    class DummyMed:
        name = 'TestMed'
        barcode = '123'
        quantity = 5
        manufacturer = 'TestManu'
    meds = [DummyMed()]
    with caplog.at_level(logging.INFO):
        success, msg = notif_manager.send_email_alert(meds)
        assert not success
        assert 'disabled' in msg
        assert '[Email] Attempted to send but email notifications are disabled' in caplog.text

@pytest.mark.skipif('pytestqt' not in sys.modules, reason='pytest-qt not available')
def test_notification_settings_dialog_ui_feedback(qtbot, monkeypatch):
    app = QApplication.instance() or QApplication([])
    dialog = NotificationSettingsDialog()
    # Patch NotificationSendWorker to immediately emit result
    class FakeWorker:
        def __init__(self, *a, **k): pass
        def start(self):
            dialog.on_test_notifications_result([
                ('Email', True, 'ok'),
                ('WhatsApp', True, 'ok'),
                ('SMS', True, 'ok')
            ])
            dialog.on_test_notifications_finished()
    monkeypatch.setattr('src.dialogs.NotificationSendWorker', FakeWorker)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.mouseClick(dialog.test_btn, Qt.LeftButton)
    qtbot.wait(100)
    assert 'successfully' in dialog.status_label.text().lower()
    # Simulate failure
    class FakeWorkerFail:
        def __init__(self, *a, **k): pass
        def start(self):
            dialog.on_test_notifications_result([
                ('Email', False, 'fail'),
                ('WhatsApp', False, 'fail'),
                ('SMS', False, 'fail')
            ])
            dialog.on_test_notifications_finished()
    monkeypatch.setattr('src.dialogs.NotificationSendWorker', FakeWorkerFail)
    qtbot.mouseClick(dialog.test_btn, Qt.LeftButton)
    qtbot.wait(100)
    assert 'failed' in dialog.status_label.text().lower()
