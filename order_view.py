import tkinter as tk
from tkinter import messagebox, ttk

from services import get_database_orders, get_order_detail
from ui_config import CONTROL_PADDING, OUTER_PADDING


class OrderDetailWindow:
    """Responsive window that displays all information for one order."""

    def __init__(self, parent, order_code, status_callback=None):
        self.status_callback = status_callback
        self.detail = get_order_detail(order_code)

        if not self.detail["success"]:
            messagebox.showwarning(
                "Order details",
                self.detail["message"],
                parent=parent,
            )
            if self.status_callback is not None:
                self.status_callback(self.detail["message"])
            self.window = None
            return

        self.window = tk.Toplevel(parent)
        self.window.title(f"Order {self.detail['order_code']}")
        self.window.geometry("820x700")
        self.window.minsize(680, 540)

        self.create_widgets()

        if self.status_callback is not None:
            self.status_callback(self.detail["message"])

    def create_widgets(self):
        """Creates order, customer, integrity insight and history sections."""

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.window, padding=OUTER_PADDING)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        order = self.detail["order"]
        customer = self.detail["customer"]

        ttk.Label(
            main_frame,
            text=f"Order {order['order_code']}",
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, OUTER_PADDING))

        summary_frame = ttk.Frame(main_frame)
        summary_frame.grid(row=1, column=0, sticky="ew")
        summary_frame.columnconfigure(0, weight=1, uniform="summary")
        summary_frame.columnconfigure(1, weight=1, uniform="summary")

        order_frame = ttk.LabelFrame(
            summary_frame,
            text="Order",
            padding=CONTROL_PADDING,
        )
        order_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, CONTROL_PADDING),
        )

        self.add_detail_row(order_frame, 0, "Database ID", order["id"])
        self.add_detail_row(order_frame, 1, "Order code", order["order_code"])
        self.add_detail_row(order_frame, 2, "Quantity", order["quantity"])
        self.add_detail_row(order_frame, 3, "Current status", order["status"])

        customer_frame = ttk.LabelFrame(
            summary_frame,
            text="Customer",
            padding=CONTROL_PADDING,
        )
        customer_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(CONTROL_PADDING, 0),
        )

        self.add_detail_row(customer_frame, 0, "Customer ID", customer["id"])
        self.add_detail_row(customer_frame, 1, "Name", customer["name"])

        insights_frame = ttk.LabelFrame(
            main_frame,
            text="Integrity insights",
            padding=CONTROL_PADDING,
        )
        insights_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(OUTER_PADDING, CONTROL_PADDING),
        )
        insights_frame.columnconfigure(0, weight=1)

        quality = self.detail["insights"].get("quality")
        if quality is not None:
            ttk.Label(
                insights_frame,
                text=(
                    f"Quality score: {quality['score']}/100 "
                    f"({quality['rating']} confidence)"
                ),
                font=("Arial", 11, "bold"),
            ).grid(row=0, column=0, sticky="w")
            ttk.Label(
                insights_frame,
                text="\n".join(
                    f"- {explanation}"
                    for explanation in quality["explanations"]
                ),
                wraplength=740,
                justify="left",
            ).grid(
                row=1,
                column=0,
                sticky="w",
                pady=(CONTROL_PADDING, CONTROL_PADDING),
            )

        duplicate_review = self.detail["insights"].get(
            "suspicious_duplicate",
            {"review_required": False, "matches": []},
        )
        matches = duplicate_review["matches"]

        if not duplicate_review["review_required"]:
            ttk.Label(
                insights_frame,
                text=(
                    "No suspicious duplicate signals detected. "
                    "Manual duplicate review is not required."
                ),
                wraplength=740,
            ).grid(row=2, column=0, sticky="w")
        else:
            ttk.Label(
                insights_frame,
                text=(
                    f"Manual review recommended: {len(matches)} possible "
                    "duplicate match(es) detected. The order is not rejected "
                    "automatically."
                ),
                wraplength=740,
            ).grid(
                row=2,
                column=0,
                sticky="w",
                pady=(0, CONTROL_PADDING),
            )

            columns = ("code", "customer", "quantity", "status", "reasons")
            duplicate_table = ttk.Treeview(
                insights_frame,
                columns=columns,
                show="headings",
                height=min(max(len(matches), 1), 4),
            )
            duplicate_table.heading("code", text="Possible duplicate")
            duplicate_table.heading("customer", text="Customer")
            duplicate_table.heading("quantity", text="Qty")
            duplicate_table.heading("status", text="Status")
            duplicate_table.heading("reasons", text="Why it is suspicious")
            duplicate_table.column("code", width=130, anchor="center")
            duplicate_table.column("customer", width=170, anchor="w")
            duplicate_table.column("quantity", width=60, anchor="center")
            duplicate_table.column("status", width=90, anchor="center")
            duplicate_table.column("reasons", width=300, anchor="w")
            duplicate_table.grid(row=3, column=0, sticky="ew")

            for match in matches:
                duplicate_table.insert(
                    "",
                    tk.END,
                    values=(
                        match["order_code"],
                        match["customer_name"],
                        match["quantity"],
                        match["status"],
                        " ".join(match["reasons"]),
                    ),
                )

        history_frame = ttk.LabelFrame(
            main_frame,
            text="Status history",
            padding=CONTROL_PADDING,
        )
        history_frame.grid(row=3, column=0, sticky="nsew")
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        columns = ("old_status", "new_status", "changed_at")
        self.history_table = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
        )
        self.history_table.heading("old_status", text="Previous status")
        self.history_table.heading("new_status", text="New status")
        self.history_table.heading("changed_at", text="Changed at")
        self.history_table.column("old_status", width=150, anchor="center")
        self.history_table.column("new_status", width=150, anchor="center")
        self.history_table.column("changed_at", width=240, anchor="center")

        scrollbar = ttk.Scrollbar(
            history_frame,
            orient="vertical",
            command=self.history_table.yview,
        )
        self.history_table.configure(yscrollcommand=scrollbar.set)
        self.history_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        history = self.detail["status_history"]
        for item in history:
            self.history_table.insert(
                "",
                tk.END,
                values=(
                    item["old_status"],
                    item["new_status"],
                    item["changed_at"],
                ),
            )

        if len(history) == 0:
            ttk.Label(
                history_frame,
                text="No status transitions have been recorded yet.",
            ).grid(row=1, column=0, sticky="w", pady=(CONTROL_PADDING, 0))

    @staticmethod
    def add_detail_row(parent, row, label, value):
        """Adds one label/value pair to a detail section."""

        ttk.Label(parent, text=f"{label}:").grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, CONTROL_PADDING),
            pady=2,
        )
        ttk.Label(parent, text=str(value)).grid(
            row=row,
            column=1,
            sticky="w",
            pady=2,
        )


class OrderBrowserWindow:
    """Database order list that can open the unified detail view."""

    def __init__(self, parent, status_callback=None):
        self.parent = parent
        self.status_callback = status_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Database orders")
        self.window.geometry("860x500")
        self.window.minsize(700, 380)

        self.create_widgets()
        self.refresh_orders()

    def create_widgets(self):
        """Creates the order table and detail controls."""

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.window, padding=OUTER_PADDING)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        ttk.Label(
            main_frame,
            text="Database orders",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, OUTER_PADDING))

        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("order_code", "customer", "quantity", "status")
        self.order_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.order_table.heading("order_code", text="Order code")
        self.order_table.heading("customer", text="Customer")
        self.order_table.heading("quantity", text="Quantity")
        self.order_table.heading("status", text="Status")
        self.order_table.column("order_code", width=150, anchor="center")
        self.order_table.column("customer", width=280, anchor="w")
        self.order_table.column("quantity", width=100, anchor="center")
        self.order_table.column("status", width=140, anchor="center")
        self.order_table.bind("<Double-1>", lambda event: self.open_selected())

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.order_table.yview,
        )
        self.order_table.configure(yscrollcommand=scrollbar.set)
        self.order_table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        controls = ttk.Frame(main_frame)
        controls.grid(row=2, column=0, sticky="ew", pady=(CONTROL_PADDING, 0))

        ttk.Button(
            controls,
            text="Refresh",
            command=self.refresh_orders,
        ).pack(side="left")
        ttk.Button(
            controls,
            text="Open details",
            command=self.open_selected,
        ).pack(side="right")

    def refresh_orders(self):
        """Reloads the database order list through the service layer."""

        for item in self.order_table.get_children():
            self.order_table.delete(item)

        orders = get_database_orders()

        for order in orders:
            self.order_table.insert(
                "",
                tk.END,
                iid=order["order_code"],
                values=(
                    order["order_code"],
                    order["customer_name"],
                    order["quantity"],
                    order["status"],
                ),
            )

        message = f"Displayed {len(orders)} database orders"
        if self.status_callback is not None:
            self.status_callback(message)

    def open_selected(self):
        """Opens the detail view for the selected database order."""

        selection = self.order_table.selection()

        if not selection:
            messagebox.showwarning(
                "Order details",
                "Select an order first.",
                parent=self.window,
            )
            return

        order_code = selection[0]
        open_order_detail(
            self.window,
            order_code,
            status_callback=self.status_callback,
        )


def open_order_detail(parent, order_code, status_callback=None):
    """Opens the unified detail window for one order code."""

    return OrderDetailWindow(
        parent,
        order_code,
        status_callback=status_callback,
    )


def open_order_browser(parent, status_callback=None):
    """Opens the database order browser window."""

    return OrderBrowserWindow(parent, status_callback=status_callback)
