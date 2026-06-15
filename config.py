# Name of the SQLite database file.
# SQLite stores the whole database inside a single local file.
DATABASE_NAME = "orders.db"

# Name of the CSV file that contains the new orders to validate.
CSV_FILE_NAME = "new_orders.csv"

# List of order statuses accepted by the program.
# Any other status will be considered invalid.
VALID_STATUSES = ["completed", "pending", "cancelled"]