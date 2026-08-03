import os
import tempfile
import unittest
from unittest.mock import patch

import database
import services


class TestStatusHistoryDatabase(unittest.TestCase):
    """Integration tests that use an isolated temporary SQLite database."""

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = os.path.join(
            self.temp_directory.name,
            "test_orders.db"
        )
        self.database_patcher = patch(
            "database.DATABASE_NAME",
            self.database_path
        )
        self.database_patcher.start()

        database.create_database()
        database.insert_order_into_database({
            "order_code": "ORD100",
            "customer_name": "Test Customer",
            "quantity": "5",
            "status": "pending"
        })

    def tearDown(self):
        self.database_patcher.stop()
        self.temp_directory.cleanup()

    def test_status_update_creates_history_entry(self):
        updated = database.update_order_status_in_database(
            " ord100 ",
            " Completed "
        )

        history = database.get_status_history_for_order("ORD100")

        self.assertTrue(updated)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["order_code"], "ORD100")
        self.assertEqual(history[0]["old_status"], "pending")
        self.assertEqual(history[0]["new_status"], "completed")
        self.assertTrue(history[0]["changed_at"])

    def test_multiple_status_changes_are_returned_oldest_first(self):
        database.update_order_status_in_database("ORD100", "completed")
        database.update_order_status_in_database("ORD100", "cancelled")

        history = database.get_status_history_for_order("ORD100")

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["old_status"], "pending")
        self.assertEqual(history[0]["new_status"], "completed")
        self.assertEqual(history[1]["old_status"], "completed")
        self.assertEqual(history[1]["new_status"], "cancelled")
        self.assertLess(history[0]["id"], history[1]["id"])

    def test_same_status_does_not_create_duplicate_history(self):
        updated = database.update_order_status_in_database(
            "ORD100",
            "pending"
        )

        history = database.get_status_history_for_order("ORD100")

        self.assertTrue(updated)
        self.assertEqual(history, [])

    def test_invalid_status_does_not_change_order_or_history(self):
        updated = database.update_order_status_in_database(
            "ORD100",
            "shipped"
        )

        order = database.get_order_by_code("ORD100")
        history = database.get_status_history_for_order("ORD100")

        self.assertFalse(updated)
        self.assertEqual(order["status"], "pending")
        self.assertEqual(history, [])

    def test_history_is_retained_after_order_deletion(self):
        database.update_order_status_in_database("ORD100", "completed")
        database.delete_order_from_database("ORD100")

        order = database.get_order_by_code("ORD100")
        history = database.get_status_history_for_order("ORD100")

        self.assertIsNone(order)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["new_status"], "completed")


class TestStatusHistoryService(unittest.TestCase):
    """Unit tests for the reusable status history service contract."""

    @patch("services.get_status_history_for_order")
    @patch("services.get_order_by_code")
    def test_service_returns_active_order_history(
        self,
        mock_get_order_by_code,
        mock_get_status_history
    ):
        mock_get_order_by_code.return_value = {
            "id": 1,
            "order_code": "ORD001",
            "customer_name": "Mario Rossi",
            "quantity": 5,
            "status": "completed"
        }
        mock_get_status_history.return_value = [{
            "id": 1,
            "order_code": "ORD001",
            "old_status": "pending",
            "new_status": "completed",
            "changed_at": "2026-08-03 08:00:00"
        }]

        result = services.get_order_status_history(" ord001 ")

        self.assertTrue(result["success"])
        self.assertEqual(result["order_code"], "ORD001")
        self.assertEqual(result["current_status"], "completed")
        self.assertEqual(len(result["history"]), 1)
        mock_get_order_by_code.assert_called_once_with("ORD001")
        mock_get_status_history.assert_called_once_with("ORD001")

    @patch("services.get_status_history_for_order")
    @patch("services.get_order_by_code", return_value=None)
    def test_service_returns_retained_history_for_deleted_order(
        self,
        mock_get_order_by_code,
        mock_get_status_history
    ):
        mock_get_status_history.return_value = [{
            "id": 1,
            "order_code": "ORD001",
            "old_status": "pending",
            "new_status": "cancelled",
            "changed_at": "2026-08-03 08:00:00"
        }]

        result = services.get_order_status_history("ORD001")

        self.assertTrue(result["success"])
        self.assertIsNone(result["current_status"])
        self.assertEqual(len(result["history"]), 1)

    @patch("services.get_status_history_for_order", return_value=[])
    @patch("services.get_order_by_code", return_value=None)
    def test_service_reports_missing_order_and_history(
        self,
        mock_get_order_by_code,
        mock_get_status_history
    ):
        result = services.get_order_status_history("missing")

        self.assertFalse(result["success"])
        self.assertEqual(result["order_code"], "MISSING")
        self.assertEqual(result["history"], [])
        self.assertIn("No order or status history found", result["message"])


if __name__ == "__main__":
    unittest.main()
