import os
import tempfile
import unittest
from functools import partial
from unittest.mock import patch

import batch_import_repository
import database
import services
from csv_import_preview import build_csv_import_preview


class AtomicCsvImportIntegrationTests(unittest.TestCase):
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
        manual_result = database.insert_order_into_database({
            "order_code": "ORD402",
            "customer_name": "Existing Customer",
            "quantity": "2",
            "status": "pending",
        })
        self.assertIsNone(manual_result)
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
        batch_insert = partial(
            batch_import_repository.insert_orders_atomically,
            database_name=self.database_path,
        )

        with patch(
            "atomic_import_service.insert_orders_atomically",
            batch_insert,
        ):
            result = services.import_csv_orders(
                stale_preview,
                confirmed=True,
            )

        orders = database.get_all_orders()
        customers = database.get_all_customers()

        self.assertFalse(result["success"])
        self.assertEqual(result["saved_orders"], [])
        self.assertFalse(result["csv_cleared"])
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
