import unittest

from quality_scorer import calculate_order_quality_score


class TestOrderQualityScoring(unittest.TestCase):
    def test_clean_valid_order_receives_maximum_score(self):
        order = {
            "order_code": "ORD100",
            "customer_name": "Mario Rossi",
            "quantity": "12",
            "status": "pending",
        }

        result = calculate_order_quality_score(order)

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["rating"], "high")
        self.assertFalse(result["review_recommended"])
        self.assertEqual(
            result["explanations"],
            ["No quality-risk signals were detected."],
        )

    def test_unusually_high_quantity_reduces_score(self):
        order = {
            "order_code": "ORD101",
            "customer_name": "Anna Verdi",
            "quantity": "650",
            "status": "pending",
        }

        result = calculate_order_quality_score(order)

        self.assertEqual(result["score"], 82)
        self.assertEqual(result["rating"], "medium")
        self.assertTrue(result["review_recommended"])
        self.assertEqual(result["penalties"][0]["code"], "unusual_quantity")

    def test_generic_customer_name_reduces_score(self):
        order = {
            "order_code": "ORD102",
            "customer_name": "Customer",
            "quantity": "5",
            "status": "completed",
        }

        result = calculate_order_quality_score(order)

        self.assertEqual(result["score"], 82)
        self.assertIn("generic", result["explanations"][0].lower())

    def test_validation_error_has_explicit_penalty(self):
        order = {
            "order_code": "ORD103",
            "customer_name": "Luca Bianchi",
            "quantity": "4",
            "status": "shipped",
        }

        result = calculate_order_quality_score(
            order,
            validation_errors=["invalid status"],
        )

        self.assertEqual(result["score"], 70)
        self.assertEqual(result["rating"], "medium")
        self.assertEqual(result["penalties"][0]["points"], 30)

    def test_suspicious_duplicate_reduces_technically_valid_order(self):
        order = {
            "id": 10,
            "order_code": "ORDX10",
            "customer_id": 1,
            "customer_name": "Mario Rossi",
            "quantity": "10",
            "status": "pending",
        }
        candidate = {
            "id": 11,
            "order_code": "ORDX1O",
            "customer_id": 1,
            "customer_name": "Mario Rossi",
            "quantity": "10",
            "status": "pending",
        }

        result = calculate_order_quality_score(
            order,
            candidate_orders=[candidate],
        )

        self.assertEqual(result["score"], 80)
        self.assertTrue(result["review_recommended"])
        self.assertEqual(len(result["duplicate_matches"]), 1)
        self.assertEqual(
            result["penalties"][0]["code"],
            "suspicious_duplicate",
        )

    def test_score_never_drops_below_zero(self):
        order = {
            "order_code": "",
            "customer_name": "",
            "quantity": "",
            "status": "unknown",
        }

        result = calculate_order_quality_score(
            order,
            validation_errors=[
                "missing order code",
                "missing customer name",
                "missing quantity",
                "invalid status",
            ],
        )

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["rating"], "low")
        self.assertTrue(result["review_recommended"])


if __name__ == "__main__":
    unittest.main()
