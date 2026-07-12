from config import EXPORT_FILE_NAME
from csv_manager import clear_csv_orders, export_orders_to_csv
from database import (
    delete_order_from_database,
    get_all_orders,
    get_order_by_code,
    get_order_statistics,
    insert_order_into_database,
    update_order_status_in_database
)
from normalizer import normalize_order, normalize_order_code, normalize_status
from validator import (
    generate_invalid_orders_report,
    validate_all_csv_orders,
    validate_order
)


def preview_csv_import():
    """
    Validates all CSV orders before importing them.

    Returns a summary containing:
    - all validation results
    - number of valid orders
    - number of invalid orders
    """

    validation_results = validate_all_csv_orders()

    valid_orders = 0
    invalid_orders = 0

    for result in validation_results:
        if len(result["errors"]) == 0:
            valid_orders = valid_orders + 1
        else:
            invalid_orders = invalid_orders + 1

    return {
        "validation_results": validation_results,
        "valid_orders": valid_orders,
        "invalid_orders": invalid_orders
    }


def import_csv_orders(validation_results):
    """
    Imports valid CSV orders into the database.

    Invalid orders are skipped, a report is generated, and the CSV file is cleared
    after the import process is completed.
    """

    saved_orders = []
    skipped_orders = []

    for result in validation_results:
        order = result["order"]
        errors = result["errors"]

        if len(errors) == 0:
            insert_order_into_database(order)
            saved_orders.append(order)
        else:
            skipped_orders.append({
                "order": order,
                "errors": errors
            })

    invalid_report_count = generate_invalid_orders_report(validation_results)
    clear_csv_orders()

    return {
        "saved_orders": saved_orders,
        "skipped_orders": skipped_orders,
        "invalid_report_count": invalid_report_count,
        "csv_cleared": True
    }


def get_database_orders():
    """
    Returns all orders stored in the database.
    """

    return get_all_orders()


def search_order(order_code):
    """
    Searches an order by code.
    """

    normalized_code = normalize_order_code(order_code)
    return get_order_by_code(normalized_code)


def create_order(order):
    """
    Validates and inserts a manually created order into the database.
    """

    normalized_order = normalize_order(order)
    errors = validate_order(normalized_order, [])

    if len(errors) > 0:
        return {
            "success": False,
            "order": normalized_order,
            "errors": errors
        }

    insert_order_into_database(normalized_order)

    return {
        "success": True,
        "order": normalized_order,
        "errors": []
    }


def get_statistics():
    """
    Returns database order statistics grouped by status.
    """

    return get_order_statistics()


def update_order_status(order_code, new_status):
    """
    Updates the status of an existing order.
    """

    normalized_code = normalize_order_code(order_code)
    normalized_status = normalize_status(new_status)

    order = get_order_by_code(normalized_code)

    if order is None:
        return {
            "success": False,
            "message": f"No order found with code {normalized_code}."
        }

    updated = update_order_status_in_database(normalized_code, normalized_status)

    if updated:
        return {
            "success": True,
            "message": f"Order {normalized_code} updated successfully."
        }

    return {
        "success": False,
        "message": f"Order {normalized_code} could not be updated."
    }


def delete_order(order_code):
    """
    Deletes an existing order from the database.
    """

    normalized_code = normalize_order_code(order_code)

    order = get_order_by_code(normalized_code)

    if order is None:
        return {
            "success": False,
            "message": f"No order found with code {normalized_code}."
        }

    deleted = delete_order_from_database(normalized_code)

    if deleted:
        return {
            "success": True,
            "message": f"Order {normalized_code} deleted successfully."
        }

    return {
        "success": False,
        "message": f"Order {normalized_code} could not be deleted."
    }


def clear_csv_input():
    """
    Clears the CSV input file while keeping its header.
    """

    clear_csv_orders()

    return {
        "success": True,
        "message": "CSV file cleared successfully."
    }

def export_database_orders():
    """
    Exports all database orders to a CSV file.

    This function is reusable by both the CLI and a future GUI.
    """

    orders = get_all_orders()

    exported_orders = export_orders_to_csv(orders)

    return {
        "success": True,
        "exported_orders": exported_orders,
        "file_name": EXPORT_FILE_NAME
    }