import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import call, patch

import numpy as np

from voice_cursor.camera_control import (
    BlinkGestureDetector,
    CameraPointerController,
    RelativePointerMapper,
    TongueGestureDetector,
)
from voice_cursor.camera_worker import _eye_ratio, eye_openness, tongue_features


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

    def test_eye_openness_decreases_when_both_eyes_close(self):
        open_landmarks = self._eye_landmarks(open_gap=0.06)
        closed_landmarks = self._eye_landmarks(open_gap=0.006)
        self.assertGreater(
            eye_openness(open_landmarks),
            eye_openness(closed_landmarks) * 4,
        )

    def test_two_rapid_blinks_produce_single_click(self):
        detector = self._calibrated_blink_detector()
        events = self._blink(detector, 2.0)
        events.extend(self._blink(detector, 2.32))
        self.assertTrue(detector.freeze_pointer)
        events.append(detector.update(0.30, now=3.18)[0])
        self.assertEqual([event for event in events if event], ["single"])
        self.assertFalse(detector.freeze_pointer)

    def test_four_rapid_blinks_produce_double_click_without_early_single(self):
        detector = self._calibrated_blink_detector()
        events = []
        for start in (4.0, 4.30, 4.60, 4.90):
            events.extend(self._blink(detector, start))
        self.assertEqual([event for event in events if event], ["double"])

    def test_one_normal_blink_does_not_click(self):
        detector = self._calibrated_blink_detector()
        events = self._blink(detector, 6.0)
        events.append(detector.update(0.30, now=7.0)[0])
        self.assertEqual([event for event in events if event], [])

    def test_three_blinks_are_ignored_instead_of_clicking(self):
        detector = self._calibrated_blink_detector()
        events = []
        for start in (8.0, 8.30, 8.60):
            events.extend(self._blink(detector, start))
        action, status = detector.update(0.30, now=9.50)
        events.append(action)
        self.assertEqual([event for event in events if event], [])
        self.assertIn("ignored", status)

    def test_holding_eyes_closed_does_not_click(self):
        detector = self._calibrated_blink_detector()
        events = [
            detector.update(0.05, now=10.0)[0],
            detector.update(0.05, now=10.05)[0],
            detector.update(0.05, now=11.0)[0],
            detector.update(0.30, now=11.05)[0],
            detector.update(0.30, now=11.10)[0],
        ]
        self.assertEqual([event for event in events if event], [])

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

    def test_simultaneous_tongue_and_blink_actions_emit_only_one_click(self):
        class FakeAutomation:
            def __init__(self):
                self.single = 0
                self.double = 0

            def click(self):
                self.single += 1

            def doubleClick(self, interval):
                self.double += 1

            def position(self):
                return SimpleNamespace(x=640, y=420)

        controller = CameraPointerController()
        blink_statuses = []
        controller._on_blink_status = blink_statuses.append
        automation = FakeAutomation()
        with patch(
            "voice_cursor.camera_control.time.monotonic",
            side_effect=(20.0, 20.1),
        ):
            controller._perform_camera_gesture_actions(
                "single",
                "double",
                automation=automation,
            )
        self.assertEqual(automation.single, 1)
        self.assertEqual(automation.double, 0)
        self.assertTrue(any("suppressed" in item for item in blink_statuses))

    def test_combined_calibration_advances_from_tongue_to_blink(self):
        controller = CameraPointerController()
        controller.mode = "head"
        controller._mapper = RelativePointerMapper(mode="head")
        controller._tongue = self._calibrated_tongue_detector()
        controller._blink = BlinkGestureDetector(calibration_frames=3)
        controller._combined_calibration_stage = "tongue"
        blink_statuses = []
        controller._on_blink_status = blink_statuses.append

        controller._handle_message(
            {
                "type": "metrics",
                "tongue_features": (0.1, 0.2, 0.1, 0.2, 0.05),
                "eye_openness": 0.30,
                "head_x": 0.5,
                "head_y": 0.5,
                "gaze_x": 0.5,
                "gaze_y": 0.5,
            }
        )

        self.assertEqual(controller._combined_calibration_stage, "blink")
        self.assertEqual(controller._blink.phase, "open_calibration")
        self.assertTrue(any("Combined calibration 2/2" in item for item in blink_statuses))

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

    @staticmethod
    def _calibrated_blink_detector():
        detector = BlinkGestureDetector(calibration_frames=3)
        detector.start_calibration()
        for index in range(3):
            detector.update(0.30, now=index * 0.05)
        for index in range(3):
            detector.update(0.05, now=1.4 + index * 0.05)
        assert detector.calibrated
        for index in range(4):
            detector.update(0.30, now=1.6 + index * 0.05)
        assert detector.phase == "ready"
        return detector

    @staticmethod
    def _blink(detector, start):
        events = [
            detector.update(0.05, now=start)[0],
            detector.update(0.05, now=start + 0.05)[0],
            detector.update(0.30, now=start + 0.12)[0],
            detector.update(0.30, now=start + 0.17)[0],
        ]
        return events

    @staticmethod
    def _eye_landmarks(*, open_gap):
        landmarks = [SimpleNamespace(x=0.5, y=0.5) for _ in range(478)]
        landmarks[33] = SimpleNamespace(x=0.30, y=0.43)
        landmarks[133] = SimpleNamespace(x=0.50, y=0.43)
        landmarks[362] = SimpleNamespace(x=0.60, y=0.43)
        landmarks[263] = SimpleNamespace(x=0.80, y=0.43)
        for upper, lower in (
            (159, 145),
            (158, 153),
            (386, 374),
            (385, 380),
        ):
            landmarks[upper] = SimpleNamespace(x=0.5, y=0.43 - open_gap / 2)
            landmarks[lower] = SimpleNamespace(x=0.5, y=0.43 + open_gap / 2)
        return landmarks


if __name__ == "__main__":
    unittest.main()
