import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta

# CHANGE THIS SECRET KEY and keep it private!
SECRET_KEY = (
    b"medibit-2024-very-secret-key"  # Use a strong, private key in production
)


def generate_license_key(customer_name, expiry_date):
    """
    Generate a license key for a customer.
    :param customer_name: str, e.g. 'John Doe'
    :param expiry_date: str, 'YYYY-MM-DD'
    :return: license key string
    """
    data = {"name": customer_name, "exp": expiry_date}
    data_json = json.dumps(data, separators=(",", ":"))
    data_b64 = base64.urlsafe_b64encode(data_json.encode()).decode()
    signature = hmac.new(
        SECRET_KEY, data_b64.encode(), hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode()
    return f"{data_b64}.{sig_b64}"


def verify_license_key(license_key):
    """
    Verify a license key and return (valid, data, error_message)
    :param license_key: str
    :return: (bool, dict or None, str or None)
    """
    try:
        data_b64, sig_b64 = license_key.split(".")
        data_json = base64.urlsafe_b64decode(data_b64.encode()).decode()
        data = json.loads(data_json)
        expected_sig = hmac.new(
            SECRET_KEY, data_b64.encode(), hashlib.sha256
        ).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64.encode())
        if not hmac.compare_digest(expected_sig, actual_sig):
            return False, None, "Invalid signature"
        # Check expiry
        exp = data.get("exp")
        if not exp:
            return False, None, "No expiry in license"
        exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
        if datetime.now().date() > exp_date:
            return False, data, "License expired"
        return True, data, None
    except Exception as e:
        return False, None, f"Invalid license format: {e}"


if __name__ == "__main__":
    # Example: generate a license for John Doe, valid for 1 year from today
    name = "John Doe"
    expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    key = generate_license_key(name, expiry)
    print("Generated license key:", key)
    # Example: verify
    valid, data, err = verify_license_key(key)
    print("Valid:", valid, "Data:", data, "Error:", err)
