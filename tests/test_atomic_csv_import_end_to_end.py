import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import atomic_import_service
import services
from batch_import_repository import insert_orders_atomically


class TestAtomicCsvImportEndToEnd(unittest.TestCase):
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
        connection.execute(
            "INSERT INTO customers (name, normalized_name) VALUES (?, ?)",
            ("Existing Customer", "existing customer"),
        )
        customer_id = connection.execute(
            "SELECT id FROM customers WHERE normalized_name = ?",
            ("existing customer",),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO orders (order_code, customer_id, quantity, status)
            VALUES (?, ?, ?, ?)
            """,
            ("ORD999", customer_id, 1, "pending"),
        )
        connection.commit()
        connection.close()

    def tearDown(self):
        self.temp_directory.cleanup()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report")
    def test_late_conflict_rolls_back_service_batch_and_preserves_csv(
        self,
        mock_generate_invalid_orders_report,
        mock_clear_csv_orders,
    ):
        preview = {
            "validation_results": [
                {
                    "order": {
                        "order_code": "ORD200",
                        "customer_name": "Brand New Customer",
                        "quantity": "4",
                        "status": "pending",
                    },
                    "errors": [],
                },
                {
                    "order": {
                        "order_code": "ORD999",
                        "customer_name": "Another New Customer",
                        "quantity": "5",
                        "status": "completed",
                    },
                    "errors": [],
                },
            ]
        }

        def persist_to_temp_database(orders):
            return insert_orders_atomically(
                orders,
                database_name=str(self.database_path),
            )

        with patch.object(
            atomic_import_service,
            "insert_orders_atomically",
            side_effect=persist_to_temp_database,
        ):
            result = services.import_csv_orders(preview, confirmed=True)

        self.assertFalse(result["success"])
        self.assertEqual(result["saved_orders"], [])
        self.assertFalse(result["csv_cleared"])
        mock_generate_invalid_orders_report.assert_not_called()
        mock_clear_csv_orders.assert_not_called()

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
