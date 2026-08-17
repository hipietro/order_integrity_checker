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
| GET | `/health` | Check API availability |
| GET | `/orders` | List all orders |
| GET | `/orders?order_code=ORD001` | Search an order by code |
| POST | `/orders` | Validate and create an order |
| PATCH | `/orders/{order_code}/status` | Update an order status |
| DELETE | `/orders/{order_code}` | Delete an order |
| GET | `/orders/{order_code}/history` | Read status history |
| GET | `/customers` | List customers |
| GET | `/customers?name=Mario` | Search customers by name |

## Example order creation

```json
{
  "order_code": "ORD100",
  "customer_name": "Mario Rossi",
  "quantity": 2,
  "status": "pending"
}
```

Accepted statuses are `completed`, `pending`, and `cancelled`. Invalid request shapes are rejected by FastAPI/Pydantic, while business validation errors are returned with HTTP 422. Missing resources return HTTP 404.

## Architecture

`api.py` is an interface layer only. Request models live in `api_schemas.py`, while business operations remain in `services.py`. This keeps the CLI, Tkinter GUI, and HTTP interface independent while sharing the same application logic.

## Tests

API tests use FastAPI's `TestClient` and mock the service boundary where appropriate:

```bash
python -m unittest tests.test_api -v
```

The regular project test suite also includes these tests through unittest discovery.
