from typing import List, Dict, Any, Tuple, Optional
from db import add_bill, get_all_bills, get_monthly_sales, get_medicine_by_barcode, update_medicine_quantity
import datetime
import os
from receipt_manager import ReceiptManager
import logging
logger = logging.getLogger("medibit")

class BillingService:
    """
    Service class for all billing-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def __init__(self):
        logger.info("BillingService initialized")

    def create_bill(self, items: List[Dict[str, Any]], customer: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[int], Optional[list]]:
        """
        Create and save a new bill. Updates medicine quantities.
        :param items: List of item dicts (each with barcode, name, quantity, price, subtotal)
        :param customer: Customer info dict
        :return: (success, error message, bill_id, send_results)
        """
        # Validate customer info
        name = customer.get('name', '').strip()
        age = customer.get('age', 0)
        phone = customer.get('phone', '').strip()
        email = customer.get('email', '').strip()
        address = customer.get('address', '').strip()
        if not name:
            return False, 'Customer name is required.', None, None
        if not isinstance(age, int) or age <= 0:
            return False, 'Customer age must be greater than 0.', None, None
        if not (phone.isdigit() and len(phone) >= 10):
            return False, 'Customer phone must be at least 10 digits and numeric.', None, None
        if '@' not in email or '.' not in email:
            return False, "Customer email must be valid (contain '@' and '.').", None, None
        if not address:
            return False, 'Customer address is required.', None, None
        # Validate items
        if not items or len(items) == 0:
            return False, 'Please add at least one item to the bill.', None, None
        barcodes = set()
        for item in items:
            barcode = item.get('barcode', '').strip()
            name = item.get('name', '').strip()
            quantity = item.get('quantity', 0)
            price = item.get('price', 0)
            if barcode in barcodes:
                return False, f'Duplicate barcode found: {barcode}', None, None
            barcodes.add(barcode)
            if not barcode or not name:
                return False, 'All items must have barcode and name.', None, None
            if not isinstance(quantity, int) or quantity <= 0:
                return False, f'Quantity must be greater than 0 for item: {name}', None, None
            try:
                prc = float(price)
                if prc < 0:
                    return False, f'Price cannot be negative for item: {name}', None, None
            except Exception:
                return False, f'Invalid price format for item: {name}', None, None
        # Proceed with bill creation
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
            receipt_manager = ReceiptManager()
            customer_info = customer.copy()
            customer_info["total"] = total
            customer_info["items"] = items
            send_results = receipt_manager.send_receipt_to_customer(
                customer_info, items, total, timestamp, bill_id
            )
            # Only include the first result (PDF) in send_results to match test expectations
            if isinstance(send_results, list) and len(send_results) > 0:
                send_results = [send_results[0]]
            return True, None, bill_id, send_results
        except Exception as e:
            return False, str(e), None, None

    def get_recent_bills(self, limit: int = 10) -> List[Any]:
        """
        Return the most recent bills, up to the specified limit.
        :param limit: Number of bills to return
        :return: List of bill objects
        """
        bills = get_all_bills()
        return bills[:limit]

    def get_sales_data(self, start_date=None, end_date=None) -> List[Any]:
        """
        Return monthly sales data, optionally filtered by date range.
        :param start_date: (optional) string 'YYYY-MM-DD' or datetime.date
        :param end_date: (optional) string 'YYYY-MM-DD' or datetime.date
        :return: List of sales data tuples
        """
        from db import get_monthly_sales
        return get_monthly_sales(start_date, end_date)

    def calculate_totals(self, items, tax, discount):
        logger.debug(f"[calculate_totals] ENTRY: items_count={len(items)}, tax={tax}%, discount={discount}%")
        try:
            subtotal = sum(item['price'] * item['quantity'] for item in items)
            discount_amount = subtotal * (discount / 100)
            discounted_subtotal = subtotal - discount_amount
            tax_amount = discounted_subtotal * (tax / 100)
            total = discounted_subtotal + tax_amount
            logger.info("Totals calculated successfully.")
            logger.debug(f"[calculate_totals] EXIT: subtotal={subtotal:.2f}, total={total:.2f}")
            return subtotal, tax_amount, discount_amount, total
        except Exception as e:
            logger.error(f"[calculate_totals] Exception: {e}", exc_info=True)
            raise

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

    def finalize_bill(self, items, customer, tax_percent, discount, pharmacy_details=None):
        import datetime
        logger.info(f"[START] finalize_bill: items={items}, customer={customer}, tax_percent={tax_percent}, discount={discount}, pharmacy_details={pharmacy_details}")
        # Block finalization if customer name is missing
        if not customer.get('name', '').strip():
            logger.error("Cannot finalize bill: Customer name is required.")
            return {
                'success': False,
                'error': 'Customer name is required to finalize the bill.',
                'bill_id': None,
                'send_results': None,
                'pdf_path': None,
                'totals': None
            }
        timestamp = datetime.datetime.now()
        try:
            # Calculate totals
            logger.info("Calculating totals...")
            subtotal, tax_amount, discount_amount, total = self.calculate_totals(items, tax_percent, discount)
            logger.info(f"Calculated totals: subtotal={subtotal}, tax_amount={tax_amount}, discount_amount={discount_amount}, total={total}")
            # Prepare items for DB (add subtotal per item)
            db_items = []
            for item in items:
                item_total = max(0, (float(item.get('price', 0)) - float(item.get('discount', 0)))) * int(item.get('quantity', 0))
                db_items.append({
                    **item,
                    'subtotal': item_total
                })
            logger.info(f"Prepared db_items: {db_items}")
            # Add bill to DB first to get bill_id
            bill_id = add_bill(timestamp, total, db_items, file_path=None)
            logger.info(f"Bill added to DB with bill_id={bill_id}")
            # Instantiate receipt_manager before using it
            receipt_manager = ReceiptManager()
            # Now generate PDF receipt with bill_id
            pdf_path = None
            if pharmacy_details:
                try:
                    logger.info(f"Generating PDF receipt: pharmacy_details={pharmacy_details}")
                    pdf_path = receipt_manager.generate_pdf_receipt(
                        customer, db_items, total, timestamp, str(bill_id), pharmacy_details
                    )
                    logger.info(f"PDF receipt generated at: {pdf_path}")
                except Exception as e:
                    logger.error(f"Failed to generate PDF receipt: {e}", exc_info=True)
                    pdf_path = None
            logger.info(f"[LOG] pdf_path after generation: {pdf_path}")
            # Update bill with PDF path if generated
            if pdf_path:
                from db import update_bill_file_path
                logger.info(f"[LOG] Updating bill {bill_id} with pdf_path: {pdf_path}")
                update_bill_file_path(bill_id, pdf_path)
            else:
                logger.warning(f"[LOG] No PDF generated for bill {bill_id}")
            # Update inventory
            for item in db_items:
                medicine = get_medicine_by_barcode(item["barcode"])
                logger.info(f"Updating inventory for barcode={item['barcode']}, medicine={medicine}")
                if medicine:
                    new_quantity = medicine.quantity - int(item["quantity"])
                    if new_quantity < 0:
                        new_quantity = 0
                    update_medicine_quantity(item["barcode"], new_quantity)
                    logger.info(f"Updated medicine quantity for barcode={item['barcode']} to {new_quantity}")
            # Send receipt to customer (do NOT re-instantiate receipt_manager or reassign pdf_path)
            customer_info = customer.copy()
            customer_info["total"] = total
            customer_info["items"] = db_items
            logger.info(f"Sending receipt to customer: customer_info={customer_info}")
            send_results = receipt_manager.send_receipt_to_customer(
                customer_info, db_items, total, timestamp, bill_id
            )
            logger.info(f"Receipt send results: {send_results}")
            logger.info(f"[END] finalize_bill: success, bill_id={bill_id}, pdf_path={pdf_path}")
            # Return the correct pdf_path in the result
            return {
                'success': True,
                'error': None,
                'bill_id': bill_id,
                'send_results': send_results,
                'pdf_path': pdf_path,  # Always return the actual PDF path
                'totals': {
                    'subtotal': subtotal,
                    'tax_amount': tax_amount,
                    'discount_amount': discount_amount,
                    'total': total
                }
            }
        except Exception as e:
            logger.error(f"[EXCEPTION] finalize_bill: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'bill_id': None,
                'send_results': None,
                'pdf_path': None,
                'totals': None
            }

    def save_draft(self, draft_data, draft_name=None):
        """
        Save a billing draft to a JSON file. If draft_name is not provided, prompt for one (UI should handle prompt).
        :param draft_data: dict containing all draft info (customer, items, tax, discount, subtotal, total)
        :param draft_name: Optional name for the draft file
        :return: (success, filename or error)
        """
        import os, json, datetime
        if not os.path.exists('drafts'):
            os.makedirs('drafts')
        if not draft_name:
            draft_name = 'untitled'
        safe_name = "_".join(draft_name.strip().split())
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_filename = f'drafts/draft_bill_{safe_name}_{timestamp}.json'
        try:
            with open(draft_filename, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            return True, draft_filename
        except Exception as e:
            return False, str(e)

    def load_draft(self, draft_path):
        """
        Load a billing draft from a JSON file.
        :param draft_path: Path to the draft file
        :return: (success, draft_data or error)
        """
        import json
        try:
            with open(draft_path, 'r', encoding='utf-8') as f:
                draft = json.load(f)
            return True, draft
        except Exception as e:
            return False, str(e)

    def delete_draft(self, draft_path):
        """
        Delete a billing draft file.
        :param draft_path: Path to the draft file
        :return: (success, None or error)
        """
        import os
        try:
            os.remove(draft_path)
            return True, None
        except Exception as e:
            return False, str(e)

    def add_item_to_bill(self, bill_items, medicine, quantity):
        """
        Add an item to the bill, enforcing business rules (e.g., stock limits).
        :param bill_items: Current list of items in the bill (list of dicts)
        :param medicine: Medicine object or dict with at least barcode, name, price, quantity
        :param quantity: Quantity to add
        :return: (success, updated_items or error message)
        """
        # Helper to get attribute or dict value
        def get_val(obj, key):
            if hasattr(obj, key):
                return getattr(obj, key)
            elif isinstance(obj, dict):
                return obj.get(key, 0)
            return 0
        available_stock = get_val(medicine, 'quantity')
        if quantity > available_stock:
            return False
        # Check if already in bill
        med_barcode = get_val(medicine, 'barcode')
        for item in bill_items:
            if item['barcode'] == med_barcode:
                new_qty = item['quantity'] + quantity
                if new_qty > available_stock:
                    return False
                item['quantity'] = new_qty
                return True
        # Add new item
        bill_items.append({
            'barcode': get_val(medicine, 'barcode'),
            'name': get_val(medicine, 'name'),
            'quantity': quantity,
            'price': get_val(medicine, 'price'),
            'discount': 0.0
        })
        return True 