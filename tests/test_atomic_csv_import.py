import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import database
import services
from csv_import_preview import build_csv_import_preview


class AtomicOrderBatchDatabaseTests(unittest.TestCase):
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
        database.create_database()

    def tearDown(self):
        self.database_patcher.stop()
        self.temp_directory.cleanup()

    def test_batch_commits_all_orders_and_reuses_customer(self):
        inserted = database.insert_orders_into_database([
            {
                "order_code": "ord100",
                "customer_name": " Mario   Rossi ",
                "quantity": "3",
                "status": "Pending",
            },
            {
                "order_code": "ORD101",
                "customer_name": "mario rossi",
                "quantity": "5",
                "status": "completed",
            },
        ])

        orders = database.get_all_orders()
        customers = database.get_all_customers()

        self.assertEqual(
            [order["order_code"] for order in inserted],
            ["ORD100", "ORD101"],
        )
        self.assertEqual(len(orders), 2)
        self.assertEqual(len(customers), 1)
        self.assertEqual(orders[0]["customer_id"], orders[1]["customer_id"])

    def test_batch_rolls_back_orders_and_customers_after_late_conflict(self):
        database.insert_order_into_database({
            "order_code": "ORD202",
            "customer_name": "Existing Customer",
            "quantity": "2",
            "status": "pending",
        })

        with self.assertRaises(database.BatchOrderInsertError) as context:
            database.insert_orders_into_database([
                {
                    "order_code": "ORD201",
                    "customer_name": "New Batch Customer",
                    "quantity": "4",
                    "status": "pending",
                },
                {
                    "order_code": "ORD202",
                    "customer_name": "Another Customer",
                    "quantity": "1",
                    "status": "completed",
                },
            ])

        orders = database.get_all_orders()
        customers = database.get_all_customers()

        self.assertEqual(context.exception.order_code, "ORD202")
        self.assertEqual(
            [order["order_code"] for order in orders],
            ["ORD202"],
        )
        self.assertEqual(
            [customer["name"] for customer in customers],
            ["Existing Customer"],
        )

    def test_batch_wraps_sqlite_conflict_as_order_specific_error(self):
        database.insert_order_into_database({
            "order_code": "ORD300",
            "customer_name": "Existing Customer",
            "quantity": "2",
            "status": "pending",
        })

        with self.assertRaises(database.BatchOrderInsertError) as context:
            database.insert_orders_into_database([{
                "order_code": "ORD300",
                "customer_name": "Existing Customer",
                "quantity": "2",
                "status": "pending",
            }])

        self.assertIsInstance(context.exception.__cause__, sqlite3.IntegrityError)
        self.assertIn("ORD300", str(context.exception))


class AtomicCsvImportServiceTests(unittest.TestCase):
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
        database.create_database()

    def tearDown(self):
        self.database_patcher.stop()
        self.temp_directory.cleanup()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report")
    def test_late_conflict_preserves_csv_and_rolls_back_earlier_order(
        self,
        mock_report,
        mock_clear,
    ):
        database.insert_order_into_database({
            "order_code": "ORD402",
            "customer_name": "Existing Customer",
            "quantity": "2",
            "status": "pending",
        })
        stale_preview = build_csv_import_preview([
            {
                "order": {
                    "order_code": "ORD401",
                    "customer_name": "New Batch Customer",
                    "quantity": "4",
                    "status": "pending",
                },
                "errors": [],
            },
            {
                "order": {
                    "order_code": "ORD402",
                    "customer_name": "Another Customer",
                    "quantity": "1",
                    "status": "completed",
                },
                "errors": [],
            },
        ])

        result = services.import_csv_orders(stale_preview, confirmed=True)

        orders = database.get_all_orders()
        customers = database.get_all_customers()

        self.assertFalse(result["success"])
        self.assertEqual(result["saved_orders"], [])
        self.assertFalse(result["csv_cleared"])
        self.assertIn("ORD402", result["message"])
        self.assertEqual(
            [order["order_code"] for order in orders],
            ["ORD402"],
        )
        self.assertEqual(
            [customer["name"] for customer in customers],
            ["Existing Customer"],
        )
        mock_report.assert_not_called()
        mock_clear.assert_not_called()


if __name__ == "__main__":
    unittest.main()
