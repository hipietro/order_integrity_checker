from database import create_database
from services import get_order_status_history


def print_status_history(result):
    """Prints a status history service result in a readable format."""

    print("\nORDER STATUS HISTORY")
    print("--------------------")
    print(f"Order code: {result['order_code']}")

    if not result["success"]:
        print(result["message"])
        return

    current_status = result["current_status"]

    if current_status is None:
        print("Current status: order no longer exists")
    else:
        print(f"Current status: {current_status}")

    history = result["history"]

    if len(history) == 0:
        print("No status changes have been recorded yet.")
        return

    print("\nChanges:")

    for position, change in enumerate(history, start=1):
        print(
            f"{position}. {change['old_status']} -> {change['new_status']} "
            f"at {change['changed_at']}"
        )


def main():
    """Runs the interactive status history command-line interface."""

    create_database()

    print("ORDER STATUS HISTORY")
    print("--------------------")

    order_code = input("Enter order code: ")
    result = get_order_status_history(order_code)
    print_status_history(result)


if __name__ == "__main__":
    main()
