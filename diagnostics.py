import sqlite3
from pathlib import Path

from config import DATABASE_NAME


REQUIRED_TABLES = frozenset({
    "customers",
    "orders",
    "order_status_history",
})


def check_database_readiness(database_path=DATABASE_NAME):
    """Checks whether the application database is readable and compatible.

    The readiness check is intentionally read-only: it opens SQLite in read-only
    mode, verifies the expected application tables, and runs SQLite's lightweight
    integrity check without creating or changing data.
    """

    path = Path(database_path)

    if not path.is_file():
        return {
            "ready": False,
            "database": path.name,
            "reason": "database file is unavailable",
            "missing_tables": sorted(REQUIRED_TABLES),
        }

    database_uri = f"file:{path.resolve().as_posix()}?mode=ro"

    try:
        connection = sqlite3.connect(database_uri, uri=True)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
        available_tables = {row[0] for row in cursor.fetchall()}
        missing_tables = sorted(REQUIRED_TABLES - available_tables)

        cursor.execute("PRAGMA quick_check")
        quick_check = cursor.fetchone()
        integrity_ok = quick_check is not None and quick_check[0] == "ok"
    except sqlite3.Error as error:
        return {
            "ready": False,
            "database": path.name,
            "reason": f"database check failed: {error}",
            "missing_tables": [],
        }
    finally:
        if "connection" in locals():
            connection.close()

    if missing_tables:
        return {
            "ready": False,
            "database": path.name,
            "reason": "database schema is incomplete",
            "missing_tables": missing_tables,
        }

    if not integrity_ok:
        return {
            "ready": False,
            "database": path.name,
            "reason": "database integrity check failed",
            "missing_tables": [],
        }

    return {
        "ready": True,
        "database": path.name,
        "reason": "database is ready",
        "missing_tables": [],
    }
