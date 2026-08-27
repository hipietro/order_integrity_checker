import unittest
from unittest.mock import patch

import services
from csv_import_preview import build_csv_import_preview
from csv_manager import CsvStructureError


class TestCsvImportPreviewBuilder(unittest.TestCase):
    def setUp(self):
        self.validation_results = [
            {
                "order": {
                    "order_code": "ORD010",
                    "customer_name": "Mario Rossi",
                    "quantity": "5",
                    "status": "pending",
                },
                "errors": [],
            },
            {
                "order": {
                    "order_code": "ORD011",
                    "customer_name": "",
                    "quantity": "0",
                    "status": "pending",
                },
                "errors": [
                    "missing customer name",
                    "quantity must be greater than zero",
                ],
                "suggestions": [
                    "Review quantity: it must be greater than zero",
                ],
            },
            {
                "order": {
                    "order_code": "ORD012",
                    "customer_name": "",
                    "quantity": "3",
                    "status": "completed",
                },
                "errors": ["missing customer name"],
            },
        ]

    def test_preview_contains_counts_and_order_details(self):
        preview = build_csv_import_preview(self.validation_results)

        self.assertTrue(preview["structure_valid"])
        self.assertEqual(preview["structural_errors"], [])
        self.assertEqual(preview["total_orders"], 3)
        self.assertEqual(preview["valid_orders"], 1)
        self.assertEqual(preview["invalid_orders"], 2)
        self.assertEqual(preview["suggestion_count"], 1)
        self.assertEqual(preview["orders_with_suggestions"], 1)
        self.assertEqual(preview["orders_to_import"][0]["order_code"], "ORD010")
        self.assertEqual(
            preview["orders_to_skip"][0]["order"]["order_code"],
            "ORD011",
        )
        self.assertEqual(
            preview["orders_to_skip"][0]["suggestions"],
            ["Review quantity: it must be greater than zero"],
        )
        self.assertTrue(preview["requires_confirmation"])

    def test_preview_summarizes_repeated_validation_reasons(self):
        preview = build_csv_import_preview(self.validation_results)
        summary = {
            item["reason"]: item["count"]
            for item in preview["error_summary"]
        }

        self.assertEqual(summary["missing customer name"], 2)
        self.assertEqual(summary["quantity must be greater than zero"], 1)

    def test_preview_summarizes_quality_scores_when_available(self):
        results = [
            {
                "order": self.validation_results[0]["order"],
                "errors": [],
                "quality": {
                    "score": 100,
                    "review_recommended": False,
                },
            },
            {
                "order": self.validation_results[1]["order"],
                "errors": self.validation_results[1]["errors"],
                "suggestions": self.validation_results[1]["suggestions"],
                "quality": {
                    "score": 50,
                    "review_recommended": True,
                },
            },
        ]

        preview = build_csv_import_preview(results)

        self.assertEqual(preview["average_quality_score"], 75.0)
        self.assertEqual(preview["review_recommended_orders"], 1)

    def test_structural_errors_disable_confirmation(self):
        preview = build_csv_import_preview(
            self.validation_results,
            structural_errors=["Missing required CSV header(s): status."],
        )

        self.assertFalse(preview["structure_valid"])
        self.assertEqual(
            preview["structural_errors"],
            ["Missing required CSV header(s): status."],
        )
        self.assertFalse(preview["requires_confirmation"])


class TestSafeCsvImportService(unittest.TestCase):
    def setUp(self):
        self.preview = build_csv_import_preview([
            {
                "order": {
                    "order_code": "ORD020",
                    "customer_name": "Anna Verdi",
                    "quantity": "4",
                    "status": "pending",
                },
                "errors": [],
            },
            {
                "order": {
                    "order_code": "ORD021",
                    "customer_name": "",
                    "quantity": "2",
                    "status": "pending",
                },
                "errors": ["missing customer name"],
                "suggestions": ["Provide a customer name"],
            },
        ])

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report")
    @patch("services.persist_validated_orders")
    def test_cancelled_import_does_not_modify_database_or_csv(
        self,
        mock_persist,
        mock_report,
        mock_clear,
    ):
        result = services.import_csv_orders(self.preview, confirmed=False)

        self.assertFalse(result["success"])
        self.assertTrue(result["cancelled"])
        self.assertFalse(result["csv_cleared"])
        self.assertEqual(
            result["skipped_orders"][0]["suggestions"],
            ["Provide a customer name"],
        )
        mock_persist.assert_not_called()
        mock_report.assert_not_called()
        mock_clear.assert_not_called()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report", return_value=1)
    @patch("services.persist_validated_orders")
    def test_confirmed_import_saves_valid_orders_and_clears_csv_last(
        self,
        mock_persist,
        mock_report,
        mock_clear,
    ):
        mock_persist.return_value = list(self.preview["orders_to_import"])

        result = services.import_csv_orders(self.preview, confirmed=True)

        self.assertTrue(result["success"])
        self.assertFalse(result["cancelled"])
        self.assertEqual(len(result["saved_orders"]), 1)
        self.assertEqual(len(result["skipped_orders"]), 1)
        self.assertEqual(
            result["skipped_orders"][0]["suggestions"],
            ["Provide a customer name"],
        )
        self.assertTrue(result["csv_cleared"])
        mock_persist.assert_called_once_with(self.preview["validation_results"])
        mock_report.assert_called_once_with(self.preview["validation_results"])
        mock_clear.assert_called_once_with()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report", return_value=1)
    @patch("services.persist_validated_orders")
    def test_confirmed_gui_validation_list_remains_supported(
        self,
        mock_persist,
        mock_report,
        mock_clear,
    ):
        mock_persist.return_value = list(self.preview["orders_to_import"])

        result = services.import_csv_orders(self.preview["validation_results"])

        self.assertTrue(result["success"])
        self.assertTrue(result["csv_cleared"])
        self.assertEqual(
            result["skipped_orders"][0]["suggestions"],
            ["Provide a customer name"],
        )
        mock_persist.assert_called_once()
        mock_report.assert_called_once()
        mock_clear.assert_called_once()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report")
    @patch(
        "services.persist_validated_orders",
        side_effect=RuntimeError("database unavailable"),
    )
    def test_failed_import_keeps_csv_file(
        self,
        mock_persist,
        mock_report,
        mock_clear,
    ):
        result = services.import_csv_orders(self.preview, confirmed=True)

        self.assertFalse(result["success"])
        self.assertFalse(result["cancelled"])
        self.assertEqual(result["saved_orders"], [])
        self.assertFalse(result["csv_cleared"])
        self.assertIn("database unavailable", result["message"])
        mock_persist.assert_called_once()
        mock_report.assert_not_called()
        mock_clear.assert_not_called()

    @patch("services.clear_csv_orders")
    @patch("services.generate_invalid_orders_report")
    @patch("services.persist_validated_orders")
    def test_structurally_invalid_preview_never_mutates_state(
        self,
        mock_persist,
        mock_report,
        mock_clear,
    ):
        invalid_preview = build_csv_import_preview(
            self.preview["validation_results"],
            structural_errors=["Unexpected CSV header(s): 'notes'."],
        )

        result = services.import_csv_orders(
            invalid_preview,
            confirmed=True,
        )

        self.assertFalse(result["success"])
        self.assertFalse(result["cancelled"])
        self.assertEqual(result["saved_orders"], [])
        self.assertEqual(
            result["structural_errors"],
            ["Unexpected CSV header(s): 'notes'."],
        )
        self.assertFalse(result["csv_cleared"])
        mock_persist.assert_not_called()
        mock_report.assert_not_called()
        mock_clear.assert_not_called()

    @patch("services.validate_all_csv_orders", return_value=[])
    def test_empty_preview_does_not_require_confirmation(self, mock_validate):
        preview = services.preview_csv_import()

        self.assertEqual(preview["total_orders"], 0)
        self.assertFalse(preview["requires_confirmation"])
        self.assertIsNone(preview["average_quality_score"])
        self.assertEqual(preview["suggestion_count"], 0)
        self.assertEqual(preview["orders_with_suggestions"], 0)
        mock_validate.assert_called_once_with()

    @patch("services.get_all_orders")
    @patch(
        "services.validate_all_csv_orders",
        side_effect=CsvStructureError([
            "Missing required CSV header(s): quantity."
        ]),
    )
    def test_preview_surfaces_structure_error_without_database_read(
        self,
        mock_validate,
        mock_get_orders,
    ):
        preview = services.preview_csv_import()

        self.assertFalse(preview["structure_valid"])
        self.assertFalse(preview["requires_confirmation"])
        self.assertEqual(preview["validation_results"], [])
        self.assertEqual(
            preview["structural_errors"],
            ["Missing required CSV header(s): quantity."],
        )
        mock_validate.assert_called_once_with()
        mock_get_orders.assert_not_called()

    @patch("services.get_all_orders", return_value=[])
    @patch("services.validate_all_csv_orders")
    def test_preview_service_attaches_quality_to_every_order(
        self,
        mock_validate,
        mock_get_orders,
    ):
        mock_validate.return_value = [
            {
                "order": {
                    "order_code": "ORD030",
                    "customer_name": "Mario Rossi",
                    "quantity": "5",
                    "status": "pending",
                },
                "errors": [],
                "suggestions": ["Example suggestion"],
            }
        ]

        preview = services.preview_csv_import()

        quality = preview["validation_results"][0]["quality"]
        self.assertEqual(quality["score"], 100)
        self.assertEqual(quality["rating"], "high")
        self.assertEqual(
            preview["validation_results"][0]["suggestions"],
            ["Example suggestion"],
        )
        self.assertEqual(preview["suggestion_count"], 1)
        self.assertEqual(preview["orders_with_suggestions"], 1)
        self.assertEqual(preview["average_quality_score"], 100.0)
        self.assertEqual(preview["review_recommended_orders"], 0)
        mock_get_orders.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
