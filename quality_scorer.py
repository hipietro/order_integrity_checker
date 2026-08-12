"""Explainable quality scoring for incoming and stored orders."""

from config import VALID_STATUSES
from duplicate_detector import find_suspicious_duplicates
from normalizer import normalize_customer_name, normalize_status

GENERIC_CUSTOMER_NAMES = {
    "client",
    "customer",
    "default",
    "generic",
    "n/a",
    "na",
    "none",
    "test",
    "unknown",
}

VALIDATION_PENALTIES = {
    "missing order code": 45,
    "duplicated order code inside CSV file": 40,
    "order code already exists in database": 45,
    "missing customer name": 40,
    "customer name too short": 25,
    "missing quantity": 35,
    "quantity must be a valid number": 35,
    "quantity must be greater than zero": 30,
    "invalid status": 30,
}


def _add_penalty(penalties, code, points, explanation):
    penalties.append({
        "code": code,
        "points": points,
        "explanation": explanation,
    })


def _quantity_penalty(quantity):
    """Returns a heuristic penalty for unusually high quantities."""

    try:
        numeric_quantity = int(quantity)
    except (TypeError, ValueError):
        return None

    if numeric_quantity > 1000:
        return 25, "Quantity is unusually high (over 1000 units)."
    if numeric_quantity > 500:
        return 18, "Quantity is high (over 500 units)."
    if numeric_quantity > 100:
        return 10, "Quantity is above the normal review threshold of 100 units."

    return None


def _customer_name_penalty(customer_name, validation_errors):
    """Returns a penalty for weak but not necessarily invalid customer names."""

    normalized_name = normalize_customer_name(customer_name)
    folded_name = normalized_name.casefold()

    if not normalized_name:
        return None

    if folded_name in GENERIC_CUSTOMER_NAMES:
        return 18, "Customer name is generic and may not identify a real customer."

    if "customer name too short" not in validation_errors and len(normalized_name) < 5:
        return 8, "Customer name is very short and may be weak identifying data."

    return None


def _rating_for_score(score):
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def calculate_order_quality_score(
    order,
    validation_errors=None,
    candidate_orders=None,
):
    """Calculates an explainable quality score from 0 to 100.

    Validation still decides whether an order can be imported. This score is a
    separate review signal: technically valid orders can still receive a lower
    score when their data looks unusual or resembles another order.
    """

    errors = list(validation_errors or [])
    candidates = list(candidate_orders or [])
    penalties = []

    for error in errors:
        points = VALIDATION_PENALTIES.get(error, 15)
        _add_penalty(
            penalties,
            code=f"validation:{error}",
            points=points,
            explanation=f"Validation problem: {error}.",
        )

    customer_penalty = _customer_name_penalty(
        order.get("customer_name", ""),
        errors,
    )
    if customer_penalty is not None:
        points, explanation = customer_penalty
        _add_penalty(
            penalties,
            code="weak_customer_name",
            points=points,
            explanation=explanation,
        )

    quantity_penalty = _quantity_penalty(order.get("quantity"))
    if quantity_penalty is not None:
        points, explanation = quantity_penalty
        _add_penalty(
            penalties,
            code="unusual_quantity",
            points=points,
            explanation=explanation,
        )

    normalized_status = normalize_status(order.get("status", ""))
    if normalized_status and normalized_status not in VALID_STATUSES:
        if "invalid status" not in errors:
            _add_penalty(
                penalties,
                code="uncommon_status",
                points=30,
                explanation=(
                    f"Status '{normalized_status}' is not one of the supported statuses."
                ),
            )

    duplicate_matches = find_suspicious_duplicates(order, candidates)
    if duplicate_matches:
        duplicate_penalty = min(35, 20 + 5 * (len(duplicate_matches) - 1))
        _add_penalty(
            penalties,
            code="suspicious_duplicate",
            points=duplicate_penalty,
            explanation=(
                f"Order resembles {len(duplicate_matches)} existing or incoming "
                "order(s) and should be reviewed for duplication."
            ),
        )

    total_penalty = sum(item["points"] for item in penalties)
    score = max(0, 100 - total_penalty)
    rating = _rating_for_score(score)

    if penalties:
        explanations = [item["explanation"] for item in penalties]
    else:
        explanations = ["No quality-risk signals were detected."]

    return {
        "score": score,
        "rating": rating,
        "review_recommended": score < 85,
        "explanations": explanations,
        "penalties": penalties,
        "duplicate_matches": duplicate_matches,
    }
