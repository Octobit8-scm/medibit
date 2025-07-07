from src.notifications import NotificationManager


def test_send_email_alert_disabled():
    notif = NotificationManager()
    notif.update_config("email", "enabled", False)
    success, msg = notif.send_email_alert([])
    assert not success
    assert "disabled" in msg.lower()


def test_send_whatsapp_alert_disabled():
    notif = NotificationManager()
    notif.update_config("whatsapp", "enabled", False)
    success, msg = notif.send_whatsapp_alert([])
    assert not success
    assert "disabled" in msg.lower()
