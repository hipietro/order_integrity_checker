import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import database
import services
from application_errors import OrderConflictError, StorageUnavailableError


VALID_ORDER = {
    "order_code": "ORD100",
    "customer_name": "Mario Rossi",
    "quantity": "2",
    "status": "pending",
}


class DatabaseWriteFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "orders.db"
        self.database_patch = patch(
            "database.DATABASE_NAME",
            str(self.database_path),
        )
        self.timeout_patch = patch(
            "database.SQLITE_BUSY_TIMEOUT_SECONDS",
            0.01,
        )
        self.database_patch.start()
        self.timeout_patch.start()
        database.create_database()
        database.insert_order_into_database(VALID_ORDER)

    def tearDown(self):
        self.timeout_patch.stop()
        self.database_patch.stop()
        self.temp_directory.cleanup()

    def test_duplicate_insert_maps_integrity_error_to_conflict(self):
        with self.assertRaises(OrderConflictError) as context:
            database.insert_order_into_database(VALID_ORDER)

        self.assertNotIn(str(self.database_path), str(context.exception))
        self.assertNotIn("UNIQUE", str(context.exception))
        self.assertEqual(len(database.get_all_orders()), 1)

    def test_create_failure_always_rolls_back_and_closes(self):
        connection = Mock()
        connection.cursor.return_value.execute.side_effect = (
            sqlite3.OperationalError("unable to open database file")
        )

        with patch("database._connect", return_value=connection):
            with self.assertRaises(StorageUnavailableError):
                database.insert_order_into_database(VALID_ORDER)

        connection.rollback.assert_called_once_with()
        connection.close.assert_called_once_with()

    def test_locked_update_rolls_back_and_maps_to_unavailable(self):
        lock = sqlite3.connect(self.database_path)
        lock.execute("BEGIN EXCLUSIVE")

        try:
            with self.assertRaises(StorageUnavailableError):
                database.update_order_status_in_database(
                    "ORD100",
                    "completed",
                )
        finally:
            lock.rollback()
            lock.close()

        self.assertEqual(database.get_order_by_code("ORD100")["status"], "pending")

    def test_locked_delete_rolls_back_and_maps_to_unavailable(self):
        lock = sqlite3.connect(self.database_path)
        lock.execute("BEGIN EXCLUSIVE")

        try:
            with self.assertRaises(StorageUnavailableError):
                database.delete_order_from_database("ORD100")
        finally:
            lock.rollback()
            lock.close()

        self.assertIsNotNone(database.get_order_by_code("ORD100"))

    def test_update_failure_always_rolls_back_and_closes(self):
        connection = Mock()
        connection.cursor.return_value.execute.side_effect = (
            sqlite3.OperationalError("database is locked")
        )

        with patch("database._connect", return_value=connection):
            with self.assertRaises(StorageUnavailableError):
                database.update_order_status_in_database(
                    "ORD100",
                    "completed",
                )

        connection.rollback.assert_called_once_with()
        connection.close.assert_called_once_with()

    def test_delete_failure_always_rolls_back_and_closes(self):
        connection = Mock()
        connection.cursor.return_value.execute.side_effect = (
            sqlite3.OperationalError("unable to open database file")
        )

        with patch("database._connect", return_value=connection):
            with self.assertRaises(StorageUnavailableError):
                database.delete_order_from_database("ORD100")

        connection.rollback.assert_called_once_with()
        connection.close.assert_called_once_with()


class ServiceWriteFailureTests(unittest.TestCase):
    @patch(
        "services.validate_order",
        side_effect=StorageUnavailableError,
    )
    def test_create_precheck_unavailable_has_explicit_semantics(
        self,
        mock_validate,
    ):
        result = services.create_order(VALID_ORDER)

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "storage_unavailable")

    @patch("services.insert_order_into_database", side_effect=OrderConflictError)
    @patch("services.validate_order", return_value=[])
    def test_late_create_conflict_has_explicit_semantics(
        self,
        mock_validate,
        mock_insert,
    ):
        result = services.create_order(VALID_ORDER)

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "conflict")
        self.assertNotIn("SQLite", result["message"])

    @patch(
        "services.update_order_status_in_database",
        side_effect=StorageUnavailableError,
    )
    @patch("services.get_order_by_code", return_value=VALID_ORDER)
    def test_update_unavailable_is_not_reported_as_missing(
        self,
        mock_get,
        mock_update,
    ):
        result = services.update_order_status("ORD100", "completed")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "storage_unavailable")

    @patch(
        "services.delete_order_from_database",
        side_effect=StorageUnavailableError,
    )
    @patch("services.get_order_by_code", return_value=VALID_ORDER)
    def test_delete_unavailable_is_not_reported_as_missing(
        self,
        mock_get,
        mock_delete,
    ):
        result = services.delete_order("ORD100")

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "storage_unavailable")


if __name__ == "__main__":
    unittest.main()
