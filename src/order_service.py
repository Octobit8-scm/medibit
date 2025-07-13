from typing import List, Dict, Any, Tuple, Optional
from db import add_order, get_all_orders, get_low_stock_medicines
from order_manager import OrderManager
import datetime
import logging
logger = logging.getLogger("medibit")

class OrderService:
    """
    Service class for all order-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def __init__(self):
        logger.info("OrderService initialized")

    def get_all(self) -> List[Any]:
        """
        Return all orders.
        :return: List of order objects
        """
        logger.debug(f"[get_all] ENTRY")
        try:
            orders = get_all_orders()
            logger.debug(f"[get_all] EXIT: success, orders_count={len(orders)}")
            return orders
        except Exception as e:
            logger.error(f"[get_all] Exception: {e}", exc_info=True)
            return []

    def get_low_stock(self) -> List[Any]:
        """
        Return all medicines that are low in stock.
        :return: List of medicine objects
        """
        logger.debug(f"[get_low_stock] ENTRY")
        try:
            low_stock_medicines = get_low_stock_medicines()
            logger.debug(f"[get_low_stock] EXIT: success, low_stock_medicines_count={len(low_stock_medicines)}")
            return low_stock_medicines
        except Exception as e:
            logger.error(f"[get_low_stock] Exception: {e}", exc_info=True)
            return []

    def add(self, timestamp: datetime.datetime, pdf_path: str, order_items: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Add a new order to the database.
        :param timestamp: Order timestamp
        :param pdf_path: Path to generated PDF
        :param order_items: List of order item dicts
        :return: (success, error message)
        """
        logger.debug(f"[add] ENTRY: timestamp={timestamp}, pdf_path={pdf_path}, order_items={order_items}")
        try:
            add_order(timestamp, pdf_path, order_items)
            logger.info("Order added.")
            logger.debug(f"[add] EXIT: success, timestamp={timestamp}, pdf_path={pdf_path}, order_items={order_items}")
            return True, None
        except Exception as e:
            logger.error(f"[add] Exception: {e}", exc_info=True)
            return False, str(e)

    def update(self, order_id: int, supplier: str, order_items: list) -> tuple:
        """
        Update an existing order (if pending).
        :param order_id: Order ID
        :param supplier: Supplier name
        :param order_items: List of medicine dicts
        :return: (success, error message)
        """
        from db import update_order
        logger.debug(f"[update] ENTRY: order_id={order_id}, supplier={supplier}, order_items={order_items}")
        try:
            update_order(order_id, supplier, order_items)
            logger.info("Order updated.")
            logger.debug(f"[update] EXIT: success, order_id={order_id}, supplier={supplier}, order_items={order_items}")
            return True, None
        except Exception as e:
            logger.error(f"[update] Exception: {e}", exc_info=True)
            return False, str(e)

    def delete(self, order_id: int) -> tuple:
        """
        Delete an order by ID (only if pending).
        :param order_id: Order ID
        :return: (success, error message)
        """
        from db import delete_order
        logger.debug(f"[delete] ENTRY: order_id={order_id}")
        try:
            delete_order(order_id)
            logger.info("Order deleted.")
            logger.debug(f"[delete] EXIT: success, order_id={order_id}")
            return True, None
        except Exception as e:
            logger.error(f"[delete] Exception: {e}", exc_info=True)
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
        logger.debug(f"[generate_order_pdf] ENTRY: order_items={order_items}, order_id={order_id}, timestamp={timestamp}, supplier_info={supplier_info}")
        try:
            pdf_path = order_manager.generate_pdf_order(order_items, order_id, timestamp, supplier_info)
            logger.debug(f"[generate_order_pdf] EXIT: success, pdf_path={pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"[generate_order_pdf] Exception: {e}", exc_info=True)
            return "" 