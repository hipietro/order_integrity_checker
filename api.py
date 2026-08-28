from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse

from api_schemas import (
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    ReadinessResponse,
)
from diagnostics import check_database_readiness
from services import (
    create_order,
    delete_order,
    get_customer_overview,
    get_database_orders,
    get_order_status_history,
    search_order,
    update_order_status,
)


app = FastAPI(
    title="Order Integrity Checker API",
    version="1.0.0",
    description="REST interface for the Order Integrity Checker service layer.",
)


def _raise_order_write_error(result):
    """Maps stable service failures to stable HTTP error envelopes."""

    error_code = result.get("error_code")
    if error_code is None:
        error_code = (
            "not_found"
            if result.get("message", "").startswith("No order found")
            else "validation"
        )
    status_codes = {
        "not_found": status.HTTP_404_NOT_FOUND,
        "conflict": status.HTTP_409_CONFLICT,
        "validation": status.HTTP_422_UNPROCESSABLE_CONTENT,
        "storage_unavailable": status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    public_codes = {
        "not_found": "order_not_found",
        "conflict": "order_conflict",
        "validation": "validation_failed",
        "storage_unavailable": "storage_unavailable",
    }

    raise HTTPException(
        status_code=status_codes[error_code],
        detail={
            "code": public_codes[error_code],
            "message": result["message"],
            "errors": result.get("errors", []),
        },
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready", response_model=ReadinessResponse)
def readiness_check():
    result = check_database_readiness()

    if not result["ready"]:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=result,
        )

    return result


@app.get("/orders")
def list_orders(order_code: str | None = Query(default=None)):
    if order_code is None:
        return get_database_orders()

    order = search_order(order_code)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return [order]


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order_endpoint(payload: OrderCreateRequest):
    result = create_order({
        "order_code": payload.order_code,
        "customer_name": payload.customer_name,
        "quantity": str(payload.quantity),
        "status": payload.status,
    })
    if not result["success"]:
        _raise_order_write_error(result)
    return result["order"]


@app.patch("/orders/{order_code}/status")
def update_order_status_endpoint(
    order_code: str,
    payload: OrderStatusUpdateRequest,
):
    result = update_order_status(order_code, payload.status)
    if not result["success"]:
        _raise_order_write_error(result)
    return result


@app.delete("/orders/{order_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_endpoint(order_code: str):
    result = delete_order(order_code)
    if not result["success"]:
        _raise_order_write_error(result)
    return None


@app.get("/orders/{order_code}/history")
def order_status_history_endpoint(order_code: str):
    result = get_order_status_history(order_code)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/customers")
def list_customers(name: str = Query(default="")):
    return get_customer_overview(name)
