# Safer CSV import preview

The CSV import workflow separates validation, user review, confirmation, and data modification.

## Preview contents

`preview_csv_import()` returns a dictionary containing:

- `total_orders`: all rows found in the CSV file
- `valid_orders`: rows that can be imported
- `invalid_orders`: rows that will be skipped
- `orders_to_import`: valid normalized orders
- `orders_to_skip`: invalid orders with their validation errors
- `error_summary`: each validation reason and its occurrence count
- `validation_results`: the complete reusable validation output
- `structure_errors`: actionable file-contract failures
- `import_blocked`: whether structural errors prevent persistence
- `requires_confirmation`: whether a structurally valid preview contains orders

Creating the preview does not insert orders, generate reports, or clear the CSV file.

The complete encoding, header, and row-width rules are documented in [`csv_contract.md`](csv_contract.md).

## Confirmation boundary

The preferred service call is:

```python
preview = preview_csv_import()
result = import_csv_orders(preview, confirmed=True)
```

When `confirmed` is false:

- no order is inserted
- no invalid-order report is generated
- the CSV file is not cleared
- the result is marked as cancelled

The existing GUI validation-list call remains supported because the GUI invokes it only after its own confirmation dialog has been accepted.

## Failure behavior

Missing, duplicate, blank, or unexpected headers and rows with extra or missing cells block the import before confirmation. Structural failures are shown in the CLI and Tkinter preview, and the CSV remains unchanged.

The CSV file is cleared only after:

1. every valid order has been committed in one atomic transaction;
2. invalid orders have been collected;
3. the invalid-order report has been generated.

If an exception occurs before completion, the service returns an unsuccessful result and preserves the CSV file for investigation or retry.

## CLI behavior

The main CLI shows the following before asking for confirmation:

- total rows
- number of rows to import
- number of rows to skip
- grouped validation-reason counts
- each skipped order and all of its validation reasons

This makes the import decision reviewable before the database or input file is modified.
