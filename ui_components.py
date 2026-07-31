"""Reusable Tkinter components for the application layout."""

from tkinter import ttk

from ui_config import BUTTON_WIDTH, CONTROL_PADDING, SECTION_PADDING


def create_section(parent, title, row, column=0):
    """Create a responsive labelled section inside a grid container."""

    frame = ttk.LabelFrame(
        parent,
        text=title,
        padding=SECTION_PADDING,
    )
    frame.grid(
        row=row,
        column=column,
        sticky="nsew",
        padx=CONTROL_PADDING,
        pady=CONTROL_PADDING,
    )
    frame.columnconfigure(1, weight=1)
    return frame


def create_action_card(parent, title, button_text, command, column):
    """Create a visually separated card containing one application action."""

    frame = ttk.LabelFrame(
        parent,
        text=title,
        padding=SECTION_PADDING,
    )
    frame.grid(
        row=0,
        column=column,
        sticky="ew",
        padx=CONTROL_PADDING,
    )
    frame.columnconfigure(0, weight=1)

    button = ttk.Button(
        frame,
        text=button_text,
        width=BUTTON_WIDTH,
        command=command,
    )
    button.grid(row=0, column=0, sticky="ew")
    return frame
