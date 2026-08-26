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

## Integrated service workflow

`services.import_csv_orders()` passes the complete validation result set to
`persist_validated_orders()`. The orchestrator filters valid rows and calls the
batch repository exactly once. After that call succeeds, the service generates
the invalid-order report and clears the input CSV.

The ordering is intentional:

1. collect invalid rows for the result;
2. persist every valid row in one atomic database batch;
3. generate the invalid-order report;
4. clear the input CSV.

If the database batch fails, the service returns `saved_orders=[]`, does not
generate the report, and preserves the CSV. If report generation or CSV
cleanup fails after the commit, the result retains the committed orders and
marks the operation unsuccessful. The GUI then warns the operator to inspect
the database before retrying instead of claiming that the import succeeded.

Manual creation still calls `database.insert_order_into_database()` and keeps
its original independent transaction and `None` return contract.

## Test coverage added

Focused tests cover:

- successful multi-order insertion;
- normalized customer reuse in one batch;
- rollback of an earlier inserted order when a later order conflicts;
- rollback of customers created earlier in a failed batch;
- filtering invalid validation results before persistence;
- avoiding a database call when there are no valid orders;
- propagation of batch failures to the caller;
- the complete service-to-repository rollback path for a stale preview;
- preservation of committed-order details after a post-commit failure;
- accurate GUI feedback for rollback and post-commit failure results.
