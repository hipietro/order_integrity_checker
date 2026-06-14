# Order Integrity Checker

Order Integrity Checker is a small Python command-line project that validates business orders imported from a CSV file and checks whether the same order codes already exist in a local SQLite database.

The goal of this project is to simulate a simple data validation workflow that could happen in a company before importing external order data into an internal system.

## Why this project

This project was created while learning Python fundamentals.

It is intentionally simple, but it tries to solve a realistic problem: checking the quality of imported business data before accepting it into a system.

The project currently focuses on:

* reading structured data from a CSV file
* checking duplicated order codes
* validating required fields
* validating quantities and statuses
* printing a clear validation summary

## Technologies used

* Python
* CSV
* SQLite

No external libraries are required.

## Project structure

```text
order_integrity_checker/
│
├── main.py
├── new_orders.csv
├── README.md
└── .gitignore
```

The SQLite database file `orders.db` is generated automatically when the program runs.

## How it works

The program follows these steps:

1. Creates a local SQLite database if it does not already exist.
2. Creates an `orders` table.
3. Inserts a few sample orders into the database.
4. Reads new orders from `new_orders.csv`.
5. Validates each order.
6. Prints all detected errors.
7. Prints a final summary.

## Validation rules

An order is considered invalid if:

* the order code is missing
* the order code already exists in the database
* the order code is duplicated inside the CSV file
* the customer name is missing
* the customer name is too short
* the quantity is missing
* the quantity is less than or equal to zero
* the status is not supported
* the quantity is not a valid number

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

## Example output

```text
ORDER INTEGRITY CHECKER
-----------------------

Checking order: ORD001
Result: invalid order
- order code already exists in database

Checking order: ORD003
Result: valid order

Checking order: ORD004
Result: invalid order
- missing customer name

Checking order: ORD005
Result: invalid order
- quantity must be greater than zero

Checking order: ORD006
Result: invalid order
- invalid status

Checking order: ORD003
Result: invalid order
- duplicated order code inside CSV file

SUMMARY
-------
Valid orders: 1
Invalid orders: 5
```

## How to run

Clone the repository and run:

```bash
python3 main.py
```

The program will automatically create the SQLite database file if it does not already exist.

## Current limitations

This is an early version of the project.

At the moment:

* valid orders are checked but not inserted into the database
* the program only supports CSV input
* the code is still contained in a single Python file
* no report file is generated yet

These limitations are intentional because the project is being developed step by step.

## Roadmap

Planned improvements:

* save valid orders into the database
* add JSON input support
* generate a validation report file
* improve error handling
* split the code into multiple Python modules
* add command-line options
* add automated tests

## Purpose

This project is part of my Python learning path and is designed to practice basic programming concepts while building something close to a real-world business scenario.
