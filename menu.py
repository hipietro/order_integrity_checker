from config import REPORT_FILE_NAME
from services import (
    clear_csv_input,
    create_order,
    delete_order,
    export_database_orders,
    get_database_orders,
    get_statistics,
    import_csv_orders,
    preview_csv_import,
    search_order,
    update_order_status
)


def print_order(order):
    """
    Prints a single order in a readable format.
    """

    print(
        f"ID: {order['id']} | "
        f"Code: {order['order_code']} | "
        f"Customer: {order['customer_name']} | "
        f"Quantity: {order['quantity']} | "
        f"Status: {order['status']}"
    )


def show_validation_problems(validation_results):
    """
    Shows invalid orders from already calculated validation results.
    """

    found_invalid_orders = False

    print("\nINVALID CSV ORDERS")
    print("------------------")

    for result in validation_results:
        order = result["order"]
        errors = result["errors"]

        if len(errors) > 0:
            found_invalid_orders = True

            print(f"\nOrder code: {order['order_code']}")
            print(f"Customer name: {order['customer_name']}")
            print(f"Quantity: {order['quantity']}")
            print(f"Status: {order['status']}")
            print("Errors:")

            for error in errors:
                print(f"- {error}")

    if not found_invalid_orders:
        print("No invalid orders found.")


def import_valid_orders_cli():
    """
    Handles the CSV import flow from the command-line interface.
    """

    preview = preview_csv_import()

    validation_results = preview["validation_results"]
    valid_orders = preview["valid_orders"]
    invalid_orders = preview["invalid_orders"]

    print("\nIMPORT CHECK")
    print("------------")
    print(f"Valid orders ready to import: {valid_orders}")
    print(f"Invalid orders found: {invalid_orders}")

    while True:
        choice = input("\nChoose: y = import, n = cancel, w = show problems: ")

        if choice == "w":
            show_validation_problems(validation_results)

        elif choice == "n":
            print("Import cancelled. No orders were saved and the CSV file was not cleared.")
            return

        elif choice == "y":
            result = import_csv_orders(validation_results)

            print("\nIMPORT RESULT")
            print("-------------")

            for order in result["saved_orders"]:
                print(f"{order['order_code']}: saved into database")

            for skipped_order in result["skipped_orders"]:
                order = skipped_order["order"]
                print(f"{order['order_code']}: NOT saved. Check the invalid orders report for details.")

            print("\nSUMMARY")
            print("-------")
            print(f"Saved orders: {len(result['saved_orders'])}")
            print(f"Invalid orders: {len(result['skipped_orders'])}")
            print(f"Invalid orders report generated: {REPORT_FILE_NAME}")
            print("CSV file cleared after import.")

            return

        else:
            print("Invalid option. Please choose y, n, or w.")


def show_invalid_orders_cli():
    """
    Shows invalid CSV orders from the command-line interface.
    """

    preview = preview_csv_import()
    show_validation_problems(preview["validation_results"])


def show_database_orders_cli():
    """
    Shows all database orders from the command-line interface.
    """

    orders = get_database_orders()

    print("\nDATABASE ORDERS")
    print("---------------")

    if len(orders) == 0:
        print("No orders found in the database.")
        return

    for order in orders:
        print_order(order)


def clear_csv_orders_cli():
    """
    Clears the CSV input file from the command-line interface.
    """

    result = clear_csv_input()
    print(result["message"])


def search_order_by_code_cli():
    """
    Searches an order from the command-line interface.
    """

    order_code = input("Enter order code to search: ")

    order = search_order(order_code)

    print("\nSEARCH RESULT")
    print("-------------")

    if order is None:
        print(f"No order found with code {order_code}.")
    else:
        print_order(order)


def insert_order_manually_cli():
    """
    Inserts an order manually from the command-line interface.
    """

    print("\nINSERT NEW ORDER")
    print("----------------")

    order = {
        "order_code": input("Order code: "),
        "customer_name": input("Customer name: "),
        "quantity": input("Quantity: "),
        "status": input("Status (completed, pending, cancelled): ")
    }

    result = create_order(order)

    if result["success"]:
        inserted_order = result["order"]
        print(f"Order {inserted_order['order_code']} inserted successfully.")
    else:
        invalid_order = result["order"]
        print(f"Order {invalid_order['order_code']} is invalid. Errors:")

        for error in result["errors"]:
            print(f"- {error}")


def show_order_statistics_cli():
    """
    Shows order statistics from the command-line interface.
    """

    statistics = get_statistics()

    print("\nORDER STATISTICS")
    print("----------------")
    print(f"Completed orders: {statistics['completed']}")
    print(f"Pending orders: {statistics['pending']}")
    print(f"Cancelled orders: {statistics['cancelled']}")
    print(f"Total orders: {statistics['total']}")


def update_order_status_cli():
    """
    Updates an order status from the command-line interface.
    """

    order_code = input("Enter order code to update: ")

    order = search_order(order_code)

    if order is None:
        print(f"No order found with code {order_code}.")
        return

    print("\nORDER FOUND")
    print("-----------")
    print_order(order)

    new_status = input("Enter new status (completed, pending, cancelled): ")

    result = update_order_status(order_code, new_status)

    print(result["message"])


def delete_order_by_code_cli():
    """
    Deletes an order from the command-line interface.
    """

    order_code = input("Enter order code to delete: ")

    order = search_order(order_code)

    if order is None:
        print(f"No order found with code {order_code}.")
        return

    print("\nORDER FOUND")
    print("-----------")
    print_order(order)

    confirmation = input("Are you sure you want to delete this order? y/n: ")

    if confirmation != "y":
        print("Delete cancelled.")
        return

    result = delete_order(order_code)

    print(result["message"])

def export_database_orders_cli():
    """
    Exports database orders from the command-line interface.
    """

    result = export_database_orders()

    print("\nEXPORT RESULT")
    print("-------------")
    print(f"Exported orders: {result['exported_orders']}")
    print(f"Output file: {result['file_name']}")


def show_menu():
    """
    Shows the main menu and handles the user's choices.
    """

    while True:
        print("\nORDER INTEGRITY CHECKER")
        print("-----------------------")
        print("1. Import valid CSV orders into database")
        print("2. Show invalid CSV orders")
        print("3. Show database orders")
        print("4. Clear new_orders.csv file")
        print("5. Search order by code")
        print("6. Insert order manually")
        print("7. Show order statistics")
        print("8. Update order status")
        print("9. Delete order by code")
        print("10. Export database orders to CSV")
        print("11. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            import_valid_orders_cli()
        elif choice == "2":
            show_invalid_orders_cli()
        elif choice == "3":
            show_database_orders_cli()
        elif choice == "4":
            clear_csv_orders_cli()
        elif choice == "5":
            search_order_by_code_cli()
        elif choice == "6":
            insert_order_manually_cli()
        elif choice == "7":
            show_order_statistics_cli()
        elif choice == "8":
            update_order_status_cli()
        elif choice == "9":
            delete_order_by_code_cli()
        elif choice == "10":
            export_database_orders_cli()
        elif choice == "11":   
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 11.")