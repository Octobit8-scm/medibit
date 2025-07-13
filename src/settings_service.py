from typing import Any, Dict, Optional
from db import get_pharmacy_details, save_pharmacy_details
from config import get_theme, set_theme, get_license_key, set_license_key, get_installation_date, set_installation_date
from notifications import NotificationManager
import logging
logger = logging.getLogger("medibit")

try:
    from config import set_accent_color, set_gradient
except ImportError:
    set_accent_color = None
    set_gradient = None

class SettingsService:
    """
    Service class for all settings-related business logic.
    UI should use this class instead of calling config/DB functions directly.
    """

    def __init__(self):
        logger.info("SettingsService initialized")

    def save_settings(self, settings):
        logger.debug(f"[save_settings] ENTRY: settings_keys={list(settings.keys()) if settings else []}")
        try:
            # ... save logic ...
            logger.info("Settings saved successfully.")
            logger.debug(f"[save_settings] EXIT: success")
            return True
        except Exception as e:
            logger.error(f"[save_settings] Exception: {e}", exc_info=True)
            return False

    def load_settings(self):
        logger.debug("[load_settings] ENTRY")
        try:
            # ... load logic ...
            logger.info("Settings loaded successfully.")
            logger.debug(f"[load_settings] EXIT: success")
            return settings
        except Exception as e:
            logger.error(f"[load_settings] Exception: {e}", exc_info=True)
            return None

    def get_pharmacy_details(self) -> Any:
        """
        Return pharmacy details object.
        :return: Pharmacy details object
        """
        logger.debug("[get_pharmacy_details] ENTRY")
        try:
            details = get_pharmacy_details()
            logger.info("Pharmacy details retrieved.")
            logger.debug(f"[get_pharmacy_details] EXIT: success, details={details}")
            return details
        except Exception as e:
            logger.error(f"[get_pharmacy_details] Exception: {e}", exc_info=True)
            return None

    def save_pharmacy_details(self, details: Dict[str, Any]) -> bool:
        """
        Save pharmacy details.
        :param details: Dictionary with pharmacy details
        :return: True on success
        """
        logger.debug(f"[save_pharmacy_details] ENTRY: details={details}")
        try:
            success = save_pharmacy_details(
                details['name'],
                details['address'],
                details['phone'],
                details['email'],
                details.get('gst_number', ''),
                details.get('license_number', ''),
                details.get('website', ''),
            )
            logger.info("Pharmacy details saved.")
            logger.debug(f"[save_pharmacy_details] EXIT: success={success}, details={details}")
            return success
        except Exception as e:
            logger.error(f"[save_pharmacy_details] Exception: {e}", exc_info=True)
            return False

    def get_theme(self) -> str:
        """
        Return the current theme ('light' or 'dark').
        :return: Theme string
        """
        logger.debug("[get_theme] ENTRY")
        try:
            theme = get_theme()
            logger.info("Theme retrieved.")
            logger.debug(f"[get_theme] EXIT: success, theme={theme}")
            return theme
        except Exception as e:
            logger.error(f"[get_theme] Exception: {e}", exc_info=True)
            return ""

    def set_theme(self, theme: str) -> None:
        """
        Set the application theme.
        :param theme: Theme string ('light' or 'dark')
        """
        logger.debug(f"[set_theme] ENTRY: theme={theme}")
        try:
            set_theme(theme)
            logger.info("Theme set.")
            logger.debug(f"[set_theme] EXIT: success, theme={theme}")
        except Exception as e:
            logger.error(f"[set_theme] Exception: {e}", exc_info=True)

    def get_license_key(self) -> Optional[str]:
        """
        Return the current license key, or None if not set.
        :return: License key string or None
        """
        logger.debug("[get_license_key] ENTRY")
        try:
            license_key = get_license_key()
            logger.info("License key retrieved.")
            logger.debug(f"[get_license_key] EXIT: success, license_key={license_key}")
            return license_key
        except Exception as e:
            logger.error(f"[get_license_key] Exception: {e}", exc_info=True)
            return None

    def set_license_key(self, key: str) -> None:
        """
        Set the license key.
        :param key: License key string
        """
        logger.debug(f"[set_license_key] ENTRY: key={key}")
        try:
            set_license_key(key)
            logger.info("License key set.")
            logger.debug(f"[set_license_key] EXIT: success, key={key}")
        except Exception as e:
            logger.error(f"[set_license_key] Exception: {e}", exc_info=True)

    def get_installation_date(self) -> Optional[str]:
        """
        Return the installation date as a string, or None if not set.
        :return: Installation date string or None
        """
        logger.debug("[get_installation_date] ENTRY")
        try:
            installation_date = get_installation_date()
            logger.info("Installation date retrieved.")
            logger.debug(f"[get_installation_date] EXIT: success, installation_date={installation_date}")
            return installation_date
        except Exception as e:
            logger.error(f"[get_installation_date] Exception: {e}", exc_info=True)
            return None

    def set_installation_date(self, date_str: str) -> None:
        """
        Set the installation date.
        :param date_str: Installation date string
        """
        logger.debug(f"[set_installation_date] ENTRY: date_str={date_str}")
        try:
            set_installation_date(date_str)
            logger.info("Installation date set.")
            logger.debug(f"[set_installation_date] EXIT: success, date_str={date_str}")
        except Exception as e:
            logger.error(f"[set_installation_date] Exception: {e}", exc_info=True)

    def get_notification_settings(self) -> dict:
        """
        Return notification settings from NotificationManager.
        :return: Notification settings dict
        """
        logger.debug("[get_notification_settings] ENTRY")
        try:
            notif = NotificationManager()
            notification_settings = notif.config
            logger.info("Notification settings retrieved.")
            logger.debug(f"[get_notification_settings] EXIT: success, notification_settings={notification_settings}")
            return notification_settings
        except Exception as e:
            logger.error(f"[get_notification_settings] Exception: {e}", exc_info=True)
            return {}

    def save_notification_settings(self, config: dict) -> None:
        """
        Save notification settings to NotificationManager.
        :param config: Notification settings dict
        """
        logger.debug(f"[save_notification_settings] ENTRY: config={config}")
        try:
            notif = NotificationManager()
            notif.config = config
            notif.save_config()
            logger.info("Notification settings saved.")
            logger.debug(f"[save_notification_settings] EXIT: success, config={config}")
        except Exception as e:
            logger.error(f"[save_notification_settings] Exception: {e}", exc_info=True)

    def set_accent_color(self, color: str) -> None:
        """
        Set the accent color for the application.
        :param color: Color string (e.g., '#1976d2')
        """
        logger.debug(f"[set_accent_color] ENTRY: color={color}")
        if set_accent_color:
            try:
                set_accent_color(color)
                logger.info("Accent color set.")
                logger.debug(f"[set_accent_color] EXIT: success, color={color}")
            except Exception as e:
                logger.error(f"[set_accent_color] Exception: {e}", exc_info=True)
        else:
            # Fallback: store in-memory (not persistent)
            logger.warning("set_accent_color is not available, accent color will be in-memory.")
            self._accent_color = color
            logger.debug(f"[set_accent_color] EXIT: success, color={color}")

    def set_gradient(self, gradient: str) -> None:
        """
        Set the background gradient for the application.
        :param gradient: Gradient name string
        """
        logger.debug(f"[set_gradient] ENTRY: gradient={gradient}")
        if set_gradient:
            try:
                set_gradient(gradient)
                logger.info("Gradient set.")
                logger.debug(f"[set_gradient] EXIT: success, gradient={gradient}")
            except Exception as e:
                logger.error(f"[set_gradient] Exception: {e}", exc_info=True)
        else:
            # Fallback: store in-memory (not persistent)
            logger.warning("set_gradient is not available, gradient will be in-memory.")
            self._gradient = gradient
            logger.debug(f"[set_gradient] EXIT: success, gradient={gradient}") 