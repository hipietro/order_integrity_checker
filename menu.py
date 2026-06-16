from csv_manager import clear_csv_orders
from database import (
    insert_order_into_database,
    search_order_by_code,
    show_database_orders,
    show_order_statistics,
    update_order_status
)
from validator import (
    generate_invalid_orders_report,
    show_invalid_orders,
    validate_all_csv_orders,
    validate_order
)

def show_validation_problems(validation_results):
    """
    Shows invalid orders from already calculated validation results.

    This function is used during the import confirmation flow, so the user can
    inspect validation problems before deciding whether to continue or cancel.
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

def import_valid_orders():
    """
    Validates all CSV orders, asks for confirmation, saves only valid orders into
    the database, generates a report for invalid orders, and clears the CSV file
    after the import is completed.
    """

    validation_results = validate_all_csv_orders()

    valid_orders = 0
    invalid_orders = 0

    for result in validation_results:
        if len(result["errors"]) == 0:
            valid_orders = valid_orders + 1
        else:
            invalid_orders = invalid_orders + 1

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
            saved_orders = 0

            print("\nIMPORT RESULT")
            print("-------------")

            for result in validation_results:
                order = result["order"]
                errors = result["errors"]
                order_code = order["order_code"]

                if len(errors) == 0:
                    insert_order_into_database(order)
                    saved_orders = saved_orders + 1
                    print(f"{order_code}: saved into database")
                else:
                    print(f"{order_code}: NOT saved. Check the invalid orders report for details.")

            generate_invalid_orders_report(validation_results)
            clear_csv_orders()

            print("\nSUMMARY")
            print("-------")
            print(f"Saved orders: {saved_orders}")
            print(f"Invalid orders: {invalid_orders}")
            print("Invalid orders report generated: invalid_orders_report.txt")
            print("CSV file cleared after import.")

            return

        else:
            print("Invalid option. Please choose y, n, or w.")

def insert_order_manually():
    """
    Allows the user to insert a new order manually through the command line.

    The function prompts the user for each field of the order, validates the input,
    and if the order is valid, it is saved into the database.
    """

    print("\nINSERT NEW ORDER")
    print("----------------")

    order_code = input("Order code: ")
    customer_name = input("Customer name: ")
    quantity = input("Quantity: ")
    status = input("Status (completed, pending, cancelled): ")

    order = {
        "order_code": order_code,
        "customer_name": customer_name,
        "quantity": quantity,
        "status": status
    }

    errors = validate_order(order, [])

    if len(errors) == 0:
        insert_order_into_database(order)
        print(f"Order {order_code} inserted successfully.")
    else:
        print(f"Order {order_code} is invalid. Errors:")
        for error in errors:
            print(f"- {error}")


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
        print("9. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":
            import_valid_orders()
        elif choice == "2":
            show_invalid_orders()
        elif choice == "3":
            show_database_orders()
        elif choice == "4":
            clear_csv_orders()
        elif choice == "5":
            search_order_by_code()
        elif choice == "6":
            insert_order_manually()
        elif choice == "7":
            show_order_statistics()
        elif choice == "8":
            update_order_status()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 9.")