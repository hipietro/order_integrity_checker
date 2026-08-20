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

The command launches the real `OrderIntegrityCheckerGUI`, waits for Tkinter to render the main window, captures the window bounds with Pillow, validates that the result is a readable PNG of suitable README dimensions, saves `docs/images/gui-main-window.png`, and exits automatically.

An alternative output path can be used for review without overwriting the canonical README asset:

```bash
python3 capture_gui_screenshot.py --output /tmp/order-integrity-gui.png
```

## CI screenshot smoke test

GitHub Actions also launches the real Tkinter application inside an Xvfb virtual display. The `gui-screenshot-smoke-test` job captures and validates the window, then uploads the result as the `gui-main-window` workflow artifact.

This headless capture is not a mockup: it exercises the same `OrderIntegrityCheckerGUI` and the same Pillow capture code used by the desktop command. Its purpose is to catch broken rendering or capture logic on every push and pull request.

The CI artifact is a reproducible verification image rather than an automatically committed documentation asset. Before replacing the canonical README screenshot, review the resulting image visually so layout regressions are not published simply because the PNG passed structural validation.

Before committing the canonical image:

1. leave the main window at its default geometry;
2. make sure all primary cards, the activity output and status bar are visible;
3. use only sample order data;
4. verify the image is readable at GitHub README width;
5. confirm the output is a real capture of the current application;
6. confirm the automated PNG validation succeeds;
7. embed it in the README with meaningful alternative text.

## Review checklist

Before committing a documentation image, verify that:

- it comes from the current application version;
- no personal, secret or production data is visible;
- labels shown in the image still exist in the source code;
- the image is stored under `docs/images/`;
- Markdown uses a relative repository path;
- the alternative text describes the useful content of the image;
- CI can still produce and validate its own real GUI capture.

This workflow keeps portfolio visuals reviewable and prevents screenshots from silently drifting away from the actual interface.
