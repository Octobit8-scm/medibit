from notifications import NotificationManager

def test_notification_config_load_and_save():
    notif = NotificationManager()
    notif.update_config("email", "enabled", True)
    assert notif.config["email"]["enabled"] is True 