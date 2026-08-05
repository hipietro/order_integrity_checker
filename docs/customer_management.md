# Customer management

## Purpose

Customer data is stored separately from order data so that multiple orders can reference the same customer record.

This avoids repeating the same customer name in every order row and creates a cleaner base for future customer-specific features.

## Database model

The `customers` table contains:

```text
id
name
normalized_name
```

The `orders` table contains `customer_id` instead of `customer_name`.

```text
orders.customer_id -> customers.id
```

Order queries join the two tables and still return `customer_name`. This keeps the existing CLI, GUI, export, filtering, and reporting code compatible with the new schema.

## Duplicate prevention

Customer names are normalized in two stages:

1. Leading, trailing, and repeated internal spaces are removed.
2. A case-insensitive key is generated with `casefold()`.

For example, these values resolve to the same customer:

```text
Mario Rossi
 mario   rossi 
MARIO ROSSI
```

The first readable version is stored in `customers.name`. The normalized key is stored in `customers.normalized_name`, which has a `UNIQUE` constraint.

## Legacy database migration

`create_database()` detects the previous `orders` schema automatically.

When the old `customer_name` column is found, the migration:

1. Renames the old orders table temporarily.
2. Creates the new customer-linked orders table.
3. Creates or reuses normalized customers.
4. Copies every existing order while preserving its ID and order code.
5. Removes the temporary legacy table.

The migration runs inside one SQLite transaction. If it fails, the transaction is rolled back.

## Order creation and CSV import

Both manual creation and confirmed CSV imports call `insert_order_into_database()`.

That database function:

1. Normalizes the order and customer name.
2. Finds an existing customer with the same normalized key.
3. Creates the customer only when no match exists.
4. Inserts the order using the resulting `customer_id`.

This means every order-entry path follows the same duplicate-prevention rule.

## Customer services

The service layer provides:

```python
list_customers()
search_customers(customer_name)
```

An empty search returns every customer. A non-empty search performs a case-insensitive partial-name match.

## Customer browser

Run:

```bash
python3 customer_browser_cli.py
```

Enter a complete or partial name, or leave the field empty to list all customers.

## Tests

Customer tests cover:

- readable-name normalization
- case-insensitive duplicate keys
- duplicate customer reuse
- partial customer search
- the new orders schema
- migration from the legacy schema
- customer reuse across manual creation and CSV import
