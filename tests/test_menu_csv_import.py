import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import menu


class TestCsvImportCliFeedback(unittest.TestCase):
    @patch("menu.import_csv_orders")
    @patch("menu.ask_confirmation", return_value=True)
    @patch("menu.show_csv_import_preview")
    @patch("menu.preview_csv_import")
    def test_post_commit_failure_warns_before_retry(
        self,
        mock_preview,
        mock_show_preview,
        mock_confirmation,
        mock_import,
    ):
        preview = {"total_orders": 1}
        mock_preview.return_value = preview
        mock_import.return_value = {
            "success": False,
            "cancelled": False,
            "saved_orders": [{"order_code": "ORD400"}],
            "skipped_orders": [],
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": "CSV import failed: cleanup unavailable",
        }

        output = io.StringIO()
        with redirect_stdout(output):
            menu.import_valid_orders_cli()

        rendered = output.getvalue()
        self.assertIn("ORD400: saved into database", rendered)
        self.assertIn("Orders were already committed", rendered)
        self.assertIn("Check the database before retrying", rendered)
        self.assertNotIn("completed successfully", rendered)
        mock_show_preview.assert_called_once_with(preview)
        mock_confirmation.assert_called_once()
        mock_import.assert_called_once_with(preview, confirmed=True)

    def test_failed_batch_shows_skipped_reasons_without_missing_report(self):
        result = {
            "success": False,
            "cancelled": False,
            "saved_orders": [],
            "skipped_orders": [{
                "order": {"order_code": "ORD401"},
                "errors": ["invalid quantity"],
            }],
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": "CSV import failed: database unavailable",
        }

        output = io.StringIO()
        with redirect_stdout(output):
            menu.show_csv_import_result(result)

        rendered = output.getvalue()
        self.assertIn("invalid quantity", rendered)
        self.assertNotIn("Invalid orders report generated", rendered)


if __name__ == "__main__":
    unittest.main()
