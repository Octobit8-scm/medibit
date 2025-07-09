#!/usr/bin/env python3
import sys
import os
import sqlite3
from datetime import datetime
from src.license_utils import generate_license_key

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'licenses.db')

# Ensure the licenses table exists
def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        license_key TEXT NOT NULL,
        issued_at TEXT NOT NULL,
        expiry TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

def email_exists(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM licenses WHERE email = ?', (email,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def save_license(email, license_key, expiry):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO licenses (email, license_key, issued_at, expiry) VALUES (?, ?, ?, ?)',
              (email, license_key, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), expiry))
    conn.commit()
    conn.close()

def main():
    if len(sys.argv) != 3:
        print('Usage: python generate_license.py <customer_email> <expiry_date: YYYY-MM-DD>')
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    expiry = sys.argv[2].strip()
    # Basic email validation
    if '@' not in email or '.' not in email:
        print('Invalid email address.')
        sys.exit(1)
    try:
        datetime.strptime(expiry, '%Y-%m-%d')
    except ValueError:
        print('Invalid expiry date format. Use YYYY-MM-DD.')
        sys.exit(1)
    ensure_db()
    if email_exists(email):
        print(f'Error: A license has already been issued for {email}.')
        sys.exit(1)
    license_key = generate_license_key(email, expiry)
    save_license(email, license_key, expiry)
    print(f'License key for {email} (expires {expiry}):\n{license_key}')

if __name__ == '__main__':
    main() 