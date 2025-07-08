from typing import List, Dict, Any, Tuple, Optional
from db import add_bill, get_all_bills, get_monthly_sales, get_medicine_by_barcode, update_medicine_quantity
import datetime
import os

class BillingService:
    """
    Service class for all billing-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def create_bill(self, items: List[Dict[str, Any]], customer: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Create and save a new bill. Updates medicine quantities.
        :param items: List of item dicts (each with barcode, name, quantity, price, subtotal)
        :param customer: Customer info dict
        :return: (success, error message, bill_id)
        """
        total = sum(item["quantity"] * item["price"] for item in items)
        timestamp = datetime.datetime.now()
        try:
            bill_id = add_bill(timestamp, total, items)
            for item in items:
                medicine = get_medicine_by_barcode(item["barcode"])
                if medicine:
                    new_quantity = medicine.quantity - item["quantity"]
                    if new_quantity < 0:
                        new_quantity = 0
                    update_medicine_quantity(item["barcode"], new_quantity)
            return True, None, bill_id
        except Exception as e:
            return False, str(e), None

    def get_recent_bills(self, limit: int = 10) -> List[Any]:
        """
        Return the most recent bills, up to the specified limit.
        :param limit: Number of bills to return
        :return: List of bill objects
        """
        bills = get_all_bills()
        return bills[-limit:]

    def get_sales_data(self) -> List[Any]:
        """
        Return monthly sales data.
        :return: List of sales data tuples
        """
        return get_monthly_sales()

    def generate_receipt(self, timestamp: datetime.datetime, items: List[Dict[str, Any]], total: float, details: Dict[str, Any]) -> Optional[str]:
        """
        Generate and save a receipt file.
        :param timestamp: Sale timestamp
        :param items: List of item dicts
        :param total: Total sale amount
        :param details: Pharmacy details dict
        :return: Receipt file path or None on error
        """
        pharmacy_name = details.get("name", "Pharmacy")
        pharmacy_address = details.get("address", "")
        pharmacy_phone = details.get("phone", "")
        receipt_content = f"""
{pharmacy_name.upper()}
{pharmacy_address}
Phone: {pharmacy_phone}
Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
{'='*40}

Items:
"""
        for item in items:
            receipt_content += f"{item['name']}\n"
            receipt_content += f"  {item['quantity']} x ₹{item['price']:.2f} = ₹{item['subtotal']:.2f}\n"
        receipt_content += f"""
{'='*40}
Total: ₹{total:.2f}
{'='*40}

Thank you for your purchase!
"""
        receipt_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "receipts")
        if not os.path.exists(receipt_dir):
            os.makedirs(receipt_dir)
        receipt_filename = f"receipt_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        receipt_path = os.path.join(receipt_dir, receipt_filename)
        try:
            with open(receipt_path, "w", encoding="utf-8") as f:
                f.write(receipt_content)
            return receipt_path
        except Exception:
            return None 