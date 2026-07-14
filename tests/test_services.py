import unittest
from unittest.mock import patch

import services


class TestOrderServices(unittest.TestCase):
    @patch("services.validate_all_csv_orders")
    def test_preview_csv_import_counts_valid_and_invalid_orders(self, mock_validate_all_csv_orders):
        mock_validate_all_csv_orders.return_value = [
            {
                "order": {
                    "order_code": "ORD001",
                    "customer_name": "Mario Rossi",
                    "quantity": "5",
                    "status": "pending"
                },
                "errors": []
            },
            {
                "order": {
                    "order_code": "ORD002",
                    "customer_name": "",
                    "quantity": "3",
                    "status": "pending"
                },
                "errors": ["missing customer name"]
            }
        ]

        result = services.preview_csv_import()

        self.assertEqual(result["valid_orders"], 1)
        self.assertEqual(result["invalid_orders"], 1)
        self.assertEqual(len(result["validation_results"]), 2)

    @patch("services.insert_order_into_database")
    @patch("services.validate_order", return_value=[])
    def test_create_order_returns_success_for_valid_order(self, mock_validate_order, mock_insert_order):
        order = {
            "order_code": " ord010 ",
            "customer_name": " Mario Rossi ",
            "quantity": "5",
            "status": " Pending "
        }

        result = services.create_order(order)

        self.assertTrue(result["success"])
        self.assertEqual(result["order"]["order_code"], "ORD010")
        self.assertEqual(result["order"]["status"], "pending")
        mock_insert_order.assert_called_once()

    @patch("services.insert_order_into_database")
    @patch("services.validate_order", return_value=["invalid status"])
    def test_create_order_returns_errors_for_invalid_order(self, mock_validate_order, mock_insert_order):
        order = {
            "order_code": "ORD010",
            "customer_name": "Mario Rossi",
            "quantity": "5",
            "status": "shipped"
        }

        result = services.create_order(order)

        self.assertFalse(result["success"])
        self.assertIn("invalid status", result["errors"])
        mock_insert_order.assert_not_called()

    @patch("services.get_all_orders")
    @patch("services.export_orders_to_csv", return_value=2)
    def test_export_database_orders_returns_export_summary(self, mock_export_orders_to_csv, mock_get_all_orders):
        mock_get_all_orders.return_value = [
            {
                "id": 1,
                "order_code": "ORD001",
                "customer_name": "Mario Rossi",
                "quantity": 5,
                "status": "pending"
            },
            {
                "id": 2,
                "order_code": "ORD002",
                "customer_name": "Luca Bianchi",
                "quantity": 3,
                "status": "completed"
            }
        ]

        result = services.export_database_orders()

        self.assertTrue(result["success"])
        self.assertEqual(result["exported_orders"], 2)
        self.assertEqual(result["file_name"], "exported_orders.csv")
        mock_export_orders_to_csv.assert_called_once()


if __name__ == "__main__":
    unittest.main()
