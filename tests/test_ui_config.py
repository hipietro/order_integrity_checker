import unittest

import ui_config


class UIConfigTests(unittest.TestCase):
    def test_default_window_is_not_smaller_than_minimum_size(self):
        width, height = (
            int(value) for value in ui_config.WINDOW_GEOMETRY.split("x")
        )

        self.assertGreaterEqual(width, ui_config.WINDOW_MIN_WIDTH)
        self.assertGreaterEqual(height, ui_config.WINDOW_MIN_HEIGHT)

    def test_layout_spacing_values_are_positive(self):
        spacing_values = (
            ui_config.OUTER_PADDING,
            ui_config.SECTION_PADDING,
            ui_config.CONTROL_PADDING,
        )

        for value in spacing_values:
            with self.subTest(value=value):
                self.assertGreater(value, 0)

    def test_control_dimensions_are_positive(self):
        self.assertGreater(ui_config.BUTTON_WIDTH, 0)
        self.assertGreater(ui_config.ENTRY_WIDTH, 0)
        self.assertGreater(ui_config.OUTPUT_HEIGHT, 0)

    def test_default_status_is_supported(self):
        self.assertEqual(ui_config.DEFAULT_STATUS, "pending")


if __name__ == "__main__":
    unittest.main()
