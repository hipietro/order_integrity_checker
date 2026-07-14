import tkinter as tk
from tkinter import messagebox

from database import create_database, insert_sample_orders
from services import (
    get_database_orders,
    get_statistics,
    import_csv_orders,
    preview_csv_import
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
        self.root.geometry("900x600")

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
            height=25,
            width=105
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