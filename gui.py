import tkinter as tk
from tkinter import messagebox

from config import VALID_STATUSES
from database import create_database, insert_sample_orders
from services import (
    create_order,
    get_database_orders,
    get_statistics,
    import_csv_orders,
    preview_csv_import,
    search_order
)


class OrderIntegrityCheckerGUI:
    """
    First graphical interface for the Order Integrity Checker project.

    The GUI uses the service layer and does not duplicate database,
    CSV or validation logic.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Order Integrity Checker")
        self.root.geometry("1000x700")

        self.create_widgets()

    def create_widgets(self):
        """
        Creates the main GUI widgets.
        """

        title_label = tk.Label(
            self.root,
            text="Order Integrity Checker",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=10)

        search_frame = tk.LabelFrame(
            self.root,
            text="Search order"
        )
        search_frame.pack(pady=10, padx=10, fill="x")

        search_label = tk.Label(
            search_frame,
            text="Order code:"
        )
        search_label.grid(row=0, column=0, padx=5, pady=5)

        self.search_entry = tk.Entry(
            search_frame,
            width=25
        )
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)

        search_button = tk.Button(
            search_frame,
            text="Search",
            width=15,
            command=self.search_order_by_code
        )
        search_button.grid(row=0, column=2, padx=5, pady=5)

        create_frame = tk.LabelFrame(
            self.root,
            text="Create order"
        )
        create_frame.pack(pady=10, padx=10, fill="x")

        order_code_label = tk.Label(
            create_frame,
            text="Order code:"
        )
        order_code_label.grid(row=0, column=0, padx=5, pady=5)

        self.create_order_code_entry = tk.Entry(
            create_frame,
            width=20
        )
        self.create_order_code_entry.grid(row=0, column=1, padx=5, pady=5)

        customer_name_label = tk.Label(
            create_frame,
            text="Customer name:"
        )
        customer_name_label.grid(row=0, column=2, padx=5, pady=5)

        self.create_customer_name_entry = tk.Entry(
            create_frame,
            width=25
        )
        self.create_customer_name_entry.grid(row=0, column=3, padx=5, pady=5)

        quantity_label = tk.Label(
            create_frame,
            text="Quantity:"
        )
        quantity_label.grid(row=1, column=0, padx=5, pady=5)

        self.create_quantity_entry = tk.Entry(
            create_frame,
            width=20
        )
        self.create_quantity_entry.grid(row=1, column=1, padx=5, pady=5)

        status_label = tk.Label(
            create_frame,
            text="Status:"
        )
        status_label.grid(row=1, column=2, padx=5, pady=5)

        self.create_status_value = tk.StringVar(self.root)
        self.create_status_value.set("pending")

        status_menu = tk.OptionMenu(
            create_frame,
            self.create_status_value,
            *VALID_STATUSES
        )
        status_menu.config(width=18)
        status_menu.grid(row=1, column=3, padx=5, pady=5)

        create_button = tk.Button(
            create_frame,
            text="Create order",
            width=20,
            command=self.create_order_from_form
        )
        create_button.grid(row=2, column=0, columnspan=4, padx=5, pady=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        show_orders_button = tk.Button(
            button_frame,
            text="Show database orders",
            width=25,
            command=self.show_database_orders
        )
        show_orders_button.grid(row=0, column=0, padx=5, pady=5)

        import_csv_button = tk.Button(
            button_frame,
            text="Import CSV orders",
            width=25,
            command=self.import_csv_orders
        )
        import_csv_button.grid(row=0, column=1, padx=5, pady=5)

        show_statistics_button = tk.Button(
            button_frame,
            text="Show statistics",
            width=25,
            command=self.show_statistics
        )
        show_statistics_button.grid(row=0, column=2, padx=5, pady=5)

        clear_output_button = tk.Button(
            button_frame,
            text="Clear output",
            width=25,
            command=self.clear_output
        )
        clear_output_button.grid(row=1, column=1, padx=5, pady=5)

        self.output_text = tk.Text(
            self.root,
            height=20,
            width=115
        )
        self.output_text.pack(padx=10, pady=10)

    def clear_output(self):
        """
        Clears the output area.
        """

        self.output_text.delete("1.0", tk.END)

    def write_output(self, text):
        """
        Writes text inside the output area.
        """

        self.output_text.insert(tk.END, text)
        self.output_text.insert(tk.END, "\n")

    def clear_create_order_form(self):
        """
        Clears the create order form fields.
        """

        self.create_order_code_entry.delete(0, tk.END)
        self.create_customer_name_entry.delete(0, tk.END)
        self.create_quantity_entry.delete(0, tk.END)
        self.create_status_value.set("pending")

    def create_order_from_form(self):
        """
        Creates a new order using the existing service layer.
        """

        order = {
            "order_code": self.create_order_code_entry.get(),
            "customer_name": self.create_customer_name_entry.get(),
            "quantity": self.create_quantity_entry.get(),
            "status": self.create_status_value.get()
        }

        result = create_order(order)

        self.clear_output()

        self.write_output("CREATE ORDER RESULT")
        self.write_output("-------------------")

        if result["success"]:
            created_order = result["order"]

            self.write_output("Order created successfully.")
            self.write_output("")
            self.write_output(f"Code: {created_order['order_code']}")
            self.write_output(f"Customer: {created_order['customer_name']}")
            self.write_output(f"Quantity: {created_order['quantity']}")
            self.write_output(f"Status: {created_order['status']}")

            self.clear_create_order_form()

            messagebox.showinfo(
                "Create order",
                "Order created successfully."
            )

            return

        self.write_output("Order could not be created.")
        self.write_output("")
        self.write_output("Validation errors:")

        for error in result["errors"]:
            self.write_output(f"- {error}")

        messagebox.showwarning(
            "Create order",
            "Order could not be created. Check the validation errors."
        )

    def show_database_orders(self):
        """
        Shows all orders stored in the database.
        """

        self.clear_output()

        orders = get_database_orders()

        self.write_output("DATABASE ORDERS")
        self.write_output("---------------")

        if len(orders) == 0:
            self.write_output("No orders found in the database.")
            return

        for order in orders:
            self.write_output(
                f"ID: {order['id']} | "
                f"Code: {order['order_code']} | "
                f"Customer: {order['customer_name']} | "
                f"Quantity: {order['quantity']} | "
                f"Status: {order['status']}"
            )

    def import_csv_orders(self):
        """
        Imports valid CSV orders using the existing service layer.
        """

        self.clear_output()

        preview = preview_csv_import()

        validation_results = preview["validation_results"]
        valid_orders = preview["valid_orders"]
        invalid_orders = preview["invalid_orders"]

        self.write_output("IMPORT CHECK")
        self.write_output("------------")
        self.write_output(f"Valid orders ready to import: {valid_orders}")
        self.write_output(f"Invalid orders found: {invalid_orders}")

        if valid_orders == 0 and invalid_orders == 0:
            messagebox.showinfo(
                "Import CSV orders",
                "No orders found in the CSV file."
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm import",
            "Valid orders will be imported into the database.\n"
            "Invalid orders will be skipped and reported.\n"
            "The CSV file will be cleared after import.\n\n"
            "Do you want to continue?"
        )

        if not confirmed:
            self.write_output("\nImport cancelled.")
            return

        result = import_csv_orders(validation_results)

        self.write_output("\nIMPORT RESULT")
        self.write_output("-------------")

        for order in result["saved_orders"]:
            self.write_output(f"{order['order_code']}: saved into database")

        for skipped_order in result["skipped_orders"]:
            order = skipped_order["order"]
            self.write_output(
                f"{order['order_code']}: NOT saved. "
                "Check the invalid orders report for details."
            )

        self.write_output("\nSUMMARY")
        self.write_output("-------")
        self.write_output(f"Saved orders: {len(result['saved_orders'])}")
        self.write_output(f"Invalid orders: {len(result['skipped_orders'])}")
        self.write_output("CSV file cleared after import.")

        messagebox.showinfo(
            "Import completed",
            "CSV import completed successfully."
        )

    def search_order_by_code(self):
        """
        Searches a database order by order code.
        """

        order_code = self.search_entry.get()

        self.clear_output()

        if order_code.strip() == "":
            messagebox.showwarning(
                "Search order",
                "Please enter an order code."
            )
            return

        order = search_order(order_code)

        self.write_output("SEARCH RESULT")
        self.write_output("-------------")

        if order is None:
            self.write_output("No order found with the provided code.")
            return

        self.write_output(f"ID: {order['id']}")
        self.write_output(f"Code: {order['order_code']}")
        self.write_output(f"Customer: {order['customer_name']}")
        self.write_output(f"Quantity: {order['quantity']}")
        self.write_output(f"Status: {order['status']}")
        self.write_output("")
        self.write_output("The order code is normalized automatically before searching.")

    def show_statistics(self):
        """
        Shows database order statistics.
        """

        self.clear_output()

        statistics = get_statistics()

        self.write_output("ORDER STATISTICS")
        self.write_output("----------------")
        self.write_output(f"Completed orders: {statistics['completed']}")
        self.write_output(f"Pending orders: {statistics['pending']}")
        self.write_output(f"Cancelled orders: {statistics['cancelled']}")
        self.write_output(f"Total orders: {statistics['total']}")


def main():
    """
    GUI entry point.
    """

    create_database()
    insert_sample_orders()

    root = tk.Tk()
    app = OrderIntegrityCheckerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
