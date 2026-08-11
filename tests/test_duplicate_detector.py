import unittest

from duplicate_detector import (
    compare_orders_for_duplicate_risk,
    find_suspicious_duplicates,
)


class SuspiciousDuplicateDetectionTests(unittest.TestCase):
    def make_order(self, **overrides):
        order = {
            "id": 1,
            "order_code": "ORD100",
            "customer_id": 10,
            "customer_name": "Mario Rossi",
            "quantity": 10,
            "status": "pending",
        }
        order.update(overrides)
        return order

    def test_missing_character_in_code_is_suspicious(self):
        order = self.make_order(order_code="ORD100")
        candidate = self.make_order(
            id=2,
            order_code="ORD10",
            customer_id=20,
            customer_name="Different Customer",
            quantity=50,
            status="completed",
        )

        match = compare_orders_for_duplicate_risk(order, candidate)

        self.assertIsNotNone(match)
        self.assertTrue(
            any("typing variation" in reason for reason in match["reasons"])
        )

    def test_adjacent_transposition_in_code_is_suspicious(self):
        order = self.make_order(order_code="ORD123")
        candidate = self.make_order(
            id=2,
            order_code="ORD132",
            customer_id=20,
            customer_name="Different Customer",
            quantity=50,
            status="completed",
        )

        match = compare_orders_for_duplicate_risk(order, candidate)

        self.assertIsNotNone(match)

    def test_sequential_numeric_codes_are_not_suspicious_by_code_alone(self):
        order = self.make_order(order_code="ORD001")
        candidate = self.make_order(
            id=2,
            order_code="ORD002",
            customer_id=20,
            customer_name="Different Customer",
            quantity=50,
            status="completed",
        )

        match = compare_orders_for_duplicate_risk(order, candidate)

        self.assertIsNone(match)

    def test_same_customer_similar_quantity_and_status_is_suspicious(self):
        order = self.make_order(order_code="ORD100", quantity=10)
        candidate = self.make_order(
            id=2,
            order_code="ORD900",
            quantity=11,
        )

        match = compare_orders_for_duplicate_risk(order, candidate)

        self.assertIsNotNone(match)
        self.assertGreaterEqual(len(match["reasons"]), 3)

    def test_small_customer_name_typo_can_be_detected(self):
        order = self.make_order(
            customer_id=None,
            customer_name="Mario Rossi",
        )
        candidate = self.make_order(
            id=2,
            order_code="XYZ900",
            customer_id=None,
            customer_name="Mario Rosi",
            quantity=10,
            status="pending",
        )

        match = compare_orders_for_duplicate_risk(order, candidate)

        self.assertIsNotNone(match)
        self.assertTrue(
            any("Customer" in reason for reason in match["reasons"])
        )

    def test_different_orders_are_not_flagged(self):
        order = self.make_order()
        candidate = self.make_order(
            id=2,
            order_code="XYZ900",
            customer_id=20,
            customer_name="Anna Verdi",
            quantity=40,
            status="completed",
        )

        match = compare_orders_for_duplicate_risk(order, candidate)

        self.assertIsNone(match)

    def test_find_duplicates_excludes_the_order_itself(self):
        order = self.make_order()
        suspicious = self.make_order(
            id=2,
            order_code="ORD10",
        )

        matches = find_suspicious_duplicates(
            order,
            [order, suspicious],
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["order_code"], "ORD10")


if __name__ == "__main__":
    unittest.main()
