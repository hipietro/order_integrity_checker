import unittest
from unittest.mock import patch

import services


class TestOrderDetailService(unittest.TestCase):
    @patch("services.get_suspicious_duplicate_review")
    @patch("services.get_status_history_for_order")
    @patch("services.get_order_by_code")
    def test_order_detail_combines_order_customer_history_and_insights(
        self,
        mock_get_order,
        mock_get_history,
        mock_duplicate_review,
    ):
        order = {
            "id": 7,
            "order_code": "ORD007",
            "customer_id": 3,
            "customer_name": "Mario Rossi",
            "quantity": 8,
            "status": "completed",
        }
        mock_get_order.return_value = order
        mock_get_history.return_value = [
            {
                "id": 1,
                "order_code": "ORD007",
                "old_status": "pending",
                "new_status": "completed",
                "changed_at": "2026-08-10 10:00:00",
            }
        ]
        mock_duplicate_review.return_value = {
            "review_required": True,
            "matches": [
                {
                    "order_code": "ORD07",
                    "customer_name": "Mario Rossi",
                    "quantity": 8,
                    "status": "completed",
                    "reasons": ["Order code looks like a typing variation."],
                }
            ],
        }

        result = services.get_order_detail(" ord007 ")

        self.assertTrue(result["success"])
        self.assertEqual(result["order_code"], "ORD007")
        self.assertEqual(result["order"]["quantity"], 8)
        self.assertEqual(result["customer"]["id"], 3)
        self.assertEqual(result["customer"]["name"], "Mario Rossi")
        self.assertEqual(len(result["status_history"]), 1)
        self.assertTrue(
            result["insights"]["suspicious_duplicate"]["review_required"]
        )
        self.assertEqual(
            result["insights"]["suspicious_duplicate"]["matches"][0][
                "order_code"
            ],
            "ORD07",
        )
        mock_get_order.assert_called_once_with("ORD007")
        mock_get_history.assert_called_once_with("ORD007")
        mock_duplicate_review.assert_called_once_with(order)

    @patch("services.get_suspicious_duplicate_review")
    @patch("services.get_status_history_for_order")
    @patch("services.get_order_by_code", return_value=None)
    def test_order_detail_handles_missing_order_cleanly(
        self,
        mock_get_order,
        mock_get_history,
        mock_duplicate_review,
    ):
        result = services.get_order_detail("missing")

        self.assertFalse(result["success"])
        self.assertEqual(result["order_code"], "MISSING")
        self.assertIsNone(result["order"])
        self.assertIsNone(result["customer"])
        self.assertEqual(result["status_history"], [])
        self.assertEqual(result["insights"], {})
        self.assertEqual(result["message"], "No order found with code MISSING.")
        mock_get_order.assert_called_once_with("MISSING")
        mock_get_history.assert_not_called()
        mock_duplicate_review.assert_not_called()


if __name__ == "__main__":
    unittest.main()
