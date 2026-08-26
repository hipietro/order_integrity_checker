import unittest

from gui_import_feedback import build_csv_import_feedback


class TestGuiImportFeedback(unittest.TestCase):
    def test_success_feedback_reports_cleared_csv(self):
        feedback = build_csv_import_feedback({
            "success": True,
            "saved_orders": [{"order_code": "ORD100"}],
            "skipped_orders": [],
        })

        self.assertEqual(feedback["dialog_kind"], "info")
        self.assertIn(
            "CSV file cleared after import.",
            feedback["summary_lines"],
        )
        self.assertIn("completed", feedback["status"])

    def test_rollback_feedback_never_claims_success_or_csv_cleanup(self):
        feedback = build_csv_import_feedback({
            "success": False,
            "saved_orders": [],
            "skipped_orders": [],
            "message": "CSV import failed: duplicate order code",
        })

        rendered = "\n".join(feedback["summary_lines"])
        self.assertEqual(feedback["dialog_kind"], "error")
        self.assertIn("CSV file was not cleared.", rendered)
        self.assertIn("CSV remains available", rendered)
        self.assertNotIn("cleared after import", rendered)
        self.assertNotIn("completed successfully", rendered)

    def test_post_commit_failure_warns_before_retry(self):
        feedback = build_csv_import_feedback({
            "success": False,
            "saved_orders": [{"order_code": "ORD200"}],
            "skipped_orders": [],
            "message": "CSV import failed: file unavailable",
        })

        rendered = "\n".join(feedback["summary_lines"])
        self.assertIn("Orders were already committed", rendered)
        self.assertIn("Check the database before retrying", rendered)
        self.assertIn("1 saved", feedback["status"])
        self.assertEqual(feedback["dialog_title"], "Import failed")


if __name__ == "__main__":
    unittest.main()
