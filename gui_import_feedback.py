def build_csv_import_feedback(result):
    """Builds accurate GUI copy for successful and failed CSV imports."""

    saved_count = len(result.get("saved_orders", []))
    skipped_count = len(result.get("skipped_orders", []))

    summary_lines = [
        f"Saved orders: {saved_count}",
        f"Invalid orders: {skipped_count}",
    ]

    if result.get("success"):
        summary_lines.append("CSV file cleared after import.")
        return {
            "summary_lines": summary_lines,
            "status": (
                f"CSV import completed: {saved_count} saved, "
                f"{skipped_count} invalid"
            ),
            "dialog_kind": "info",
            "dialog_title": "Import completed",
            "dialog_message": "CSV import completed successfully.",
        }

    summary_lines.append("CSV file was not cleared.")
    summary_lines.append(result.get("message", "CSV import failed."))

    if saved_count == 0:
        guidance = (
            "No orders were saved; the CSV remains available for "
            "inspection or retry."
        )
    else:
        guidance = (
            "Orders were already committed before CSV finalization failed. "
            "Check the database before retrying."
        )

    summary_lines.append(guidance)
    return {
        "summary_lines": summary_lines,
        "status": (
            f"CSV import failed: {saved_count} saved, "
            f"{skipped_count} invalid"
        ),
        "dialog_kind": "error",
        "dialog_title": "Import failed",
        "dialog_message": (
            f"{result.get('message', 'CSV import failed.')}\n\n{guidance}"
        ),
    }
