import argparse

from backup_service import (
    create_database_backup,
    list_database_backups,
    restore_database_backup,
)


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Create, inspect, and restore Order Integrity Checker backups."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("backup", help="Create a timestamped database backup.")
    subparsers.add_parser("list", help="List available database backups.")

    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore one validated database backup.",
    )
    restore_parser.add_argument("backup_path", help="Path of the backup to restore.")

    return parser


def _create_backup_cli():
    try:
        backup_path = create_database_backup()
    except (FileNotFoundError, ValueError) as error:
        print(f"Backup failed: {error}")
        return 1

    print("Database backup created successfully.")
    print(f"Backup file: {backup_path}")
    return 0


def _list_backups_cli():
    backups = list_database_backups()

    if not backups:
        print("No database backups are available.")
        return 0

    print("AVAILABLE DATABASE BACKUPS")
    print("--------------------------")

    for index, backup in enumerate(backups, start=1):
        print(
            f"{index}. {backup['name']} "
            f"({backup['size_bytes']} bytes) - {backup['path']}"
        )

    return 0


def _restore_backup_cli(backup_path):
    print("WARNING: restoring a backup replaces the current local database.")
    confirmation = input("Type RESTORE to continue: ").strip()

    result = restore_database_backup(
        backup_path,
        confirmed=confirmation == "RESTORE",
    )
    print(result["message"])
    return 0 if result["success"] or result["cancelled"] else 1


def main(argv=None):
    """Runs the recovery command-line interface."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)

    if arguments.command == "backup":
        return _create_backup_cli()

    if arguments.command == "list":
        return _list_backups_cli()

    return _restore_backup_cli(arguments.backup_path)


if __name__ == "__main__":
    raise SystemExit(main())
