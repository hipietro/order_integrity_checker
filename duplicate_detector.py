"""Deterministic suspicious-duplicate detection for business orders."""

from difflib import SequenceMatcher

from normalizer import normalize_customer_name, normalize_order_code

CUSTOMER_SIMILARITY_THRESHOLD = 0.90
QUANTITY_RELATIVE_TOLERANCE = 0.10


def _edit_distance(left, right):
    """Returns the Levenshtein edit distance between two strings."""

    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous_row = list(range(len(right) + 1))

    for left_index, left_character in enumerate(left, start=1):
        current_row = [left_index]

        for right_index, right_character in enumerate(right, start=1):
            insertion = current_row[right_index - 1] + 1
            deletion = previous_row[right_index] + 1
            substitution = (
                previous_row[right_index - 1]
                + (left_character != right_character)
            )
            current_row.append(min(insertion, deletion, substitution))

        previous_row = current_row

    return previous_row[-1]


def _is_adjacent_transposition(left, right):
    """Detects a single adjacent-character transposition."""

    if len(left) != len(right) or left == right:
        return False

    differences = [
        index
        for index, (left_character, right_character) in enumerate(
            zip(left, right)
        )
        if left_character != right_character
    ]

    if len(differences) != 2:
        return False

    first, second = differences
    return (
        second == first + 1
        and left[first] == right[second]
        and left[second] == right[first]
    )


def _codes_look_like_typo(left_code, right_code):
    """Returns True when two different codes resemble a likely typing error."""

    left = normalize_order_code(left_code)
    right = normalize_order_code(right_code)

    if left == right:
        return False

    if _is_adjacent_transposition(left, right):
        return True

    distance = _edit_distance(left, right)

    if distance != 1:
        return False

    if len(left) != len(right):
        return True

    differing_pairs = [
        (left_character, right_character)
        for left_character, right_character in zip(left, right)
        if left_character != right_character
    ]

    if len(differing_pairs) != 1:
        return False

    left_character, right_character = differing_pairs[0]

    # Sequential numeric identifiers such as ORD001 and ORD002 are common and
    # should not be flagged solely because one suffix digit differs.
    return not (left_character.isdigit() and right_character.isdigit())


def _customers_are_similar(left_order, right_order):
    """Returns True for the same customer or a very similar customer name."""

    left_customer_id = left_order.get("customer_id")
    right_customer_id = right_order.get("customer_id")

    if (
        left_customer_id is not None
        and right_customer_id is not None
        and left_customer_id == right_customer_id
    ):
        return True

    left_name = normalize_customer_name(
        left_order.get("customer_name", "")
    ).casefold()
    right_name = normalize_customer_name(
        right_order.get("customer_name", "")
    ).casefold()

    if not left_name or not right_name:
        return False

    similarity = SequenceMatcher(None, left_name, right_name).ratio()
    return similarity >= CUSTOMER_SIMILARITY_THRESHOLD


def _quantities_are_similar(left_quantity, right_quantity):
    """Returns True when quantities differ by at most 10%, with a floor of 1."""

    try:
        left = int(left_quantity)
        right = int(right_quantity)
    except (TypeError, ValueError):
        return False

    reference = max(abs(left), abs(right), 1)
    tolerance = max(1, int(reference * QUANTITY_RELATIVE_TOLERANCE))
    return abs(left - right) <= tolerance


def compare_orders_for_duplicate_risk(order, candidate):
    """Returns an explained suspicious match or None when risk is too low."""

    if order.get("id") is not None and order.get("id") == candidate.get("id"):
        return None

    left_code = normalize_order_code(order.get("order_code", ""))
    right_code = normalize_order_code(candidate.get("order_code", ""))

    if left_code == right_code:
        return None

    code_typo = _codes_look_like_typo(left_code, right_code)
    customer_similar = _customers_are_similar(order, candidate)
    quantity_similar = _quantities_are_similar(
        order.get("quantity"),
        candidate.get("quantity"),
    )
    same_status = order.get("status") == candidate.get("status")

    suspicious = code_typo or (
        customer_similar and quantity_similar and same_status
    )

    if not suspicious:
        return None

    reasons = []

    if code_typo:
        reasons.append(
            f"Order code looks like a typing variation of {right_code}."
        )
    if customer_similar:
        reasons.append("Customer identity or name is very similar.")
    if quantity_similar:
        reasons.append(
            "Quantities are identical or within the configured tolerance."
        )
    if same_status:
        reasons.append(f"Both orders have status '{order.get('status')}'.")

    return {
        "order_code": right_code,
        "customer_name": candidate.get("customer_name"),
        "quantity": candidate.get("quantity"),
        "status": candidate.get("status"),
        "reasons": reasons,
    }


def find_suspicious_duplicates(order, candidates):
    """Returns explained candidate matches that should be manually reviewed."""

    matches = []

    for candidate in candidates:
        match = compare_orders_for_duplicate_risk(order, candidate)
        if match is not None:
            matches.append(match)

    return sorted(
        matches,
        key=lambda match: (-len(match["reasons"]), match["order_code"]),
    )
