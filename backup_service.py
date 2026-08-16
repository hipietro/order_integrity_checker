import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from config import BACKUP_DIRECTORY, BACKUP_FILE_PREFIX, DATABASE_NAME


_REQUIRED_SCHEMA = {
    "customers": {"id", "name", "normalized_name"},
    "orders": {"id", "order_code", "customer_id", "quantity", "status"},
    "order_status_history": {
        "id",
        "order_code",
        "old_status",
        "new_status",
        "changed_at",
    },
}


def validate_database_file(database_path):
    """Checks SQLite integrity and the minimum schema required by the app."""

    path = Path(database_path)

    if not path.is_file():
        return False, "Database file does not exist."

    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cursor = connection.cursor()

        integrity_result = cursor.execute("PRAGMA integrity_check").fetchone()
        if integrity_result is None or integrity_result[0] != "ok":
            return False, "SQLite integrity check failed."

        for table_name, required_columns in _REQUIRED_SCHEMA.items():
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {row[1] for row in cursor.fetchall()}

            if not required_columns.issubset(columns):
                return False, f"Backup is missing the required {table_name} schema."
    except sqlite3.DatabaseError:
        return False, "File is not a valid SQLite database."
    finally:
        if "connection" in locals():
            connection.close()

    return True, "Database is valid and compatible."


def create_database_backup(
    database_path=DATABASE_NAME,
    backup_directory=BACKUP_DIRECTORY,
    current_time=None,
):
    """Creates a timestamped, transaction-consistent SQLite backup."""

    source_path = Path(database_path)
    backup_dir = Path(backup_directory)

    if not source_path.is_file():
        raise FileNotFoundError(f"Database file not found: {source_path}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = current_time or datetime.now(timezone.utc)
    filename = f"{BACKUP_FILE_PREFIX}_{timestamp:%Y%m%d_%H%M%S}.db"
    backup_path = backup_dir / filename

    source = sqlite3.connect(source_path)
    destination = sqlite3.connect(backup_path)

    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    valid, message = validate_database_file(backup_path)
    if not valid:
        backup_path.unlink(missing_ok=True)
        raise ValueError(f"Created backup failed validation: {message}")

    return backup_path


def list_database_backups(backup_directory=BACKUP_DIRECTORY):
    """Returns available application backups from newest to oldest."""

    backup_dir = Path(backup_directory)
    if not backup_dir.is_dir():
        return []

    backups = []
    pattern = f"{BACKUP_FILE_PREFIX}_*.db"

    for backup_path in backup_dir.glob(pattern):
        if backup_path.is_file():
            backups.append({
                "path": str(backup_path),
                "name": backup_path.name,
                "size_bytes": backup_path.stat().st_size,
                "modified_at": backup_path.stat().st_mtime,
            })

    return sorted(backups, key=lambda item: item["modified_at"], reverse=True)


def restore_database_backup(
    backup_path,
    confirmed=False,
    database_path=DATABASE_NAME,
):
    """Restores a validated backup atomically after explicit confirmation."""

    if not confirmed:
        return {
            "success": False,
            "cancelled": True,
            "message": "Database restore cancelled. No data was modified.",
        }

    source_path = Path(backup_path)
    target_path = Path(database_path)
    valid, validation_message = validate_database_file(source_path)

    if not valid:
        return {
            "success": False,
            "cancelled": False,
            "message": f"Restore refused: {validation_message}",
        }

    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with NamedTemporaryFile(
            prefix="order_integrity_restore_",
            suffix=".db",
            dir=target_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        source = sqlite3.connect(source_path)
        destination = sqlite3.connect(temporary_path)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        copied_valid, copied_message = validate_database_file(temporary_path)
        if not copied_valid:
            return {
                "success": False,
                "cancelled": False,
                "message": f"Restore refused: {copied_message}",
            }

        os.replace(temporary_path, target_path)
        temporary_path = None
    except (OSError, sqlite3.DatabaseError) as error:
        return {
            "success": False,
            "cancelled": False,
            "message": f"Database restore failed: {error}",
        }
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return {
        "success": True,
        "cancelled": False,
        "message": f"Database restored from {source_path.name}.",
    }
