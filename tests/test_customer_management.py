import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import database
import services
from csv_import_preview import build_csv_import_preview
from normalizer import normalize_customer_key, normalize_customer_name


class CustomerDatabaseTestCase(unittest.TestCase):
    """Provides an isolated SQLite database for customer tests."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(
            self.temp_directory.name,
            "test_orders.db",
        )
        self.database_patcher = patch(
            "database.DATABASE_NAME",
            self.database_path,
        )
        self.database_patcher.start()

    def tearDown(self):
        self.database_patcher.stop()
        self.temp_directory.cleanup()


class TestCustomerNormalization(unittest.TestCase):
    def test_customer_name_collapses_repeated_spaces(self):
        self.assertEqual(
            normalize_customer_name("  Mario   Rossi  "),
            "Mario Rossi",
        )

    def test_customer_key_is_case_insensitive(self):
        self.assertEqual(
            normalize_customer_key("  MARIO   Rossi "),
            "mario rossi",
        )


class TestCustomerDatabase(CustomerDatabaseTestCase):
    def setUp(self):
        super().setUp()
        database.create_database()

    def test_equivalent_names_reuse_one_customer(self):
        database.insert_order_into_database({
            "order_code": "ORD100",
            "customer_name": " Mario   Rossi ",
            "quantity": "5",
            "status": "pending",
        })
        database.insert_order_into_database({
            "order_code": "ORD101",
            "customer_name": "mario rossi",
            "quantity": "2",
            "status": "completed",
        })

        customers = database.get_all_customers()
        orders = database.get_all_orders()

        self.assertEqual(len(customers), 1)
        self.assertEqual(customers[0]["name"], "Mario Rossi")
        self.assertEqual(customers[0]["normalized_name"], "mario rossi")
        self.assertEqual(orders[0]["customer_id"], orders[1]["customer_id"])
        self.assertEqual(orders[0]["customer_name"], "Mario Rossi")
        self.assertEqual(orders[1]["customer_name"], "Mario Rossi")

    def test_customer_search_is_partial_and_case_insensitive(self):
        database.get_or_create_customer("Mario Rossi")
        database.get_or_create_customer("Anna Verdi")

        results = database.search_customers_by_name("ROSS")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Mario Rossi")

    def test_orders_store_customer_id_instead_of_customer_name(self):
        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(orders)")
        columns = {row[1] for row in cursor.fetchall()}
        connection.close()

        self.assertIn("customer_id", columns)
        self.assertNotIn("customer_name", columns)


class TestLegacyCustomerMigration(CustomerDatabaseTestCase):
    def test_legacy_orders_are_migrated_without_duplicate_customers(self):
        connection = sqlite3.connect(self.database_path)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL
            )
        """)
        cursor.executemany("""
            INSERT INTO orders (
                order_code,
                customer_name,
                quantity,
                status
            )
            VALUES (?, ?, ?, ?)
        """, [
            ("ORD200", "Mario Rossi", 5, "pending"),
            ("ORD201", " mario   rossi ", 3, "completed"),
        ])
        connection.commit()
        connection.close()

        database.create_database()

        customers = database.get_all_customers()
        orders = database.get_all_orders()

        self.assertEqual(len(customers), 1)
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]["order_code"], "ORD200")
        self.assertEqual(orders[1]["order_code"], "ORD201")
        self.assertEqual(orders[0]["customer_id"], orders[1]["customer_id"])


class TestCustomerServiceIntegration(CustomerDatabaseTestCase):
    def setUp(self):
        super().setUp()
        database.create_database()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report", return_value=0)
    def test_manual_creation_and_csv_import_share_customer(
        self,
        mock_report,
        mock_clear_csv,
    ):
        created = services.create_order({
            "order_code": "ORD300",
            "customer_name": "Anna Verdi",
            "quantity": "4",
            "status": "pending",
        })

        preview = build_csv_import_preview([{
            "order": {
                "order_code": "ORD301",
                "customer_name": "  ANNA   VERDI ",
                "quantity": "2",
                "status": "completed",
            },
            "errors": [],
        }])
        imported = services.import_csv_orders(preview, confirmed=True)

        customers = services.list_customers()
        matching_customers = services.search_customers("anna")
        orders = database.get_all_orders()

        self.assertTrue(created["success"])
        self.assertTrue(imported["success"])
        self.assertEqual(len(customers), 1)
        self.assertEqual(len(matching_customers), 1)
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0]["customer_id"], orders[1]["customer_id"])
        mock_report.assert_called_once()
        mock_clear_csv.assert_called_once()


class TestCustomerOverviewService(unittest.TestCase):
    @patch("services.get_all_orders")
    @patch("services.search_customers")
    def test_customer_overview_counts_orders_per_customer(
        self,
        mock_search_customers,
        mock_get_all_orders,
    ):
        mock_search_customers.return_value = [
            {
                "id": 1,
                "name": "Mario Rossi",
                "normalized_name": "mario rossi",
            },
            {
                "id": 2,
                "name": "Anna Verdi",
                "normalized_name": "anna verdi",
            },
        ]
        mock_get_all_orders.return_value = [
            {"customer_id": 1},
            {"customer_id": 1},
            {"customer_id": 2},
        ]

        overview = services.get_customer_overview()

        self.assertEqual(overview[0]["order_count"], 2)
        self.assertEqual(overview[1]["order_count"], 1)
        mock_search_customers.assert_called_once_with("")
        mock_get_all_orders.assert_called_once_with()

    @patch("services.get_all_orders", return_value=[])
    @patch("services.search_customers")
    def test_customer_overview_reuses_filtered_customer_search(
        self,
        mock_search_customers,
        mock_get_all_orders,
    ):
        mock_search_customers.return_value = [{
            "id": 7,
            "name": "ACME Srl",
            "normalized_name": "acme srl",
        }]

        overview = services.get_customer_overview("  acme  ")

        self.assertEqual(len(overview), 1)
        self.assertEqual(overview[0]["id"], 7)
        self.assertEqual(overview[0]["order_count"], 0)
        mock_search_customers.assert_called_once_with("  acme  ")
        mock_get_all_orders.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
