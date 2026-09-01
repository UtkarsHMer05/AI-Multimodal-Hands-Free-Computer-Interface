import unittest

from voice_cursor.window_visibility import (
    intersection_area,
    subtract_rectangle,
    visible_regions,
)


class WindowVisibilityTests(unittest.TestCase):
    def test_non_overlapping_window_leaves_source_unchanged(self):
        source = (0, 0, 800, 700)
        self.assertEqual(
            subtract_rectangle(source, (900, 100, 1200, 600)),
            [source],
        )

    def test_foreground_window_removes_only_covered_project_area(self):
        source = (0, 0, 800, 700)
        finder = (300, 100, 750, 650)
        regions = visible_regions(source, (finder,))

        self.assertGreater(len(regions), 0)
        self.assertEqual(
            sum((right - left) * (bottom - top) for left, top, right, bottom in regions),
            800 * 700 - 450 * 550,
        )
        self.assertTrue(all(intersection_area(region, finder) == 0 for region in regions))

    def test_fully_covered_project_window_has_no_visible_exclusion(self):
        source = (100, 100, 700, 600)
        self.assertEqual(visible_regions(source, ((0, 0, 900, 800),)), ())


if __name__ == "__main__":
    unittest.main()
