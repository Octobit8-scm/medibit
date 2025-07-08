import json
import logging
import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging.handlers import RotatingFileHandler

import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
receipt_logger = logging.getLogger("medibit.receipt")


class ReceiptManager:
    def __init__(self):
        # Set config directory at project root
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        self.config_file = os.path.join(config_dir, "notification_config.json")
        self.load_config()

    def load_config(self):
        """Load notification configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except json.JSONDecodeError as e:
                receipt_logger.error(f"Failed to decode receipt config JSON: {e}")
                self.config = {"email": {"enabled": False}, "whatsapp": {"enabled": False}}
            except Exception as e:
                receipt_logger.error(f"Failed to read receipt config: {e}")
                self.config = {"email": {"enabled": False}, "whatsapp": {"enabled": False}}
        else:
            self.config = {"email": {"enabled": False}, "whatsapp": {"enabled": False}}

    def generate_pdf_receipt(self, customer_info, items, total, timestamp, receipt_id):
        """Generate a professional PDF receipt"""

        # Create receipts directory
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "receipts")
        os.makedirs(receipts_dir, exist_ok=True)

        # Fix filename construction for datetime
        if isinstance(timestamp, str):
            ts_str = timestamp.replace(":", "-").replace(" ", "_")
        else:
            ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"receipt_{receipt_id}_{ts_str}.pdf"
        filepath = os.path.join(receipts_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor("#1976d2"),
        )
        title = Paragraph("medibit Pharmacy", title_style)
        story.append(title)

        # Subtitle
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Heading2"],
            fontSize=16,
            spaceAfter=20,
            alignment=1,
            textColor=colors.HexColor("#666666"),
        )
        subtitle = Paragraph("Digital Receipt", subtitle_style)
        story.append(subtitle)

        story.append(Spacer(1, 20))

        # Customer Information
        if customer_info:
            customer_data = [
                ["Customer Information"],
                ["Name:", customer_info.get("name", "N/A")],
                ["Phone:", customer_info.get("phone", "N/A")],
                ["Email:", customer_info.get("email", "N/A")],
            ]

            customer_table = Table(customer_data, colWidths=[2 * inch, 4 * inch])
            customer_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1976d2")),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dddddd")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            story.append(customer_table)
            story.append(Spacer(1, 20))

        # Receipt Details
        receipt_data = [
            ["Receipt ID:", receipt_id],
            ["Date:", timestamp],
            ["Payment Method:", "Cash/Card"],
        ]

        receipt_table = Table(receipt_data, colWidths=[2 * inch, 4 * inch])
        receipt_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f5f5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1976d2")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dddddd")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(receipt_table)
        story.append(Spacer(1, 20))

        # Items Table
        items_data = [
            ["S.No", "Medicine Name", "Barcode", "Price (₹)", "Qty", "Subtotal (₹)"]
        ]

        for i, item in enumerate(items, 1):
            try:
                items_data.append(
                    [
                        str(i),
                        item.get("name", "N/A"),
                        item.get("barcode", "N/A"),
                        f"{float(item.get('price', 0)):.2f}",
                        str(item.get("quantity", 0)),
                        f"{float(item.get('subtotal', 0)):.2f}",
                    ]
                )
            except Exception as e:
                items_data.append([str(i), "ERROR", "ERROR", "0.00", "0", "0.00"])

        items_table = Table(
            items_data,
            colWidths=[
                0.5 * inch,
                2 * inch,
                1.5 * inch,
                1 * inch,
                0.5 * inch,
                1.5 * inch,
            ],
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1976d2")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#dddddd")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 20))

        # Total
        total_style = ParagraphStyle(
            "Total",
            parent=styles["Heading2"],
            fontSize=16,
            spaceAfter=20,
            alignment=2,  # Right alignment
            textColor=colors.HexColor("#1976d2"),
        )
        total_text = f"Total Amount: ₹{total/100:.2f}"
        total_para = Paragraph(total_text, total_style)
        story.append(total_para)

        # Footer
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.HexColor("#666666"),
        )
        footer_text = """
        Thank you for choosing medibit Pharmacy!<br/>
        For any queries, please contact us.<br/>
        This is a computer generated receipt.
        """
        footer = Paragraph(footer_text, footer_style)
        story.append(footer)

        # Build PDF
        doc.build(story)

        return filepath

    def send_receipt_email(self, customer_info, pdf_path):
        """Send receipt via email"""
        if not self.config["email"]["enabled"]:
            return False, "Email notifications are disabled"

        if not customer_info.get("email"):
            return False, "Customer email not provided"

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config["email"]["sender_email"]
            msg["To"] = customer_info["email"]
            msg["Subject"] = (
                f"Your medibit Pharmacy Receipt - {datetime.now().strftime('%Y-%m-%d')}"
            )

            # Email body
            body = f"""
            Dear {customer_info.get('name', 'Valued Customer')},
            
            Thank you for your purchase at medibit Pharmacy!
            
            Please find your receipt attached to this email.
            
            Receipt Details:
            - Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            - Total Amount: ₹{customer_info.get('total', 'N/A')}
            
            If you have any questions about your purchase, please don't hesitate to contact us.
            
            Best regards,
            medibit Pharmacy Team
            
            ---
            This is an automated message. Please do not reply to this email.
            """

            msg.attach(MIMEText(body, "plain"))

            # Attach PDF
            try:
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=receipt_{customer_info.get('name', 'customer')}.pdf",
                )
                msg.attach(part)
            except Exception as e:
                receipt_logger.error(f"Failed to attach PDF to receipt email: {e}")
                return False, f"Failed to attach PDF: {e}"

            # Send email
            server = smtplib.SMTP(
                self.config["email"]["smtp_server"], self.config["email"]["smtp_port"]
            )
            server.starttls()
            server.login(
                self.config["email"]["sender_email"],
                self.config["email"]["sender_password"],
            )
            server.send_message(msg)
            server.quit()

            return True, f"Receipt sent to {customer_info['email']}"

        except Exception as e:
            return False, f"Email sending failed: {str(e)}"

    def send_receipt_whatsapp(self, customer_info, pdf_path):
        """Send receipt via WhatsApp"""
        if not self.config["whatsapp"]["enabled"]:
            return False, "WhatsApp notifications are disabled"

        if not customer_info.get("phone"):
            return False, "Customer phone number not provided"

        try:
            # Parse Twilio credentials
            api_key = self.config["whatsapp"]["api_key"]
            if ":" not in api_key:
                return False, "Invalid Twilio API key format"

            account_sid, auth_token = api_key.split(":", 1)

            # Create detailed receipt message (since PDF attachment is limited)
            message = f"""
🧾 *medibit Pharmacy Receipt*

Dear {customer_info.get('name', 'Valued Customer')},

Thank you for your purchase! Here's your receipt:

📋 *Receipt Details:*
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Total Amount: ₹{customer_info.get('total', 'N/A')}

📄 *Items Purchased:*
"""

            # Add items to message
            for i, item in enumerate(customer_info.get("items", []), 1):
                message += f"• {item['name']} - ₹{item['price']:.2f} x {item['quantity']} = ₹{item['subtotal']:.2f}\n"

            message += f"""
💳 *Payment Summary:*
• Subtotal: ₹{customer_info.get('total', 'N/A')}
• Tax: ₹0.00
• Total: ₹{customer_info.get('total', 'N/A')}

📧 *PDF Receipt:*
Your detailed PDF receipt has been sent to your email address.

For any queries, please contact us.

Best regards,
medibit Pharmacy Team
            """

            # Send WhatsApp message
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            from_number = "whatsapp:+14155238886"  # Twilio WhatsApp sandbox
            to_number = f"whatsapp:{customer_info['phone']}"

            text_payload = {"From": from_number, "To": to_number, "Body": message}

            response = requests.post(
                url, data=text_payload, auth=(account_sid, auth_token)
            )

            if response.status_code in [200, 201]:
                return (
                    True,
                    f"WhatsApp receipt sent to {customer_info['phone']} (detailed text + PDF via email)",
                )
            else:
                return False, f"WhatsApp failed: {response.text}"

        except Exception as e:
            return False, f"WhatsApp sending failed: {str(e)}"

    def send_receipt_to_customer(
        self, customer_info, items, total, timestamp, receipt_id
    ):
        """Send receipt to customer via all enabled channels"""
        results = []

        # Generate PDF receipt
        try:
            pdf_path = self.generate_pdf_receipt(
                customer_info, items, total, timestamp, receipt_id
            )
            results.append(("PDF Generation", True, f"Receipt saved to: {pdf_path}"))
        except Exception as e:
            results.append(
                ("PDF Generation", False, f"Failed to generate PDF: {str(e)}")
            )
            return results

        # Send via email
        if self.config["email"]["enabled"] and customer_info.get("email"):
            success, message = self.send_receipt_email(customer_info, pdf_path)
            results.append(("Email", success, message))

        # Send via WhatsApp
        if self.config["whatsapp"]["enabled"] and customer_info.get("phone"):
            success, message = self.send_receipt_whatsapp(customer_info, pdf_path)
            results.append(("WhatsApp", success, message))

        return results
