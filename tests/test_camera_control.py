import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import call, patch

import numpy as np

from voice_cursor.camera_control import (
    CameraPointerController,
    RelativePointerMapper,
    TongueGestureDetector,
)
from voice_cursor.camera_worker import _eye_ratio, tongue_features


class CameraControlTests(unittest.TestCase):
    def test_head_mapper_calibrates_before_moving(self):
        mapper = RelativePointerMapper(mode="head")
        results = [mapper.update(0.5, 0.5) for _ in range(24)]
        self.assertTrue(mapper.calibrated)
        self.assertTrue(all(result is None for result in results))
        dx, dy = mapper.update(0.64, 0.5)
        self.assertGreater(dx, 0)
        self.assertEqual(dy, 0)

    def test_gaze_mapper_has_a_dead_zone_around_calibration(self):
        mapper = RelativePointerMapper(mode="gaze")
        for _ in range(24):
            mapper.update(0.5, 0.5)
        self.assertEqual(mapper.update(0.52, 0.48), (0, 0))
        dx, dy = mapper.update(0.3, 0.7)
        self.assertLess(dx, 0)
        self.assertGreater(dy, 0)

    def test_eye_ratio_is_relative_to_eye_bounds(self):
        landmarks = [SimpleNamespace(x=0.0, y=0.0) for _ in range(8)]
        landmarks[0] = SimpleNamespace(x=0.25, y=0.5)
        landmarks[1] = SimpleNamespace(x=0.75, y=0.5)
        landmarks[2] = SimpleNamespace(x=0.5, y=0.25)
        landmarks[3] = SimpleNamespace(x=0.5, y=0.75)
        for index in (4, 5, 6, 7):
            landmarks[index] = SimpleNamespace(x=0.625, y=0.375)
        horizontal, vertical = _eye_ratio(
            landmarks,
            iris=(4, 5, 6, 7),
            corners=(0, 1),
            lids=(2, 3),
        )
        self.assertAlmostEqual(horizontal, 0.75)
        self.assertAlmostEqual(vertical, 0.25)

    def test_tongue_pixel_features_increase_for_red_mouth_region(self):
        landmarks = [SimpleNamespace(x=0.5, y=0.5) for _ in range(478)]
        landmarks[61] = SimpleNamespace(x=0.3, y=0.5)
        landmarks[291] = SimpleNamespace(x=0.7, y=0.5)
        landmarks[13] = SimpleNamespace(x=0.5, y=0.45)
        landmarks[14] = SimpleNamespace(x=0.5, y=0.52)
        landmarks[17] = SimpleNamespace(x=0.5, y=0.55)
        neutral = np.full((100, 100, 3), (180, 140, 120), dtype=np.uint8)
        tongue = neutral.copy()
        tongue[55:72, 40:60] = (225, 65, 95)
        neutral_features = tongue_features(neutral, landmarks)
        tongue_values = tongue_features(tongue, landmarks)
        self.assertGreater(tongue_values[0], neutral_features[0])
        self.assertGreater(tongue_values[2], neutral_features[2])

    def test_one_tongue_gesture_produces_one_single_click(self):
        detector = self._calibrated_tongue_detector()
        tongue = (0.5, 0.6, 0.7, 0.6, 0.3)
        neutral = (0.1, 0.2, 0.1, 0.2, 0.05)
        events = self._tongue_tap(detector, 2.0, tongue, neutral)
        self.assertTrue(detector.freeze_pointer)
        events.append(detector.update(neutral, now=3.06)[0])
        self.assertEqual([event for event in events if event], ["single"])
        self.assertFalse(detector.freeze_pointer)

    def test_two_quick_tongue_gestures_produce_double_click(self):
        detector = self._calibrated_tongue_detector()
        tongue = (0.5, 0.6, 0.7, 0.6, 0.3)
        neutral = (0.1, 0.2, 0.1, 0.2, 0.05)
        events = self._tongue_tap(detector, 4.0, tongue, neutral)
        events.extend(self._tongue_tap(detector, 4.55, tongue, neutral))
        events.append(detector.update(neutral, now=5.61)[0])
        self.assertEqual([event for event in events if event], ["double"])

    def test_three_quick_tongue_gestures_produce_triple_click(self):
        detector = self._calibrated_tongue_detector()
        tongue = (0.5, 0.6, 0.7, 0.6, 0.3)
        neutral = (0.1, 0.2, 0.1, 0.2, 0.05)
        events = self._tongue_tap(detector, 6.0, tongue, neutral)
        events.extend(self._tongue_tap(detector, 6.55, tongue, neutral))
        events.extend(self._tongue_tap(detector, 7.10, tongue, neutral))
        self.assertEqual([event for event in events if event], ["triple"])

    def test_holding_tongue_does_not_emit_repeated_or_double_clicks(self):
        detector = self._calibrated_tongue_detector()
        tongue = (0.5, 0.6, 0.7, 0.6, 0.3)
        neutral = (0.1, 0.2, 0.1, 0.2, 0.05)
        events = [
            detector.update(tongue, now=8.0)[0],
            detector.update(tongue, now=8.05)[0],
            detector.update(tongue, now=8.10)[0],
            detector.update(tongue, now=9.5)[0],
            detector.update(tongue, now=10.5)[0],
        ]
        for now in (10.55, 10.60, 10.65):
            events.append(detector.update(neutral, now=now)[0])
        events.append(detector.update(neutral, now=11.36)[0])
        self.assertEqual([event for event in events if event], ["single"])

    def test_controller_maps_tongue_events_to_mouse_clicks(self):
        class FakeAutomation:
            def __init__(self):
                self.single = 0
                self.double = 0
                self.triple = 0

            def click(self, clicks=1, interval=None):
                if clicks == 1:
                    self.single += 1
                else:
                    self.triple += clicks
                    self.interval = interval

            def doubleClick(self, interval):
                self.double += 1
                self.interval = interval

            def position(self):
                return SimpleNamespace(x=640, y=420)

        controller = CameraPointerController()
        feedback = []
        controller._on_click_feedback = (
            lambda action, x, y: feedback.append((action, x, y))
        )
        automation = FakeAutomation()
        controller._perform_tongue_action("single", automation=automation)
        controller._perform_tongue_action("double", automation=automation)
        controller._perform_tongue_action("triple", automation=automation)
        self.assertEqual(automation.single, 1)
        self.assertEqual(automation.double, 1)
        self.assertEqual(automation.triple, 3)
        self.assertEqual(automation.interval, 0.12)
        self.assertEqual(
            feedback,
            [
                ("single", 640, 420),
                ("double", 640, 420),
                ("triple", 640, 420),
            ],
        )

    def test_real_macos_tongue_multi_clicks_use_native_click_states(self):
        automation = ModuleType("fake_pyautogui")
        automation.position = lambda: SimpleNamespace(x=640, y=420)
        automation.doubleClick = lambda **_kwargs: self.fail(
            "PyAutoGUI doubleClick must not be used on macOS"
        )
        automation.click = lambda **_kwargs: self.fail(
            "repeated PyAutoGUI clicks must not be used on macOS"
        )
        controller = CameraPointerController()

        with (
            patch("voice_cursor.camera_control.sys.platform", "darwin"),
            patch(
                "voice_cursor.camera_control.activate_application_at_point",
                return_value=SimpleNamespace(changed=False),
            ),
            patch(
                "voice_cursor.camera_control.post_left_click_sequence"
            ) as native_click,
        ):
            controller._perform_tongue_action("double", automation=automation)
            controller._perform_tongue_action("triple", automation=automation)

        self.assertEqual(
            native_click.call_args_list,
            [call(640, 420, 2), call(640, 420, 3)],
        )

    @staticmethod
    def _calibrated_tongue_detector():
        detector = TongueGestureDetector(calibration_frames=3)
        detector.start_calibration()
        neutral = (0.1, 0.2, 0.1, 0.2, 0.05)
        tongue = (0.5, 0.6, 0.7, 0.6, 0.3)
        for index in range(3):
            detector.update(neutral, now=index * 0.05)
        for index in range(3):
            detector.update(tongue, now=1.4 + index * 0.05)
        assert detector.calibrated
        for index in range(5):
            detector.update(neutral, now=1.6 + index * 0.05)
        assert detector.phase == "ready"
        return detector

    @staticmethod
    def _tongue_tap(detector, start, tongue, neutral):
        events = []
        for offset in (0.0, 0.05, 0.10, 0.20):
            events.append(detector.update(tongue, now=start + offset)[0])
        for offset in (0.25, 0.30, 0.35):
            events.append(detector.update(neutral, now=start + offset)[0])
        return events


if __name__ == "__main__":
    unittest.main()
