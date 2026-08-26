import sqlite3

from config import DATABASE_NAME
from normalizer import (
    normalize_customer_key,
    normalize_customer_name,
    normalize_order,
)


def _connect(database_name):
    """Creates a SQLite connection suitable for one atomic import batch."""

    connection = sqlite3.connect(database_name)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _get_or_create_customer(cursor, customer_name):
    """Returns a customer ID while reusing normalized customer names."""

    normalized_name = normalize_customer_name(customer_name)
    normalized_key = normalize_customer_key(customer_name)

    cursor.execute(
        """
        SELECT id
        FROM customers
        WHERE normalized_name = ?
        """,
        (normalized_key,),
    )
    row = cursor.fetchone()

    if row is not None:
        return row[0]

    cursor.execute(
        """
        INSERT INTO customers (name, normalized_name)
        VALUES (?, ?)
        """,
        (normalized_name, normalized_key),
    )
    return cursor.lastrowid


def insert_orders_atomically(orders, database_name=DATABASE_NAME):
    """Inserts every order in one transaction or persists none of them.

    The caller is expected to pass already validated orders. Normalization is
    repeated at the database boundary so manual and CSV persistence paths use
    the same stored representation.
    """

    normalized_orders = [normalize_order(order) for order in orders]

    if not normalized_orders:
        return []

    connection = _connect(database_name)
    cursor = connection.cursor()

    try:
        for order in normalized_orders:
            customer_id = _get_or_create_customer(
                cursor,
                order["customer_name"],
            )
            cursor.execute(
                """
                INSERT INTO orders (
                    order_code,
                    customer_id,
                    quantity,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    order["order_code"],
                    customer_id,
                    int(order["quantity"]),
                    order["status"],
                ),
            )

        connection.commit()
        return normalized_orders
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
