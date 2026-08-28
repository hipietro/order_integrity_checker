import csv

from application_errors import CsvStructureError
from config import CSV_FILE_NAME, EXPORT_FILE_NAME


CSV_COLUMNS = ("order_code", "customer_name", "quantity", "status")


def _describe_columns(columns):
    """Returns readable column names, including an empty header cell."""

    return ", ".join(column if column else "[blank]" for column in columns)


def read_orders_from_csv():
    """
    Reads all orders from the CSV file.

    Returns:
        A list of orders.
        Each order is represented as a dictionary.
    """

    with open(CSV_FILE_NAME, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, None)

        if header is None:
            raise CsvStructureError([
                "CSV header is missing. Expected columns: "
                f"{_describe_columns(CSV_COLUMNS)}."
            ])

        missing = [column for column in CSV_COLUMNS if column not in header]
        duplicate = sorted({
            column for column in header if header.count(column) > 1
        })
        unexpected = sorted({
            column for column in header if column not in CSV_COLUMNS
        })
        errors = []

        if missing:
            errors.append(
                "Missing required CSV column(s): "
                f"{_describe_columns(missing)}."
            )
        if duplicate:
            errors.append(
                "Duplicate CSV column(s): "
                f"{_describe_columns(duplicate)}."
            )
        if unexpected:
            errors.append(
                "Unexpected CSV column(s): "
                f"{_describe_columns(unexpected)}."
            )

        if errors:
            raise CsvStructureError(errors)

        orders = []
        expected_cell_count = len(CSV_COLUMNS)

        for line_number, row in enumerate(reader, start=2):
            difference = len(row) - expected_cell_count

            if difference > 0:
                errors.append(
                    f"CSV row {line_number} has {difference} extra cell(s); "
                    f"expected {expected_cell_count}."
                )
                continue
            if difference < 0:
                errors.append(
                    f"CSV row {line_number} is missing {-difference} cell(s); "
                    f"expected {expected_cell_count}."
                )
                continue

            orders.append(dict(zip(header, row)))

        if errors:
            raise CsvStructureError(errors)

        return orders


def clear_csv_orders():
    """
    Clears the CSV file while keeping the header row.

    This allows the file to remain valid and ready for new orders.
    """

    with open(CSV_FILE_NAME, "w", encoding="utf-8", newline="") as file:
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

    with open(EXPORT_FILE_NAME, "w", encoding="utf-8", newline="") as file:
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
