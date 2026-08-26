import csv
import os
import tempfile
from pathlib import Path

from config import CSV_FILE_NAME, EXPORT_FILE_NAME


CSV_HEADER = "order_code,customer_name,quantity,status\n"


def _write_csv_header(file_handle):
    """Writes and synchronizes the replacement CSV contents."""

    file_handle.write(CSV_HEADER)
    file_handle.flush()
    os.fsync(file_handle.fileno())


def read_orders_from_csv():
    """
    Reads all orders from the CSV file.

    Returns:
        A list of orders.
        Each order is represented as a dictionary.
    """

    orders = []

    with open(CSV_FILE_NAME, "r") as file:
        reader = csv.DictReader(file)

        for order in reader:
            orders.append(order)

    return orders


def clear_csv_orders():
    """
    Atomically replaces the CSV contents with the header row.

    This allows the file to remain valid and ready for new orders.
    If writing or replacing the temporary file fails, the original input is
    left untouched.
    """

    csv_path = Path(CSV_FILE_NAME)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=csv_path.parent,
            prefix=f".{csv_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            _write_csv_header(temporary_file)

        os.replace(temporary_path, csv_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


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
