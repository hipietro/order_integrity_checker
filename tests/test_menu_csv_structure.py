import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import menu


class TestMenuCsvStructureErrors(unittest.TestCase):
    def setUp(self):
        self.invalid_preview = {
            "structure_valid": False,
            "structural_errors": [
                "Missing required CSV header(s): quantity."
            ],
            "validation_results": [],
        }

    @patch("menu.import_csv_orders")
    @patch("menu.ask_confirmation")
    @patch("menu.preview_csv_import")
    def test_import_stops_before_confirmation_for_structural_errors(
        self,
        mock_preview,
        mock_confirmation,
        mock_import,
    ):
        mock_preview.return_value = self.invalid_preview

        output = io.StringIO()
        with redirect_stdout(output):
            menu.import_valid_orders_cli()

        self.assertIn("CSV STRUCTURE ERRORS", output.getvalue())
        self.assertIn("Missing required CSV header", output.getvalue())
        mock_confirmation.assert_not_called()
        mock_import.assert_not_called()

    @patch("menu.show_validation_problems")
    @patch("menu.preview_csv_import")
    def test_invalid_order_view_does_not_treat_malformed_csv_as_empty(
        self,
        mock_preview,
        mock_show_validation,
    ):
        mock_preview.return_value = self.invalid_preview

        output = io.StringIO()
        with redirect_stdout(output):
            menu.show_invalid_orders_cli()

        self.assertIn("CSV STRUCTURE ERRORS", output.getvalue())
        self.assertNotIn("No invalid orders found", output.getvalue())
        mock_show_validation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
