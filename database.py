import sqlite3

from config import DATABASE_NAME, VALID_STATUSES
from normalizer import normalize_order, normalize_order_code, normalize_status


def create_database():
    """
    Creates the SQLite database and the orders table if they do not already exist.
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


def row_to_order(row):
    """
    Converts a database row into a dictionary.

    This makes database results easier to reuse in both CLI and future GUI code.
    """

    return {
        "id": row[0],
        "order_code": row[1],
        "customer_name": row[2],
        "quantity": row[3],
        "status": row[4]
    }


def get_all_orders():
    """
    Returns all orders stored in the database.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, order_code, customer_name, quantity, status
        FROM orders
        ORDER BY id
    """)

    rows = cursor.fetchall()

    connection.close()

    orders = []

    for row in rows:
        orders.append(row_to_order(row))

    return orders


def get_order_by_code(order_code):
    """
    Returns one order by order code.

    If no order is found, returns None.
    """

    normalized_code = normalize_order_code(order_code)

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, order_code, customer_name, quantity, status
        FROM orders
        WHERE order_code = ?
    """, (normalized_code,))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return row_to_order(row)


def order_exists_in_database(order_code):
    """
    Checks whether an order code already exists in the SQLite database.
    """

    return get_order_by_code(order_code) is not None


def insert_order_into_database(order):
    """
    Inserts a valid order into the SQLite database.
    """

    normalized_order = normalize_order(order)

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO orders (order_code, customer_name, quantity, status)
        VALUES (?, ?, ?, ?)
    """, (
        normalized_order["order_code"],
        normalized_order["customer_name"],
        int(normalized_order["quantity"]),
        normalized_order["status"]
    ))

    connection.commit()
    connection.close()


def get_order_statistics():
    """
    Returns statistics about the orders stored in the database.
    """

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM orders
        GROUP BY status
    """)

    rows = cursor.fetchall()

    connection.close()

    statistics = {
        "completed": 0,
        "pending": 0,
        "cancelled": 0
    }

    for row in rows:
        status = row[0]
        count = row[1]

        statistics[status] = count

    statistics["total"] = sum(statistics.values())

    return statistics


def update_order_status_in_database(order_code, new_status):
    """
    Updates the status of an existing order.

    Returns True if an order was updated, False otherwise.
    """

    normalized_code = normalize_order_code(order_code)
    normalized_status = normalize_status(new_status)

    if normalized_status not in VALID_STATUSES:
        return False

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE orders
        SET status = ?
        WHERE order_code = ?
    """, (normalized_status, normalized_code))

    connection.commit()

    updated_rows = cursor.rowcount

    connection.close()

    return updated_rows > 0


def delete_order_from_database(order_code):
    """
    Deletes an order from the database.

    Returns True if an order was deleted, False otherwise.
    """

    normalized_code = normalize_order_code(order_code)

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM orders
        WHERE order_code = ?
    """, (normalized_code,))

    connection.commit()

    deleted_rows = cursor.rowcount

    connection.close()

    return deleted_rows > 0