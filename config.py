# Name of the SQLite database file.
# SQLite stores the whole database inside a single local file.
DATABASE_NAME = "orders.db"

# Maximum time a write waits for a locked SQLite database.
SQLITE_BUSY_TIMEOUT_SECONDS = 2.0

# Directory and filename prefix used for local database recovery points.
BACKUP_DIRECTORY = "backups"
BACKUP_FILE_PREFIX = "orders_backup"

# Name of the CSV file that contains the new orders to validate.
CSV_FILE_NAME = "new_orders.csv"

# List of order statuses accepted by the program.
# Any other status will be considered invalid.
VALID_STATUSES = ["completed", "pending", "cancelled"]

# Name of the text file where the report of invalid orders will be saved.
REPORT_FILE_NAME = "invalid_orders_report.txt"

# Name of the CSV file generated when exporting database orders.
EXPORT_FILE_NAME = "exported_orders.csv"
