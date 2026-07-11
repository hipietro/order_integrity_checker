from config import VALID_STATUSES, REPORT_FILE_NAME
from csv_manager import read_orders_from_csv
from database import order_exists_in_database
from normalizer import normalize_order

def validate_order(order, order_codes_in_file):
    """
    Validates a single order coming from the CSV file.

    The function checks:
    - missing order code
    - duplicated order code inside the CSV file
    - duplicated order code in the database
    - missing or too short customer name
    - missing or invalid quantity
    - unsupported order status

    Parameters:
        order: one row of the CSV file, represented as a dictionary.
        order_codes_in_file: list of order codes already found while reading the CSV.

    Returns:
        A list of error messages.
        If the list is empty, the order is valid.
    """

    errors = []

    order.update(normalize_order(order))
    order_code = order["order_code"]
    customer_name = order["customer_name"]
    quantity_text = order["quantity"]
    status = order["status"]

    if order_code == "":
        errors.append("missing order code")
    elif order_code in order_codes_in_file:
        errors.append("duplicated order code inside CSV file")
    elif order_exists_in_database(order_code):
        errors.append("order code already exists in database")

    if customer_name == "":
        errors.append("missing customer name")
    elif len(customer_name) < 3:
        errors.append("customer name too short")

    if quantity_text == "":
        errors.append("missing quantity")
    elif not quantity_text.isdigit():
        errors.append("quantity must be a valid number")
    elif int(quantity_text) <= 0:
        errors.append("quantity must be greater than zero")

    if status not in VALID_STATUSES:
        errors.append("invalid status")

    return errors


def validate_all_csv_orders():
    """
    Validates all orders from the CSV file.

    Returns:
        A list of validation results.

    Each validation result contains:
    - the original order
    - the list of validation errors
    """

    orders = read_orders_from_csv()
    order_codes_in_file = []
    validation_results = []

    for order in orders:
        errors = validate_order(order, order_codes_in_file)

        validation_results.append({
            "order": order,
            "errors": errors
        })

        order_codes_in_file.append(order["order_code"])

    return validation_results


def show_invalid_orders():
    """
    Shows only the invalid orders found in the CSV file.

    For each invalid order, the function prints the order code and the reasons
    why the order is not valid.
    """

    validation_results = validate_all_csv_orders()

    found_invalid_orders = False

    print("\nINVALID CSV ORDERS")
    print("------------------")

    for result in validation_results:
        order = result["order"]
        errors = result["errors"]

        if len(errors) > 0:
            found_invalid_orders = True

            print(f"\nOrder code: {order['order_code']}")
            print(f"Customer name: {order['customer_name']}")
            print(f"Quantity: {order['quantity']}")
            print(f"Status: {order['status']}")
            print("Errors:")

            for error in errors:
                print(f"- {error}")

    if not found_invalid_orders:
        print("No invalid orders found.")

def generate_invalid_orders_report(validation_results):
    """
    Generates a text report containing all invalid CSV orders and their errors.

    The report is regenerated every time the CSV import process runs.
    """

    invalid_orders = []

    for result in validation_results:
        if len(result["errors"]) > 0:
            invalid_orders.append(result)

    with open(REPORT_FILE_NAME, "w") as file:
        file.write("INVALID ORDERS REPORT\n")
        file.write("---------------------\n\n")

        if len(invalid_orders) == 0:
            file.write("No invalid orders found.\n")
        else:
            for result in invalid_orders:
                order = result["order"]
                errors = result["errors"]

                file.write(f"Order code: {order['order_code']}\n")
                file.write(f"Customer name: {order['customer_name']}\n")
                file.write(f"Quantity: {order['quantity']}\n")
                file.write(f"Status: {order['status']}\n")
                file.write("Errors:\n")

                for error in errors:
                    file.write(f"- {error}\n")

                file.write("\n")

    return len(invalid_orders)