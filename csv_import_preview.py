def build_csv_import_preview(validation_results, structural_errors=None):
    """Builds a reusable, read-only summary of validated CSV orders."""

    structural_errors = list(structural_errors or [])
    orders_to_import = []
    orders_to_skip = []
    error_counts = {}
    quality_scores = []
    review_recommended_orders = 0
    suggestion_count = 0
    orders_with_suggestions = 0

    for result in validation_results:
        order = result["order"]
        errors = list(result["errors"])
        suggestions = list(result.get("suggestions", []))
        quality = result.get("quality")

        if suggestions:
            suggestion_count += len(suggestions)
            orders_with_suggestions += 1

        if quality is not None:
            quality_scores.append(quality["score"])
            if quality["review_recommended"]:
                review_recommended_orders += 1

        if len(errors) == 0:
            orders_to_import.append(order)
            continue

        orders_to_skip.append({
            "order": order,
            "errors": errors,
            "suggestions": suggestions,
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

    average_quality_score = None
    if quality_scores:
        average_quality_score = round(sum(quality_scores) / len(quality_scores), 1)

    return {
        "structure_valid": len(structural_errors) == 0,
        "structural_errors": structural_errors,
        "validation_results": validation_results,
        "total_orders": len(validation_results),
        "valid_orders": len(orders_to_import),
        "invalid_orders": len(orders_to_skip),
        "orders_to_import": orders_to_import,
        "orders_to_skip": orders_to_skip,
        "error_summary": error_summary,
        "suggestion_count": suggestion_count,
        "orders_with_suggestions": orders_with_suggestions,
        "average_quality_score": average_quality_score,
        "review_recommended_orders": review_recommended_orders,
        "requires_confirmation": (
            len(validation_results) > 0 and len(structural_errors) == 0
        ),
    }
