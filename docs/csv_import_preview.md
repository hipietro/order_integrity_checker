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
- `requires_confirmation`: whether the preview contains any orders

Creating the preview does not insert orders, generate reports, or clear the CSV file.

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

All valid rows in one confirmed preview are inserted through a single SQLite
transaction. The transaction also includes any normalized customer records
created for those rows.

The CSV file is cleared only after:

1. invalid orders have been collected;
2. every valid order has been committed together;
3. the invalid-order report has been generated;
4. a complete header-only replacement CSV has been written and synchronized.

The final cleanup uses an atomic file replacement in the same directory. An
error while writing or replacing the temporary file leaves the original CSV
untouched instead of truncating it in place.

If any order fails, the complete transaction is rolled back. Earlier orders
and customers from the same batch are not left behind:

- the result contains `saved_orders=[]`;
- the invalid-order report is not generated;
- the CSV input is preserved for investigation or retry.

Manual single-order creation keeps its independent transaction because it is
not part of the confirmed CSV batch.

If the database commit succeeds but a later report or CSV cleanup operation
fails, the unsuccessful result still lists the orders that were committed and
the CSV remains available. This distinguishes a rolled-back batch from a
post-commit file-handling problem.

The GUI and CLI present these outcomes differently. A rolled-back or otherwise
unsaved batch reports that no orders were saved and that the CSV is available
for inspection. A post-commit failure reports the codes already committed and
warns the operator to check the database before retrying. Skipped-row reasons
are shown directly if the invalid-order report was not generated. No failure
path claims that the CSV was cleared or that the import completed successfully.

## CLI behavior

The main CLI shows the following before asking for confirmation:

- total rows
- number of rows to import
- number of rows to skip
- grouped validation-reason counts
- each skipped order and all of its validation reasons

This makes the import decision reviewable before the database or input file is modified.
