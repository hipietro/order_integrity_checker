# Atomic CSV import persistence

Confirmed CSV imports need an all-or-nothing persistence boundary. Saving rows one at a time can leave earlier orders committed when a later row fails, which makes retries unsafe and gives operators a misleading picture of what was imported.

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

## Current integration status

The atomic repository and orchestration boundary are implemented and covered by focused tests. The existing `services.import_csv_orders()` entry point still uses the older per-order insert loop, so issue #31 remains open until that entry point is switched to `persist_validated_orders()` and its existing service tests are updated.

When that integration is completed, the service must also keep these external behaviors:

- return `saved_orders=[]` after any batch failure;
- preserve the CSV file after failure;
- generate the invalid-order report only after the database batch commits;
- clear the CSV only after the committed batch and report generation succeed;
- keep manual single-order creation unchanged.

## Test coverage added

Focused tests cover:

- successful multi-order insertion;
- normalized customer reuse in one batch;
- rollback of an earlier inserted order when a later order conflicts;
- rollback of customers created earlier in a failed batch;
- filtering invalid validation results before persistence;
- avoiding a database call when there are no valid orders;
- propagation of batch failures to the caller.
