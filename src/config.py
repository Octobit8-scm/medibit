import json
import logging
import os
from logging.handlers import RotatingFileHandler

CONFIG_FILE = "config.json"
DEFAULT_THRESHOLD = 10

log_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
config_logger = logging.getLogger("medibit.config")


def get_threshold():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_THRESHOLD
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data.get("low_stock_threshold", DEFAULT_THRESHOLD)


def set_threshold(value):
    data = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    data["low_stock_threshold"] = value
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def get_theme():
    if not os.path.exists(CONFIG_FILE):
        return "light"
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data.get("theme", "light")


def set_theme(theme):
    data = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    data["theme"] = theme
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def get_license_key():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data.get("license_key")


def set_license_key(key):
    data = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    data["license_key"] = key
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)


def get_installation_date():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data.get("installation_date")


def set_installation_date(date_str):
    data = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
    data["installation_date"] = date_str
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)
