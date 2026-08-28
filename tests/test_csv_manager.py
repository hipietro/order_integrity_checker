import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from application_errors import CsvStructureError
from csv_manager import read_orders_from_csv


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


if __name__ == "__main__":
    unittest.main()
