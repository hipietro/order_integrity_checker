import csv
import sqlite3


# Name of the SQLite database file.
# SQLite stores the whole database inside a single local file.
DATABASE_NAME = "orders.db"

# Name of the CSV file that contains the new orders to validate.
CSV_FILE_NAME = "new_orders.csv"

# List of order statuses accepted by the program.
# Any other status will be considered invalid.
VALID_STATUSES = ["completed", "pending", "cancelled"]


def create_database():
    """
    Creates the SQLite database and the orders table if they do not already exist.

    The orders table represents the orders that are already stored in the company's
    internal system. New imported orders will be checked against this table to avoid
    duplicate order codes.
    """

    # Open a connection to the SQLite database.
    # If the database file does not exist, SQLite creates it automatically.
    connection = sqlite3.connect(DATABASE_NAME)

    # The cursor is used to execute SQL commands.
    cursor = connection.cursor()

    # Create the orders table only if it does not already exist.
    # The order_code field is marked as UNIQUE because two orders should not have
    # the same business identifier.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            customer_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # Save the changes to the database.
    connection.commit()

    # Close the database connection.
    connection.close()


def insert_sample_orders():
    """
    Inserts a few sample orders into the database.

    These records simulate orders that already exist in the company's internal
    system before importing a new CSV file.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # Sample orders already stored in the database.
    # ORD001 is intentionally used also inside the CSV file to test the duplicate check.
    sample_orders = [
        ("ORD001", "Mario Rossi", 12, "completed"),
        ("ORD002", "Luca Bianchi", 5, "pending"),
    ]

    # Insert each sample order.
    # INSERT OR IGNORE prevents the program from crashing if the same sample order
    # already exists from a previous execution.
    for order in sample_orders:
        cursor.execute("""
            INSERT OR IGNORE INTO orders (order_code, customer_name, quantity, status)
            VALUES (?, ?, ?, ?)
        """, order)

    connection.commit()
    connection.close()


def order_exists_in_database(order_code):
    """
    Checks whether an order code already exists in the SQLite database.

    Parameters:
        order_code: the business identifier of the order.

    Returns:
        True if the order code already exists in the database.
        False otherwise.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    # The question mark is a placeholder.
    # It allows SQLite to safely insert the value of order_code into the query.
    cursor.execute("""
        SELECT order_code
        FROM orders
        WHERE order_code = ?
    """, (order_code,))

    # fetchone() returns the first matching row, or None if no row was found.
    result = cursor.fetchone()

    connection.close()

    return result is not None


def validate_order(order, order_codes_in_file):
    """
    Validates a single order coming from the CSV file.

    The function checks:
    - missing order code
    - duplicated order code in the database
    - duplicated order code inside the CSV file
    - missing or too short customer name
    - missing or invalid quantity
    - unsupported order status

    Parameters:
        order: one row of the CSV file, represented as a dictionary.
        order_codes_in_file: list of order codes already found while reading the CSV.

    Returns:
        A list of error messages.
        If the list is empty, the order is valid.
    """

    errors = []

    # Extract the values from the CSV row.
    # csv.DictReader uses the first line of the CSV file as field names.
    order_code = order["order_code"]
    customer_name = order["customer_name"]
    quantity_text = order["quantity"]
    status = order["status"]

    # Check if the order code is missing, already present in the database,
    # or duplicated inside the same CSV file.
    if order_code == "":
        errors.append("missing order code")
    elif order_exists_in_database(order_code):
        errors.append("order code already exists in database")
    elif order_code in order_codes_in_file:
        errors.append("duplicated order code inside CSV file")

    # Check if the customer name is missing or too short.
    if customer_name == "":
        errors.append("missing customer name")
    elif len(customer_name) < 3:
        errors.append("customer name too short")

    # Check if the quantity is missing or not greater than zero.
    # At this stage, the project assumes that the quantity field contains a number.
    # More advanced error handling can be added later.
    if quantity_text == "":
        errors.append("missing quantity")
    elif not quantity_text.isdigit():
        errors.append("quantity must be a valid number")
    elif int(quantity_text) <= 0:
        errors.append("quantity must be greater than zero")
    
    # Check if the order status is one of the accepted values.
    if status not in VALID_STATUSES:
        errors.append("invalid status")

    return errors


def check_orders_from_csv():
    """
    Reads the CSV file, validates each order, and prints a final summary.

    This function represents the main workflow of the program:
    1. open the CSV file
    2. read each order
    3. validate the order
    4. print validation errors
    5. print a final summary
    """

    valid_orders = 0
    invalid_orders = 0

    # This list is used to detect duplicated order codes inside the CSV file itself.
    order_codes_in_file = []

    print("ORDER INTEGRITY CHECKER")
    print("-----------------------")

    # Open the CSV file in read mode.
    # DictReader converts each row into a dictionary.
    # Example:
    # {
    #     "order_code": "ORD001",
    #     "customer_name": "Mario Rossi",
    #     "quantity": "12",
    #     "status": "completed"
    # }
    with open(CSV_FILE_NAME, "r") as file:
        reader = csv.DictReader(file)

        # Process one order at a time.
        for order in reader:
            order_code = order["order_code"]

            print(f"\nChecking order: {order_code}")

            # Validate the current order and collect all errors.
            errors = validate_order(order, order_codes_in_file)

            # If there are no errors, the order is valid.
            if len(errors) == 0:
                print("Result: valid order")
                valid_orders = valid_orders + 1

            # Otherwise, print all validation errors.
            else:
                print("Result: invalid order")
                invalid_orders = invalid_orders + 1

                for error in errors:
                    print(f"- {error}")

            # Add the current order code to the list of codes already seen in the CSV.
            # This is done after validation so that the first occurrence is not marked
            # as a duplicate, while later occurrences are.
            order_codes_in_file.append(order_code)

    # Print the final validation summary.
    print("\nSUMMARY")
    print("-------")
    print(f"Valid orders: {valid_orders}")
    print(f"Invalid orders: {invalid_orders}")


# Program entry point.
# These three steps prepare the database, insert sample data, and then validate
# the orders coming from the CSV file.
create_database()
insert_sample_orders()
check_orders_from_csv()