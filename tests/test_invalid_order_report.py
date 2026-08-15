import os
import tempfile
import unittest
from unittest.mock import patch

import validator


class TestInvalidOrderReport(unittest.TestCase):
    def test_report_includes_errors_and_actionable_suggestions(self):
        validation_results = [
            {
                "order": {
                    "order_code": "ORD007",
                    "customer_name": "Mario Rossi",
                    "quantity": "0",
                    "status": "pendng",
                },
                "errors": [
                    "quantity must be greater than zero",
                    "invalid status",
                ],
                "suggestions": [
                    "Review quantity: it must be greater than zero",
                    "Did you mean status: pending?",
                ],
            }
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            report_path = os.path.join(
                temporary_directory,
                "invalid_orders_report.txt",
            )

            with patch("validator.REPORT_FILE_NAME", report_path):
                invalid_count = validator.generate_invalid_orders_report(
                    validation_results
                )

            with open(report_path, "r") as report_file:
                report = report_file.read()

        self.assertEqual(invalid_count, 1)
        self.assertIn("Errors:", report)
        self.assertIn("- invalid status", report)
        self.assertIn("Suggestions:", report)
        self.assertIn("- Did you mean status: pending?", report)
        self.assertIn(
            "- Review quantity: it must be greater than zero",
            report,
        )

    def test_report_omits_suggestion_section_when_none_are_available(self):
        validation_results = [
            {
                "order": {
                    "order_code": "ORD008",
                    "customer_name": "",
                    "quantity": "2",
                    "status": "pending",
                },
                "errors": ["missing customer name"],
                "suggestions": [],
            }
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            report_path = os.path.join(
                temporary_directory,
                "invalid_orders_report.txt",
            )

            with patch("validator.REPORT_FILE_NAME", report_path):
                validator.generate_invalid_orders_report(validation_results)

            with open(report_path, "r") as report_file:
                report = report_file.read()

        self.assertIn("Errors:", report)
        self.assertNotIn("Suggestions:", report)


if __name__ == "__main__":
    unittest.main()
