from typing import Literal

from pydantic import BaseModel, Field


OrderStatus = Literal["completed", "pending", "cancelled"]


class OrderCreateRequest(BaseModel):
    order_code: str = Field(min_length=1)
    customer_name: str = Field(min_length=1)
    quantity: int
    status: OrderStatus


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus


class ErrorResponse(BaseModel):
    detail: str
    errors: list[str] = []
