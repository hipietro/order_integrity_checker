from database import get_all_orders
from normalizer import normalize_status


SORT_FIELDS = ("order_code", "quantity")
SORT_DIRECTIONS = ("ascending", "descending")


def filter_orders(orders, status="", customer_name=""):
    """Returns orders matching the optional status and customer filters."""

    normalized_status = normalize_status(status) if status else ""
    normalized_customer = customer_name.strip().lower()

    filtered_orders = []

    for order in orders:
        order_status = str(order["status"]).strip().lower()
        order_customer = str(order["customer_name"]).strip().lower()

        status_matches = (
            normalized_status in ("", "all")
            or order_status == normalized_status
        )
        customer_matches = (
            normalized_customer == ""
            or normalized_customer in order_customer
        )

        if status_matches and customer_matches:
            filtered_orders.append(order)

    return filtered_orders


def sort_orders(orders, sort_by="order_code", direction="ascending"):
    """Returns a new list sorted by order code or quantity."""

    if sort_by not in SORT_FIELDS:
        raise ValueError(
            f"Unsupported sort field: {sort_by}. "
            f"Choose one of: {', '.join(SORT_FIELDS)}."
        )

    if direction not in SORT_DIRECTIONS:
        raise ValueError(
            f"Unsupported sort direction: {direction}. "
            f"Choose one of: {', '.join(SORT_DIRECTIONS)}."
        )

    reverse = direction == "descending"

    if sort_by == "quantity":
        key_function = lambda order: int(order["quantity"])
    else:
        key_function = lambda order: str(order["order_code"]).upper()

    return sorted(orders, key=key_function, reverse=reverse)


def filter_and_sort_orders(
    orders,
    status="",
    customer_name="",
    sort_by="order_code",
    direction="ascending",
):
    """Applies filters first and sorting second without mutating the input."""

    filtered_orders = filter_orders(
        orders,
        status=status,
        customer_name=customer_name,
    )

    return sort_orders(
        filtered_orders,
        sort_by=sort_by,
        direction=direction,
    )


def get_filtered_and_sorted_orders(
    status="",
    customer_name="",
    sort_by="order_code",
    direction="ascending",
):
    """Loads database orders and applies the requested query options."""

    orders = get_all_orders()

    return filter_and_sort_orders(
        orders,
        status=status,
        customer_name=customer_name,
        sort_by=sort_by,
        direction=direction,
    )
