# Screenshot workflow

The README uses visual examples to make the project understandable before a reader inspects the source code. Visual documentation must stay faithful to the real application.

## CLI example

The committed `docs/images/cli-validation-example.svg` presents the same labels and structure produced by the CSV preview functions in `menu.py`.

When CLI presentation text changes:

1. run the affected command locally;
2. compare the real terminal output with the SVG;
3. update the SVG text if required;
4. keep the alternative text in the README descriptive rather than decorative.

The SVG is intentionally text-based so reviewers can inspect changes in a normal Git diff.

## GUI screenshot

The GUI image must be captured from a real Tkinter application session. Do not replace it with a hand-drawn mockup.

Install the development dependencies, then run the dedicated capture command from a desktop session:

```bash
python3 -m pip install -r requirements-dev.txt
python3 capture_gui_screenshot.py
```

The command launches the real `OrderIntegrityCheckerGUI`, waits for Tkinter to render the main window, captures the window bounds with Pillow, saves `docs/images/gui-main-window.png`, and exits automatically.

An alternative output path can be used for review without overwriting the canonical README asset:

```bash
python3 capture_gui_screenshot.py --output /tmp/order-integrity-gui.png
```

The capture must run in an interactive desktop session. Headless CI is intentionally not treated as the source of truth for the portfolio screenshot because window-manager rendering differs across platforms.

Before committing the canonical image:

1. leave the main window at its default geometry;
2. make sure all primary cards, the activity output and status bar are visible;
3. use only sample order data;
4. verify the image is readable at GitHub README width;
5. confirm the output is a real capture of the current application;
6. embed it in the README with meaningful alternative text.

## Review checklist

Before committing a documentation image, verify that:

- it comes from the current application version;
- no personal, secret or production data is visible;
- labels shown in the image still exist in the source code;
- the image is stored under `docs/images/`;
- Markdown uses a relative repository path;
- the alternative text describes the useful content of the image.

This workflow keeps portfolio visuals reviewable and prevents screenshots from silently drifting away from the actual interface.
