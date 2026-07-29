import unittest

from voice_cursor.macos_clicks import post_left_click_sequence


class FakeQuartz:
    kCGEventLeftMouseDown = "down"
    kCGEventLeftMouseUp = "up"
    kCGMouseButtonLeft = "left"
    kCGMouseEventClickState = "click_state"
    kCGHIDEventTap = "hid"

    def __init__(self):
        self.posted = []

    @staticmethod
    def CGEventCreateMouseEvent(_source, event_type, point, button):
        return {
            "type": event_type,
            "point": point,
            "button": button,
        }

    @staticmethod
    def CGEventSetIntegerValueField(event, field, value):
        event[field] = value

    def CGEventPost(self, tap, event):
        self.posted.append((tap, dict(event)))


class MacOSClickTests(unittest.TestCase):
    def test_double_click_uses_native_click_states_at_one_fixed_point(self):
        quartz = FakeQuartz()
        sleeps = []

        post_left_click_sequence(
            640,
            420,
            2,
            quartz=quartz,
            sleep=sleeps.append,
        )

        self.assertEqual(
            [
                (event["type"], event["click_state"])
                for _, event in quartz.posted
            ],
            [("down", 1), ("up", 1), ("down", 2), ("up", 2)],
        )
        self.assertTrue(
            all(event["point"] == (640.0, 420.0) for _, event in quartz.posted)
        )
        self.assertEqual(sleeps, [0.025, 0.10, 0.025])

    def test_triple_click_marks_the_third_click_as_three(self):
        quartz = FakeQuartz()

        post_left_click_sequence(
            100,
            200,
            3,
            quartz=quartz,
            sleep=lambda _seconds: None,
        )

        self.assertEqual(
            [event["click_state"] for _, event in quartz.posted],
            [1, 1, 2, 2, 3, 3],
        )

    def test_unsupported_click_count_is_rejected(self):
        with self.assertRaises(ValueError):
            post_left_click_sequence(
                100,
                200,
                4,
                quartz=FakeQuartz(),
                sleep=lambda _seconds: None,
            )


if __name__ == "__main__":
    unittest.main()
