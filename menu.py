from csv_manager import clear_csv_orders
from database import (
    insert_order_into_database,
    search_order_by_code,
    show_database_orders,
    show_order_statistics,
    update_order_status
)
from validator import show_invalid_orders, validate_all_csv_orders, validate_order


def import_valid_orders():
    """
    Validates all CSV orders and saves only valid orders into the database.
    Invalid orders are not inserted.
    """

    validation_results = validate_all_csv_orders()

    valid_orders = 0
    invalid_orders = 0

    print("\nIMPORT RESULT")
    print("-------------")

    for result in validation_results:
        order = result["order"]
        errors = result["errors"]
        order_code = order["order_code"]

        if len(errors) == 0:
            insert_order_into_database(order)
            valid_orders = valid_orders + 1
            print(f"{order_code}: saved into database")
        else:
            invalid_orders = invalid_orders + 1
            print(f"{order_code}: NOT saved. For reasons: press 2")

    print("\nSUMMARY")
    print("-------")
    print(f"Saved orders: {valid_orders}")
    print(f"Invalid orders: {invalid_orders}")


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