# Order Integrity Checker

![Run tests](https://github.com/hipietro/order_integrity_checker/actions/workflows/tests.yml/badge.svg)

Order Integrity Checker is a small Python application that validates, imports, manages, and exports business orders stored in a local SQLite database.

The project simulates a realistic internal data-quality workflow: before external CSV orders are accepted into a company system, they are normalized, validated, checked for duplicates, and either imported or reported as invalid.

## Why this project

This project was created as a practical Python portfolio project.

It is intentionally simple, but it focuses on realistic software development concepts:

- input validation
- CSV processing
- SQLite persistence
- service-layer separation
- CLI interaction
- Tkinter GUI prototype
- automated unit testing
- GitHub Actions CI

## Features

- Import orders from `new_orders.csv`
- Validate required fields
- Detect duplicated order codes inside the CSV file
- Detect orders already existing in the database
- Normalize order codes and statuses
- Save valid orders into SQLite
- Skip invalid orders and generate a report
- Search orders by code
- Insert orders manually
- Update order status
- Delete orders
- Export database orders to CSV
- Use the project from both CLI and GUI
- Run automated tests locally and on GitHub Actions

## Technologies used

- Python
- SQLite
- CSV
- Tkinter
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
├── tests/
│   ├── __init__.py
│   ├── test_services.py
│   └── test_validator.py
│
├── config.py
├── csv_manager.py
├── database.py
├── gui.py
├── main.py
├── menu.py
├── new_orders.csv
├── normalizer.py
├── services.py
├── validator.py
├── README.md
└── .gitignore
```

Generated files such as `orders.db`, `invalid_orders_report.txt`, and `exported_orders.csv` are ignored by Git.

## How it works

The application follows this workflow:

1. Creates a local SQLite database if it does not already exist.
2. Reads orders from `new_orders.csv`.
3. Normalizes order data.
4. Validates each order.
5. Imports only valid orders.
6. Skips invalid orders.
7. Generates an invalid orders report.
8. Allows the user to manage database orders from the CLI or GUI.
9. Allows exporting database orders to CSV.

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

## How to run the GUI

```bash
python3 gui.py
```

The GUI is built with Tkinter and reuses the same service layer used by the CLI.

## How to run tests

```bash
python3 -m unittest discover -s tests -v
```

The test suite covers validation rules, normalization behavior, duplicate detection, service-layer import previews, manual order creation, and CSV export behavior.

## Continuous integration

This repository includes a GitHub Actions workflow that runs the unit tests automatically on every push and pull request.

Workflow file:

```text
.github/workflows/tests.yml
```

## Purpose

This project is part of my Python learning path and is designed to practice real-world software development habits while building something close to a business data-validation tool.
