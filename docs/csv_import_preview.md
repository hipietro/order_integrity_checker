# Safer CSV import preview

The CSV import workflow separates validation, user review, confirmation, and data modification.

## Supported CSV structure

The input file must be UTF-8 encoded. A UTF-8 byte-order mark (BOM) is
accepted, and CSV newlines are handled without platform-specific translation.

The header must contain each of these case-sensitive names exactly once:

- `order_code`
- `customer_name`
- `quantity`
- `status`

The four columns may appear in any order. Every record must contain exactly one
cell for each header. Quoted commas and quoted newlines remain part of a cell.
An explicitly empty cell is structurally valid and is passed to the normal
business validation; an omitted cell or an extra cell is a structural error.

## Preview contents

`preview_csv_import()` returns a dictionary containing:

- `total_orders`: all rows found in the CSV file
- `valid_orders`: rows that can be imported
- `invalid_orders`: rows that will be skipped
- `orders_to_import`: valid normalized orders
- `orders_to_skip`: invalid orders with their validation errors
- `error_summary`: each validation reason and its occurrence count
- `validation_results`: the complete reusable validation output
- `structure_valid`: whether the file-level CSV contract is satisfied
- `structural_errors`: actionable header or row-shape errors
- `requires_confirmation`: whether the preview contains orders and has valid structure

Creating the preview does not insert orders, generate reports, or clear the CSV file.

Structural errors are file-level failures, not skipped orders. A malformed file
is rejected as a whole: row validation and quality scoring do not run, no
database lookup is performed, confirmation is disabled, and the input file is
left unchanged. The CLI and GUI show the structural errors before any empty-file
or confirmation flow.

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

Legacy callers that already hold validation results remain supported. New
interfaces should pass the complete preview so file-level structural state is
preserved across the confirmation boundary.

## Failure behavior

The CSV file is cleared only after:

1. every valid order has been processed;
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
