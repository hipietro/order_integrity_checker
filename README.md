# Order Integrity Checker

![Run tests](https://github.com/hipietro/order_integrity_checker/actions/workflows/tests.yml/badge.svg)

Order Integrity Checker is a small Python application that validates, imports, manages, and exports business orders stored in a local SQLite database.

The project simulates a realistic internal data-quality workflow: before external CSV orders are accepted into a company system, they are normalized, validated, checked for duplicates, and either imported or reported as invalid.

## Why this project

This project was created as a practical Python portfolio project.

It is intentionally simple, but it focuses on realistic software development concepts:

- input validation
- CSV processing
- relational SQLite persistence
- automatic schema migration
- transactional audit history
- service-layer separation
- CLI interaction
- responsive Tkinter GUI
- reusable interface components
- automated unit testing
- GitHub Actions CI

## Features

- Import orders from `new_orders.csv`
- Preview every CSV import before modifying data
- Show how many orders will be imported or skipped
- Show grouped and per-order validation reasons before confirmation
- Require explicit confirmation for the preferred import service API
- Preserve the CSV file when an import is cancelled or fails
- Validate required fields
- Detect duplicated order codes inside the CSV file
- Detect orders already existing in the database
- Normalize order codes, statuses, and customer names
- Store customers separately from orders
- Link orders to customers through `customer_id`
- Avoid duplicate customers with case-insensitive normalized names
- Migrate existing databases from the legacy embedded-customer schema
- List and search customers through reusable services
- Inspect customers from a dedicated CLI
- Save valid orders into SQLite
- Skip invalid orders and generate a report
- Search orders by code
- Insert orders manually
- Update order status
- Record old status, new status, and timestamp for every real transition
- Preserve status history after an order is deleted
- Inspect status history from a dedicated CLI
- Delete orders safely from the CLI or GUI
- Preview order details before confirming a GUI deletion
- Filter database orders by status
- Filter database orders by partial customer name
- Sort orders by order code or quantity
- Choose ascending or descending sort direction
- Use a responsive two-column GUI workspace
- Keep search, creation, update, deletion, import, and statistics visually separated
- Display results in a scrollable activity panel
- Show operation feedback in a status bar
- Export database orders to CSV
- Run automated tests locally and on GitHub Actions

## Technologies used

- Python
- SQLite
- CSV
- Tkinter and ttk
- unittest
- GitHub Actions

No external Python libraries are required.

## Project structure

```text
order_integrity_checker/
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── docs/
│   ├── csv_import_preview.md
│   ├── customer_management.md
│   ├── gui_layout.md
│   ├── gui_manual_test_checklist.md
│   └── status_history.md
│
├── tests/
│   ├── __init__.py
│   ├── test_csv_import_preview.py
│   ├── test_customer_management.py
│   ├── test_order_query_service.py
│   ├── test_order_update_services.py
│   ├── test_services.py
│   ├── test_status_history.py
│   ├── test_ui_config.py
│   └── test_validator.py
│
├── config.py
├── csv_import_preview.py
├── csv_manager.py
├── customer_browser_cli.py
├── database.py
├── gui.py
├── main.py
├── menu.py
├── new_orders.csv
├── normalizer.py
├── order_browser_cli.py
├── order_query_service.py
├── services.py
├── status_history_cli.py
├── ui_components.py
├── ui_config.py
├── validator.py
├── README.md
└── .gitignore
```

Generated files such as `orders.db`, `invalid_orders_report.txt`, and `exported_orders.csv` are ignored by Git.

## How it works

The application follows this workflow:

1. Creates the SQLite database and migrates a legacy orders table when necessary.
2. Stores unique normalized customers in the `customers` table.
3. Links each order to a customer through `orders.customer_id`.
4. Reads and normalizes orders from `new_orders.csv`.
5. Validates every order without modifying the database or CSV file.
6. Builds a preview with import counts, skipped orders, and validation reasons.
7. Shows the preview and asks the user for confirmation.
8. Imports only valid orders after confirmation, reusing existing customers.
9. Skips invalid orders and generates an invalid-order report.
10. Clears the CSV only after the confirmed import completes successfully.
11. Allows the user to manage database orders from the CLI or GUI.
12. Records each real status transition in the same transaction as the update.
13. Allows retrieving status history in chronological order.
14. Allows filtering and sorting database orders without modifying them.
15. Allows exporting database orders to CSV.

## Customer data model

Customer names are not duplicated inside the orders table. Each order stores a `customer_id` that references the `customers` table.

Names are normalized by removing extra spaces and generating a case-insensitive key. Values such as `Mario Rossi`, ` mario   rossi `, and `MARIO ROSSI` therefore reuse the same customer record.

Existing databases using the old `orders.customer_name` column are migrated automatically when `create_database()` runs. Details are available in [`docs/customer_management.md`](docs/customer_management.md).

## Validation rules

An order is considered invalid if:

- the order code is missing
- the order code already exists in the database
- the order code is duplicated inside the CSV file
- the customer name is missing
- the customer name is too short
- the quantity is missing
- the quantity is not a valid number
- the quantity is less than or equal to zero
- the status is not supported

Supported statuses are:

```text
completed
pending
cancelled
```

## Example CSV input

```csv
order_code,customer_name,quantity,status
ORD001,Mario Rossi,12,completed
ORD003,Anna Verdi,3,pending
ORD004,,5,completed
ORD005,Luca Bianchi,0,pending
ORD006,Sara Neri,7,unknown
ORD003,Paolo Gialli,4,completed
```

## How to run the CLI

```bash
python3 main.py
```

The CLI opens an interactive menu that allows importing, searching, updating, deleting, exporting, and inspecting orders.

Before a CSV import, it displays the total rows, importable rows, skipped rows, grouped error counts, and the reasons attached to each invalid order. Cancelling leaves both the database and CSV unchanged. Design details are available in [`docs/csv_import_preview.md`](docs/csv_import_preview.md).

### Browse customers

```bash
python3 customer_browser_cli.py
```

Enter a complete or partial customer name. Leave the field empty to list every customer. Search is case-insensitive and uses the normalized customer key.

### Filter and sort database orders

```bash
python3 order_browser_cli.py
```

The order browser lets you:

- select all orders or a specific status
- search by a complete or partial customer name
- sort by `order_code` or `quantity`
- choose `ascending` or `descending` order

The query service returns a new list and does not modify the orders stored in SQLite.

### Inspect order status history

```bash
python3 status_history_cli.py
```

Enter an order code to display its current status and every recorded transition from oldest to newest. Each entry contains the previous status, the new status, and the SQLite timestamp.

History is created only when the status actually changes. It remains available after the active order is deleted. Design details are available in [`docs/status_history.md`](docs/status_history.md).

## How to run the GUI

```bash
python3 gui.py
```

The Tkinter GUI reuses the same service layer used by the CLI. It supports searching, creating, updating, deleting, importing, and inspecting orders.

The interface groups search and creation in the left workspace column, update and deletion in the right column, and keeps database, CSV import, statistics, and output tools in separate cards. The activity panel is scrollable and expands when the window is resized.

Before deleting an order, the GUI displays its code, customer, quantity, and current status. Before importing CSV orders, it displays import and skipped counts and asks for explicit confirmation.

Layout documentation is available in [`docs/gui_layout.md`](docs/gui_layout.md). A broader manual regression checklist is available in [`docs/gui_manual_test_checklist.md`](docs/gui_manual_test_checklist.md).

## How to run tests

```bash
python3 -m unittest discover -s tests -v
```

The test suite covers validation rules, normalization behavior, duplicate detection, safe CSV previews and confirmation boundaries, customer creation and legacy migration, service-layer imports, manual order creation, order updates, transactional status history, retained audit history, order deletion, order filtering and sorting, CSV export behavior, and GUI configuration constraints.

## Continuous integration

This repository includes a GitHub Actions workflow that runs the unit tests automatically on every push and pull request.

Workflow file:

```text
.github/workflows/tests.yml
```

## Purpose

This project is part of my Python learning path and is designed to practice real-world software development habits while building something close to a business data-validation tool.
