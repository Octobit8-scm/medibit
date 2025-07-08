import json
import logging
import os
from logging.handlers import RotatingFileHandler

# Set config directory at project root
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_THRESHOLD = 10

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
config_logger = logging.getLogger("medibit.config")


def get_threshold() -> float:
    """
    Get the current low stock threshold.

    Returns:
        float: The current low stock threshold.
    """
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_THRESHOLD
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("low_stock_threshold", DEFAULT_THRESHOLD)
    except json.JSONDecodeError as e:
        config_logger.error(f"Failed to decode config JSON in get_threshold: {e}")
        return DEFAULT_THRESHOLD
    except Exception as e:
        config_logger.error(f"Failed to read config in get_threshold: {e}")
        return DEFAULT_THRESHOLD


def set_threshold(value: float):
    """
    Set the low stock threshold.

    Args:
        value (float): The new low stock threshold.
    """
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            config_logger.error(f"Failed to read config in set_threshold: {e}")
            data = {}
    data["low_stock_threshold"] = value
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        config_logger.error(f"Failed to write config in set_threshold: {e}")


def get_theme() -> str:
    """
    Get the current theme.

    Returns:
        str: The current theme.
    """
    if not os.path.exists(CONFIG_FILE):
        return "light"
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("theme", "light")
    except json.JSONDecodeError as e:
        config_logger.error(f"Failed to decode config JSON in get_theme: {e}")
        return "light"
    except Exception as e:
        config_logger.error(f"Failed to read config in get_theme: {e}")
        return "light"


def set_theme(theme: str):
    """
    Set the theme.

    Args:
        theme (str): The new theme.
    """
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            config_logger.error(f"Failed to read config in set_theme: {e}")
            data = {}
    data["theme"] = theme
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        config_logger.error(f"Failed to write config in set_theme: {e}")


def get_license_key() -> str:
    """
    Get the current license key.

    Returns:
        str: The current license key.
    """
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("license_key")
    except json.JSONDecodeError as e:
        config_logger.error(f"Failed to decode config JSON in get_license_key: {e}")
        return None
    except Exception as e:
        config_logger.error(f"Failed to read config in get_license_key: {e}")
        return None


def set_license_key(key: str):
    """
    Set the license key.

    Args:
        key (str): The new license key.
    """
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            config_logger.error(f"Failed to read config in set_license_key: {e}")
            data = {}
    data["license_key"] = key
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        config_logger.error(f"Failed to write config in set_license_key: {e}")


def get_installation_date() -> str:
    """
    Get the installation date.

    Returns:
        str: The installation date.
    """
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        return data.get("installation_date")
    except json.JSONDecodeError as e:
        config_logger.error(f"Failed to decode config JSON in get_installation_date: {e}")
        return None
    except Exception as e:
        config_logger.error(f"Failed to read config in get_installation_date: {e}")
        return None


def set_installation_date(date_str: str):
    """
    Set the installation date.

    Args:
        date_str (str): The new installation date.
    """
    data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
        except Exception as e:
            config_logger.error(f"Failed to read config in set_installation_date: {e}")
            data = {}
    data["installation_date"] = date_str
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        config_logger.error(f"Failed to write config in set_installation_date: {e}")
