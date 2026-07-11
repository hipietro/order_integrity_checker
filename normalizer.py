def normalize_text(value):
    """
    Removes leading and trailing spaces from a text value.

    If the value is missing, it returns an empty string.
    """

    if value is None:
        return ""

    return value.strip()


def normalize_order_code(order_code):
    """
    Normalizes an order code.

    Order codes are stored and searched using uppercase letters.
    """

    return normalize_text(order_code).upper()


def normalize_status(status):
    """
    Normalizes an order status.

    Status values are stored and checked using lowercase letters.
    """

    return normalize_text(status).lower()


def normalize_order(order):
    """
    Normalizes all relevant fields of an order.

    This keeps imported and manually inserted orders consistent before validation
    and database insertion.
    """

    return {
        "order_code": normalize_order_code(order.get("order_code", "")),
        "customer_name": normalize_text(order.get("customer_name", "")),
        "quantity": normalize_text(order.get("quantity", "")),
        "status": normalize_status(order.get("status", ""))
    }