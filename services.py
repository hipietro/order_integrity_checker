from atomic_import_service import persist_validated_orders
from config import EXPORT_FILE_NAME
from csv_import_preview import build_csv_import_preview
from csv_manager import (
    CsvStructureError,
    clear_csv_orders,
    export_orders_to_csv,
)
from database import (
    delete_order_from_database,
    get_all_customers,
    get_all_orders,
    get_order_by_code,
    get_order_statistics,
    get_status_history_for_order,
    insert_order_into_database,
    search_customers_by_name,
    update_order_status_in_database,
)
from duplicate_detector import find_suspicious_duplicates
from normalizer import (
    normalize_customer_name,
    normalize_order,
    normalize_order_code,
    normalize_status,
)
from quality_scorer import calculate_order_quality_score
from validator import (
    generate_invalid_orders_report,
    validate_all_csv_orders,
    validate_order,
)


def _score_csv_validation_results(validation_results):
    """Returns validation results enriched with explainable quality scores."""

    if not validation_results:
        return []

    database_orders = get_all_orders()
    csv_orders = [result["order"] for result in validation_results]
    scored_results = []

    for index, result in enumerate(validation_results):
        peer_csv_orders = [
            order
            for peer_index, order in enumerate(csv_orders)
            if peer_index != index
        ]
        candidates = database_orders + peer_csv_orders
        quality = calculate_order_quality_score(
            result["order"],
            validation_errors=result["errors"],
            candidate_orders=candidates,
        )
        scored_results.append({
            "order": result["order"],
            "errors": list(result["errors"]),
            "suggestions": list(result.get("suggestions", [])),
            "quality": quality,
        })

    return scored_results


def preview_csv_import():
    """Validates and scores CSV orders without modifying stored data."""

    try:
        validation_results = validate_all_csv_orders()
    except CsvStructureError as error:
        return build_csv_import_preview(
            [],
            structural_errors=error.errors,
        )

    scored_results = _score_csv_validation_results(validation_results)
    return build_csv_import_preview(scored_results)


def import_csv_orders(preview, confirmed=False):
    """
    Imports orders from a previously generated preview.

    Valid orders are persisted as one atomic batch. The CSV is cleared only
    after the database transaction commits and the invalid-order report is
    generated successfully.

    The preferred API receives the preview dictionary and requires explicit
    confirmation. A validation-result list is accepted for compatibility with
    the existing GUI, which calls this service after its confirmation dialog.
    """

    if isinstance(preview, list):
        preview = build_csv_import_preview(preview)
        confirmed = True

    structural_errors = list(preview.get("structural_errors", []))
    structure_valid = preview.get(
        "structure_valid",
        len(structural_errors) == 0,
    )

    if not structure_valid or structural_errors:
        details = " ".join(structural_errors)
        message = "CSV structure is invalid. Fix the file before importing."
        if details:
            message += f" {details}"

        return {
            "success": False,
            "cancelled": False,
            "saved_orders": [],
            "skipped_orders": [],
            "invalid_report_count": 0,
            "csv_cleared": False,
            "structural_errors": structural_errors,
            "message": message,
        }

    if not confirmed:
        return {
            "success": False,
            "cancelled": True,
            "saved_orders": [],
            "skipped_orders": preview.get("orders_to_skip", []),
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": "CSV import cancelled. No data was modified.",
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
            "message": "No CSV orders are available to import.",
        }

    skipped_orders = [
        {
            "order": result["order"],
            "errors": list(result["errors"]),
            "suggestions": list(result.get("suggestions", [])),
        }
        for result in validation_results
        if len(result["errors"]) > 0
    ]

    try:
        saved_orders = persist_validated_orders(validation_results)
        invalid_report_count = generate_invalid_orders_report(
            validation_results
        )
        clear_csv_orders()
    except Exception as error:
        return {
            "success": False,
            "cancelled": False,
            "saved_orders": [],
            "skipped_orders": skipped_orders,
            "invalid_report_count": 0,
            "csv_cleared": False,
            "message": f"CSV import failed: {error}",
        }

    return {
        "success": True,
        "cancelled": False,
        "saved_orders": saved_orders,
        "skipped_orders": skipped_orders,
        "invalid_report_count": invalid_report_count,
        "csv_cleared": True,
        "message": "CSV import completed successfully.",
    }


def get_database_orders():
    """Returns all orders stored in the database."""

    return get_all_orders()


def list_customers():
    """Returns all customers in normalized alphabetical order."""

    return get_all_customers()


def search_customers(customer_name):
    """Searches customers by complete or partial normalized name."""

    normalized_name = normalize_customer_name(customer_name)

    if normalized_name == "":
        return get_all_customers()

    return search_customers_by_name(normalized_name)


def get_customer_overview(customer_name=""):
    """Returns customers enriched with their current number of orders."""

    customers = search_customers(customer_name)
    orders = get_all_orders()
    order_counts = {}

    for order in orders:
        customer_id = order["customer_id"]
        order_counts[customer_id] = order_counts.get(customer_id, 0) + 1

    overview = []

    for customer in customers:
        overview.append({
            "id": customer["id"],
            "name": customer["name"],
            "normalized_name": customer["normalized_name"],
            "order_count": order_counts.get(customer["id"], 0),
        })

    return overview


def search_order(order_code):
    """Searches an order by code."""

    normalized_code = normalize_order_code(order_code)
    return get_order_by_code(normalized_code)


def get_suspicious_duplicate_review(order):
    """Returns explained possible duplicates without rejecting the order."""

    matches = find_suspicious_duplicates(order, get_all_orders())
    return {
        "review_required": len(matches) > 0,
        "matches": matches,
    }


def get_order_detail(order_code):
    """Returns one complete order detail object for presentation layers."""

    normalized_code = normalize_order_code(order_code)
    order = get_order_by_code(normalized_code)

    if order is None:
        return {
            "success": False,
            "order_code": normalized_code,
            "order": None,
            "customer": None,
            "status_history": [],
            "insights": {},
            "message": f"No order found with code {normalized_code}.",
        }

    history = get_status_history_for_order(normalized_code)
    quality = calculate_order_quality_score(
        order,
        candidate_orders=get_all_orders(),
    )
    duplicate_review = {
        "review_required": len(quality["duplicate_matches"]) > 0,
        "matches": quality["duplicate_matches"],
    }

    return {
        "success": True,
        "order_code": normalized_code,
        "order": {
            "id": order["id"],
            "order_code": order["order_code"],
            "quantity": order["quantity"],
            "status": order["status"],
        },
        "customer": {
            "id": order["customer_id"],
            "name": order["customer_name"],
        },
        "status_history": history,
        "insights": {
            "quality": quality,
            "suspicious_duplicate": duplicate_review,
        },
        "message": f"Order {normalized_code} details loaded successfully.",
    }


def create_order(order):
    """
    Validates and inserts an order linked to a normalized customer.
    """

    normalized_order = normalize_order(order)
    errors = validate_order(normalized_order, [])

    if len(errors) > 0:
        return {
            "success": False,
            "order": normalized_order,
            "errors": errors,
        }

    insert_order_into_database(normalized_order)

    return {
        "success": True,
        "order": normalized_order,
        "errors": [],
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
            "message": f"No order found with code {normalized_code}.",
        }

    updated = update_order_status_in_database(
        normalized_code,
        normalized_status,
    )

    if updated:
        return {
            "success": True,
            "message": f"Order {normalized_code} updated successfully.",
        }

    return {
        "success": False,
        "message": f"Order {normalized_code} could not be updated.",
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
            "message": (
                "No order or status history found for code "
                f"{normalized_code}."
            ),
        }

    current_status = None

    if order is not None:
        current_status = order["status"]

    return {
        "success": True,
        "order_code": normalized_code,
        "current_status": current_status,
        "history": history,
        "message": (
            f"Found {len(history)} status changes for order "
            f"{normalized_code}."
        ),
    }


def delete_order(order_code):
    """Deletes an existing order from the database."""

    normalized_code = normalize_order_code(order_code)
    order = get_order_by_code(normalized_code)

    if order is None:
        return {
            "success": False,
            "message": f"No order found with code {normalized_code}.",
        }

    deleted = delete_order_from_database(normalized_code)

    if deleted:
        return {
            "success": True,
            "message": f"Order {normalized_code} deleted successfully.",
        }

    return {
        "success": False,
        "message": f"Order {normalized_code} could not be deleted.",
    }


def clear_csv_input():
    """Clears the CSV input file while keeping its header."""

    clear_csv_orders()

    return {
        "success": True,
        "message": "CSV file cleared successfully.",
    }


def export_database_orders():
    """Exports all database orders to a CSV file."""

    orders = get_all_orders()
    exported_orders = export_orders_to_csv(orders)

    return {
        "success": True,
        "exported_orders": exported_orders,
        "file_name": EXPORT_FILE_NAME,
    }
