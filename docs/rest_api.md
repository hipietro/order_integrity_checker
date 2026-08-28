# REST API

Order Integrity Checker exposes an optional FastAPI interface on top of the existing service layer. The API does not duplicate database logic: routes delegate validation, normalization, queries, updates, and deletion to `services.py`.

## Install development dependencies

```bash
python -m pip install -r requirements-dev.txt
```

## Run locally

```bash
python -m uvicorn api:app --reload
```

The default development server is available at `http://127.0.0.1:8000`.

FastAPI generates interactive OpenAPI documentation automatically:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness check for the API process |
| GET | `/ready` | Readiness check for SQLite access and schema compatibility |
| GET | `/orders` | List all orders |
| GET | `/orders?order_code=ORD001` | Search an order by code |
| POST | `/orders` | Validate and create an order |
| PATCH | `/orders/{order_code}/status` | Update an order status |
| DELETE | `/orders/{order_code}` | Delete an order |
| GET | `/orders/{order_code}/history` | Read status history |
| GET | `/customers` | List customers |
| GET | `/customers?name=Mario` | Search customers by name |

## Liveness and readiness

`GET /health` answers a deliberately small question: is the FastAPI process running and able to serve HTTP? It does not touch SQLite and normally returns HTTP 200:

```json
{
  "status": "ok"
}
```

`GET /ready` answers the stronger operational question: can this application instance safely serve requests that depend on its data? The diagnostics service opens the configured SQLite database in read-only mode, checks the required application tables, and runs `PRAGMA quick_check` without changing persistent data.

A ready instance returns HTTP 200:

```json
{
  "ready": true,
  "database": "orders.db",
  "reason": "database is ready",
  "missing_tables": []
}
```

If the database file is missing, unreadable, corrupt, or does not contain the expected application schema, the endpoint returns HTTP 503 with the same response shape. For example:

```json
{
  "ready": false,
  "database": "orders.db",
  "reason": "database schema is incomplete",
  "missing_tables": ["customers"]
}
```

This separation makes the endpoints suitable for deployment probes: liveness can detect a stuck process, while readiness can keep traffic away from an instance whose storage is not usable yet.

## Example order creation

```json
{
  "order_code": "ORD100",
  "customer_name": "Mario Rossi",
  "quantity": 2,
  "status": "pending"
}
```

Accepted statuses are `completed`, `pending`, and `cancelled`. Invalid request shapes and business validation failures return HTTP 422. Missing resources return HTTP 404, duplicate order codes return HTTP 409, and locked or unavailable SQLite storage returns HTTP 503.

## Write error responses

Expected write failures use a stable FastAPI error envelope:

```json
{
  "detail": {
    "code": "order_conflict",
    "message": "An order with code ORD100 already exists.",
    "errors": []
  }
}
```

| Status | `detail.code` | Meaning |
| --- | --- | --- |
| 404 | `order_not_found` | The target order does not exist |
| 409 | `order_conflict` | The order code conflicts with stored data |
| 422 | `validation_failed` | The request fails business validation |
| 503 | `storage_unavailable` | SQLite is locked or cannot complete the operation |

Storage failures never include raw SQLite messages or local filesystem paths. Create, update, and delete writes roll back and close their database connections on failure.

## Architecture

`api.py` is an interface layer only. Request and response models live in `api_schemas.py`. Operational storage diagnostics live in `diagnostics.py`, while business operations remain in `services.py`. This keeps the CLI, Tkinter GUI, and HTTP interface independent while sharing the same application logic.

## Tests

API tests use FastAPI's `TestClient` and mock the service boundary where appropriate. Database diagnostics also have isolated tests that build temporary SQLite files and never touch the developer's real database:

```bash
python -m unittest tests.test_api tests.test_diagnostics -v
```

The regular project test suite also includes these tests through unittest discovery.
