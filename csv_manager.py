import csv
from collections import Counter

from config import CSV_FILE_NAME, EXPORT_FILE_NAME


EXPECTED_CSV_COLUMNS = (
    "order_code",
    "customer_name",
    "quantity",
    "status",
)


class CsvStructureError(ValueError):
    """Reports one or more structural problems in a CSV input file."""

    def __init__(self, errors):
        self.errors = tuple(errors)
        super().__init__(" ".join(self.errors))


def _validate_headers(headers):
    """Returns deterministic errors for an invalid CSV header row."""

    if not headers:
        return ["CSV file is missing the required header row."]

    header_counts = Counter(headers)
    missing = [
        header
        for header in EXPECTED_CSV_COLUMNS
        if header_counts[header] == 0
    ]
    duplicates = list(dict.fromkeys(
        header for header in headers if header_counts[header] > 1
    ))
    unexpected = list(dict.fromkeys(
        header for header in headers if header not in EXPECTED_CSV_COLUMNS
    ))
    errors = []

    if missing:
        errors.append(
            "Missing required CSV header(s): " + ", ".join(missing) + "."
        )

    if duplicates:
        errors.append(
            "Duplicate CSV header(s): "
            + ", ".join(duplicates)
            + ". Each header must appear once."
        )

    if unexpected:
        errors.append(
            "Unexpected CSV header(s): "
            + ", ".join(repr(header) for header in unexpected)
            + ". Expected only: "
            + ", ".join(EXPECTED_CSV_COLUMNS)
            + "."
        )

    return errors


def read_orders_from_csv():
    """
    Reads all orders from the CSV file.

    Returns:
        A list of orders.
        Each order is represented as a dictionary.
    """

    orders = []
    reader = None

    try:
        with open(
            CSV_FILE_NAME,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file, strict=True)
            headers = next(reader, None)
            header_errors = _validate_headers(headers)

            if header_errors:
                raise CsvStructureError(header_errors)

            row_errors = []

            for row in reader:
                row_number = reader.line_num

                if len(row) < len(headers):
                    missing_columns = headers[len(row):]
                    missing_count = len(missing_columns)
                    cell_description = (
                        "a cell" if missing_count == 1
                        else f"{missing_count} cells"
                    )
                    row_errors.append(
                        f"CSV row {row_number} is missing "
                        f"{cell_description} for: "
                        + ", ".join(missing_columns)
                        + "."
                    )
                    continue

                if len(row) > len(headers):
                    extra_count = len(row) - len(headers)
                    cell_word = "cell" if extra_count == 1 else "cells"
                    row_errors.append(
                        f"CSV row {row_number} has {extra_count} extra "
                        f"{cell_word}; expected exactly {len(headers)}."
                    )
                    continue

                orders.append(dict(zip(headers, row)))

            if row_errors:
                raise CsvStructureError(row_errors)
    except CsvStructureError:
        raise
    except UnicodeDecodeError as error:
        raise CsvStructureError([
            "CSV input must be UTF-8 encoded; an optional UTF-8 BOM is "
            "supported."
        ]) from error
    except csv.Error as error:
        line_number = reader.line_num if reader is not None else "unknown"
        raise CsvStructureError([
            f"Malformed CSV data near line {line_number}: {error}."
        ]) from error

    return orders


def clear_csv_orders():
    """
    Clears the CSV file while keeping the header row.

    This allows the file to remain valid and ready for new orders.
    """

    with open(CSV_FILE_NAME, "w") as file:
        file.write("order_code,customer_name,quantity,status\n")

    print(f"{CSV_FILE_NAME} cleared successfully.")

def export_orders_to_csv(orders):
    '''
    Exports database orders to a CSV file. 

    Parameters:
        orders: list of orders coming from the database.

    Returns:
        The number of exported orders.
    '''

    fieldnames = ["id", "order_code", "customer_name", "quantity", "status"]

    with open(EXPORT_FILE_NAME, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for order in orders:
            writer.writerow({
                "id": order["id"],
                "order_code": order["order_code"],
                "customer_name": order["customer_name"],
                "quantity": order["quantity"],
                "status": order["status"]
            })

    return len(orders)
