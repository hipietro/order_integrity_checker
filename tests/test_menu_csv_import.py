import contextlib
import io
import unittest
from unittest.mock import patch

import menu


class CsvImportCliFeedbackTests(unittest.TestCase):
    @patch("menu.ask_confirmation", return_value=True)
    @patch("menu.preview_csv_import")
    @patch("menu.import_csv_orders")
    def test_post_commit_failure_warns_before_retry_without_claiming_success(
        self,
        mock_import,
        mock_preview,
        mock_confirm,
    ):
        mock_preview.return_value = {
            "total_orders": 1,
            "valid_orders": 1,
            "invalid_orders": 0,
            "validation_results": [],
            "error_summary": [],
            "average_quality_score": None,
            "review_recommended_orders": 0,
            "import_blocked": False,
        }
        mock_import.return_value = {
            "success": False,
            "cancelled": False,
            "saved_orders": [{"order_code": "ORD100"}],
            "skipped_orders": [],
            "invalid_report_count": 0,
            "report_generated": False,
            "csv_cleared": False,
            "orders_committed": True,
            "failure_stage": "invalid_report",
            "message": (
                "1 order was saved to the database, but the report failed. "
                "Inspect the database before retrying."
            ),
        }

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            menu.import_valid_orders_cli()

        rendered = output.getvalue()
        self.assertIn("ORD100: saved into database", rendered)
        self.assertIn("Inspect the database before retrying", rendered)
        self.assertIn("CSV file was not cleared", rendered)
        self.assertNotIn("CSV import completed successfully", rendered)
        mock_confirm.assert_called_once()


if __name__ == "__main__":
    unittest.main()
