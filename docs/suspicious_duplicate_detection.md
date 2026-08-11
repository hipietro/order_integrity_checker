# Suspicious duplicate detection

The duplicate detector identifies orders that are not exact duplicates but may represent the same business operation entered more than once.

The feature is deliberately conservative: suspicious orders are marked for manual review and are never rejected automatically.

## Detection signals

A pair of orders can be flagged when at least one of these patterns is found:

1. **Likely order-code typo**
   - one missing or extra character
   - one adjacent-character transposition
   - one non-numeric character substitution

2. **Strong business-data similarity**
   - same customer or a very similar normalized customer name
   - quantities within a 10% tolerance, with a minimum tolerance of one unit
   - same order status

Sequential numeric codes such as `ORD001` and `ORD002` are not considered suspicious from the code alone. This prevents ordinary sequential identifiers from generating a large number of false positives.

## Explainable results

Every suspicious match contains:

- candidate order code
- customer name
- quantity
- status
- a list of human-readable reasons

The service layer exposes the result inside the unified order detail object:

```python
{
    "insights": {
        "suspicious_duplicate": {
            "review_required": True,
            "matches": [
                {
                    "order_code": "ORD10",
                    "customer_name": "Mario Rossi",
                    "quantity": 10,
                    "status": "pending",
                    "reasons": [
                        "Order code looks like a typing variation of ORD10.",
                        "Customer identity or name is very similar.",
                    ],
                }
            ],
        }
    }
}
```

## GUI behavior

The unified order detail window displays the result in the **Integrity insights** section.

When no candidate is found, the GUI reports that manual duplicate review is not required.

When candidates are found, the GUI clearly states that review is recommended and displays each candidate together with the reasons. The original order remains valid and is not deleted, rejected, or modified.

## Architecture

The rules live in `duplicate_detector.py`, which is independent of SQLite and Tkinter. The service layer supplies database orders to the detector, and presentation layers consume the resulting data structure.

This separation allows the same detector to be reused later by:

- CSV import previews
- FastAPI endpoints
- background quality checks
- future quality-score calculations

## Testing

The tests cover:

- missing-character code typos
- adjacent transpositions
- sequential numeric codes that should not be flagged by code alone
- same-customer orders with similar quantity and status
- small customer-name typing differences
- clearly unrelated orders
- exclusion of the order itself from candidate matches
