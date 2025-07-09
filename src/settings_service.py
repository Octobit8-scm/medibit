from typing import Any, Dict, Optional
from db import get_pharmacy_details, save_pharmacy_details
from config import get_theme, set_theme, get_license_key, set_license_key, get_installation_date, set_installation_date
from notifications import NotificationManager

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

    def get_pharmacy_details(self) -> Any:
        """
        Return pharmacy details object.
        :return: Pharmacy details object
        """
        return get_pharmacy_details()

    def save_pharmacy_details(self, details: Dict[str, Any]) -> bool:
        """
        Save pharmacy details.
        :param details: Dictionary with pharmacy details
        :return: True on success
        """
        return save_pharmacy_details(
            details['name'],
            details['address'],
            details['phone'],
            details['email'],
            details.get('gst_number', ''),
            details.get('license_number', ''),
            details.get('website', ''),
        )

    def get_theme(self) -> str:
        """
        Return the current theme ('light' or 'dark').
        :return: Theme string
        """
        return get_theme()

    def set_theme(self, theme: str) -> None:
        """
        Set the application theme.
        :param theme: Theme string ('light' or 'dark')
        """
        set_theme(theme)

    def get_license_key(self) -> Optional[str]:
        """
        Return the current license key, or None if not set.
        :return: License key string or None
        """
        return get_license_key()

    def set_license_key(self, key: str) -> None:
        """
        Set the license key.
        :param key: License key string
        """
        print(f"[DEBUG] set_license_key called with: {key}")
        set_license_key(key)

    def get_installation_date(self) -> Optional[str]:
        """
        Return the installation date as a string, or None if not set.
        :return: Installation date string or None
        """
        return get_installation_date()

    def set_installation_date(self, date_str: str) -> None:
        """
        Set the installation date.
        :param date_str: Installation date string
        """
        set_installation_date(date_str)

    def get_notification_settings(self) -> dict:
        """
        Return notification settings from NotificationManager.
        :return: Notification settings dict
        """
        notif = NotificationManager()
        return notif.config

    def save_notification_settings(self, config: dict) -> None:
        """
        Save notification settings to NotificationManager.
        :param config: Notification settings dict
        """
        notif = NotificationManager()
        notif.config = config
        notif.save_config()

    def set_accent_color(self, color: str) -> None:
        """
        Set the accent color for the application.
        :param color: Color string (e.g., '#1976d2')
        """
        if set_accent_color:
            set_accent_color(color)
        else:
            # Fallback: store in-memory (not persistent)
            self._accent_color = color

    def set_gradient(self, gradient: str) -> None:
        """
        Set the background gradient for the application.
        :param gradient: Gradient name string
        """
        if set_gradient:
            set_gradient(gradient)
        else:
            # Fallback: store in-memory (not persistent)
            self._gradient = gradient 