# Unified order detail view

The unified order detail view gives the GUI one place to display everything currently known about an active order.

## Service contract

Presentation layers call:

```python
get_order_detail(order_code)
```

The service normalizes the order code and returns a structured result containing:

- the active order data
- customer ID and customer name
- chronological status history
- an `insights` dictionary reserved for future integrity analysis
- a clear success or failure message

The GUI does not query SQLite directly.

A successful result has this shape:

```python
{
    "success": True,
    "order_code": "ORD007",
    "order": {
        "id": 7,
        "order_code": "ORD007",
        "quantity": 8,
        "status": "completed",
    },
    "customer": {
        "id": 3,
        "name": "Mario Rossi",
    },
    "status_history": [
        {
            "old_status": "pending",
            "new_status": "completed",
            "changed_at": "2026-08-10 10:00:00",
        }
    ],
    "insights": {},
    "message": "Order ORD007 details loaded successfully.",
}
```

Missing active orders return `success: False` and do not try to load status history.

## GUI navigation

There are two ways to reach the same detail window.

### Search

Enter an order code in the main search section and use **Search and open details**. A successful search opens the detail window immediately.

### Database order browser

Use **Database → Browse orders** from the main GUI. The browser displays current database orders in a table.

Open the unified detail window by:

- double-clicking an order row, or
- selecting an order and pressing **Open details**

The database order list is loaded through the existing service layer.

## Detail window

The detail view contains four logical areas:

1. **Order** — database ID, code, quantity, and current status.
2. **Customer** — customer ID and name.
3. **Integrity insights** — reserved extension area for upcoming quality scoring and suspicious-duplicate detection.
4. **Status history** — previous status, new status, and timestamp for every recorded transition.

The history section also handles orders that have never changed status by displaying an explicit empty-state message.

## Extensibility

The `insights` dictionary is intentionally empty today. Future integrity features can enrich it without forcing the GUI to redesign the basic order/customer/history contract.

Expected future examples include:

```python
"insights": {
    "quality_score": 82,
    "suspicious_duplicates": [...],
    "suggested_fixes": [...],
}
```

This keeps the order detail view as the central place where future data-quality analysis can be presented to the user.
