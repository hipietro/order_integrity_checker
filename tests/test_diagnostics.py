import sqlite3
import tempfile
import unittest
from pathlib import Path

from diagnostics import check_database_readiness


class DatabaseReadinessTests(unittest.TestCase):
    def _create_database(self, path, tables):
        connection = sqlite3.connect(path)
        try:
            for table_name in tables:
                connection.execute(
                    f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY)"
                )
            connection.commit()
        finally:
            connection.close()

    def test_ready_database_has_required_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "orders.db"
            self._create_database(
                database_path,
                ["customers", "orders", "order_status_history"],
            )

            result = check_database_readiness(database_path)

        self.assertTrue(result["ready"])
        self.assertEqual(result["reason"], "database is ready")
        self.assertEqual(result["missing_tables"], [])

    def test_missing_database_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "missing.db"

            result = check_database_readiness(database_path)

        self.assertFalse(result["ready"])
        self.assertEqual(result["reason"], "database file is unavailable")
        self.assertIn("orders", result["missing_tables"])

    def test_incomplete_schema_reports_missing_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "orders.db"
            self._create_database(database_path, ["orders"])

            result = check_database_readiness(database_path)

        self.assertFalse(result["ready"])
        self.assertEqual(result["reason"], "database schema is incomplete")
        self.assertEqual(
            result["missing_tables"],
            ["customers", "order_status_history"],
        )


if __name__ == "__main__":
    unittest.main()
