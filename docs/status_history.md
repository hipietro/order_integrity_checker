# Order status history

The application records every real order status transition in SQLite.

## Database structure

The `order_status_history` table stores:

- a unique history entry ID
- the normalized order code
- the previous status
- the new status
- the SQLite `CURRENT_TIMESTAMP` value

An index on `order_code` keeps history lookup efficient.

## Transaction behavior

`update_order_status_in_database()` performs the order update and history insert using the same SQLite connection and transaction.

The operation follows this sequence:

1. Normalize and validate the requested status.
2. Read the current order status.
3. Skip history creation when the requested status is unchanged.
4. Update the order.
5. Insert the old and new status into the history table.
6. Commit both changes together.

If SQLite raises an error, the transaction is rolled back. This prevents an order from changing status without the matching audit record.

## Retained audit history

Deleting an order does not delete its recorded status history. The history service can therefore show previous transitions even after the active order no longer exists.

## Command-line usage

Run:

```bash
python3 status_history_cli.py
```

Then enter an order code. The command displays:

- the normalized order code
- the current status, when the order still exists
- every recorded transition in chronological order
- the timestamp of each transition

A newly created order has no history until its status changes for the first time.

## Tests

`tests/test_status_history.py` uses a temporary SQLite database to verify:

- table creation
- status transition recording
- chronological retrieval
- no duplicate entry for an unchanged status
- rejection of unsupported statuses
- retained history after deletion

The same file also tests the service contract with mocks.
