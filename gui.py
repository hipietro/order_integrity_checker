import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from config import VALID_STATUSES
from customer_view import open_customer_browser
from database import create_database, insert_sample_orders
from services import (
    create_order,
    delete_order,
    get_database_orders,
    get_statistics,
    import_csv_orders,
    preview_csv_import,
    search_order,
    update_order_status,
)
from ui_components import create_action_card, create_section
from ui_config import (
    BUTTON_WIDTH,
    CONTROL_PADDING,
    DEFAULT_STATUS,
    ENTRY_WIDTH,
    OUTER_PADDING,
    OUTPUT_HEIGHT,
    WINDOW_GEOMETRY,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_TITLE,
)


class OrderIntegrityCheckerGUI:
    """Graphical interface for the Order Integrity Checker project."""

    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self.status_message = tk.StringVar(value="Ready")
        self.customer_browser = None
        self.create_widgets()

    def create_widgets(self):
        """Creates the responsive application layout."""

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding=OUTER_PADDING)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=2)

        ttk.Label(
            main_frame,
            text=WINDOW_TITLE,
            font=("Arial", 20, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, OUTER_PADDING))

        workspace = ttk.Frame(main_frame)
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.columnconfigure(0, weight=1, uniform="workspace")
        workspace.columnconfigure(1, weight=1, uniform="workspace")
        workspace.rowconfigure(0, weight=1)

        left_column = ttk.Frame(workspace)
        left_column.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, CONTROL_PADDING),
        )
        left_column.columnconfigure(0, weight=1)

        right_column = ttk.Frame(workspace)
        right_column.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(CONTROL_PADDING, 0),
        )
        right_column.columnconfigure(0, weight=1)

        self.create_search_section(left_column)
        self.create_order_creation_section(left_column)
        self.create_status_update_section(right_column)
        self.create_order_deletion_section(right_column)

        self.create_action_tools(main_frame)
        self.create_output_area(main_frame)
        self.create_status_bar(main_frame)

        self.search_entry.focus_set()

    def create_search_section(self, parent):
        """Creates the order search section."""

        search_frame = create_section(parent, "Search order", row=0)

        ttk.Label(search_frame, text="Order code:").grid(
            row=0,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )

        self.search_entry = ttk.Entry(search_frame, width=ENTRY_WIDTH)
        self.search_entry.grid(
            row=0,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )
        self.search_entry.bind(
            "<Return>",
            lambda event: self.search_order_by_code(),
        )

        ttk.Button(
            search_frame,
            text="Search",
            width=BUTTON_WIDTH,
            command=self.search_order_by_code,
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

    def create_order_creation_section(self, parent):
        """Creates the manual order creation section."""

        create_frame = create_section(parent, "Create order", row=1)

        ttk.Label(create_frame, text="Order code:").grid(
            row=0,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )
        self.create_order_code_entry = ttk.Entry(
            create_frame,
            width=ENTRY_WIDTH,
        )
        self.create_order_code_entry.grid(
            row=0,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

        ttk.Label(create_frame, text="Customer name:").grid(
            row=1,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )
        self.create_customer_name_entry = ttk.Entry(
            create_frame,
            width=ENTRY_WIDTH,
        )
        self.create_customer_name_entry.grid(
            row=1,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

        ttk.Label(create_frame, text="Quantity:").grid(
            row=2,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )
        self.create_quantity_entry = ttk.Entry(
            create_frame,
            width=ENTRY_WIDTH,
        )
        self.create_quantity_entry.grid(
            row=2,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

        ttk.Label(create_frame, text="Status:").grid(
            row=3,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )

        self.create_status_value = tk.StringVar(value=DEFAULT_STATUS)
        ttk.Combobox(
            create_frame,
            textvariable=self.create_status_value,
            values=VALID_STATUSES,
            state="readonly",
            width=ENTRY_WIDTH - 2,
        ).grid(
            row=3,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

        ttk.Button(
            create_frame,
            text="Create order",
            width=BUTTON_WIDTH,
            command=self.create_order_from_form,
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

    def create_status_update_section(self, parent):
        """Creates the order status update section."""

        update_frame = create_section(parent, "Update order status", row=0)

        ttk.Label(update_frame, text="Order code:").grid(
            row=0,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )
        self.update_order_code_entry = ttk.Entry(
            update_frame,
            width=ENTRY_WIDTH,
        )
        self.update_order_code_entry.grid(
            row=0,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

        ttk.Label(update_frame, text="New status:").grid(
            row=1,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )

        self.update_status_value = tk.StringVar(value=DEFAULT_STATUS)
        ttk.Combobox(
            update_frame,
            textvariable=self.update_status_value,
            values=VALID_STATUSES,
            state="readonly",
            width=ENTRY_WIDTH - 2,
        ).grid(
            row=1,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

        ttk.Button(
            update_frame,
            text="Update status",
            width=BUTTON_WIDTH,
            command=self.update_order_status_from_form,
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

    def create_order_deletion_section(self, parent):
        """Creates the safe order deletion section."""

        delete_frame = create_section(parent, "Delete order", row=1)

        ttk.Label(delete_frame, text="Order code:").grid(
            row=0,
            column=0,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )
        self.delete_order_code_entry = ttk.Entry(
            delete_frame,
            width=ENTRY_WIDTH,
        )
        self.delete_order_code_entry.grid(
            row=0,
            column=1,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )
        self.delete_order_code_entry.bind(
            "<Return>",
            lambda event: self.delete_order_from_form(),
        )

        ttk.Label(
            delete_frame,
            text="A confirmation preview is shown before permanent deletion.",
            wraplength=320,
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="w",
        )

        ttk.Button(
            delete_frame,
            text="Delete order",
            width=BUTTON_WIDTH,
            command=self.delete_order_from_form,
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            padx=CONTROL_PADDING,
            pady=CONTROL_PADDING,
            sticky="ew",
        )

    def create_action_tools(self, parent):
        """Creates action cards for database, customer and CSV tools."""

        tools_frame = ttk.Frame(parent)
        tools_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(OUTER_PADDING, CONTROL_PADDING),
        )

        for column in range(5):
            tools_frame.columnconfigure(column, weight=1, uniform="tools")

        create_action_card(
            tools_frame,
            title="Database",
            button_text="Show orders",
            command=self.show_database_orders,
            column=0,
        )
        create_action_card(
            tools_frame,
            title="Customers",
            button_text="Browse customers",
            command=self.open_customer_management,
            column=1,
        )
        create_action_card(
            tools_frame,
            title="CSV import",
            button_text="Import orders",
            command=self.import_csv_orders,
            column=2,
        )
        create_action_card(
            tools_frame,
            title="Statistics",
            button_text="Show statistics",
            command=self.show_statistics,
            column=3,
        )
        create_action_card(
            tools_frame,
            title="Output",
            button_text="Clear output",
            command=self.clear_output,
            column=4,
        )

    def create_output_area(self, parent):
        """Creates a labelled, scrollable area for operation results."""

        output_frame = ttk.LabelFrame(
            parent,
            text="Activity output",
            padding=CONTROL_PADDING,
        )
        output_frame.grid(row=3, column=0, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=OUTPUT_HEIGHT,
            wrap=tk.WORD,
            font=("Courier", 11),
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

    def create_status_bar(self, parent):
        """Creates the status bar displayed below the output area."""

        ttk.Separator(parent, orient="horizontal").grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(CONTROL_PADDING, 0),
        )
        ttk.Label(
            parent,
            textvariable=self.status_message,
            anchor="w",
        ).grid(
            row=5,
            column=0,
            sticky="ew",
            pady=(CONTROL_PADDING, 0),
        )

    def set_status(self, message):
        """Updates the status bar message."""

        self.status_message.set(message)

    def clear_output(self):
        """Clears the output area."""

        self.output_text.delete("1.0", tk.END)
        self.set_status("Output cleared")

    def write_output(self, text):
        """Writes text inside the output area."""

        self.output_text.insert(tk.END, text)
        self.output_text.insert(tk.END, "\n")
        self.output_text.see(tk.END)

    def clear_create_order_form(self):
        """Clears the create order form fields."""

        self.create_order_code_entry.delete(0, tk.END)
        self.create_customer_name_entry.delete(0, tk.END)
        self.create_quantity_entry.delete(0, tk.END)
        self.create_status_value.set(DEFAULT_STATUS)

    def create_order_from_form(self):
        """Creates a new order using the existing service layer."""

        order = {
            "order_code": self.create_order_code_entry.get(),
            "customer_name": self.create_customer_name_entry.get(),
            "quantity": self.create_quantity_entry.get(),
            "status": self.create_status_value.get(),
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
            self.set_status(f"Created order {created_order['order_code']}")
            messagebox.showinfo("Create order", "Order created successfully.")
            return

        self.write_output("Order could not be created.")
        self.write_output("")
        self.write_output("Validation errors:")

        for error in result["errors"]:
            self.write_output(f"- {error}")

        self.set_status("Order creation failed validation")
        messagebox.showwarning(
            "Create order",
            "Order could not be created. Check the validation errors.",
        )

    def update_order_status_from_form(self):
        """Updates an order status using the existing service layer."""

        order_code = self.update_order_code_entry.get()
        new_status = self.update_status_value.get()
        self.clear_output()

        if order_code.strip() == "":
            self.set_status("Status update requires an order code")
            messagebox.showwarning(
                "Update order status",
                "Please enter an order code.",
            )
            return

        result = update_order_status(order_code, new_status)

        self.write_output("UPDATE STATUS RESULT")
        self.write_output("--------------------")
        self.write_output(result["message"])
        self.set_status(result["message"])

        if result["success"]:
            self.update_order_code_entry.delete(0, tk.END)
            self.update_status_value.set(DEFAULT_STATUS)
            messagebox.showinfo("Update order status", result["message"])
        else:
            messagebox.showwarning("Update order status", result["message"])

    def delete_order_from_form(self):
        """Deletes an order after displaying a confirmation preview."""

        order_code = self.delete_order_code_entry.get()
        self.clear_output()
        self.write_output("DELETE ORDER RESULT")
        self.write_output("-------------------")

        if order_code.strip() == "":
            self.write_output("No order code was provided.")
            self.set_status("Deletion requires an order code")
            messagebox.showwarning("Delete order", "Please enter an order code.")
            return

        order = search_order(order_code)

        if order is None:
            self.write_output("No order found with the provided code.")
            self.set_status("Order not found")
            messagebox.showwarning(
                "Delete order",
                "No order found with the provided code.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm order deletion",
            f"Delete order {order['order_code']}?\n\n"
            f"Customer: {order['customer_name']}\n"
            f"Quantity: {order['quantity']}\n"
            f"Status: {order['status']}\n\n"
            "This action cannot be undone.",
        )

        if not confirmed:
            message = f"Deletion of order {order['order_code']} cancelled."
            self.write_output(message)
            self.set_status(message)
            return

        result = delete_order(order["order_code"])
        self.write_output(result["message"])
        self.set_status(result["message"])

        if result["success"]:
            self.delete_order_code_entry.delete(0, tk.END)
            self.delete_order_code_entry.focus_set()
            messagebox.showinfo("Delete order", result["message"])
        else:
            messagebox.showwarning("Delete order", result["message"])

    def show_database_orders(self):
        """Shows all orders stored in the database."""

        self.clear_output()
        orders = get_database_orders()

        self.write_output("DATABASE ORDERS")
        self.write_output("---------------")

        if len(orders) == 0:
            self.write_output("No orders found in the database.")
            self.set_status("Database contains no orders")
            return

        for order in orders:
            self.write_output(
                f"ID: {order['id']} | "
                f"Code: {order['order_code']} | "
                f"Customer: {order['customer_name']} | "
                f"Quantity: {order['quantity']} | "
                f"Status: {order['status']}"
            )

        self.set_status(f"Displayed {len(orders)} database orders")

    def open_customer_management(self):
        """Opens or focuses the reusable customer management window."""

        if (
            self.customer_browser is not None
            and self.customer_browser.window.winfo_exists()
        ):
            self.customer_browser.window.lift()
            self.customer_browser.window.focus_force()
            return

        self.customer_browser = open_customer_browser(
            self.root,
            status_callback=self.set_status,
        )

    def import_csv_orders(self):
        """Imports valid CSV orders using the existing service layer."""

        self.clear_output()
        preview = preview_csv_import()

        valid_orders = preview["valid_orders"]
        invalid_orders = preview["invalid_orders"]

        self.write_output("IMPORT CHECK")
        self.write_output("------------")
        self.write_output(f"Valid orders ready to import: {valid_orders}")
        self.write_output(f"Invalid orders found: {invalid_orders}")

        if valid_orders == 0 and invalid_orders == 0:
            self.set_status("CSV file contains no orders")
            messagebox.showinfo(
                "Import CSV orders",
                "No orders found in the CSV file.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm import",
            "Valid orders will be imported into the database.\n"
            "Invalid orders will be skipped and reported.\n"
            "The CSV file will be cleared after import.\n\n"
            "Do you want to continue?",
        )

        if not confirmed:
            self.write_output("\nImport cancelled.")
            self.set_status("CSV import cancelled")
            return

        result = import_csv_orders(preview, confirmed=True)

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

        saved_count = len(result["saved_orders"])
        skipped_count = len(result["skipped_orders"])

        self.write_output("\nSUMMARY")
        self.write_output("-------")
        self.write_output(f"Saved orders: {saved_count}")
        self.write_output(f"Invalid orders: {skipped_count}")
        self.write_output("CSV file cleared after import.")

        self.set_status(
            f"CSV import completed: {saved_count} saved, "
            f"{skipped_count} invalid"
        )
        messagebox.showinfo(
            "Import completed",
            "CSV import completed successfully.",
        )

    def search_order_by_code(self):
        """Searches a database order by order code."""

        order_code = self.search_entry.get()
        self.clear_output()

        if order_code.strip() == "":
            self.set_status("Search requires an order code")
            messagebox.showwarning("Search order", "Please enter an order code.")
            return

        order = search_order(order_code)

        self.write_output("SEARCH RESULT")
        self.write_output("-------------")

        if order is None:
            self.write_output("No order found with the provided code.")
            self.set_status("Order not found")
            return

        self.write_output(f"ID: {order['id']}")
        self.write_output(f"Code: {order['order_code']}")
        self.write_output(f"Customer: {order['customer_name']}")
        self.write_output(f"Quantity: {order['quantity']}")
        self.write_output(f"Status: {order['status']}")
        self.write_output("")
        self.write_output(
            "The order code is normalized automatically before searching."
        )
        self.set_status(f"Found order {order['order_code']}")

    def show_statistics(self):
        """Shows database order statistics."""

        self.clear_output()
        statistics = get_statistics()

        self.write_output("ORDER STATISTICS")
        self.write_output("----------------")
        self.write_output(f"Completed orders: {statistics['completed']}")
        self.write_output(f"Pending orders: {statistics['pending']}")
        self.write_output(f"Cancelled orders: {statistics['cancelled']}")
        self.write_output(f"Total orders: {statistics['total']}")

        self.set_status(
            f"Displayed statistics for {statistics['total']} orders"
        )


def main():
    """GUI entry point."""

    create_database()
    insert_sample_orders()

    root = tk.Tk()
    OrderIntegrityCheckerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
