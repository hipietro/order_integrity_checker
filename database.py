import sqlite3

from config import DATABASE_NAME, VALID_STATUSES


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