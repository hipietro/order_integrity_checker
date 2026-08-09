import tkinter as tk
from tkinter import ttk

from services import get_customer_overview
from ui_config import CONTROL_PADDING, OUTER_PADDING


class CustomerBrowserWindow:
    """Responsive Tkinter window for listing and searching customers."""

    def __init__(self, parent, status_callback=None):
        self.status_callback = status_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Customers")
        self.window.geometry("760x460")
        self.window.minsize(620, 360)

        self.search_value = tk.StringVar()
        self.result_message = tk.StringVar(value="Ready")

        self.create_widgets()
        self.refresh_customers()
        self.search_entry.focus_set()

    def create_widgets(self):
        """Creates the search controls and responsive customer table."""

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.window, padding=OUTER_PADDING)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        ttk.Label(
            main_frame,
            text="Customer management",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, OUTER_PADDING))

        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, sticky="ew")
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Customer name:").grid(
            row=0,
            column=0,
            padx=(0, CONTROL_PADDING),
            sticky="w",
        )

        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_value,
        )
        self.search_entry.grid(
            row=0,
            column=1,
            padx=(0, CONTROL_PADDING),
            sticky="ew",
        )
        self.search_entry.bind(
            "<Return>",
            lambda event: self.refresh_customers(),
        )

        ttk.Button(
            search_frame,
            text="Search",
            command=self.refresh_customers,
        ).grid(
            row=0,
            column=2,
            padx=(0, CONTROL_PADDING),
        )

        ttk.Button(
            search_frame,
            text="Show all",
            command=self.show_all_customers,
        ).grid(row=0, column=3)

        table_frame = ttk.Frame(main_frame)
        table_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            pady=(OUTER_PADDING, CONTROL_PADDING),
        )
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("id", "name", "normalized_name", "orders")
        self.customer_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        self.customer_table.heading("id", text="ID")
        self.customer_table.heading("name", text="Customer")
        self.customer_table.heading("normalized_name", text="Normalized name")
        self.customer_table.heading("orders", text="Orders")

        self.customer_table.column("id", width=70, anchor="center", stretch=False)
        self.customer_table.column("name", width=220, anchor="w")
        self.customer_table.column("normalized_name", width=220, anchor="w")
        self.customer_table.column(
            "orders",
            width=90,
            anchor="center",
            stretch=False,
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.customer_table.yview,
        )
        self.customer_table.configure(yscrollcommand=scrollbar.set)

        self.customer_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        ttk.Label(
            main_frame,
            textvariable=self.result_message,
            anchor="w",
        ).grid(row=3, column=0, sticky="ew")

    def clear_table(self):
        """Removes all currently displayed customer rows."""

        for item in self.customer_table.get_children():
            self.customer_table.delete(item)

    def refresh_customers(self):
        """Loads customers matching the current search text."""

        search_text = self.search_value.get()
        customers = get_customer_overview(search_text)

        self.clear_table()

        for customer in customers:
            self.customer_table.insert(
                "",
                tk.END,
                values=(
                    customer["id"],
                    customer["name"],
                    customer["normalized_name"],
                    customer["order_count"],
                ),
            )

        if search_text.strip():
            message = f"Found {len(customers)} matching customers"
        else:
            message = f"Displayed {len(customers)} customers"

        self.result_message.set(message)

        if self.status_callback is not None:
            self.status_callback(message)

    def show_all_customers(self):
        """Clears the search field and reloads the full customer list."""

        self.search_value.set("")
        self.refresh_customers()
        self.search_entry.focus_set()


def open_customer_browser(parent, status_callback=None):
    """Opens and returns a customer browser window."""

    return CustomerBrowserWindow(parent, status_callback=status_callback)
