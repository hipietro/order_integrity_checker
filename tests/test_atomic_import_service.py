import unittest
from unittest.mock import Mock

from atomic_import_service import persist_validated_orders


class TestAtomicImportService(unittest.TestCase):
    def test_persists_only_valid_orders_in_one_batch_call(self):
        valid_order = {
            "order_code": "ORD300",
            "customer_name": "Anna Verdi",
            "quantity": "2",
            "status": "pending",
        }
        invalid_order = {
            "order_code": "ORD301",
            "customer_name": "",
            "quantity": "2",
            "status": "pending",
        }
        validation_results = [
            {"order": valid_order, "errors": []},
            {"order": invalid_order, "errors": ["missing customer name"]},
        ]
        batch_insert = Mock(return_value=[valid_order])

        saved = persist_validated_orders(
            validation_results,
            batch_insert=batch_insert,
        )

        self.assertEqual(saved, [valid_order])
        batch_insert.assert_called_once_with([valid_order])

    def test_skips_database_call_when_no_valid_orders_exist(self):
        validation_results = [
            {
                "order": {
                    "order_code": "ORD302",
                    "customer_name": "",
                    "quantity": "1",
                    "status": "pending",
                },
                "errors": ["missing customer name"],
            }
        ]
        batch_insert = Mock()

        saved = persist_validated_orders(
            validation_results,
            batch_insert=batch_insert,
        )

        self.assertEqual(saved, [])
        batch_insert.assert_not_called()

    def test_propagates_batch_failure_without_claiming_partial_saves(self):
        validation_results = [
            {
                "order": {
                    "order_code": "ORD303",
                    "customer_name": "Failure Example",
                    "quantity": "1",
                    "status": "pending",
                },
                "errors": [],
            }
        ]
        batch_insert = Mock(side_effect=RuntimeError("batch failed"))

        with self.assertRaisesRegex(RuntimeError, "batch failed"):
            persist_validated_orders(
                validation_results,
                batch_insert=batch_insert,
            )


if __name__ == "__main__":
    unittest.main()
