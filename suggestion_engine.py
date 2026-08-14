import difflib
import re

from config import VALID_STATUSES
from normalizer import normalize_customer_name, normalize_status


UNUSUALLY_HIGH_QUANTITY = 1000
ORDER_CODE_PATTERN = re.compile(r"^ORD\d{3,}$")


def suggest_order_code(order_code):
    """Returns a normalized ORD-style code when a safe suggestion is possible."""

    raw_code = "" if order_code is None else str(order_code).strip().upper()
    compact_code = re.sub(r"[\s_-]+", "", raw_code)

    if ORDER_CODE_PATTERN.fullmatch(compact_code):
        return compact_code

    match = re.fullmatch(r"(?:ORD)?(\d+)", compact_code)
    if match is None:
        return None

    digits = match.group(1)
    return f"ORD{int(digits):03d}"


def suggest_status(status):
    """Returns the closest valid status for a likely misspelling."""

    normalized_status = normalize_status(status)

    if normalized_status in VALID_STATUSES or normalized_status == "":
        return None

    matches = difflib.get_close_matches(
        normalized_status,
        VALID_STATUSES,
        n=1,
        cutoff=0.6,
    )
    return matches[0] if matches else None


def generate_order_suggestions(raw_order, errors):
    """Builds actionable suggestions for an invalid order without mutating it."""

    suggestions = []
    raw_order_code = raw_order.get("order_code", "")
    suggested_code = suggest_order_code(raw_order_code)

    if "invalid order code format" in errors and suggested_code is not None:
        suggestions.append(f"Use normalized order code: {suggested_code}")

    raw_status = raw_order.get("status", "")
    suggested_status = suggest_status(raw_status)

    if "invalid status" in errors and suggested_status is not None:
        suggestions.append(f"Did you mean status: {suggested_status}?")

    raw_customer_name = raw_order.get("customer_name", "")
    normalized_customer_name = normalize_customer_name(raw_customer_name)

    if str(raw_customer_name) != normalized_customer_name:
        suggestions.append(
            f"Trim extra spaces from customer name: {normalized_customer_name}"
        )

    quantity_text = str(raw_order.get("quantity", "")).strip()

    if quantity_text.lstrip("-").isdigit():
        quantity = int(quantity_text)

        if quantity <= 0:
            suggestions.append("Review quantity: it must be greater than zero")
        elif quantity > UNUSUALLY_HIGH_QUANTITY:
            suggestions.append(
                f"Review unusually high quantity: {quantity}"
            )

    return suggestions
