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
    update_order_status,
)


def normalize_cli_choice(choice):
    """Normalizes a CLI choice by trimming spaces and using lowercase."""

    return choice.strip().lower()


def ask_confirmation(message):
    """Asks the user for a case-insensitive y/n confirmation."""

    while True:
        choice = normalize_cli_choice(input(f"{message} y/n: "))

        if choice == "y":
            return True

        if choice == "n":
            return False

        if choice == "":
            print("Confirmation cannot be empty. Please choose y or n.")
        else:
            print("Invalid confirmation. Please choose y or n.")


def read_menu_choice():
    """Reads and normalizes the main menu choice."""

    choice = input("\nChoose an option: ").strip()

    if choice == "":
        print("Menu choice cannot be empty.")
        return ""

    return choice


def print_order(order):
    """Prints a single order in a readable format."""

    print(
        f"ID: {order['id']} | "
        f"Code: {order['order_code']} | "
        f"Customer: {order['customer_name']} | "
        f"Quantity: {order['quantity']} | "
        f"Status: {order['status']}"
    )


def show_validation_problems(validation_results):
    """Shows invalid orders from already calculated validation results."""

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
            print("Reasons for skipping:")

            for error in errors:
                print(f"- {error}")

    if not found_invalid_orders:
        print("No invalid orders found.")


def show_order_quality_scores(preview):
    """Shows the explainable quality score attached to each CSV order."""

    if preview["average_quality_score"] is None:
        return

    print("\nORDER QUALITY")
    print("-------------")
    print(f"Average quality score: {preview['average_quality_score']}/100")
    print(
        "Orders recommended for review: "
        f"{preview['review_recommended_orders']}"
    )

    for result in preview["validation_results"]:
        order = result["order"]
        quality = result.get("quality")

        if quality is None:
            continue

        print(
            f"\n{order['order_code'] or '[missing code]'}: "
            f"{quality['score']}/100 ({quality['rating']})"
        )
        for explanation in quality["explanations"]:
            print(f"- {explanation}")


def show_csv_import_preview(preview):
    """Shows counts, quality scores, error totals and skipped-order reasons."""

    print("\nCSV IMPORT PREVIEW")
    print("------------------")
    print(f"Total CSV orders: {preview['total_orders']}")
    print(f"Orders to import: {preview['valid_orders']}")
    print(f"Orders to skip: {preview['invalid_orders']}")

    show_order_quality_scores(preview)

    if len(preview["error_summary"]) > 0:
        print("\nVALIDATION REASON SUMMARY")
        print("-------------------------")

        for item in preview["error_summary"]:
            print(f"- {item['reason']}: {item['count']}")

        show_validation_problems(preview["validation_results"])


def import_valid_orders_cli():
    """Handles the safe CSV preview and confirmed import flow."""

    preview = preview_csv_import()
    show_csv_import_preview(preview)

    if preview["total_orders"] == 0:
        print("No orders found. The database and CSV file were not modified.")
        return

    confirmed = ask_confirmation(
        "Import the valid orders and clear the CSV after completion?"
    )
    result = import_csv_orders(preview, confirmed=confirmed)

    if result["cancelled"]:
        print(result["message"])
        return

    if not result["success"]:
        print(result["message"])
        print("The CSV file was preserved.")
        return

    print("\nIMPORT RESULT")
    print("-------------")

    for order in result["saved_orders"]:
        print(f"{order['order_code']}: saved into database")

    for skipped_order in result["skipped_orders"]:
        order = skipped_order["order"]
        reasons = "; ".join(skipped_order["errors"])
        print(f"{order['order_code']}: skipped — {reasons}")

    print("\nSUMMARY")
    print("-------")
    print(f"Saved orders: {len(result['saved_orders'])}")
    print(f"Invalid orders: {len(result['skipped_orders'])}")
    print(f"Invalid orders report generated: {REPORT_FILE_NAME}")
    print("CSV file cleared after successful import.")


def show_invalid_orders_cli():
    """Shows invalid CSV orders from the command-line interface."""

    preview = preview_csv_import()
    show_validation_problems(preview["validation_results"])


def show_database_orders_cli():
    """Shows all database orders from the command-line interface."""

    orders = get_database_orders()

    print("\nDATABASE ORDERS")
    print("---------------")

    if len(orders) == 0:
        print("No orders found in the database.")
        return

    for order in orders:
        print_order(order)


def clear_csv_orders_cli():
    """Clears the CSV input file from the command-line interface."""

    confirmed = ask_confirmation(
        "Are you sure you want to clear new_orders.csv? This action cannot be undone."
    )

    if not confirmed:
        print("Clear CSV cancelled.")
        return

    result = clear_csv_input()
    print(result["message"])


def search_order_by_code_cli():
    """Searches an order from the command-line interface."""

    order_code = input("Enter order code to search: ")
    order = search_order(order_code)

    print("\nSEARCH RESULT")
    print("-------------")

    if order is None:
        print(f"No order found with code {order_code}.")
    else:
        print_order(order)


def insert_order_manually_cli():
    """Inserts an order manually from the command-line interface."""

    print("\nINSERT NEW ORDER")
    print("----------------")

    order = {
        "order_code": input("Order code: "),
        "customer_name": input("Customer name: "),
        "quantity": input("Quantity: "),
        "status": input("Status (completed, pending, cancelled): "),
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
    """Shows order statistics from the command-line interface."""

    statistics = get_statistics()

    print("\nORDER STATISTICS")
    print("----------------")
    print(f"Completed orders: {statistics['completed']}")
    print(f"Pending orders: {statistics['pending']}")
    print(f"Cancelled orders: {statistics['cancelled']}")
    print(f"Total orders: {statistics['total']}")


def update_order_status_cli():
    """Updates an order status from the command-line interface."""

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
    """Deletes an order from the command-line interface."""

    order_code = input("Enter order code to delete: ")
    order = search_order(order_code)

    if order is None:
        print(f"No order found with code {order_code}.")
        return

    print("\nORDER FOUND")
    print("-----------")
    print_order(order)

    confirmed = ask_confirmation("Are you sure you want to delete this order?")

    if not confirmed:
        print("Delete cancelled.")
        return

    result = delete_order(order_code)
    print(result["message"])


def export_database_orders_cli():
    """Exports database orders from the command-line interface."""

    result = export_database_orders()

    print("\nEXPORT RESULT")
    print("-------------")
    print(f"Exported orders: {result['exported_orders']}")
    print(f"Output file: {result['file_name']}")


def show_menu():
    """Shows the main menu and handles the user's choices."""

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

        choice = read_menu_choice()

        if choice == "":
            continue

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
