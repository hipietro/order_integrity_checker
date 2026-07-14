import unittest
from unittest.mock import patch

from validator import validate_order


class TestOrderValidation(unittest.TestCase):
    def make_order(self, order_code="ORD001", customer_name="Mario Rossi", quantity="5", status="pending"):
        return {
            "order_code": order_code,
            "customer_name": customer_name,
            "quantity": quantity,
            "status": status
        }

    @patch("validator.order_exists_in_database", return_value=False)
    def test_valid_order_has_no_errors(self, mock_order_exists):
        order = self.make_order()

        errors = validate_order(order, [])

        self.assertEqual(errors, [])

    @patch("validator.order_exists_in_database", return_value=False)
    def test_missing_customer_name_is_invalid(self, mock_order_exists):
        order = self.make_order(customer_name="")

        errors = validate_order(order, [])

        self.assertIn("missing customer name", errors)

    @patch("validator.order_exists_in_database", return_value=False)
    def test_invalid_quantity_is_invalid(self, mock_order_exists):
        order = self.make_order(quantity="abc")

        errors = validate_order(order, [])

        self.assertIn("quantity must be a valid number", errors)

    @patch("validator.order_exists_in_database", return_value=False)
    def test_invalid_status_is_invalid(self, mock_order_exists):
        order = self.make_order(status="shipped")

        errors = validate_order(order, [])

        self.assertIn("invalid status", errors)

    @patch("validator.order_exists_in_database", return_value=False)
    def test_duplicate_order_code_inside_csv_is_invalid(self, mock_order_exists):
        order = self.make_order(order_code="ORD001")

        errors = validate_order(order, ["ORD001"])

        self.assertIn("duplicated order code inside CSV file", errors)

    @patch("validator.order_exists_in_database", return_value=False)
    def test_order_values_are_normalized_before_validation(self, mock_order_exists):
        order = self.make_order(
            order_code=" ord010 ",
            customer_name=" Mario Rossi ",
            quantity=" 7 ",
            status=" Pending "
        )

        errors = validate_order(order, [])

        self.assertEqual(errors, [])
        self.assertEqual(order["order_code"], "ORD010")
        self.assertEqual(order["customer_name"], "Mario Rossi")
        self.assertEqual(order["quantity"], "7")
        self.assertEqual(order["status"], "pending")


if __name__ == "__main__":
    unittest.main()
