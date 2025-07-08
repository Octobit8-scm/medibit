from typing import List, Any, Tuple
from db import get_low_stock_medicines
from notifications import NotificationManager

class AlertService:
    """
    Service class for all alert-related business logic.
    UI should use this class instead of calling DB/notification functions directly.
    """

    def get_low_stock(self) -> List[Any]:
        """
        Return all medicines that are low in stock.
        :return: List of medicine objects
        """
        return get_low_stock_medicines()

    def send_all_alerts(self) -> Tuple[bool, str]:
        """
        Send low stock alerts via all enabled channels.
        :return: (success, message)
        """
        low_stock = self.get_low_stock()
        if not low_stock:
            return False, "No low stock medicines."
        notif = NotificationManager()
        email_success, email_msg = notif.send_email_alert(low_stock)
        whatsapp_success, whatsapp_msg = notif.send_whatsapp_alert(low_stock)
        sms_success, sms_msg = notif.send_sms_alert(low_stock)
        if email_success or whatsapp_success or sms_success:
            return True, f"Email: {email_msg}\nWhatsApp: {whatsapp_msg}\nSMS: {sms_msg}"
        else:
            return False, f"Email: {email_msg}\nWhatsApp: {whatsapp_msg}\nSMS: {sms_msg}" 