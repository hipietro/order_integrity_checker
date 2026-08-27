# GUI Manual Test Checklist

Use this checklist after changing `gui.py` to confirm that the main order-management workflows still work correctly.

## Preparation

1. Start the application with:

   ```bash
   python3 gui.py
   ```

2. Confirm that the main window opens without errors.
3. Use an existing order code or create a temporary order for the deletion tests.

## Create order

- Enter a valid order code, customer name, quantity, and status.
- Select **Create order**.
- Confirm that a success message appears.
- Select **Show database orders** and verify that the order is present.

## Search order

- Search using the exact order code.
- Repeat the search using lowercase letters and surrounding spaces.
- Confirm that both searches find the same normalized order.
- Search for a missing code and confirm that the GUI reports no result.

## Update order status

- Enter an existing order code.
- Select a different supported status.
- Select **Update status**.
- Confirm that a success message appears.
- Display the database orders and verify the new status.

## Delete order

- Leave the deletion field empty and select **Delete order**.
- Confirm that the GUI requests an order code.
- Enter a missing order code and confirm that no deletion dialog appears.
- Enter an existing order code and select **Delete order**.
- Verify that the confirmation dialog displays the order code, customer, quantity, and status.
- Select **No** and confirm that the order remains in the database.
- Repeat the operation, select **Yes**, and confirm that the order is removed.
- Verify that the deletion field is cleared after a successful deletion.
- Confirm that pressing **Enter** inside the deletion field starts the same deletion workflow.

## CSV import and statistics

- Preview and import a CSV containing both valid and invalid orders.
- Confirm that invalid orders are skipped and reported.
- Import a valid UTF-8 CSV whose first header includes a BOM and confirm that the
  order code is recognized normally.
- Try a CSV with a missing, duplicate, or unexpected header and confirm that the
  GUI lists structural errors without showing the confirmation dialog.
- Try records with one missing cell and one extra cell. Confirm that both line
  numbers are reported, no order is imported, and the CSV remains unchanged.
- Confirm that a header-only valid CSV is reported as containing no orders,
  while a completely empty file is reported as structurally invalid.
- Display statistics and verify that the total matches the database contents.

## Regression check

Run the automated tests:

```bash
python3 -m unittest discover -s tests -v
```

All tests should pass before the change is considered complete.
