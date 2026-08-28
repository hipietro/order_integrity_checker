"""Stable application errors shared by persistence and interface layers."""


class OrderIntegrityError(Exception):
    """Base class for expected order-management failures."""


class OrderNotFoundError(OrderIntegrityError):
    """Raised when a write targets an order that no longer exists."""


class OrderConflictError(OrderIntegrityError):
    """Raised when persisted data conflicts with an existing order."""


class StorageUnavailableError(OrderIntegrityError):
    """Raised when SQLite cannot safely complete an operation."""


class CsvStructureError(OrderIntegrityError):
    """Raised when a CSV file does not match the supported contract."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("CSV structure is invalid.")
