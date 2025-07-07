from datetime import datetime, timedelta

import license_utils


def test_license_key_generation_and_validation():
    customer = "Test User"
    expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    key = license_utils.generate_license_key(customer, expiry)
    print(f"Generated key: {key}")
    valid, info, err = license_utils.verify_license_key(key)
    print(f"Verification result: valid={valid}, info={info}, err={err}")
    assert valid
    assert info["name"] == customer
    assert info["exp"] == expiry
