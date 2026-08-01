import unittest
from unittest.mock import patch

import services


class TestOrderStatusUpdateService(unittest.TestCase):
    """Tests the service-layer behavior for order status updates."""

    @patch("services.update_order_status_in_database", return_value=True)
    @patch("services.get_order_by_code")
    def test_update_order_status_returns_success_for_existing_order(
        self,
        mock_get_order_by_code,
        mock_update_order_status_in_database
    ):
        mock_get_order_by_code.return_value = {
            "id": 1,
            "order_code": "ORD001",
            "customer_name": "Mario Rossi",
            "quantity": 5,
            "status": "pending"
        }

        result = services.update_order_status(" ord001 ", " Completed ")

        self.assertTrue(result["success"])
        self.assertEqual(
            result["message"],
            "Order ORD001 updated successfully."
        )
        mock_get_order_by_code.assert_called_once_with("ORD001")
        mock_update_order_status_in_database.assert_called_once_with(
            "ORD001",
            "completed"
        )

    @patch("services.update_order_status_in_database")
    @patch("services.get_order_by_code", return_value=None)
    def test_update_order_status_returns_error_for_missing_order(
        self,
        mock_get_order_by_code,
        mock_update_order_status_in_database
    ):
        result = services.update_order_status(" missing ", "completed")

        self.assertFalse(result["success"])
        self.assertEqual(
            result["message"],
            "No order found with code MISSING."
        )
        mock_get_order_by_code.assert_called_once_with("MISSING")
        mock_update_order_status_in_database.assert_not_called()

    @patch("services.update_order_status_in_database", return_value=False)
    @patch("services.get_order_by_code")
    def test_update_order_status_reports_database_failure(
        self,
        mock_get_order_by_code,
        mock_update_order_status_in_database
    ):
        mock_get_order_by_code.return_value = {
            "id": 1,
            "order_code": "ORD001",
            "customer_name": "Mario Rossi",
            "quantity": 5,
            "status": "pending"
        }

        result = services.update_order_status("ORD001", "cancelled")

        self.assertFalse(result["success"])
        self.assertEqual(
            result["message"],
            "Order ORD001 could not be updated."
        )
        mock_update_order_status_in_database.assert_called_once_with(
            "ORD001",
            "cancelled"
        )


if __name__ == "__main__":
    unittest.main()
