import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from application_errors import CsvStructureError
from csv_manager import CSV_HEADER, clear_csv_orders, read_orders_from_csv


class CsvStructureTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_directory.name) / "orders.csv"

    def tearDown(self):
        self.temp_directory.cleanup()

    def read(self, content):
        self.csv_path.write_text(content, encoding="utf-8")
        with patch("csv_manager.CSV_FILE_NAME", str(self.csv_path)):
            return read_orders_from_csv()

    def assert_structure_errors(self, content):
        with self.assertRaises(CsvStructureError) as context:
            self.read(content)
        return context.exception.errors

    def test_valid_csv_and_utf8_bom_are_supported(self):
        orders = self.read(
            "\ufefforder_code,customer_name,quantity,status\r\n"
            'ORD100,"Mario, Rossi",2,pending\r\n'
        )

        self.assertEqual(orders, [{
            "order_code": "ORD100",
            "customer_name": "Mario, Rossi",
            "quantity": "2",
            "status": "pending",
        }])

    def test_missing_duplicate_and_unexpected_headers_are_reported(self):
        errors = self.assert_structure_errors(
            "order_code,order_code,customer_name,notes\n"
        )

        self.assertIn("Missing required CSV column(s): quantity, status.", errors)
        self.assertIn("Duplicate CSV column(s): order_code.", errors)
        self.assertIn("Unexpected CSV column(s): notes.", errors)

    def test_extra_and_missing_row_cells_are_reported_with_line_numbers(self):
        errors = self.assert_structure_errors(
            "order_code,customer_name,quantity,status\n"
            "ORD100,Mario Rossi,2,pending,extra\n"
            "ORD101,Anna Verdi,3\n"
        )

        self.assertEqual(errors, [
            "CSV row 2 has 1 extra cell(s); expected 4.",
            "CSV row 3 is missing 1 cell(s); expected 4.",
        ])

    def test_empty_file_reports_the_expected_contract(self):
        errors = self.assert_structure_errors("")

        self.assertEqual(len(errors), 1)
        self.assertIn("CSV header is missing", errors[0])


class CsvCleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_directory.name) / "orders.csv"
        self.original_contents = (
            "order_code,customer_name,quantity,status\n"
            "ORD100,Mario Rossi,2,pending\n"
        )
        self.csv_path.write_text(self.original_contents, encoding="utf-8")

    def tearDown(self):
        self.temp_directory.cleanup()

    def temporary_files(self):
        return list(self.csv_path.parent.glob(f".{self.csv_path.name}.*.tmp"))

    @patch("builtins.print")
    def test_successful_cleanup_atomically_replaces_csv_with_header(
        self,
        mock_print,
    ):
        with patch("csv_manager.CSV_FILE_NAME", str(self.csv_path)):
            clear_csv_orders()

        self.assertEqual(
            self.csv_path.read_text(encoding="utf-8"),
            CSV_HEADER,
        )
        self.assertEqual(self.temporary_files(), [])
        mock_print.assert_not_called()

    def test_partial_temporary_write_failure_preserves_original_csv(self):
        def fail_after_partial_write(file):
            file.write("order_code")
            raise OSError("simulated write failure")

        with (
            patch("csv_manager.CSV_FILE_NAME", str(self.csv_path)),
            patch(
                "csv_manager._write_cleared_csv_contents",
                side_effect=fail_after_partial_write,
            ),
            self.assertRaises(OSError),
        ):
            clear_csv_orders()

        self.assertEqual(
            self.csv_path.read_text(encoding="utf-8"),
            self.original_contents,
        )
        self.assertEqual(self.temporary_files(), [])

    def test_replace_failure_preserves_original_csv_and_removes_temporary_file(
        self,
    ):
        with (
            patch("csv_manager.CSV_FILE_NAME", str(self.csv_path)),
            patch("csv_manager.os.replace", side_effect=OSError("disk full")),
            self.assertRaises(OSError),
        ):
            clear_csv_orders()

        self.assertEqual(
            self.csv_path.read_text(encoding="utf-8"),
            self.original_contents,
        )
        self.assertEqual(self.temporary_files(), [])


if __name__ == "__main__":
    unittest.main()
