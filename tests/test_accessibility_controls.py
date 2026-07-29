import unittest

from voice_cursor.accessibility_controls import (
    AccessibilityControlLocator,
    InteractiveControl,
)


def control(
    label,
    *,
    x=100,
    y=200,
    role="AXButton",
    app_name="Target App",
):
    return InteractiveControl(
        element=object(),
        label=label,
        role=role,
        app_name=app_name,
        pid=123,
        x=x,
        y=y,
        width=120,
        height=40,
    )


class FakeLocator(AccessibilityControlLocator):
    def __init__(self, controls):
        super().__init__(excluded_pid=999)
        self.controls = controls

    def interactive_controls(self):
        return self.controls


class AccessibilityControlTests(unittest.TestCase):
    def test_exact_button_title_is_selected(self):
        matches = FakeLocator(
            [control("Cancel"), control("Enable")]
        ).find("enable")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].label, "Enable")
        self.assertEqual(matches[0].center, (160, 220))

    def test_target_matching_is_word_sensitive(self):
        locator = FakeLocator(
            [control("Project"), control("Projects", x=400)]
        )
        singular = locator.find("project")
        plural = locator.find("projects")
        self.assertEqual([item.label for item in singular], ["Project"])
        self.assertEqual([item.label for item in plural], ["Projects"])
        self.assertEqual(locator.find("projected"), [])

    def test_differently_named_desktop_icons_are_excluded_from_ocr(self):
        locator = FakeLocator(
            [
                control(
                    "Projects",
                    x=1378,
                    y=585,
                    role="AXImage",
                    app_name="Finder",
                )
            ]
        )
        matches, exclusions = locator.find_with_ocr_exclusions("project")
        self.assertEqual(matches, [])
        self.assertEqual(exclusions, ((1308, 577, 1568, 695),))

    def test_duplicate_button_titles_remain_ambiguous(self):
        matches = FakeLocator(
            [control("Open", x=100), control("Open", x=500)]
        ).find("open")
        self.assertEqual(len(matches), 2)

    def test_visible_window_list_can_explicitly_exclude_one_process(self):
        class FakeQuartz:
            kCGWindowListOptionOnScreenOnly = 1
            kCGWindowListExcludeDesktopElements = 16
            kCGNullWindowID = 0
            kCGWindowOwnerPID = "pid"
            kCGWindowLayer = "layer"
            kCGWindowAlpha = "alpha"
            kCGWindowBounds = "bounds"
            kCGWindowOwnerName = "name"

            @staticmethod
            def CGWindowListCopyWindowInfo(options, window_id):
                return [
                    {
                        "pid": 999,
                        "layer": 0,
                        "alpha": 1,
                        "bounds": {"Width": 780, "Height": 650},
                        "name": "Voice Cursor",
                    },
                    {
                        "pid": 123,
                        "layer": 0,
                        "alpha": 1,
                        "bounds": {"Width": 900, "Height": 700},
                        "name": "Target App",
                    },
                    {
                        "pid": 456,
                        "layer": 25,
                        "alpha": 1,
                        "bounds": {"Width": 900, "Height": 30},
                        "name": "Menu Bar",
                    },
                ]

        locator = AccessibilityControlLocator(excluded_pid=999)
        self.assertEqual(
            locator._visible_application_pids(FakeQuartz),
            [(123, "Target App")],
        )

        locator_without_exclusion = AccessibilityControlLocator()
        self.assertEqual(
            locator_without_exclusion._visible_application_pids(FakeQuartz),
            [(999, "Voice Cursor"), (123, "Target App")],
        )


if __name__ == "__main__":
    unittest.main()
