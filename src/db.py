import datetime
import logging
import os
from logging.handlers import RotatingFileHandler

from sqlalchemy import Column, Date, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload

from config import get_threshold

Base = declarative_base()

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, "medibit_app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=2 * 1024 * 1024, backupCount=5)],
)
db_logger = logging.getLogger("medibit.db")


class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True)
    barcode = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    expiry = Column(Date)
    manufacturer = Column(String)
    price = Column(Integer, default=0)
    threshold = Column(Integer, default=10)  # Individual stock threshold


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # 'pending' or 'completed'
    medicines = relationship("OrderMedicine", back_populates="order")


class OrderMedicine(Base):
    __tablename__ = "order_medicines"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    barcode = Column(String, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    expiry = Column(String)
    manufacturer = Column(String)
    order_quantity = Column(Integer, nullable=True)
    order = relationship("Order", back_populates="medicines")


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True)
    timestamp = Column(String, nullable=False)
    total = Column(Integer, nullable=False)
    file_path = Column(String, nullable=True)
    items = relationship("BillItem", back_populates="bill")


class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    barcode = Column(String, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Integer, nullable=False)
    discount = Column(Integer, nullable=True, default=0)
    bill = relationship("Bill", back_populates="items")


class PharmacyDetails(Base):
    __tablename__ = "pharmacy_details"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    gst_number = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    website = Column(String, nullable=True)


# Set database directory at project root
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
DB_FILENAME = os.path.join(DATABASE_DIR, "pharmacy_inventory.db")
DB_URL = f"sqlite:///{DB_FILENAME}"
engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

LOW_STOCK_THRESHOLD = 10


def init_db() -> None:
    """
    Initialize the database and create tables if they do not exist.
    Handles schema migrations for threshold and pharmacy_details.
    """
    if not os.path.exists(DB_FILENAME):
        Base.metadata.create_all(engine)
    else:
        # Check if threshold column exists, if not add it
        try:
            session = Session()
            session.query(Medicine.threshold).first()
            session.close()
        except:
            # Threshold column doesn't exist, add it
            print("Adding threshold column to existing medicines...")
            from sqlalchemy import text

            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE medicines ADD COLUMN "
                        "threshold INTEGER DEFAULT 10"
                    )
                )
                conn.commit()
            print("Threshold column added successfully!")

        # Check if status column exists in orders, if not add it
        try:
            session = Session()
            session.query(Order.status).first()
            session.close()
        except:
            print("Adding status column to existing orders...")
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE orders ADD COLUMN "
                        "status VARCHAR DEFAULT 'pending'"
                    )
                )
                conn.commit()
            print("Status column added successfully!")

        # Check if pharmacy_details table exists, if not create it
        try:
            session = Session()
            session.query(PharmacyDetails).first()
            session.close()
            print("Pharmacy details table exists and is accessible")
        except Exception as e:
            # pharmacy_details table doesn't exist, create it
            print(f"Creating pharmacy_details table... Error: {e}")
            try:
                PharmacyDetails.__table__.create(engine, checkfirst=True)
                print("Pharmacy details table created successfully!")
            except Exception as create_error:
                print(f"Error creating pharmacy_details table: {create_error}")
                # Try creating all tables
                Base.metadata.create_all(engine)
                print("All tables created successfully!")

        # Create default pharmacy details if none exist
        create_default_pharmacy_details()


def get_all_medicines() -> list:
    """
    Retrieve all medicines from the inventory.
    :return: List of Medicine objects
    """
    session = Session()
    medicines = session.query(Medicine).all()
    session.expunge_all()  # Force reload of all objects
    session.close()
    return medicines


def get_medicine_by_barcode(barcode: str) -> 'Medicine':
    """
    Retrieve a medicine by its barcode.
    :param barcode: Medicine barcode
    :return: Medicine object or None
    """
    session = Session()
    medicine = session.query(Medicine).filter_by(barcode=barcode).first()
    session.close()
    return medicine


def update_medicine_threshold(barcode: str, threshold: int) -> tuple:
    """
    Update the threshold value for a medicine.
    :param barcode: Medicine barcode
    :param threshold: New threshold value
    :return: (success, error message)
    """
    session = Session()
    try:
        medicine = session.query(Medicine).filter_by(barcode=barcode).first()
        if medicine:
            medicine.threshold = threshold
            session.commit()
            return True, None
        else:
            return False, "Medicine not found"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def update_medicine(barcode: str, name: str, quantity: int, expiry, manufacturer: str, price: int, threshold: int) -> tuple:
    """
    Update all fields of a medicine by barcode.
    :param barcode: Medicine barcode
    :param name: Medicine name
    :param quantity: Quantity in stock
    :param expiry: Expiry date
    :param manufacturer: Manufacturer name
    :param price: Price per unit
    :param threshold: Stock threshold
    :return: (success, error message)
    """
    session = Session()
    try:
        medicine = session.query(Medicine).filter_by(barcode=barcode).first()
        if medicine:
            medicine.name = name
            medicine.quantity = quantity
            medicine.expiry = expiry
            medicine.manufacturer = manufacturer
            medicine.price = price
            medicine.threshold = threshold
            session.commit()
            return True, None
        else:
            return False, "Medicine not found"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def update_medicine_quantity(barcode: str, new_quantity: int) -> tuple:
    """
    Update the quantity of a medicine by barcode.
    :param barcode: Medicine barcode
    :param new_quantity: New quantity value
    :return: (success, error message)
    """
    session = Session()
    try:
        medicine = session.query(Medicine).filter_by(barcode=barcode).first()
        if medicine:
            medicine.quantity = new_quantity
            session.commit()
            return True, None
        else:
            return False, "Medicine not found"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def add_medicine(barcode: str, name: str, quantity: int, expiry, manufacturer: str, price: int = 0, threshold: int = 10) -> tuple:
    """
    Add a new medicine or update an existing one by barcode.
    :param barcode: Medicine barcode
    :param name: Medicine name
    :param quantity: Quantity to add
    :param expiry: Expiry date
    :param manufacturer: Manufacturer name
    :param price: Price per unit
    :param threshold: Stock threshold
    :return: (success, message)
    """
    session = Session()
    try:
        # Check if medicine with this barcode already exists
        existing_medicine = session.query(Medicine).filter_by(barcode=barcode).first()

        if existing_medicine:
            # Update existing medicine
            existing_medicine.name = name
            existing_medicine.quantity += quantity  # Add to existing quantity
            existing_medicine.expiry = expiry
            existing_medicine.manufacturer = manufacturer
            existing_medicine.price = price
            existing_medicine.threshold = threshold
            session.commit()
            return (
                True,
                f"Updated existing medicine '{name}' and added " f"{quantity} units",
            )
        else:
            # Create new medicine
            med = Medicine(
                barcode=barcode,
                name=name,
                quantity=quantity,
                expiry=expiry,
                manufacturer=manufacturer,
                price=price,
                threshold=threshold,
            )
            session.add(med)
            session.commit()
            return True, f"Added new medicine '{name}'"

    except IntegrityError as e:
        session.rollback()
        return False, str(e)
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def get_low_stock_medicines() -> list:
    """
    Retrieve all medicines that are below their individual stock threshold.
    :return: List of Medicine objects
    """
    session = Session()
    # Use individual thresholds instead of global threshold
    medicines = (
        session.query(Medicine).filter(Medicine.quantity < Medicine.threshold).all()
    )
    session.close()
    return medicines


def add_order(timestamp: str, file_path: str, medicines: list) -> None:
    """
    Add a new order to the database.
    :param timestamp: Order timestamp
    :param file_path: Path to order PDF
    :param medicines: List of medicine dicts or objects
    """
    session = Session()
    order = Order(timestamp=timestamp, file_path=file_path)
    session.add(order)
    session.flush()  # get order.id
    for med in medicines:
        # Support both dict and ORM object
        if isinstance(med, dict):
            barcode = med.get("barcode")
            name = med.get("name")
            quantity = med.get("quantity")
            expiry = str(med.get("expiry")) if med.get("expiry") else ""
            manufacturer = med.get("manufacturer") or ""
            order_quantity = med.get("order_quantity", None)
        else:
            barcode = getattr(med, "barcode", None)
            name = getattr(med, "name", None)
            quantity = getattr(med, "quantity", None)
            expiry = (
                str(getattr(med, "expiry", "")) if getattr(med, "expiry", None) else ""
            )
            manufacturer = getattr(med, "manufacturer", "") or ""
            order_quantity = getattr(med, "order_quantity", None)
        order_med = OrderMedicine(
            order_id=order.id,
            barcode=barcode,
            name=name,
            quantity=quantity,
            expiry=expiry,
            manufacturer=manufacturer,
            order_quantity=order_quantity,
        )
        session.add(order_med)
    session.commit()
    session.close()
    # NOTE: If you get a DB error about missing 'order_quantity', \
    # delete pharmacy_inventory.db and restart the app to recreate the DB.


def get_all_orders() -> list:
    """
    Retrieve all orders from the database.
    :return: List of Order objects
    """
    session = Session()
    orders = session.query(Order).order_by(Order.id.desc()).all()
    # Eager load medicines
    for order in orders:
        order.meds = session.query(OrderMedicine).filter_by(order_id=order.id).all()
    session.close()
    return orders


def get_order_items(order_id: int) -> list:
    """
    Retrieve all order items (OrderMedicine) for a given order ID.
    :param order_id: Order ID
    :return: List of OrderMedicine objects
    """
    session = Session()
    items = session.query(OrderMedicine).filter_by(order_id=order_id).all()
    session.close()
    return items


def add_bill(timestamp: str, total: int, items: list, file_path: str = None) -> int:
    """
    Add a new bill to the database.
    :param timestamp: Bill timestamp
    :param total: Total bill amount
    :param items: List of bill item dicts
    :param file_path: Optional path to bill PDF
    :return: Bill ID
    """
    session = Session()
    bill = Bill(timestamp=timestamp, total=total, file_path=file_path)
    session.add(bill)
    session.flush()
    for item in items:
        bill_item = BillItem(
            bill_id=bill.id,
            barcode=item["barcode"],
            name=item["name"],
            price=item["price"],
            quantity=item["quantity"],
            subtotal=item["subtotal"],
            discount=item.get("discount", 0)
        )
        session.add(bill_item)
    session.commit()
    bill_id = bill.id  # Capture the ID before closing the session
    session.close()
    return bill_id


def get_all_bills() -> list:
    """
    Retrieve all bills from the database.
    :return: List of Bill objects
    """
    session = Session()
    bills = session.query(Bill).options(joinedload(Bill.items)).order_by(Bill.id.desc()).all()
    session.close()
    return bills


def get_monthly_sales(start_date=None, end_date=None) -> list:
    """
    Return a list of (Month, Total Sales, Bill Count, Average Bill) for each month with sales, filtered by date range if provided.
    :param start_date: (optional) string 'YYYY-MM-DD' or datetime.date
    :param end_date: (optional) string 'YYYY-MM-DD' or datetime.date
    :return: List of tuples (month_name, total, count, avg)
    """
    session = Session()
    try:
        import calendar
        from collections import defaultdict
        import datetime
        # Prepare date filters
        query = session.query(Bill)
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(Bill.timestamp >= str(start_date))
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(Bill.timestamp <= str(end_date))
        bills = query.order_by(Bill.timestamp).all()
        monthly = defaultdict(lambda: {"total": 0, "count": 0})
        for bill in bills:
            try:
                dt = datetime.datetime.strptime(bill.timestamp[:10], "%Y-%m-%d")
            except Exception:
                continue
            key = (dt.year, dt.month)
            monthly[key]["total"] += bill.total
            monthly[key]["count"] += 1
        result = []
        for (year, month), data in sorted(monthly.items()):
            month_name = f"{calendar.month_name[month]} {year}"
            total = data["total"]
            count = data["count"]
            avg = total / count if count else 0
            result.append((month_name, total, count, avg))
        return result
    finally:
        session.close()


def get_pharmacy_details() -> 'PharmacyDetails':
    """
    Retrieve pharmacy details from the database.
    :return: PharmacyDetails object or None
    """
    session = Session()
    try:
        details = session.query(PharmacyDetails).first()
        session.close()
        print(f"Retrieved pharmacy details: {details}")
        return details
    except Exception as e:
        print(f"Error getting pharmacy details: {e}")
        session.close()
        return None


def save_pharmacy_details(
    name: str, address: str, phone: str, email: str, gst_number: str = "", license_number: str = "", website: str = ""
) -> tuple:
    """
    Save or update pharmacy details in the database.
    :param name: Pharmacy name
    :param address: Address
    :param phone: Phone number
    :param email: Email address
    :param gst_number: GST number (optional)
    :param license_number: License number (optional)
    :param website: Website (optional)
    :return: (success, message)
    """
    session = Session()
    try:
        # Check if pharmacy details already exist
        existing = session.query(PharmacyDetails).first()
        if existing:
            # Update existing details
            existing.name = name
            existing.address = address
            existing.phone = phone
            existing.email = email
            existing.gst_number = gst_number
            existing.license_number = license_number
            existing.website = website
            print(f"Updated existing pharmacy details: {existing.name}")
        else:
            # Create new pharmacy details
            details = PharmacyDetails(
                name=name,
                address=address,
                phone=phone,
                email=email,
                gst_number=gst_number,
                license_number=license_number,
                website=website,
            )
            session.add(details)
            print(f"Created new pharmacy details: {details.name}")

        session.commit()
        return True, "Pharmacy details saved successfully"
    except Exception as e:
        session.rollback()
        print(f"Error saving pharmacy details: {e}")
        return False, str(e)
    finally:
        session.close()


def create_default_pharmacy_details() -> bool:
    """
    Create default pharmacy details if none exist.
    :return: True if created, False if already exists or error
    """
    session = Session()
    try:
        existing = session.query(PharmacyDetails).first()
        if not existing:
            default_details = PharmacyDetails(
                name="medibit Pharmacy",
                address="123 Main Street, City, State 12345",
                phone="+1-555-123-4567",
                email="info@medibitpharmacy.com",
                gst_number="",
                license_number="",
                website="www.medibitpharmacy.com",
            )
            session.add(default_details)
            session.commit()
            print("Created default pharmacy details")
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error creating default pharmacy details: {e}")
        return False
    finally:
        session.close()


def delete_medicine(barcode: str) -> tuple:
    """
    Delete a single medicine from the inventory by barcode.
    :param barcode: Medicine barcode
    :return: (success, error message)
    """
    session = Session()
    try:
        medicine = session.query(Medicine).filter_by(barcode=barcode).first()
        if medicine:
            session.delete(medicine)
            session.commit()
            return True, None
        else:
            return False, "Medicine not found"
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def clear_inventory() -> tuple:
    """
    Delete all medicines from the inventory.
    :return: (success, number deleted or error message)
    """
    session = Session()
    try:
        num_deleted = session.query(Medicine).delete()
        session.commit()
        return True, num_deleted
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()


def clear_all_bills() -> None:
    """
    Delete all bills from the database.
    """
    session = Session()
    try:
        session.query(BillItem).delete()
        session.query(Bill).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error clearing all bills: {e}")
        return False
    finally:
        session.close()


def update_order_status(order_id: int, status: str) -> bool:
    """
    Update the status of an order.
    :param order_id: Order ID
    :param status: New status ('pending' or 'completed')
    :return: True if updated, False otherwise
    """
    session = Session()
    try:
        order = session.query(Order).filter_by(id=order_id).first()
        if order:
            order.status = status
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error updating order status: {e}")
        return False
    finally:
        session.close()


def update_bill_file_path(bill_id: int, file_path: str) -> None:
    """
    Update the file_path of a bill after PDF generation.
    :param bill_id: Bill ID
    :param file_path: Path to the PDF receipt
    """
    session = Session()
    bill = session.query(Bill).filter_by(id=bill_id).first()
    if bill:
        bill.file_path = file_path
        session.commit()
        print(f"[DEBUG] Updated bill {bill_id} with file_path: {file_path}")
        session.expire_all()  # Force session refresh
    else:
        print(f"[DEBUG] Bill {bill_id} not found for file_path update!")
    session.close()


def update_order(order_id: int, supplier: str, medicines: list) -> None:
    """
    Update an existing order and its medicines. Only allowed if order is pending.
    :param order_id: Order ID
    :param supplier: Supplier name
    :param medicines: List of medicine dicts
    """
    session = Session()
    order = session.query(Order).filter_by(id=order_id).first()
    if not order:
        session.close()
        raise Exception("Order not found")
    if order.status != "pending":
        session.close()
        raise Exception("Only pending orders can be edited")
    # Update supplier for all medicines
    # Remove existing medicines
    session.query(OrderMedicine).filter_by(order_id=order_id).delete()
    # Add new medicines
    for med in medicines:
        order_med = OrderMedicine(
            order_id=order_id,
            barcode=med.get("barcode"),
            name=med.get("name"),
            quantity=med.get("quantity"),
            expiry=str(med.get("expiry")) if med.get("expiry") else "",
            manufacturer=med.get("manufacturer") or supplier,
            order_quantity=med.get("order_quantity", None),
        )
        session.add(order_med)
    session.commit()
    session.close()


def delete_order(order_id: int) -> None:
    """
    Delete an order and its medicines by ID, only if the order is pending.
    :param order_id: Order ID
    """
    session = Session()
    order = session.query(Order).filter_by(id=order_id).first()
    if not order:
        session.close()
        raise Exception("Order not found")
    if order.status != "pending":
        session.close()
        raise Exception("Only pending orders can be deleted")
    session.query(OrderMedicine).filter_by(order_id=order_id).delete()
    session.delete(order)
    session.commit()
    session.close()


def update_order_file_path(order_id: int, file_path: str) -> None:
    """
    Update the file_path of an order by ID.
    :param order_id: Order ID
    :param file_path: Path to PDF file
    """
    session = Session()
    order = session.query(Order).filter_by(id=order_id).first()
    if not order:
        session.close()
        raise Exception("Order not found")
    order.file_path = file_path
    session.commit()
    session.close()

print(f"[DEBUG] Using DB file: {os.path.abspath(DB_FILENAME)}")
