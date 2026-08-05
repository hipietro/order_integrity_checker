from database import create_database, insert_sample_orders
from services import list_customers, search_customers


def print_customers(customers):
    """Prints customers in a compact, readable format."""

    if len(customers) == 0:
        print("No customers found.")
        return

    for customer in customers:
        print(
            f"ID: {customer['id']} | "
            f"Name: {customer['name']}"
        )


def main():
    """Runs the customer listing and search interface."""

    create_database()
    insert_sample_orders()

    print("CUSTOMER BROWSER")
    print("----------------")
    print("Leave the search field empty to show every customer.")

    search_text = input("Customer name contains: ")
    customers = search_customers(search_text)

    print("\nCUSTOMERS")
    print("---------")
    print_customers(customers)
    print(f"\nCustomers found: {len(customers)}")


if __name__ == "__main__":
    main()
