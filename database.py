import sqlite3

from config import DATABASE_NAME, VALID_STATUSES
from normalizer import (
    normalize_customer_key,
    normalize_customer_name,
    normalize_order,
    normalize_order_code,
    normalize_status,
)


class BatchOrderInsertError(Exception):
    """Reports which order caused an atomic batch insert to roll back."""

    def __init__(self, order_code):
        self.order_code = order_code or "<unknown>"
        super().__init__(
            f"Could not import order {self.order_code}. No orders were saved."
        )


def _connect():
    """Creates a SQLite connection with foreign-key checks enabled."""

    connection = sqlite3.connect(DATABASE_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _create_orders_table(cursor):
    """Creates the current orders table linked to customers."""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            customer_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
                ON DELETE RESTRICT
        )
    """)


def _get_or_create_customer_with_cursor(cursor, customer_name):
    """Returns one customer ID, reusing normalized duplicate names."""

    normalized_name = normalize_customer_name(customer_name)
    normalized_key = normalize_customer_key(customer_name)

    cursor.execute("""
        SELECT id
        FROM customers
        WHERE normalized_name = ?
    """, (normalized_key,))

    row = cursor.fetchone()

    if row is not None:
        return row[0]

    cursor.execute("""
        INSERT INTO customers (name, normalized_name)
        VALUES (?, ?)
    """, (normalized_name, normalized_key))

    return cursor.lastrowid


def _migrate_legacy_orders(cursor):
    """Moves legacy customer_name values into the customers table."""

    cursor.execute("ALTER TABLE orders RENAME TO orders_legacy")
    _create_orders_table(cursor)

    cursor.execute("""
        SELECT id, order_code, customer_name, quantity, status
        FROM orders_legacy
        ORDER BY id
    """)

    for order_id, order_code, customer_name, quantity, status in cursor.fetchall():
        customer_id = _get_or_create_customer_with_cursor(
            cursor,
            customer_name,
        )

        cursor.execute("""
            INSERT INTO orders (
                id,
                order_code,
                customer_id,
                quantity,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            order_id,
            order_code,
            customer_id,
            quantity,
            status,
        ))

    cursor.execute("DROP TABLE orders_legacy")


def create_database():
    """
    Creates the current SQLite schema and migrates legacy orders safely.
    """

    connection = _connect()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL,
                old_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_history_order_code
            ON order_status_history (order_code)
        """)

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = 'orders'
        """)

        orders_table_exists = cursor.fetchone() is not None

        if not orders_table_exists:
            _create_orders_table(cursor)
        else:
            cursor.execute("PRAGMA table_info(orders)")
            order_columns = {row[1] for row in cursor.fetchall()}

            if "customer_id" not in order_columns:
                _migrate_legacy_orders(cursor)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_customer_id
            ON orders (customer_id)
        """)

        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def insert_sample_orders():
    """Inserts sample orders while reusing existing customers."""

    sample_orders = [
        {
            "order_code": "ORD001",
            "customer_name": "Mario Rossi",
            "quantity": 12,
            "status": "completed",
        },
        {
            "order_code": "ORD002",
            "customer_name": "Luca Bianchi",
            "quantity": 5,
            "status": "pending",
        },
    ]

    connection = _connect()
    cursor = connection.cursor()

    try:
        for order in sample_orders:
            normalized_order = normalize_order(order)
            customer_id = _get_or_create_customer_with_cursor(
                cursor,
                normalized_order["customer_name"],
            )

            cursor.execute("""
                INSERT OR IGNORE INTO orders (
                    order_code,
                    customer_id,
                    quantity,
                    status
                )
                VALUES (?, ?, ?, ?)
            """, (
                normalized_order["order_code"],
                customer_id,
                int(normalized_order["quantity"]),
                normalized_order["status"],
            ))

        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def row_to_order(row):
    """Converts a joined order/customer row into a dictionary."""

    return {
        "id": row[0],
        "order_code": row[1],
        "customer_id": row[2],
        "customer_name": row[3],
        "quantity": row[4],
        "status": row[5],
    }


def row_to_customer(row):
    """Converts a customer row into a dictionary."""

    return {
        "id": row[0],
        "name": row[1],
        "normalized_name": row[2],
    }


def row_to_status_history(row):
    """Converts a status history row into a dictionary."""

    return {
        "id": row[0],
        "order_code": row[1],
        "old_status": row[2],
        "new_status": row[3],
        "changed_at": row[4],
    }


def get_all_customers():
    """Returns all customers in alphabetical order."""

    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, normalized_name
        FROM customers
        ORDER BY normalized_name, id
    """)

    customers = [row_to_customer(row) for row in cursor.fetchall()]
    connection.close()
    return customers


def search_customers_by_name(customer_name):
    """Returns customers whose normalized name contains the search text."""

    search_key = normalize_customer_key(customer_name)

    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, normalized_name
        FROM customers
        WHERE normalized_name LIKE ?
        ORDER BY normalized_name, id
    """, (f"%{search_key}%",))

    customers = [row_to_customer(row) for row in cursor.fetchall()]
    connection.close()
    return customers


def get_or_create_customer(customer_name):
    """Returns a customer and avoids normalized-name duplicates."""

    connection = _connect()
    cursor = connection.cursor()

    try:
        customer_id = _get_or_create_customer_with_cursor(
            cursor,
            customer_name,
        )

        cursor.execute("""
            SELECT id, name, normalized_name
            FROM customers
            WHERE id = ?
        """, (customer_id,))

        customer = row_to_customer(cursor.fetchone())
        connection.commit()
        return customer
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_all_orders():
    """Returns all orders with their customer names."""

    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            orders.id,
            orders.order_code,
            customers.id,
            customers.name,
            orders.quantity,
            orders.status
        FROM orders
        INNER JOIN customers ON customers.id = orders.customer_id
        ORDER BY orders.id
    """)

    orders = [row_to_order(row) for row in cursor.fetchall()]
    connection.close()
    return orders


def get_order_by_code(order_code):
    """Returns one order by code, including its customer name."""

    normalized_code = normalize_order_code(order_code)

    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            orders.id,
            orders.order_code,
            customers.id,
            customers.name,
            orders.quantity,
            orders.status
        FROM orders
        INNER JOIN customers ON customers.id = orders.customer_id
        WHERE orders.order_code = ?
    """, (normalized_code,))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return row_to_order(row)


def get_status_history_for_order(order_code):
    """Returns all recorded status changes for one order, oldest first."""

    normalized_code = normalize_order_code(order_code)

    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, order_code, old_status, new_status, changed_at
        FROM order_status_history
        WHERE order_code = ?
        ORDER BY id
    """, (normalized_code,))

    history = [row_to_status_history(row) for row in cursor.fetchall()]
    connection.close()
    return history


def order_exists_in_database(order_code):
    """Checks whether an order code already exists in SQLite."""

    return get_order_by_code(order_code) is not None


def _insert_order_with_cursor(cursor, order):
    """Inserts one normalized order through an existing transaction cursor."""

    normalized_order = normalize_order(order)
    customer_id = _get_or_create_customer_with_cursor(
        cursor,
        normalized_order["customer_name"],
    )

    cursor.execute("""
        INSERT INTO orders (
            order_code,
            customer_id,
            quantity,
            status
        )
        VALUES (?, ?, ?, ?)
    """, (
        normalized_order["order_code"],
        customer_id,
        int(normalized_order["quantity"]),
        normalized_order["status"],
    ))

    return normalized_order


def insert_order_into_database(order):
    """Inserts an order and links it to a normalized customer."""

    connection = _connect()
    cursor = connection.cursor()

    try:
        normalized_order = _insert_order_with_cursor(cursor, order)
        connection.commit()
        return normalized_order
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()


def insert_orders_into_database(orders):
    """Inserts every order in one transaction or rolls the whole batch back."""

    connection = _connect()
    cursor = connection.cursor()
    inserted_orders = []
    current_order_code = "<unknown>"

    try:
        for order in orders:
            if isinstance(order, dict):
                current_order_code = normalize_order_code(
                    order.get("order_code", "")
                )

            inserted_orders.append(
                _insert_order_with_cursor(cursor, order)
            )

        connection.commit()
        return inserted_orders
    except Exception as error:
        connection.rollback()
        raise BatchOrderInsertError(current_order_code) from error
    finally:
        connection.close()


def get_order_statistics():
    """Returns statistics about orders grouped by status."""

    connection = _connect()
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
        "cancelled": 0,
    }

    for status, count in rows:
        statistics[status] = count

    statistics["total"] = sum(statistics.values())
    return statistics


def update_order_status_in_database(order_code, new_status):
    """Updates an order status and records the change transactionally."""

    normalized_code = normalize_order_code(order_code)
    normalized_status = normalize_status(new_status)

    if normalized_status not in VALID_STATUSES:
        return False

    connection = _connect()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT status
            FROM orders
            WHERE order_code = ?
        """, (normalized_code,))

        row = cursor.fetchone()

        if row is None:
            return False

        old_status = row[0]

        if old_status == normalized_status:
            return True

        cursor.execute("""
            UPDATE orders
            SET status = ?
            WHERE order_code = ?
        """, (normalized_status, normalized_code))

        if cursor.rowcount == 0:
            connection.rollback()
            return False

        cursor.execute("""
            INSERT INTO order_status_history (
                order_code,
                old_status,
                new_status
            )
            VALUES (?, ?, ?)
        """, (
            normalized_code,
            old_status,
            normalized_status,
        ))

        connection.commit()
        return True
    except sqlite3.Error:
        connection.rollback()
        return False
    finally:
        connection.close()


def delete_order_from_database(order_code):
    """Deletes an order while retaining its status audit history."""

    normalized_code = normalize_order_code(order_code)

    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM orders
        WHERE order_code = ?
    """, (normalized_code,))

    connection.commit()
    deleted_rows = cursor.rowcount
    connection.close()

    return deleted_rows > 0
