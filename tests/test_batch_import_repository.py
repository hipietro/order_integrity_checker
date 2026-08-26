import sqlite3
import tempfile
import unittest
from pathlib import Path

from batch_import_repository import insert_orders_atomically


class TestAtomicBatchImportRepository(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "orders.db"
        connection = sqlite3.connect(self.database_path)
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
                    ON DELETE RESTRICT
            );
            """
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_successful_batch_reuses_normalized_customer(self):
        orders = [
            {
                "order_code": "ord100",
                "customer_name": "  Mario   Rossi ",
                "quantity": "2",
                "status": "PENDING",
            },
            {
                "order_code": "ORD101",
                "customer_name": "mario rossi",
                "quantity": "3",
                "status": "completed",
            },
        ]

        saved = insert_orders_atomically(
            orders,
            database_name=str(self.database_path),
        )

        self.assertEqual(
            [order["order_code"] for order in saved],
            ["ORD100", "ORD101"],
        )

        connection = sqlite3.connect(self.database_path)
        customers = connection.execute(
            "SELECT id, normalized_name FROM customers ORDER BY id"
        ).fetchall()
        stored_orders = connection.execute(
            "SELECT order_code, customer_id, quantity, status "
            "FROM orders ORDER BY id"
        ).fetchall()
        connection.close()

        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0][1], "mario rossi")
        self.assertEqual(
            stored_orders,
            [
                ("ORD100", customers[0][0], 2, "pending"),
                ("ORD101", customers[0][0], 3, "completed"),
            ],
        )

    def test_late_duplicate_rolls_back_orders_and_new_customers(self):
        connection = sqlite3.connect(self.database_path)
        connection.execute(
            "INSERT INTO customers (name, normalized_name) VALUES (?, ?)",
            ("Existing Customer", "existing customer"),
        )
        existing_customer_id = connection.execute(
            "SELECT id FROM customers WHERE normalized_name = ?",
            ("existing customer",),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO orders (order_code, customer_id, quantity, status)
            VALUES (?, ?, ?, ?)
            """,
            ("ORD999", existing_customer_id, 1, "pending"),
        )
        connection.commit()
        connection.close()

        orders = [
            {
                "order_code": "ORD200",
                "customer_name": "Brand New Customer",
                "quantity": "4",
                "status": "pending",
            },
            {
                "order_code": "ORD999",
                "customer_name": "Another New Customer",
                "quantity": "5",
                "status": "completed",
            },
        ]

        with self.assertRaises(sqlite3.IntegrityError):
            insert_orders_atomically(
                orders,
                database_name=str(self.database_path),
            )

        connection = sqlite3.connect(self.database_path)
        stored_codes = connection.execute(
            "SELECT order_code FROM orders ORDER BY id"
        ).fetchall()
        customers = connection.execute(
            "SELECT normalized_name FROM customers ORDER BY id"
        ).fetchall()
        connection.close()

        self.assertEqual(stored_codes, [("ORD999",)])
        self.assertEqual(customers, [("existing customer",)])


if __name__ == "__main__":
    unittest.main()
