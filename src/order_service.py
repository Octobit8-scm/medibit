from typing import List, Dict, Any, Tuple, Optional
from db import add_order, get_all_orders, get_low_stock_medicines
from order_manager import OrderManager
import datetime

class OrderService:
    """
    Service class for all order-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def get_all(self) -> List[Any]:
        """
        Return all orders.
        :return: List of order objects
        """
        return get_all_orders()

    def get_low_stock(self) -> List[Any]:
        """
        Return all medicines that are low in stock.
        :return: List of medicine objects
        """
        return get_low_stock_medicines()

    def add(self, timestamp: datetime.datetime, pdf_path: str, order_items: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Add a new order to the database.
        :param timestamp: Order timestamp
        :param pdf_path: Path to generated PDF
        :param order_items: List of order item dicts
        :return: (success, error message)
        """
        try:
            add_order(timestamp, pdf_path, order_items)
            return True, None
        except Exception as e:
            return False, str(e)

    def generate_order_pdf(self, order_items: List[Dict[str, Any]], order_id: int, timestamp: str, supplier_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a PDF for the order and return the file path.
        :param order_items: List of order item dicts
        :param order_id: Unique order ID
        :param timestamp: Order timestamp string
        :param supplier_info: Optional supplier info dict
        :return: Path to generated PDF file
        """
        order_manager = OrderManager()
        return order_manager.generate_pdf_order(order_items, order_id, timestamp, supplier_info) 