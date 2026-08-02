import unittest
from unittest.mock import patch

from order_query_service import (
    filter_and_sort_orders,
    filter_orders,
    get_filtered_and_sorted_orders,
    sort_orders,
)


SAMPLE_ORDERS = [
    {
        "id": 1,
        "order_code": "ORD010",
        "customer_name": "Mario Rossi",
        "quantity": 12,
        "status": "pending",
    },
    {
        "id": 2,
        "order_code": "ORD002",
        "customer_name": "Anna Verdi",
        "quantity": 3,
        "status": "completed",
    },
    {
        "id": 3,
        "order_code": "ORD007",
        "customer_name": "Mario Bianchi",
        "quantity": 8,
        "status": "cancelled",
    },
]


class TestOrderQueryService(unittest.TestCase):
    def test_filter_orders_by_status(self):
        result = filter_orders(SAMPLE_ORDERS, status=" Completed ")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["order_code"], "ORD002")

    def test_filter_orders_by_partial_customer_name_case_insensitively(self):
        result = filter_orders(SAMPLE_ORDERS, customer_name="mArIo")

        self.assertEqual(
            [order["order_code"] for order in result],
            ["ORD010", "ORD007"],
        )

    def test_sort_orders_by_order_code(self):
        result = sort_orders(SAMPLE_ORDERS, sort_by="order_code")

        self.assertEqual(
            [order["order_code"] for order in result],
            ["ORD002", "ORD007", "ORD010"],
        )

    def test_sort_orders_by_quantity_descending(self):
        result = sort_orders(
            SAMPLE_ORDERS,
            sort_by="quantity",
            direction="descending",
        )

        self.assertEqual(
            [order["quantity"] for order in result],
            [12, 8, 3],
        )

    def test_filter_and_sort_orders_combines_both_operations(self):
        result = filter_and_sort_orders(
            SAMPLE_ORDERS,
            customer_name="mario",
            sort_by="quantity",
            direction="ascending",
        )

        self.assertEqual(
            [order["order_code"] for order in result],
            ["ORD007", "ORD010"],
        )

    @patch("order_query_service.get_all_orders", return_value=SAMPLE_ORDERS)
    def test_get_filtered_and_sorted_orders_uses_database_orders(
        self,
        mock_get_all_orders,
    ):
        result = get_filtered_and_sorted_orders(
            status="pending",
            sort_by="quantity",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["order_code"], "ORD010")
        mock_get_all_orders.assert_called_once_with()

    def test_sort_orders_rejects_unsupported_field(self):
        with self.assertRaises(ValueError):
            sort_orders(SAMPLE_ORDERS, sort_by="customer_name")


if __name__ == "__main__":
    unittest.main()
