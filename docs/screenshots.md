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

Recommended capture procedure:

```bash
python3 gui.py
```

Then:

1. leave the main window at its default geometry;
2. make sure all primary cards, the activity output and status bar are visible;
3. use only sample order data;
4. capture the complete application window;
5. save the result as `docs/images/gui-main-window.png`;
6. verify the image is readable at GitHub README width;
7. embed it in the README with meaningful alternative text.

## Review checklist

Before committing a documentation image, verify that:

- it comes from the current application version;
- no personal, secret or production data is visible;
- labels shown in the image still exist in the source code;
- the image is stored under `docs/images/`;
- Markdown uses a relative repository path;
- the alternative text describes the useful content of the image.

This workflow keeps portfolio visuals reviewable and prevents screenshots from silently drifting away from the actual interface.
