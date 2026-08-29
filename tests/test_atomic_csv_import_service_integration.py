import unittest
from unittest.mock import patch

import services


class TestAtomicCsvImportServiceIntegration(unittest.TestCase):
    def _preview(self):
        return {
            "validation_results": [
                {
                    "order": {
                        "order_code": "ORD101",
                        "customer_name": "Mario Rossi",
                        "quantity": "2",
                        "status": "pending",
                    },
                    "errors": [],
                },
                {
                    "order": {
                        "order_code": "ORD102",
                        "customer_name": "",
                        "quantity": "1",
                        "status": "pending",
                    },
                    "errors": ["missing customer name"],
                    "suggestions": ["Provide a customer name."],
                },
            ]
        }

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report", return_value=1)
    @patch("services.persist_validated_orders")
    def test_confirmed_import_persists_batch_before_report_and_csv_clear(
        self,
        mock_persist_validated_orders,
        mock_generate_invalid_orders_report,
        mock_clear_csv_orders,
    ):
        preview = self._preview()
        saved_order = preview["validation_results"][0]["order"]
        mock_persist_validated_orders.return_value = [saved_order]

        result = services.import_csv_orders(preview, confirmed=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["orders_committed"])
        self.assertIsNone(result["failure_stage"])
        self.assertEqual(result["saved_orders"], [saved_order])
        self.assertEqual(result["invalid_report_count"], 1)
        self.assertTrue(result["csv_cleared"])
        self.assertEqual(len(result["skipped_orders"]), 1)
        self.assertEqual(
            result["skipped_orders"][0]["suggestions"],
            ["Provide a customer name."],
        )
        mock_persist_validated_orders.assert_called_once_with(
            preview["validation_results"]
        )
        mock_generate_invalid_orders_report.assert_called_once_with(
            preview["validation_results"]
        )
        mock_clear_csv_orders.assert_called_once_with()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report")
    @patch(
        "services.persist_validated_orders",
        side_effect=RuntimeError("late batch conflict"),
    )
    def test_failed_batch_returns_no_saved_orders_and_preserves_csv(
        self,
        mock_persist_validated_orders,
        mock_generate_invalid_orders_report,
        mock_clear_csv_orders,
    ):
        preview = self._preview()

        result = services.import_csv_orders(preview, confirmed=True)

        self.assertFalse(result["success"])
        self.assertFalse(result["cancelled"])
        self.assertFalse(result["orders_committed"])
        self.assertEqual(result["failure_stage"], "persistence")
        self.assertEqual(result["saved_orders"], [])
        self.assertEqual(result["invalid_report_count"], 0)
        self.assertFalse(result["csv_cleared"])
        self.assertNotIn("late batch conflict", result["message"])
        self.assertIn("No data was modified", result["message"])
        self.assertEqual(len(result["skipped_orders"]), 1)
        mock_persist_validated_orders.assert_called_once_with(
            preview["validation_results"]
        )
        mock_generate_invalid_orders_report.assert_not_called()
        mock_clear_csv_orders.assert_not_called()


if __name__ == "__main__":
    unittest.main()
