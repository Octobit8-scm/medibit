from typing import List, Optional, Tuple, Dict, Any
from db import (
    add_medicine,
    get_all_medicines,
    update_medicine,
    update_medicine_quantity,
    delete_medicine,
    clear_inventory,
)
import logging
logger = logging.getLogger("medibit")

class InventoryService:
    """
    Service class for all inventory-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def __init__(self):
        logger.info("InventoryService initialized")

    def get_all(self) -> List[Any]:
        try:
            result = get_all_medicines()
            logging.info(f"Fetched {len(result)} medicines from inventory.")
            return result
        except Exception as e:
            logging.error(f"Error fetching all medicines: {e}", exc_info=True)
            return []

    def add(self, data):
        logger.debug(f"[add] ENTRY: barcode={data.get('barcode', 'N/A')}")
        try:
            barcode = data["barcode"]
            existing = [m for m in get_all_medicines() if m.barcode == barcode]
            if existing:
                logger.warning(f"Attempted to add duplicate barcode: {barcode}")
                return False, "A medicine with this barcode already exists."
            result = add_medicine(
                data["barcode"],
                data["name"],
                data["quantity"],
                data["expiry"],
                data["manufacturer"],
                data.get("price", 0),
                data.get("threshold", 10),
            )
            logger.info(f"Medicine added: {barcode}")
            logger.debug(f"[add] EXIT: success, barcode={barcode}")
            if result[0]:
                return True, None
            else:
                return False, result[1]
        except Exception as e:
            logger.error(f"[add] Exception: {e}", exc_info=True)
            return False, str(e)

    def update(self, barcode: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        logger.debug(f"[update] ENTRY: barcode={barcode}, data={data}")
        try:
            result, msg = update_medicine(
                barcode,
                data["name"],
                data["quantity"],
                data["expiry"],
                data["manufacturer"],
                data["price"],
                data["threshold"],
            )
            logging.info(f"Updated medicine: {barcode}, result: {result}")
            logger.debug(f"[update] EXIT: success, barcode={barcode}")
            if result:
                return True, "Updated"
            else:
                return False, msg
        except Exception as e:
            logging.error(f"[update] Exception: {e}", exc_info=True)
            return False, str(e)

    def update_quantity(self, barcode: str, quantity: int) -> Tuple[bool, Optional[str]]:
        logger.debug(f"[update_quantity] ENTRY: barcode={barcode}, quantity={quantity}")
        try:
            result, msg = update_medicine_quantity(barcode, quantity)
            logging.info(f"Updated quantity for {barcode} to {quantity}, result: {result}")
            logger.debug(f"[update_quantity] EXIT: success, barcode={barcode}")
            if result:
                return True, "Quantity Updated"
            else:
                return False, msg
        except Exception as e:
            logging.error(f"[update_quantity] Exception: {e}", exc_info=True)
            return False, str(e)

    def delete(self, barcode: str) -> Tuple[bool, Optional[str]]:
        logger.debug(f"[delete] ENTRY: barcode={barcode}")
        try:
            result, msg = delete_medicine(barcode)
            logging.info(f"Deleted medicine: {barcode}, result: {result}")
            logger.info("Medicine deleted from inventory.")
            logger.debug(f"[delete] EXIT: success, barcode={barcode}")
            if result:
                return True, "Deleted"
            else:
                return False, msg
        except Exception as e:
            logging.error(f"[delete] Exception: {e}", exc_info=True)
            return False, str(e)

    def clear(self) -> Tuple[bool, Optional[str]]:
        logger.debug(f"[clear] ENTRY")
        try:
            result, msg = clear_inventory()
            logging.info(f"Cleared inventory, result: {result}")
            logger.debug(f"[clear] EXIT: success")
            if result:
                return True, "Cleared"
            else:
                return False, msg
        except Exception as e:
            logging.error(f"[clear] Exception: {e}", exc_info=True)
            return False, str(e)

    def search(self, query: str) -> List[Any]:
        logger.debug(f"[search] ENTRY: query={query}")
        try:
            query = query.strip().lower()
            result = [
                m for m in get_all_medicines()
                if query in m.name.lower()
                or query in m.barcode.lower()
                or (m.manufacturer and query in m.manufacturer.lower())
            ]
            logging.info(f"Search for '{query}' returned {len(result)} results.")
            logger.debug(f"[search] EXIT: success, query={query}")
            return result
        except Exception as e:
            logging.error(f"[search] Exception: {e}", exc_info=True)
            return [] 