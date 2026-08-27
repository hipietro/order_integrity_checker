import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import csv_manager


class TestCsvStructureValidation(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_directory.name) / "orders.csv"
        self.csv_patcher = patch.object(
            csv_manager,
            "CSV_FILE_NAME",
            str(self.csv_path),
        )
        self.csv_patcher.start()

    def tearDown(self):
        self.csv_patcher.stop()
        self.temp_directory.cleanup()

    def test_valid_csv_preserves_order_dictionary_contract(self):
        self._write_text(
            "status,quantity,customer_name,order_code\r\n"
            'pending,2,"Rossi, Mario",ORD100\r\n'
        )

        orders = csv_manager.read_orders_from_csv()

        self.assertEqual(orders, [{
            "status": "pending",
            "quantity": "2",
            "customer_name": "Rossi, Mario",
            "order_code": "ORD100",
        }])

    def test_utf8_bom_is_removed_from_first_header(self):
        self._write_text(
            "order_code,customer_name,quantity,status\n"
            "ORD101,Anna Verdi,3,completed\n",
            encoding="utf-8-sig",
        )

        orders = csv_manager.read_orders_from_csv()

        self.assertEqual(orders[0]["order_code"], "ORD101")
        self.assertEqual(set(orders[0]), set(csv_manager.EXPECTED_CSV_COLUMNS))

    def test_empty_file_is_rejected_without_a_header(self):
        self._write_text("")

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertEqual(
            context.exception.errors,
            ("CSV file is missing the required header row.",),
        )

    def test_missing_required_header_is_rejected(self):
        self._write_text(
            "order_code,customer_name,status\n"
            "ORD102,Mario Rossi,pending\n"
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertIn("quantity", context.exception.errors[0])

    def test_duplicate_header_is_rejected(self):
        self._write_text(
            "order_code,customer_name,status,status\n"
            "ORD103,Mario Rossi,pending,pending\n"
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        rendered = "\n".join(context.exception.errors)
        self.assertIn("Duplicate CSV header(s): status", rendered)
        self.assertIn("Missing required CSV header(s): quantity", rendered)

    def test_unexpected_header_is_rejected(self):
        self._write_text(
            "order_code,customer_name,quantity,status,notes\n"
            "ORD104,Mario Rossi,4,pending,urgent\n"
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertIn("'notes'", context.exception.errors[0])

    def test_extra_cell_is_rejected_with_row_number(self):
        self._write_text(
            "order_code,customer_name,quantity,status\n"
            "ORD105,Mario Rossi,4,pending,unexpected\n"
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertEqual(
            context.exception.errors,
            ("CSV row 2 has 1 extra cell; expected exactly 4.",),
        )

    def test_missing_cell_is_rejected_with_column_and_row_number(self):
        self._write_text(
            "order_code,customer_name,quantity,status\n"
            "ORD106,Mario Rossi,4\n"
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertEqual(
            context.exception.errors,
            ("CSV row 2 is missing a cell for: status.",),
        )

    def test_empty_cell_remains_available_for_business_validation(self):
        self._write_text(
            "order_code,customer_name,quantity,status\n"
            "ORD107,Mario Rossi,4,\n"
        )

        orders = csv_manager.read_orders_from_csv()

        self.assertEqual(orders[0]["status"], "")

    def test_non_utf8_input_is_rejected_with_actionable_message(self):
        self.csv_path.write_bytes(
            b"order_code,customer_name,quantity,status\n"
            b"ORD108,\xff,4,pending\n"
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertIn("must be UTF-8 encoded", context.exception.errors[0])

    def test_malformed_quoted_field_is_rejected(self):
        self._write_text(
            "order_code,customer_name,quantity,status\n"
            'ORD109,"Mario Rossi,4,pending\n'
        )

        with self.assertRaises(csv_manager.CsvStructureError) as context:
            csv_manager.read_orders_from_csv()

        self.assertIn("Malformed CSV data", context.exception.errors[0])

    def _write_text(self, contents, encoding="utf-8"):
        self.csv_path.write_text(contents, encoding=encoding, newline="")


if __name__ == "__main__":
    unittest.main()
