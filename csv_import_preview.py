def build_csv_import_preview(validation_results):
    """Builds a reusable, read-only summary of validated CSV orders."""

    orders_to_import = []
    orders_to_skip = []
    error_counts = {}

    for result in validation_results:
        order = result["order"]
        errors = list(result["errors"])

        if len(errors) == 0:
            orders_to_import.append(order)
            continue

        orders_to_skip.append({
            "order": order,
            "errors": errors,
        })

        for error in errors:
            error_counts[error] = error_counts.get(error, 0) + 1

    error_summary = [
        {
            "reason": reason,
            "count": count,
        }
        for reason, count in error_counts.items()
    ]

    return {
        "validation_results": validation_results,
        "total_orders": len(validation_results),
        "valid_orders": len(orders_to_import),
        "invalid_orders": len(orders_to_skip),
        "orders_to_import": orders_to_import,
        "orders_to_skip": orders_to_skip,
        "error_summary": error_summary,
        "requires_confirmation": len(validation_results) > 0,
    }
