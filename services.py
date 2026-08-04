from config import EXPORT_FILE_NAME
from csv_import_preview import build_csv_import_preview
from csv_manager import clear_csv_orders, export_orders_to_csv
from database import (
    delete_order_from_database,
    get_all_orders,
    get_order_by_code,
    get_order_statistics,
    get_status_history_for_order,
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
    """Validates CSV orders and returns a detailed, read-only preview."""

    validation_results = validate_all_csv_orders()
    return build_csv_import_preview(validation_results)


def import_csv_orders(preview, confirmed=False):
    """
    Imports orders from a previously generated preview.

    The preferred API receives the preview dictionary and requires explicit
    confirmation. A validation-result list is accepted for compatibility with
    the existing GUI, which calls this service only after its confirmation
    dialog has been accepted.
    """

    if isinstance(preview, list):
        preview = build_csv_import_preview(preview)
        confirmed = True

    if not confirmed:
        return {
            "success": False,
            "cancelled": True,
            "saved_orders": [],
            "skipped_orders": preview.get("orders_to_skip", []),
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": "CSV import cancelled. No data was modified."
        }

    validation_results = preview.get("validation_results", [])

    if len(validation_results) == 0:
        return {
            "success": False,
            "cancelled": False,
            "saved_orders": [],
            "skipped_orders": [],
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": "No CSV orders are available to import."
        }

    saved_orders = []
    skipped_orders = []

    try:
        for result in validation_results:
            order = result["order"]
            errors = result["errors"]

            if len(errors) == 0:
                insert_order_into_database(order)
                saved_orders.append(order)
            else:
                skipped_orders.append({
                    "order": order,
                    "errors": list(errors)
                })

        invalid_report_count = generate_invalid_orders_report(validation_results)
        clear_csv_orders()
    except Exception as error:
        return {
            "success": False,
            "cancelled": False,
            "saved_orders": saved_orders,
            "skipped_orders": skipped_orders,
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": f"CSV import failed: {error}"
        }

    return {
        "success": True,
        "cancelled": False,
        "saved_orders": saved_orders,
        "skipped_orders": skipped_orders,
        "invalid_report_count": invalid_report_count,
        "csv_cleared": True,
        "message": "CSV import completed successfully."
    }


def get_database_orders():
    """Returns all orders stored in the database."""

    return get_all_orders()


def search_order(order_code):
    """Searches an order by code."""

    normalized_code = normalize_order_code(order_code)
    return get_order_by_code(normalized_code)


def create_order(order):
    """Validates and inserts a manually created order into the database."""

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
    """Returns database order statistics grouped by status."""

    return get_order_statistics()


def update_order_status(order_code, new_status):
    """Updates the status of an existing order."""

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


def get_order_status_history(order_code):
    """
    Returns the recorded status history for an order code.

    History remains available after an order is deleted. If neither an active
    order nor history exists for the normalized code, the service returns an
    unsuccessful result.
    """

    normalized_code = normalize_order_code(order_code)
    order = get_order_by_code(normalized_code)
    history = get_status_history_for_order(normalized_code)

    if order is None and len(history) == 0:
        return {
            "success": False,
            "order_code": normalized_code,
            "current_status": None,
            "history": [],
            "message": f"No order or status history found for code {normalized_code}."
        }

    current_status = None

    if order is not None:
        current_status = order["status"]

    return {
        "success": True,
        "order_code": normalized_code,
        "current_status": current_status,
        "history": history,
        "message": f"Found {len(history)} status changes for order {normalized_code}."
    }


def delete_order(order_code):
    """Deletes an existing order from the database."""

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
    """Clears the CSV input file while keeping its header."""

    clear_csv_orders()

    return {
        "success": True,
        "message": "CSV file cleared successfully."
    }


def export_database_orders():
    """Exports all database orders to a CSV file."""

    orders = get_all_orders()
    exported_orders = export_orders_to_csv(orders)

    return {
        "success": True,
        "exported_orders": exported_orders,
        "file_name": EXPORT_FILE_NAME
    }
