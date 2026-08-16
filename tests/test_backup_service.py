import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backup_service import (
    create_database_backup,
    list_database_backups,
    restore_database_backup,
    validate_database_file,
)


class TestDatabaseBackupService(unittest.TestCase):
    """Exercises backup creation, discovery, validation, and safe restore."""

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "orders.db"
        self.backup_directory = self.root / "backups"
        self._create_compatible_database(self.database_path, "ORD001")

    def tearDown(self):
        self.temporary_directory.cleanup()

    @staticmethod
    def _create_compatible_database(path, order_code):
        connection = sqlite3.connect(path)
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL UNIQUE,
                customer_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE order_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT NOT NULL,
                old_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                changed_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            "INSERT INTO customers (name, normalized_name) VALUES (?, ?)",
            ("Mario Rossi", "mario rossi"),
        )
        cursor.execute(
            """
            INSERT INTO orders (order_code, customer_id, quantity, status)
            VALUES (?, 1, 2, 'pending')
            """,
            (order_code,),
        )
        connection.commit()
        connection.close()

    def _read_order_code(self, path):
        connection = sqlite3.connect(path)
        try:
            row = connection.execute("SELECT order_code FROM orders").fetchone()
            return row[0]
        finally:
            connection.close()

    def test_create_database_backup_creates_valid_timestamped_copy(self):
        backup_path = create_database_backup(
            database_path=self.database_path,
            backup_directory=self.backup_directory,
            current_time=datetime(2026, 8, 16, 13, 0, 5, tzinfo=timezone.utc),
        )

        self.assertEqual(backup_path.name, "orders_backup_20260816_130005.db")
        self.assertTrue(backup_path.is_file())
        self.assertEqual(self._read_order_code(backup_path), "ORD001")
        self.assertEqual(
            validate_database_file(backup_path),
            (True, "Database is valid and compatible."),
        )

    def test_list_database_backups_returns_only_managed_backup_files(self):
        first = create_database_backup(
            database_path=self.database_path,
            backup_directory=self.backup_directory,
            current_time=datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc),
        )
        second = create_database_backup(
            database_path=self.database_path,
            backup_directory=self.backup_directory,
            current_time=datetime(2026, 8, 16, 13, 0, tzinfo=timezone.utc),
        )
        (self.backup_directory / "notes.txt").write_text("not a backup")
        first.touch()
        second.touch()

        backups = list_database_backups(self.backup_directory)

        self.assertEqual({item["name"] for item in backups}, {first.name, second.name})

    def test_restore_requires_explicit_confirmation(self):
        backup_path = create_database_backup(
            database_path=self.database_path,
            backup_directory=self.backup_directory,
        )

        result = restore_database_backup(
            backup_path,
            confirmed=False,
            database_path=self.database_path,
        )

        self.assertFalse(result["success"])
        self.assertTrue(result["cancelled"])
        self.assertEqual(self._read_order_code(self.database_path), "ORD001")

    def test_restore_rejects_invalid_backup_without_touching_database(self):
        invalid_backup = self.root / "invalid.db"
        invalid_backup.write_text("not sqlite")

        result = restore_database_backup(
            invalid_backup,
            confirmed=True,
            database_path=self.database_path,
        )

        self.assertFalse(result["success"])
        self.assertFalse(result["cancelled"])
        self.assertIn("Restore refused", result["message"])
        self.assertEqual(self._read_order_code(self.database_path), "ORD001")

    def test_restore_replaces_database_with_valid_backup(self):
        backup_source = self.root / "replacement.db"
        self._create_compatible_database(backup_source, "ORD999")

        result = restore_database_backup(
            backup_source,
            confirmed=True,
            database_path=self.database_path,
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["cancelled"])
        self.assertEqual(self._read_order_code(self.database_path), "ORD999")


if __name__ == "__main__":
    unittest.main()
