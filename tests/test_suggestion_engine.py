from suggestion_engine import (
    generate_order_suggestions,
    suggest_order_code,
    suggest_status,
)


def test_suggest_order_code_normalizes_numeric_codes():
    assert suggest_order_code(" 12 ") == "ORD012"
    assert suggest_order_code("ord-7") == "ORD007"
    assert suggest_order_code("ORD001") == "ORD001"


def test_suggest_order_code_returns_none_when_no_safe_fix_exists():
    assert suggest_order_code("customer-a") is None


def test_suggest_status_returns_closest_valid_status():
    assert suggest_status("pendng") == "pending"
    assert suggest_status("COMPLETED") is None


def test_generate_order_suggestions_combines_actionable_fixes():
    raw_order = {
        "order_code": " ord-7 ",
        "customer_name": "  Mario   Rossi  ",
        "quantity": "0",
        "status": "pendng",
    }
    errors = [
        "invalid order code format",
        "quantity must be greater than zero",
        "invalid status",
    ]

    suggestions = generate_order_suggestions(raw_order, errors)

    assert "Use normalized order code: ORD007" in suggestions
    assert "Did you mean status: pending?" in suggestions
    assert "Trim extra spaces from customer name: Mario Rossi" in suggestions
    assert "Review quantity: it must be greater than zero" in suggestions


def test_generate_order_suggestions_flags_unusually_high_quantity():
    suggestions = generate_order_suggestions(
        {
            "order_code": "ORD123",
            "customer_name": "Mario Rossi",
            "quantity": "5000",
            "status": "pending",
        },
        [],
    )

    assert "Review unusually high quantity: 5000" in suggestions
