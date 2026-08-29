from config import REPORT_FILE_NAME


POST_COMMIT_FAILURE_STAGES = {"invalid_report", "csv_cleanup"}


def _order_code(order):
    return order.get("order_code") or "[missing code]"


def build_csv_import_feedback(result):
    """Builds truthful, interface-neutral feedback for one import result."""

    saved_orders = list(result.get("saved_orders", []))
    skipped_orders = list(result.get("skipped_orders", []))
    failure_stage = result.get("failure_stage")
    post_commit_failure = failure_stage in POST_COMMIT_FAILURE_STAGES

    if result.get("success", False):
        outcome = "success"
        dialog_title = "Import completed"
        status_message = (
            f"CSV import completed: {len(saved_orders)} saved, "
            f"{len(skipped_orders)} invalid"
        )
    elif post_commit_failure:
        outcome = "post_commit_failure"
        dialog_title = "Import incomplete"
        status_message = (
            "CSV import incomplete after persistence: "
            f"{len(saved_orders)} saved"
        )
    else:
        outcome = "failure"
        dialog_title = "Import failed"
        status_message = "CSV import failed before database commit"

    lines = [result["message"], ""]

    for order in saved_orders:
        lines.append(f"{_order_code(order)}: saved into database")

    for skipped_order in skipped_orders:
        order = skipped_order.get("order", {})
        errors = skipped_order.get("errors", [])
        reasons = "; ".join(errors) if errors else "validation failed"
        lines.append(f"{_order_code(order)}: skipped — {reasons}")

    lines.extend([
        "",
        "SUMMARY",
        "-------",
        f"Saved orders: {len(saved_orders)}",
        f"Invalid orders: {len(skipped_orders)}",
    ])

    if result.get("report_generated", False):
        lines.append(f"Invalid orders report generated: {REPORT_FILE_NAME}")

    if result.get("csv_cleared", False):
        lines.append("CSV file cleared after successful import.")
    else:
        lines.append("CSV file was not cleared.")

    return {
        "outcome": outcome,
        "lines": lines,
        "status_message": status_message,
        "dialog_title": dialog_title,
        "dialog_message": result["message"],
    }
