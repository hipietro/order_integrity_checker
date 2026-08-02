from database import create_database, insert_sample_orders
from order_query_service import (
    SORT_DIRECTIONS,
    SORT_FIELDS,
    get_filtered_and_sorted_orders,
)


VALID_STATUS_FILTERS = ("all", "completed", "pending", "cancelled")


def ask_choice(prompt, valid_choices, default):
    """Reads a normalized choice and keeps asking until it is valid."""

    choices_text = ", ".join(valid_choices)

    while True:
        value = input(
            f"{prompt} ({choices_text}) [{default}]: "
        ).strip().lower()

        if value == "":
            return default

        if value in valid_choices:
            return value

        print(f"Invalid choice. Choose one of: {choices_text}.")


def print_order(order):
    """Prints one filtered order in a readable format."""

    print(
        f"ID: {order['id']} | "
        f"Code: {order['order_code']} | "
        f"Customer: {order['customer_name']} | "
        f"Quantity: {order['quantity']} | "
        f"Status: {order['status']}"
    )


def browse_orders_cli():
    """Runs the interactive order filtering and sorting workflow."""

    print("\nFILTER AND SORT DATABASE ORDERS")
    print("-------------------------------")

    status = ask_choice(
        "Status filter",
        VALID_STATUS_FILTERS,
        default="all",
    )
    customer_name = input(
        "Customer name contains [leave empty for all]: "
    ).strip()
    sort_by = ask_choice(
        "Sort by",
        SORT_FIELDS,
        default="order_code",
    )
    direction = ask_choice(
        "Direction",
        SORT_DIRECTIONS,
        default="ascending",
    )

    orders = get_filtered_and_sorted_orders(
        status=status,
        customer_name=customer_name,
        sort_by=sort_by,
        direction=direction,
    )

    print("\nQUERY RESULT")
    print("------------")

    if len(orders) == 0:
        print("No orders match the selected filters.")
        return

    for order in orders:
        print_order(order)

    print(f"\nDisplayed orders: {len(orders)}")


def main():
    """Prepares the database and opens the order browser."""

    create_database()
    insert_sample_orders()
    browse_orders_cli()


if __name__ == "__main__":
    main()
