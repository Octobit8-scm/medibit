from typing import List, Any, Tuple
from db import get_low_stock_medicines
from notifications import NotificationManager
import logging
logger = logging.getLogger("medibit")

class AlertService:
    """
    Service class for all alert-related business logic.
    UI should use this class instead of calling DB/notification functions directly.
    """

    def __init__(self):
        logger.info("AlertService initialized")

    def get_low_stock(self) -> List[Any]:
        """
        Return all medicines that are low in stock.
        :return: List of medicine objects
        """
        return get_low_stock_medicines()

    def send_alerts(self, alert_data):
        logger.debug(f"[send_alerts] ENTRY: alert_count={len(alert_data) if alert_data else 0}")
        try:
            low_stock = self.get_low_stock()
            if not low_stock:
                logger.info("No low stock alerts to send.")
                return True, "No alerts needed."
            notif = NotificationManager()
            email_success, email_msg = notif.send_email_alert(low_stock)
            whatsapp_success, whatsapp_msg = notif.send_whatsapp_alert(low_stock)
            sms_success, sms_msg = notif.send_sms_alert(low_stock)
            if email_success or whatsapp_success or sms_success:
                logger.info("Alerts sent successfully.")
                logger.debug(f"[send_alerts] EXIT: success")
                return True, "Alerts sent"
            else:
                logger.error("Alerts sending failed.")
                return False, f"Email: {email_msg}\nWhatsApp: {whatsapp_msg}\nSMS: {sms_msg}"
        except Exception as e:
            logger.error(f"[send_alerts] Exception: {e}", exc_info=True)
            return False, str(e)

    def send_all_alerts(self):
        """Send all alerts using NotificationManager"""
        notif = NotificationManager()
        low_stock = self.get_low_stock()
        results = notif.send_all_alerts(low_stock)
        # Aggregate results into a summary string and overall success
        if not results:
            return True, "No alert channels enabled."
        success = any(r[1] for r in results)
        summary = "\n".join([f"{r[0]}: {'Success' if r[1] else 'Failed'} - {r[2]}" for r in results])
        return success, summary 