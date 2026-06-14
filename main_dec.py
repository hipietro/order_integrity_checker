import csv
import sqlite3

DATABASE_NAME = "orders.db"
CSV_FILE_NAME = "new_orders.csv"
VALID_STATUSES = ["completed", "pending", "cancelled"]

def create_database():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            customer_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)
    connection.commit()
    connection.close()

def insert_sample_orders():
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    sample_orders = [
        ("ORD001", "Mario Rossi", 12, "completed"),
        ("ORD002", "Luca Bianchi", 5, "pending"),
    ]
    for order in sample_orders:
        cursor.execute("""
            INSERT OR IGNORE INTO orders (order_code, customer_name, quantity, status)
            VALUES (?, ?, ?, ?)
        """, order)
    connection.commit()
    connection.close()

def order_exists_in_database(order_code):
    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT order_code
        FROM orders
        WHERE order_code = ?
    """, (order_code,))
    result = cursor.fetchone()
    connection.close()
    return result is not None

def validate_order(order, order_codes_in_file):
    errors = []
    order_code = order["order_code"]
    customer_name = order["customer_name"]
    quantity_text = order["quantity"]
    status = order["status"]
    if order_code == "":
        errors.append("missing order code")
    elif order_exists_in_database(order_code):
        errors.append("order code already exists in database")
    elif order_code in order_codes_in_file:
        errors.append("duplicated order code inside CSV file")
    if customer_name == "":
        errors.append("missing customer name")
    elif len(customer_name) < 3:
        errors.append("customer name too short")
    if quantity_text == "":
        errors.append("missing quantity")
    elif not quantity_text.isdigit():
        errors.append("quantity must be a valid number")
    elif int(quantity_text) <= 0:
        errors.append("quantity must be greater than zero")
    if status not in VALID_STATUSES:
        errors.append("invalid status")
    return errors

def check_orders_from_csv():
    valid_orders = 0
    invalid_orders = 0
    order_codes_in_file = []
    print("ORDER INTEGRITY CHECKER")
    print("-----------------------")
    with open(CSV_FILE_NAME, "r") as file:
        reader = csv.DictReader(file)
        for order in reader:
            order_code = order["order_code"]
            print(f"\nChecking order: {order_code}")
            errors = validate_order(order, order_codes_in_file)
            if len(errors) == 0:
                print("Result: valid order")
                valid_orders = valid_orders + 1
            else:
                print("Result: invalid order")
                invalid_orders = invalid_orders + 1
                for error in errors:
                    print(f"- {error}")
            order_codes_in_file.append(order_code)
    print("\nSUMMARY")
    print("-------")
    print(f"Valid orders: {valid_orders}")
    print(f"Invalid orders: {invalid_orders}")

create_database()
insert_sample_orders()
check_orders_from_csv()