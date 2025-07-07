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

log_dir = os.path.join(os.getcwd(), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
order_logger = logging.getLogger("medibit.order")


class OrderManager:
    def __init__(self):
        self.config_file = "notification_config.json"
        self.load_config()

    def load_config(self):
        """Load notification configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            except:
                self.config = {
                    "email": {"enabled": False},
                    "whatsapp": {"enabled": False},
                }
        else:
            self.config = {"email": {"enabled": False}, "whatsapp": {"enabled": False}}

    def generate_pdf_order(self, order_items, order_id, timestamp, supplier_info=None):
        """Generate a professional PDF order"""

        # Create orders directory
        orders_dir = os.path.join(os.getcwd(), "orders")
        os.makedirs(orders_dir, exist_ok=True)

        # Generate filename
        filename = f"order_{order_id}_{timestamp.replace(':','-').replace(' ','_')}.pdf"
        filepath = os.path.join(orders_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Get pharmacy details
        try:
            from db import get_pharmacy_details

            pharmacy_details = get_pharmacy_details()
            print(f"Pharmacy details in order generation: {pharmacy_details}")
        except Exception as e:
            print(f"Error getting pharmacy details in order: {e}")
            pharmacy_details = None

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor("#1976d2"),
        )

        # Use pharmacy name if available, otherwise use default
        pharmacy_name = (
            pharmacy_details.name if pharmacy_details else "medibit Pharmacy"
        )
        title = Paragraph(pharmacy_name, title_style)
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
        subtitle = Paragraph("Purchase Order", subtitle_style)
        story.append(subtitle)

        story.append(Spacer(1, 20))

        # Pharmacy Details Section
        if pharmacy_details:
            pharmacy_data = [
                ["Pharmacy Information"],
                ["Name:", pharmacy_details.name],
                ["Address:", pharmacy_details.address],
                ["Phone:", pharmacy_details.phone],
                ["Email:", pharmacy_details.email],
            ]

            # Add optional fields if available
            if pharmacy_details.gst_number:
                pharmacy_data.append(["GST Number:", pharmacy_details.gst_number])
            if pharmacy_details.license_number:
                pharmacy_data.append(
                    ["License Number:", pharmacy_details.license_number]
                )
            if pharmacy_details.website:
                pharmacy_data.append(["Website:", pharmacy_details.website])

            pharmacy_table = Table(pharmacy_data, colWidths=[2 * inch, 4 * inch])
            pharmacy_table.setStyle(
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
            story.append(pharmacy_table)
            story.append(Spacer(1, 20))

        # Order Details
        order_data = [
            ["Order Information"],
            ["Order ID:", order_id],
            ["Date:", timestamp],
            ["Status:", "Pending"],
        ]

        order_table = Table(order_data, colWidths=[2 * inch, 4 * inch])
        order_table.setStyle(
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
        story.append(order_table)
        story.append(Spacer(1, 20))

        # Items Table
        items_data = [
            [
                "S.No",
                "Medicine Name",
                "Barcode",
                "Current Stock",
                "Order Quantity",
                "Manufacturer",
            ]
        ]

        total_quantity = 0
        for i, item in enumerate(order_items, 1):
            items_data.append(
                [
                    str(i),
                    item["name"],
                    item["barcode"],
                    str(item["quantity"]),
                    str(item["order_quantity"]),
                    item.get("manufacturer", "N/A"),
                ]
            )
            total_quantity += item["order_quantity"]

        items_table = Table(
            items_data,
            colWidths=[
                0.5 * inch,
                2 * inch,
                1.5 * inch,
                1 * inch,
                1 * inch,
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

        # Summary
        summary_style = ParagraphStyle(
            "Summary",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=20,
            alignment=2,  # Right alignment
            textColor=colors.HexColor("#1976d2"),
        )
        summary_text = (
            f"Total Items: {len(order_items)} | Total Quantity: {total_quantity}"
        )
        summary_para = Paragraph(summary_text, summary_style)
        story.append(summary_para)

        # Instructions
        instructions_style = ParagraphStyle(
            "Instructions",
            parent=styles["Normal"],
            fontSize=11,
            spaceAfter=20,
            alignment=0,  # Left alignment
            textColor=colors.HexColor("#666666"),
        )
        instructions_text = """
        <b>Instructions:</b><br/>
        • Please process this order as soon as possible<br/>
        • Ensure all medicines are within expiry date<br/>
        • Contact us for any clarifications<br/>
        • Expected delivery: Within 3-5 business days
        """
        instructions = Paragraph(instructions_text, instructions_style)
        story.append(instructions)

        # Footer
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.HexColor("#666666"),
        )

        if pharmacy_details:
            footer_text = f"""
            Thank you for your business!<br/>
            {pharmacy_details.name}<br/>
            {pharmacy_details.address}<br/>
            Phone: {pharmacy_details.phone} | Email: {pharmacy_details.email}<br/>
            This is a computer generated order.
            """
        else:
            footer_text = """
            Thank you for your business!<br/>
            medibit Pharmacy Management System<br/>
            This is a computer generated order.
            """

        footer = Paragraph(footer_text, footer_style)
        story.append(footer)

        # Build PDF
        doc.build(story)

        return filepath

    def send_order_email(self, supplier_info, pdf_path, order_items, order_id):
        """Send order via email"""
        if not self.config["email"]["enabled"]:
            return False, "Email notifications are disabled"

        if not supplier_info.get("email"):
            return False, "Supplier email not provided"

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config["email"]["sender_email"]
            msg["To"] = supplier_info["email"]
            msg["Subject"] = (
                f"Purchase Order #{order_id} - medibit Pharmacy - {datetime.now().strftime('%Y-%m-%d')}"
            )

            # Email body
            body = f"""
            Dear {supplier_info.get('name', 'Valued Supplier')},
            
            Please find attached our purchase order for the following items:
            
            Order Details:
            - Order ID: {order_id}
            - Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            - Total Items: {len(order_items)}
            - Total Quantity: {sum(item['order_quantity'] for item in order_items)}
            
            Items Required:
            """

            for item in order_items:
                body += f"- {item['name']} (Barcode: {item['barcode']}) - Qty: {item['order_quantity']}\n"

            body += f"""
            
            Please process this order as soon as possible and ensure all medicines are within expiry date.
            
            Expected delivery: Within 3-5 business days
            
            If you have any questions about this order, please don't hesitate to contact us.
            
            Best regards,
            medibit Pharmacy Team
            
            ---
            This is an automated message. Please do not reply to this email.
            """

            msg.attach(MIMEText(body, "plain"))

            # Attach PDF
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(pdf_path)}",
            )
            msg.attach(part)

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

            return True, f"Order sent to {supplier_info['email']}"

        except Exception as e:
            return False, f"Email sending failed: {str(e)}"

    def send_order_whatsapp(self, supplier_info, pdf_path, order_items, order_id):
        """Send order via WhatsApp"""
        if not self.config["whatsapp"]["enabled"]:
            return False, "WhatsApp notifications are disabled"

        if not supplier_info.get("phone"):
            return False, "Supplier phone number not provided"

        try:
            # Parse Twilio credentials
            api_key = self.config["whatsapp"]["api_key"]
            if ":" not in api_key:
                return False, "Invalid Twilio API key format"

            account_sid, auth_token = api_key.split(":", 1)

            # Create detailed order message
            message = f"""
📋 *Purchase Order #{order_id}*

Dear {supplier_info.get('name', 'Valued Supplier')},

Please find our purchase order details:

📅 *Order Information:*
• Order ID: {order_id}
• Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Total Items: {len(order_items)}
• Total Quantity: {sum(item['order_quantity'] for item in order_items)}

📦 *Items Required:*
"""

            # Add items to message
            for i, item in enumerate(order_items, 1):
                message += f"• {item['name']} - Qty: {item['order_quantity']} (Barcode: {item['barcode']})\n"

            message += f"""
📄 *PDF Order:*
Your detailed PDF order has been sent to your email address.

⏰ *Expected Delivery:* Within 3-5 business days

For any clarifications, please contact us.

Best regards,
medibit Pharmacy Team
            """

            # Send WhatsApp message
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            from_number = "whatsapp:+14155238886"  # Twilio WhatsApp sandbox
            to_number = f"whatsapp:{supplier_info['phone']}"

            text_payload = {"From": from_number, "To": to_number, "Body": message}

            response = requests.post(
                url, data=text_payload, auth=(account_sid, auth_token)
            )

            if response.status_code in [200, 201]:
                return (
                    True,
                    f"Order notification sent to {supplier_info['phone']} (detailed text + PDF via email)",
                )
            else:
                return False, f"WhatsApp failed: {response.text}"

        except Exception as e:
            return False, f"WhatsApp sending failed: {str(e)}"

    def send_order_to_supplier(self, supplier_info, order_items, order_id, timestamp):
        """Send order to supplier via all enabled channels"""
        results = []

        # Generate PDF order
        try:
            pdf_path = self.generate_pdf_order(
                order_items, order_id, timestamp, supplier_info
            )
            results.append(("PDF Generation", True, f"Order saved to: {pdf_path}"))
        except Exception as e:
            results.append(
                ("PDF Generation", False, f"Failed to generate PDF: {str(e)}")
            )
            return results

        # Send via email
        if self.config["email"]["enabled"] and supplier_info.get("email"):
            success, message = self.send_order_email(
                supplier_info, pdf_path, order_items, order_id
            )
            results.append(("Email", success, message))

        # Send via WhatsApp
        if self.config["whatsapp"]["enabled"] and supplier_info.get("phone"):
            success, message = self.send_order_whatsapp(
                supplier_info, pdf_path, order_items, order_id
            )
            results.append(("WhatsApp", success, message))

        return results
