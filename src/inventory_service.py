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

class InventoryService:
    """
    Service class for all inventory-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def get_all(self) -> List[Any]:
        try:
            result = get_all_medicines()
            logging.info(f"Fetched {len(result)} medicines from inventory.")
            return result
        except Exception as e:
            logging.error(f"Error fetching all medicines: {e}", exc_info=True)
            return []

    def add(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            barcode = data["barcode"]
            existing = [m for m in get_all_medicines() if m.barcode == barcode]
            if existing:
                logging.warning(f"Attempted to add duplicate barcode: {barcode}")
                return False, "A medicine with this barcode already exists."
            result = add_medicine(
                data["barcode"],
                data["name"],
                data["quantity"],
                data["expiry"],
                data["manufacturer"],
                data["price"],
                data["threshold"],
            )
            logging.info(f"Added medicine: {barcode}, result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error adding medicine: {data.get('barcode', 'N/A')}: {e}", exc_info=True)
            return False, str(e)

    def update(self, barcode: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            result = update_medicine(
                barcode,
                data["name"],
                data["quantity"],
                data["expiry"],
                data["manufacturer"],
                data["price"],
                data["threshold"],
            )
            logging.info(f"Updated medicine: {barcode}, result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error updating medicine: {barcode}: {e}", exc_info=True)
            return False, str(e)

    def update_quantity(self, barcode: str, quantity: int) -> Tuple[bool, Optional[str]]:
        try:
            result = update_medicine_quantity(barcode, quantity), None
            logging.info(f"Updated quantity for {barcode} to {quantity}, result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error updating quantity for {barcode}: {e}", exc_info=True)
            return False, str(e)

    def delete(self, barcode: str) -> Tuple[bool, Optional[str]]:
        try:
            result = delete_medicine(barcode)
            logging.info(f"Deleted medicine: {barcode}, result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error deleting medicine: {barcode}: {e}", exc_info=True)
            return False, str(e)

    def clear(self) -> Tuple[bool, Optional[str]]:
        try:
            result = clear_inventory()
            logging.info(f"Cleared inventory, result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error clearing inventory: {e}", exc_info=True)
            return False, str(e)

    def search(self, query: str) -> List[Any]:
        try:
            query = query.strip().lower()
            result = [
                m for m in get_all_medicines()
                if query in m.name.lower()
                or query in m.barcode.lower()
                or (m.manufacturer and query in m.manufacturer.lower())
            ]
            logging.info(f"Search for '{query}' returned {len(result)} results.")
            return result
        except Exception as e:
            logging.error(f"Error searching medicines: {e}", exc_info=True)
            return [] 