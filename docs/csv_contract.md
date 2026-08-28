# CSV input contract

Order Integrity Checker validates the complete file structure before it validates individual orders. A structural failure blocks the preview confirmation boundary, performs no database write, creates no invalid-order report, and leaves the input file untouched.

## Encoding and CSV rules

- Files are read as UTF-8; an optional UTF-8 byte-order mark (BOM) is accepted.
- CSV parsing uses newline-safe handling and supports standard quoted values, including commas inside a quoted customer name.
- The header must contain exactly four unique columns: `order_code`, `customer_name`, `quantity`, and `status`.
- Header order may vary, but missing, duplicate, blank, or unexpected columns are rejected.
- Every data row must contain exactly four cells. Short and long rows are reported with their CSV line number.

Valid example:

```csv
order_code,customer_name,quantity,status
ORD100,Mario Rossi,2,pending
ORD101,"Rossi, Anna",4,completed
```

## Failure behavior

Structural problems are returned in `structure_errors` on the import preview. The same preview sets:

```text
import_blocked = true
requires_confirmation = false
```

CLI and Tkinter users see the actionable structural messages. Even if a caller manually sends the blocked preview to `import_csv_orders(..., confirmed=True)`, the service refuses the import and preserves the CSV file.

Once the structure is valid, ordinary row-level business validation applies. Invalid business rows may be skipped and reported, while all valid rows are persisted in one atomic transaction after explicit confirmation.
