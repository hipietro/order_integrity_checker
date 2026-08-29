import unittest

from csv_import_feedback import build_csv_import_feedback


SAVED_ORDER = {
    "order_code": "ORD100",
    "customer_name": "Mario Rossi",
    "quantity": 2,
    "status": "pending",
}
SKIPPED_ORDER = {
    "order": {
        "order_code": "ORD101",
        "customer_name": "",
        "quantity": 1,
        "status": "pending",
    },
    "errors": ["missing customer name"],
}


class CsvImportFeedbackTests(unittest.TestCase):
    def test_success_lists_saved_skipped_report_and_cleared_csv(self):
        feedback = build_csv_import_feedback({
            "success": True,
            "saved_orders": [SAVED_ORDER],
            "skipped_orders": [SKIPPED_ORDER],
            "report_generated": True,
            "csv_cleared": True,
            "failure_stage": None,
            "message": "CSV import completed successfully.",
        })

        self.assertEqual(feedback["outcome"], "success")
        self.assertIn("ORD100: saved into database", feedback["lines"])
        self.assertIn(
            "ORD101: skipped — missing customer name",
            feedback["lines"],
        )
        self.assertIn(
            "Invalid orders report generated: invalid_orders_report.txt",
            feedback["lines"],
        )
        self.assertIn(
            "CSV file cleared after successful import.",
            feedback["lines"],
        )

    def test_rollback_failure_does_not_claim_saved_rows_or_report(self):
        feedback = build_csv_import_feedback({
            "success": False,
            "saved_orders": [],
            "skipped_orders": [SKIPPED_ORDER],
            "report_generated": False,
            "csv_cleared": False,
            "failure_stage": "persistence",
            "message": "Import failed before commit. No data was modified.",
        })

        self.assertEqual(feedback["outcome"], "failure")
        self.assertIn("Saved orders: 0", feedback["lines"])
        self.assertIn("CSV file was not cleared.", feedback["lines"])
        self.assertFalse(any(
            "report generated" in line for line in feedback["lines"]
        ))

    def test_report_failure_warns_that_order_is_already_committed(self):
        feedback = build_csv_import_feedback({
            "success": False,
            "saved_orders": [SAVED_ORDER],
            "skipped_orders": [SKIPPED_ORDER],
            "report_generated": False,
            "csv_cleared": False,
            "failure_stage": "invalid_report",
            "message": (
                "1 order was saved, but the report failed. Inspect the "
                "database before retrying."
            ),
        })

        self.assertEqual(feedback["outcome"], "post_commit_failure")
        self.assertIn("ORD100: saved into database", feedback["lines"])
        self.assertIn("Saved orders: 1", feedback["lines"])
        self.assertIn("CSV file was not cleared.", feedback["lines"])
        self.assertFalse(any(
            "report generated" in line for line in feedback["lines"]
        ))
        self.assertIn("incomplete", feedback["dialog_title"].lower())

    def test_cleanup_failure_mentions_report_only_after_it_completed(self):
        feedback = build_csv_import_feedback({
            "success": False,
            "saved_orders": [SAVED_ORDER],
            "skipped_orders": [SKIPPED_ORDER],
            "report_generated": True,
            "csv_cleared": False,
            "failure_stage": "csv_cleanup",
            "message": "1 order was saved, but CSV cleanup failed.",
        })

        self.assertEqual(feedback["outcome"], "post_commit_failure")
        self.assertIn(
            "Invalid orders report generated: invalid_orders_report.txt",
            feedback["lines"],
        )
        self.assertIn("CSV file was not cleared.", feedback["lines"])


if __name__ == "__main__":
    unittest.main()
