import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch("api.check_database_readiness")
    def test_ready_endpoint_returns_database_diagnostics(
        self,
        check_database_readiness,
    ):
        check_database_readiness.return_value = {
            "ready": True,
            "database": "orders.db",
            "reason": "database is ready",
            "missing_tables": [],
        }

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ready"])
        self.assertEqual(response.json()["database"], "orders.db")

    @patch("api.check_database_readiness")
    def test_ready_endpoint_returns_503_when_database_is_not_ready(
        self,
        check_database_readiness,
    ):
        check_database_readiness.return_value = {
            "ready": False,
            "database": "orders.db",
            "reason": "database schema is incomplete",
            "missing_tables": ["customers"],
        }

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json()["ready"])
        self.assertEqual(response.json()["missing_tables"], ["customers"])

    @patch("api.get_database_orders")
    def test_list_orders_uses_service_layer(self, get_database_orders):
        get_database_orders.return_value = [{"order_code": "ORD001"}]
        response = self.client.get("/orders")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"order_code": "ORD001"}])

    @patch("api.search_order")
    def test_search_missing_order_returns_404(self, search_order):
        search_order.return_value = None
        response = self.client.get("/orders?order_code=missing")
        self.assertEqual(response.status_code, 404)

    @patch("api.create_order")
    def test_create_order_returns_201(self, create_order):
        create_order.return_value = {
            "success": True,
            "order": {
                "order_code": "ORD100",
                "customer_name": "Mario Rossi",
                "quantity": "2",
                "status": "pending",
            },
            "errors": [],
        }
        response = self.client.post(
            "/orders",
            json={
                "order_code": "ORD100",
                "customer_name": "Mario Rossi",
                "quantity": 2,
                "status": "pending",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["order_code"], "ORD100")

    @patch("api.create_order")
    def test_duplicate_creation_returns_stable_409_envelope(self, create_order):
        create_order.return_value = {
            "success": False,
            "order": {"order_code": "ORD100"},
            "errors": [],
            "error_code": "conflict",
            "message": "An order with code ORD100 already exists.",
        }

        response = self.client.post(
            "/orders",
            json={
                "order_code": "ORD100",
                "customer_name": "Mario Rossi",
                "quantity": 2,
                "status": "pending",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {
            "detail": {
                "code": "order_conflict",
                "message": "An order with code ORD100 already exists.",
                "errors": [],
            }
        })

    @patch("api.create_order")
    def test_business_validation_preserves_422_semantics(self, create_order):
        create_order.return_value = {
            "success": False,
            "order": {"order_code": "BAD"},
            "errors": ["invalid order code format"],
            "error_code": "validation",
            "message": "Order validation failed.",
        }

        response = self.client.post(
            "/orders",
            json={
                "order_code": "BAD",
                "customer_name": "Mario Rossi",
                "quantity": 2,
                "status": "pending",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], {
            "code": "validation_failed",
            "message": "Order validation failed.",
            "errors": ["invalid order code format"],
        })

    @patch("api.create_order")
    def test_storage_failure_returns_sanitized_503_envelope(self, create_order):
        create_order.return_value = {
            "success": False,
            "order": {"order_code": "ORD100"},
            "errors": [],
            "error_code": "storage_unavailable",
            "message": "Order storage is temporarily unavailable.",
        }

        response = self.client.post(
            "/orders",
            json={
                "order_code": "ORD100",
                "customer_name": "Mario Rossi",
                "quantity": 2,
                "status": "pending",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], {
            "code": "storage_unavailable",
            "message": "Order storage is temporarily unavailable.",
            "errors": [],
        })
        self.assertNotIn("SQLite", response.text)

    @patch("api.delete_order")
    def test_delete_storage_failure_returns_503_not_404(self, delete_order):
        delete_order.return_value = {
            "success": False,
            "error_code": "storage_unavailable",
            "message": "Order storage is temporarily unavailable.",
        }

        response = self.client.delete("/orders/ORD100")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"]["code"],
            "storage_unavailable",
        )

    @patch("api.update_order_status")
    def test_update_storage_failure_returns_503_not_404(
        self,
        update_order_status,
    ):
        update_order_status.return_value = {
            "success": False,
            "error_code": "storage_unavailable",
            "message": "Order storage is temporarily unavailable.",
        }

        response = self.client.patch(
            "/orders/ORD100/status",
            json={"status": "completed"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"]["code"],
            "storage_unavailable",
        )

    @patch("api.update_order_status")
    def test_update_missing_order_returns_404(self, update_order_status):
        update_order_status.return_value = {
            "success": False,
            "message": "No order found with code UNKNOWN.",
        }
        response = self.client.patch(
            "/orders/UNKNOWN/status",
            json={"status": "completed"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"]["code"],
            "order_not_found",
        )

    @patch("api.get_customer_overview")
    def test_customer_search_is_delegated_to_service(self, get_customer_overview):
        get_customer_overview.return_value = [{"name": "Mario Rossi"}]
        response = self.client.get("/customers?name=Mario")
        self.assertEqual(response.status_code, 200)
        get_customer_overview.assert_called_once_with("Mario")


if __name__ == "__main__":
    unittest.main()
