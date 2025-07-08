import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging.handlers import RotatingFileHandler

import requests

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
notif_logger = logging.getLogger("medibit.notifications")


class NotificationManager:
    def __init__(self):
        # Set config directory at project root
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        self.config_file = os.path.join(config_dir, "notification_config.json")
        self.load_config()

    def load_config(self):
        """Load notification configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except json.JSONDecodeError as e:
                notif_logger.error(f"Failed to decode notification config JSON: {e}")
                self.create_default_config()
            except Exception as e:
                notif_logger.error(f"Failed to read notification config: {e}")
                self.create_default_config()
        else:
            self.create_default_config()

    def create_default_config(self):
        """Create default configuration file"""
        self.config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_emails": [],
            },
            "whatsapp": {"enabled": False, "api_key": "", "phone_numbers": []},
            "sms": {"enabled": False, "api_key": "", "phone_numbers": []},
        }
        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            notif_logger.error(f"Failed to save notification config: {e}")

    def send_email_alert(self, low_stock_medicines):
        """Send email alert for low stock medicines"""
        if not self.config["email"]["enabled"]:
            return False, "Email notifications are disabled"

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config["email"]["sender_email"]
            msg["To"] = ", ".join(self.config["email"]["recipient_emails"])
            msg["Subject"] = (
                f"Low Stock Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )

            # Create email body
            body = "Low Stock Alert - medibit Pharmacy Management System\n\n"
            body += "The following medicines are running low on stock:\n\n"

            for med in low_stock_medicines:
                body += f"• {med.name} (Barcode: {med.barcode})\n"
                body += f"  Current Stock: {med.quantity}\n"
                body += f"  Manufacturer: {med.manufacturer or 'N/A'}\n\n"

            body += "\nPlease take necessary action to restock these items.\n"
            body += f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(
                self.config["email"]["smtp_server"],
                self.config["email"]["smtp_port"],
            )
            server.starttls()
            server.login(
                self.config["email"]["sender_email"],
                self.config["email"]["sender_password"],
            )

            for recipient in self.config["email"]["recipient_emails"]:
                server.send_message(msg)

            server.quit()
            return (
                True,
                f"Email alert sent to {len(self.config['email']['recipient_emails'])} recipients",
            )

        except smtplib.SMTPAuthenticationError as e:
            if "534" in str(e) and "application specific password" in str(e).lower():
                return (
                    False,
                    f"Email alert failed: Gmail requires an App Password. Please generate one at: "
                    "Google Account → Security → 2-Step Verification → App passwords",
                )
            else:
                return False, f"Email authentication failed: {str(e)}"
        except Exception as e:
            return False, f"Email alert failed: {str(e)}"

    def send_whatsapp_alert(self, low_stock_medicines):
        """Send WhatsApp alert for low stock medicines using Twilio"""
        if not self.config["whatsapp"]["enabled"]:
            return False, "WhatsApp notifications are disabled"

        try:
            # Parse Twilio credentials
            api_key = self.config["whatsapp"]["api_key"]
            if ":" not in api_key:
                return (
                    False,
                    "Invalid Twilio API key format. Use: Account SID:Auth Token",
                )

            account_sid, auth_token = api_key.split(":", 1)

            # Create message
            message = "🚨 *Low Stock Alert - medibit*\n\n"
            message += "The following medicines are running low on stock:\n\n"

            for med in low_stock_medicines:
                message += f"• *{med.name}*\n"
                message += f"  📦 Current Stock: {med.quantity}\n"
                message += f"  📋 Barcode: {med.barcode}\n"
                if med.manufacturer:
                    message += f"  🏭 Manufacturer: {med.manufacturer}\n"
                message += "\n"

            message += (
                f"\n⏰ Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Send to each phone number using Twilio WhatsApp API
            success_count = 0
            for phone in self.config["whatsapp"]["phone_numbers"]:
                try:
                    # Twilio WhatsApp API endpoint
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

                    # For WhatsApp, use the whatsapp: prefix
                    from_number = (
                        "whatsapp:+14155238886"  # Twilio WhatsApp sandbox number
                    )
                    to_number = f"whatsapp:{phone}"

                    payload = {"From": from_number, "To": to_number, "Body": message}

                    response = requests.post(
                        url, data=payload, auth=(account_sid, auth_token)
                    )

                    if response.status_code in [200, 201]:
                        success_count += 1

                except Exception as e:
                    pass

            if success_count > 0:
                return True, f"WhatsApp alert sent to {success_count} recipients"
            else:
                return False, "WhatsApp alert failed for all recipients"

        except Exception as e:
            return False, f"WhatsApp alert failed: {str(e)}"

    def send_sms_alert(self, low_stock_medicines):
        """Send SMS alert for low stock medicines using Twilio"""
        if not self.config["sms"]["enabled"]:
            return False, "SMS notifications are disabled"

        try:
            # Parse Twilio credentials
            api_key = self.config["sms"]["api_key"]
            if ":" not in api_key:
                return (
                    False,
                    "Invalid Twilio API key format. Use: Account SID:Auth Token",
                )

            account_sid, auth_token = api_key.split(":", 1)

            # Create message (SMS has character limit)
            message = "Low Stock Alert - medibit\n\n"

            # Add first few medicines (SMS has 160 character limit)
            for i, med in enumerate(
                low_stock_medicines[:3]
            ):  # Limit to first 3 medicines
                message += f"{med.name}: {med.quantity} left\n"

            if len(low_stock_medicines) > 3:
                message += f"...and {len(low_stock_medicines) - 3} more items"

            # Send to each phone number using Twilio SMS API
            success_count = 0
            for phone in self.config["sms"]["phone_numbers"]:
                try:
                    # Twilio SMS API endpoint
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

                    # You need to replace this with your actual Twilio phone number
                    from_number = (
                        "+16203178530"  # Replace with your Twilio phone number
                    )

                    payload = {"From": from_number, "To": phone, "Body": message}

                    response = requests.post(
                        url, data=payload, auth=(account_sid, auth_token)
                    )

                    if response.status_code in [200, 201]:
                        success_count += 1

                except Exception as e:
                    pass

            if success_count > 0:
                return True, f"SMS alert sent to {success_count} recipients"
            else:
                return False, "SMS alert failed for all recipients"

        except Exception as e:
            return False, f"SMS alert failed: {str(e)}"

    def send_all_alerts(self, low_stock_medicines):
        """Send alerts through all enabled channels"""
        results = []

        # Send email alert
        if self.config["email"]["enabled"]:
            success, message = self.send_email_alert(low_stock_medicines)
            results.append(("Email", success, message))

        # Send WhatsApp alert
        if self.config["whatsapp"]["enabled"]:
            success, message = self.send_whatsapp_alert(low_stock_medicines)
            results.append(("WhatsApp", success, message))

        # Send SMS alert
        if self.config["sms"]["enabled"]:
            success, message = self.send_sms_alert(low_stock_medicines)
            results.append(("SMS", success, message))

        return results

    def update_config(self, section, key, value):
        """Update configuration"""
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            self.save_config()
            return True
        return False

    def send_daily_sales_summary_email(self, sales_summary, bill_details):
        """Send daily sales summary via email to all recipients."""
        if not self.config["email"]["enabled"]:
            return False, "Email notifications are disabled"
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["email"]["sender_email"]
            msg["To"] = ", ".join(self.config["email"]["recipient_emails"])
            msg["Subject"] = (
                f"Daily Sales Summary - {datetime.now().strftime('%Y-%m-%d')}"
            )
            body = f"Daily Sales Summary for {datetime.now().strftime('%Y-%m-%d')}\n\n"
            body += f"Total Sales: ₹{sales_summary['total']:.2f}\n"
            body += f"Number of Bills: {sales_summary['count']}\n"
            body += f"Average Bill: ₹{sales_summary['avg']:.2f}\n\n"
            body += "Bill Details:\n"
            for bill in bill_details:
                body += f"- Time: {bill['time']}, Amount: ₹{bill['total']:.2f}\n"
            body += "\nThis is an automated message."
            msg.attach(MIMEText(body, "plain"))
            server = smtplib.SMTP(
                self.config["email"]["smtp_server"], self.config["email"]["smtp_port"]
            )
            server.starttls()
            server.login(
                self.config["email"]["sender_email"],
                self.config["email"]["sender_password"],
            )
            for recipient in self.config["email"]["recipient_emails"]:
                server.send_message(msg)
            server.quit()
            return (
                True,
                f"Daily sales summary sent to {len(self.config['email']['recipient_emails'])} recipients",
            )
        except Exception as e:
            return False, f"Daily sales summary email failed: {str(e)}"

    def send_daily_sales_summary_whatsapp(self, sales_summary, bill_details):
        """Send daily sales summary via WhatsApp to all configured numbers."""
        if not self.config["whatsapp"]["enabled"]:
            return False, "WhatsApp notifications are disabled"
        try:
            api_key = self.config["whatsapp"]["api_key"]
            if ":" not in api_key:
                return (
                    False,
                    "Invalid Twilio API key format. Use: Account SID:Auth Token",
                )
            account_sid, auth_token = api_key.split(":", 1)
            message = (
                f"📊 *Daily Sales Summary - {datetime.now().strftime('%Y-%m-%d')}*\n\n"
            )
            message += f"*Total Sales:* ₹{sales_summary['total']:.2f}\n"
            message += f"*Number of Bills:* {sales_summary['count']}\n"
            message += f"*Average Bill:* ₹{sales_summary['avg']:.2f}\n\n"
            message += "*Bill Details:*\n"
            for bill in bill_details:
                message += f"- Time: {bill['time']}, Amount: ₹{bill['total']:.2f}\n"
            message += "\n_Automated message from Medibit Pharmacy_"
            success_count = 0
            for phone in self.config["whatsapp"]["phone_numbers"]:
                try:
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
                    from_number = "whatsapp:+14155238886"
                    to_number = f"whatsapp:{phone}"
                    payload = {"From": from_number, "To": to_number, "Body": message}
                    response = requests.post(
                        url, data=payload, auth=(account_sid, auth_token)
                    )
                    if response.status_code in [200, 201]:
                        success_count += 1
                except Exception as e:
                    pass
            if success_count > 0:
                return (
                    True,
                    f"WhatsApp daily sales summary sent to {success_count} recipients",
                )
            else:
                return (
                    False,
                    "WhatsApp daily sales summary failed for all recipients",
                )
        except Exception as e:
            return False, f"WhatsApp daily sales summary failed: {str(e)}"
