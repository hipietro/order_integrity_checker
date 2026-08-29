# Atomic CSV import persistence

Confirmed CSV imports use an all-or-nothing persistence boundary. Saving rows one at a time can leave earlier orders committed when a later row fails, which makes retries unsafe and gives operators a misleading picture of what was imported.

## Transactional repository

`batch_import_repository.insert_orders_atomically()` is the database boundary for a confirmed batch of valid orders.

It provides these guarantees:

- every order in the batch uses one SQLite connection and one transaction;
- order and customer values are normalized again at the persistence boundary;
- customers are reused by normalized name within the same transaction;
- the transaction commits only after every order has been inserted;
- any exception rolls back both orders and customers created by the batch;
- the connection is closed whether the batch succeeds or fails.

A late UNIQUE conflict is therefore unable to leave an earlier order or a newly created customer behind.

## Orchestration boundary

`atomic_import_service.persist_validated_orders()` separates validation-result filtering from database persistence. It collects only results without validation errors and sends them to the batch repository in one call. Invalid rows are deliberately not sent to the repository.

This separation keeps three responsibilities distinct:

1. validation decides which rows are acceptable;
2. orchestration selects the valid orders for the confirmed operation;
3. the repository owns the SQLite transaction.

## Service integration

`services.import_csv_orders()` now uses `persist_validated_orders()` for every confirmed preview instead of inserting valid rows individually.

The lifecycle is intentionally ordered as follows:

1. collect invalid rows for the skipped-order response;
2. persist all valid rows in one atomic SQLite batch;
3. generate the invalid-order report only after the batch commits;
4. write and sync replacement CSV contents in a temporary file;
5. atomically replace the input only after persistence and report generation succeed;
6. return the committed orders in `saved_orders`.

If batch persistence raises an exception, the service returns `success=False`, reports `saved_orders=[]`, leaves `csv_cleared=False`, and does not generate a report or clear the CSV. This matches the database rollback contract and avoids claiming that partially inserted rows were saved.

Report and cleanup failures happen after the database transaction has committed. These outcomes also return `success=False`, but retain every committed order in `saved_orders`, expose `failure_stage` as `invalid_report` or `csv_cleanup`, and warn the operator to inspect the database before retrying. `report_generated` records whether report creation completed even when its invalid-row count is zero. Atomic replacement ensures that cleanup failures do not leave a truncated input file.

Manual single-order creation remains independent: `services.create_order()` still validates one order and calls `database.insert_order_into_database()` directly.

## Test coverage

Automated coverage includes:

- successful multi-order insertion;
- normalized customer reuse in one batch;
- rollback of an earlier inserted order when a later order conflicts;
- rollback of customers created earlier in a failed batch;
- filtering invalid validation results before persistence;
- avoiding a database call when there are no valid orders;
- propagation of batch failures to the caller;
- confirmed service imports delegating to the atomic batch boundary;
- report generation and CSV clearing after successful persistence;
- `saved_orders=[]`, no report, and no CSV clearing after batch failure;
- committed-order reporting after report or cleanup failure;
- preservation of the original CSV after partial temporary writes or failed replacement;
- identical retry-safe outcome wording in CLI and Tkinter interfaces;
- a service-level SQLite integration test that forces a late UNIQUE conflict and verifies both the earlier order and newly created customers are rolled back.
