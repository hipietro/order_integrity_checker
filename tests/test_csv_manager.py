import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import csv_manager


class TestAtomicCsvCleanup(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_directory.name) / "new_orders.csv"
        self.original_contents = (
            "order_code,customer_name,quantity,status\n"
            "ORD100,Mario Rossi,2,pending\n"
        )
        self.csv_path.write_text(self.original_contents, encoding="utf-8")
        self.csv_patcher = patch.object(
            csv_manager,
            "CSV_FILE_NAME",
            str(self.csv_path),
        )
        self.csv_patcher.start()

    def tearDown(self):
        self.csv_patcher.stop()
        self.temp_directory.cleanup()

    def test_success_replaces_orders_with_header(self):
        csv_manager.clear_csv_orders()

        self.assertEqual(
            self.csv_path.read_text(encoding="utf-8"),
            csv_manager.CSV_HEADER,
        )
        self.assertEqual(self._temporary_files(), [])

    def test_write_failure_preserves_original_and_removes_temporary_file(self):
        def fail_after_partial_write(temporary_file):
            temporary_file.write("partial")
            temporary_file.flush()
            raise OSError("temporary write failed")

        with patch.object(
            csv_manager,
            "_write_csv_header",
            side_effect=fail_after_partial_write,
        ):
            with self.assertRaisesRegex(OSError, "temporary write failed"):
                csv_manager.clear_csv_orders()

        self.assertEqual(
            self.csv_path.read_text(encoding="utf-8"),
            self.original_contents,
        )
        self.assertEqual(self._temporary_files(), [])

    def test_replace_failure_preserves_original_and_removes_temporary_file(self):
        with patch.object(
            csv_manager.os,
            "replace",
            side_effect=OSError("replace failed"),
        ):
            with self.assertRaisesRegex(OSError, "replace failed"):
                csv_manager.clear_csv_orders()

        self.assertEqual(
            self.csv_path.read_text(encoding="utf-8"),
            self.original_contents,
        )
        self.assertEqual(self._temporary_files(), [])

    def _temporary_files(self):
        names = os.listdir(self.temp_directory.name)
        return [name for name in names if name != self.csv_path.name]


if __name__ == "__main__":
    unittest.main()
