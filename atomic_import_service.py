from batch_import_repository import insert_orders_atomically


def persist_validated_orders(validation_results, batch_insert=None):
    """Persists only valid validation results using one atomic batch write.

    This small orchestration boundary keeps CSV result filtering out of the
    repository and makes the batch writer easy to substitute in service tests.
    """

    if batch_insert is None:
        batch_insert = insert_orders_atomically

    valid_orders = [
        result["order"]
        for result in validation_results
        if len(result.get("errors", [])) == 0
    ]

    if not valid_orders:
        return []

    return batch_insert(valid_orders)
