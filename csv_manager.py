import csv

from config import CSV_FILE_NAME, EXPORT_FILE_NAME


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