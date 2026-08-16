# Database backup and recovery

Order Integrity Checker includes a local recovery workflow for the SQLite database. Backups are created with SQLite's backup API, stored under `backups/`, and excluded from Git so real business data is not committed accidentally.

## Create a backup

Run:

```bash
python3 recovery_cli.py backup
```

The command creates a timestamped file such as:

```text
backups/orders_backup_20260816_130005.db
```

The backup is validated immediately after creation. If integrity or schema validation fails, the invalid backup is deleted and the operation reports an error.

## List available backups

Run:

```bash
python3 recovery_cli.py list
```

Only files created with the managed `orders_backup_*.db` naming convention are listed. The newest backups are shown first together with their size and path.

## Restore a backup

Run:

```bash
python3 recovery_cli.py restore backups/orders_backup_20260816_130005.db
```

Restore is intentionally destructive and therefore requires explicit confirmation. The CLI asks you to type:

```text
RESTORE
```

Before replacing `orders.db`, the recovery service checks SQLite integrity and verifies that the required `customers`, `orders`, and `order_status_history` schemas are present.

The selected backup is copied into a temporary SQLite file and validated again. Only then is the temporary database atomically moved into place. This prevents an invalid or incompatible backup from overwriting the current database.

## Recovery safety guarantees

The workflow is designed around four rules:

1. Backup creation never modifies the active database.
2. Restore never runs without explicit confirmation.
3. Invalid or incompatible backups are rejected before the active database is replaced.
4. The final database replacement uses an atomic filesystem operation after the restored copy has passed validation.

## Automated tests

`tests/test_backup_service.py` covers:

- timestamped backup creation
- backup integrity and schema validation
- managed backup discovery
- restore confirmation
- rejection of invalid backups without changing the active database
- successful restore from a compatible backup

Run the complete test suite with:

```bash
python3 -m unittest discover -v
```
