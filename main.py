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
    """
    Inserts a few sample orders into the database.

    These records simulate orders that already exist in the company's internal
    system before importing a new CSV file.
    """

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

    cursor.execute("""
        SELECT order_code
        FROM orders
        WHERE order_code = ?
    """, (order_code,))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def insert_order_into_database(order):
    """
    Inserts a valid order into the SQLite database.

    This function is called only after the order has passed all validation checks.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO orders (order_code, customer_name, quantity, status)
        VALUES (?, ?, ?, ?)
    """, (
        order["order_code"],
        order["customer_name"],
        int(order["quantity"]),
        order["status"]
    ))

    connection.commit()
    connection.close()


def read_orders_from_csv():
    """
    Reads all orders from the CSV file.

    Returns:
        A list of orders.
        Each order is represented as a dictionary.
    """

    orders = []

    with open(CSV_FILE_NAME, "r") as file:
        reader = csv.DictReader(file)

        for order in reader:
            orders.append(order)

    return orders


def validate_order(order, order_codes_in_file):
    """
    Validates a single order coming from the CSV file.

    The function checks:
    - missing order code
    - duplicated order code inside the CSV file
    - duplicated order code in the database
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

    order_code = order["order_code"]
    customer_name = order["customer_name"]
    quantity_text = order["quantity"]
    status = order["status"]

    if order_code == "":
        errors.append("missing order code")
    elif order_code in order_codes_in_file:
        errors.append("duplicated order code inside CSV file")
    elif order_exists_in_database(order_code):
        errors.append("order code already exists in database")

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


def validate_all_csv_orders():
    """
    Validates all orders from the CSV file.

    Returns:
        A list of validation results.

    Each validation result contains:
    - the original order
    - the list of validation errors
    """

    orders = read_orders_from_csv()
    order_codes_in_file = []
    validation_results = []

    for order in orders:
        errors = validate_order(order, order_codes_in_file)

        validation_results.append({
            "order": order,
            "errors": errors
        })

        order_codes_in_file.append(order["order_code"])

    return validation_results


def import_valid_orders():
    """
    Validates all CSV orders and saves only valid orders into the database.
    Invalid orders are not inserted.
    """

    validation_results = validate_all_csv_orders()

    valid_orders = 0
    invalid_orders = 0

    print("\nIMPORT RESULT")
    print("-------------")

    for result in validation_results:
        order = result["order"]
        errors = result["errors"]
        order_code = order["order_code"]

        if len(errors) == 0:
            insert_order_into_database(order)
            valid_orders = valid_orders + 1
            print(f"{order_code}: saved into database")
        else:
            invalid_orders = invalid_orders + 1
            print(f"{order_code}: NOT saved. For reasons: press 2")

    print("\nSUMMARY")
    print("-------")
    print(f"Saved orders: {valid_orders}")
    print(f"Invalid orders: {invalid_orders}")


def show_invalid_orders():
    """
    Shows only the invalid orders found in the CSV file.

    For each invalid order, the function prints the order code and the reasons
    why the order is not valid.
    """

    validation_results = validate_all_csv_orders()

    found_invalid_orders = False

    print("\nINVALID CSV ORDERS")
    print("------------------")

    for result in validation_results:
        order = result["order"]
        errors = result["errors"]

        if len(errors) > 0:
            found_invalid_orders = True

            print(f"\nOrder code: {order['order_code']}")
            print(f"Customer name: {order['customer_name']}")
            print(f"Quantity: {order['quantity']}")
            print(f"Status: {order['status']}")
            print("Errors:")

            for error in errors:
                print(f"- {error}")

    if not found_invalid_orders:
        print("No invalid orders found.")


def show_database_orders():
    """
    Prints all orders currently stored in the SQLite database.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, order_code, customer_name, quantity, status
        FROM orders
        ORDER BY id
    """)

    orders = cursor.fetchall()

    connection.close()

    print("\nDATABASE ORDERS")
    print("---------------")

    if len(orders) == 0:
        print("No orders found in the database.")
    else:
        for order in orders:
            print(
                f"ID: {order[0]} | "
                f"Code: {order[1]} | "
                f"Customer: {order[2]} | "
                f"Quantity: {order[3]} | "
                f"Status: {order[4]}"
            )

def clear_csv_orders():
    """
    Clears the CSV file while keeping the header row.

    This allows the file to remain valid and ready for new orders.
    """

    with open(CSV_FILE_NAME, "w") as file:
        file.write("order_code,customer_name,quantity,status\n")

    print(f"{CSV_FILE_NAME} cleared successfully.")

def insert_order_manually():
    """
    Allows the user to insert a new order manually through the command line.

    The function prompts the user for each field of the order, validates the input,
    and if the order is valid, it is saved into the database.
    """

    print("\nINSERT NEW ORDER")
    print("----------------")

    order_code = input("Order code: ")
    customer_name = input("Customer name: ")
    quantity = input("Quantity: ")
    status = input("Status (completed, pending, cancelled): ")

    order = {
        "order_code": order_code,
        "customer_name": customer_name,
        "quantity": quantity,
        "status": status
    }

    errors = validate_order(order, [])

    if len(errors) == 0:
        insert_order_into_database(order)
        print(f"Order {order_code} inserted successfully.")
    else:
        print(f"Order {order_code} is invalid. Errors:")
        for error in errors:
            print(f"- {error}")

def search_order_by_code():
    """
    Searches for an order in the SQLite database using its order code.

    The function asks the user to type an order code, then searches the database
    and prints the matching order if it exists.
    """

    order_code = input("Enter order code to search: ")

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, order_code, customer_name, quantity, status
        FROM orders
        WHERE order_code = ?
    """, (order_code,))

    order = cursor.fetchone()

    connection.close()

    print("\nSEARCH RESULT")
    print("-------------")

    if order is None:
        print(f"No order found with code {order_code}.")
    else:
        print(
            f"ID: {order[0]} | "
            f"Code: {order[1]} | "
            f"Customer: {order[2]} | "
            f"Quantity: {order[3]} | "
            f"Status: {order[4]}"
        )

def show_order_statistics():
    """
    Shows statistics about the orders stored in the database.

    The function counts how many orders exist for each status:
    completed, pending, and cancelled.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM orders
        GROUP BY status
    """)

    results = cursor.fetchall()

    connection.close()

    statistics = {
        "completed": 0,
        "pending": 0,
        "cancelled": 0
    }

    for result in results:
        status = result[0]
        count = result[1]

        statistics[status] = count

    print("\nORDER STATISTICS")
    print("----------------")
    print(f"Completed orders: {statistics['completed']}")
    print(f"Pending orders: {statistics['pending']}")
    print(f"Cancelled orders: {statistics['cancelled']}")
    print(f"Total orders: {sum(statistics.values())}")


def update_order_status():
    """
    Updates the status of an existing order in the SQLite database.

    The function asks the user for an order code, checks if the order exists,
    then asks for a new status and updates the database if the status is valid.
    """

    order_code = input("Enter order code to update: ")

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, order_code, customer_name, quantity, status
        FROM orders
        WHERE order_code = ?
    """, (order_code,))

    order = cursor.fetchone()

    if order is None:
        connection.close()
        print(f"No order found with code {order_code}.")
        return

    print("\nORDER FOUND")
    print("-----------")
    print(
        f"ID: {order[0]} | "
        f"Code: {order[1]} | "
        f"Customer: {order[2]} | "
        f"Quantity: {order[3]} | "
        f"Current status: {order[4]}"
    )

    new_status = input("Enter new status (completed, pending, cancelled): ")

    if new_status not in VALID_STATUSES:
        connection.close()
        print(f"Invalid status. Accepted values are: {', '.join(VALID_STATUSES)}")
        return

    cursor.execute("""
        UPDATE orders
        SET status = ?
        WHERE order_code = ?
    """, (new_status, order_code))

    connection.commit()
    connection.close()

    print(f"Order {order_code} updated successfully.")

def show_menu():
    """
    Shows the main menu and handles the user's choices.
    """

    while True:
        print("\nORDER INTEGRITY CHECKER")
        print("-----------------------")
        print("1. Import valid CSV orders into database")
        print("2. Show invalid CSV orders")
        print("3. Show database orders")
        print("4. Clear new_orders.csv file")
        print("5. Search order by code")
        print("6. Insert order manually")
        print("7. Show order statistics")
        print("8. Update order status")
        print("9. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            import_valid_orders()
        elif choice == "2":
            show_invalid_orders()
        elif choice == "3":
            show_database_orders()
        elif choice == "4":
            clear_csv_orders()
        elif choice == "5":
            search_order_by_code()
        elif choice == "6":
            insert_order_manually()
        elif choice == "7":
            show_order_statistics()
        elif choice == "8":
            update_order_status()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 9.")


# Program entry point.
# The database is prepared before showing the menu.
create_database()
insert_sample_orders()
show_menu()