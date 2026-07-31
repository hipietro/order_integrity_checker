# GUI layout organization

The Tkinter interface is organized as a responsive workspace rather than a single vertical list of controls.

## Structure

The main window contains:

1. A header with the application name.
2. A two-column order workspace.
3. A row of independent application tools.
4. A scrollable activity output panel.
5. A status bar for immediate feedback.

### Left workspace column

- Search order
- Create order

### Right workspace column

- Update order status
- Delete order

### Application tools

Each of these actions has its own labelled card:

- Show database orders
- Import CSV orders
- Show statistics
- Clear output

## Design decisions

- `gui.py` remains responsible only for interface behavior.
- Validation, normalization, persistence, CSV processing, and business rules remain in the service layer.
- Shared dimensions and spacing values live in `ui_config.py`.
- Reusable labelled sections and action cards live in `ui_components.py`.
- The window and output area expand when the user resizes the application.
- Status selectors use read-only comboboxes to prevent unsupported values.

## Manual verification checklist

Run:

```bash
python3 gui.py
```

Then verify that:

- search and creation appear in the left column;
- update and deletion appear in the right column;
- database, CSV import, statistics, and output actions are visually separated;
- the activity output has a vertical scrollbar;
- resizing the window expands the workspace and output area;
- the status bar changes after search, creation, update, deletion, import, statistics, and clear actions;
- all existing business operations still behave as before.
