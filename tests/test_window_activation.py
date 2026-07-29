import unittest

from voice_cursor.window_activation import window_owner_at_point


class FakeQuartz:
    kCGWindowLayer = "layer"
    kCGWindowAlpha = "alpha"
    kCGWindowBounds = "bounds"
    kCGWindowOwnerPID = "pid"
    kCGWindowOwnerName = "owner"


def window(owner, pid, *, x, y, width, height, layer=0):
    return {
        "owner": owner,
        "pid": pid,
        "layer": layer,
        "alpha": 1,
        "bounds": {
            "X": x,
            "Y": y,
            "Width": width,
            "Height": height,
        },
    }


class WindowActivationTests(unittest.TestCase):
    def test_frontmost_application_window_under_point_is_selected(self):
        windows = [
            window("Voice Cursor", 10, x=0, y=0, width=300, height=500),
            window("Finder", 20, x=300, y=0, width=900, height=700),
        ]
        self.assertEqual(
            window_owner_at_point(
                windows,
                700,
                350,
                quartz=FakeQuartz,
            ),
            (20, "Finder"),
        )

    def test_system_ui_does_not_activate_an_application_behind_it(self):
        windows = [
            window("Dock", 30, x=0, y=700, width=1200, height=100, layer=0),
            window("Finder", 20, x=0, y=0, width=1200, height=800),
        ]
        self.assertEqual(
            window_owner_at_point(
                windows,
                600,
                750,
                quartz=FakeQuartz,
            ),
            (None, None),
        )

    def test_point_outside_windows_has_no_activation_target(self):
        windows = [
            window("Finder", 20, x=300, y=0, width=500, height=500),
        ]
        self.assertEqual(
            window_owner_at_point(
                windows,
                50,
                700,
                quartz=FakeQuartz,
            ),
            (None, None),
        )


if __name__ == "__main__":
    unittest.main()
