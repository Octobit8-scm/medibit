from typing import List, Optional, Tuple, Dict, Any
from db import (
    add_medicine,
    get_all_medicines,
    update_medicine,
    update_medicine_quantity,
    delete_medicine,
    clear_inventory,
)

class InventoryService:
    """
    Service class for all inventory-related business logic and data access.
    UI should use this class instead of calling DB functions directly.
    """

    def get_all(self) -> List[Any]:
        """
        Return all medicines in inventory.
        :return: List of medicine objects
        """
        return get_all_medicines()

    def add(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Add a new medicine to inventory. Prevents duplicate barcodes.
        :param data: Dictionary with medicine fields
        :return: (success, error message)
        """
        barcode = data["barcode"]
        existing = [m for m in get_all_medicines() if m.barcode == barcode]
        if existing:
            return False, "A medicine with this barcode already exists."
        return add_medicine(
            data["barcode"],
            data["name"],
            data["quantity"],
            data["expiry"],
            data["manufacturer"],
            data["price"],
            data["threshold"],
        )

    def update(self, barcode: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Update an existing medicine by barcode.
        :param barcode: Medicine barcode
        :param data: Dictionary with updated fields
        :return: (success, error message)
        """
        return update_medicine(
            barcode,
            data["name"],
            data["quantity"],
            data["expiry"],
            data["manufacturer"],
            data["price"],
            data["threshold"],
        )

    def update_quantity(self, barcode: str, quantity: int) -> Tuple[bool, Optional[str]]:
        """
        Update the quantity of a medicine by barcode.
        :param barcode: Medicine barcode
        :param quantity: New quantity
        :return: (success, error message)
        """
        return update_medicine_quantity(barcode, quantity), None

    def delete(self, barcode: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a medicine by barcode.
        :param barcode: Medicine barcode
        :return: (success, error message)
        """
        return delete_medicine(barcode)

    def clear(self) -> Tuple[bool, Optional[str]]:
        """
        Clear all medicines from inventory.
        :return: (success, result message)
        """
        return clear_inventory()

    def search(self, query: str) -> List[Any]:
        """
        Search medicines by name, barcode, or manufacturer (case-insensitive).
        :param query: Search string
        :return: List of matching medicine objects
        """
        query = query.strip().lower()
        return [
            m for m in get_all_medicines()
            if query in m.name.lower()
            or query in m.barcode.lower()
            or (m.manufacturer and query in m.manufacturer.lower())
        ] 