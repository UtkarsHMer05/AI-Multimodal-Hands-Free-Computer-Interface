import unittest
from collections import namedtuple
from unittest.mock import patch

from voice_cursor.accessibility_controls import InteractiveControl
from voice_cursor.actions import ActionExecutor
from voice_cursor.commands import (
    CommandName,
    interpret_command,
    interpret_screen_text_action,
)
from voice_cursor.screen_text import ScreenTextMatch

Point = namedtuple("Point", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])


def command(phrase):
    matched = interpret_command(phrase)
    assert matched is not None
    return matched


class ActionExecutorTests(unittest.TestCase):
    def test_click_emits_visual_feedback_at_cursor_position(self):
        class FakeAutomation:
            def click(self):
                return None

            def position(self):
                return Point(320, 240)

        feedback = []
        executor = ActionExecutor(
            start_enabled=True,
            on_click_feedback=(
                lambda action, x, y: feedback.append((action, x, y))
            ),
        )
        executor._pyautogui = FakeAutomation()
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute(command("click"))
        self.assertTrue(result.success)
        self.assertEqual(feedback, [("single", 320, 240)])

    def test_starts_paused(self):
        executor = ActionExecutor(dry_run=True)
        result = executor.execute(command("move left"))
        self.assertFalse(result.success)
        self.assertIn("paused", result.message)

    def test_resume_enables_dry_run_action(self):
        executor = ActionExecutor(dry_run=True)
        executor.execute(command("resume control"))
        result = executor.execute(command("double click"))
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Dry run: Double click")

    def test_pause_disables_actions_again(self):
        executor = ActionExecutor(dry_run=True)
        executor.execute(command("resume control"))
        executor.execute(command("pause control"))
        result = executor.execute(command("scroll down"))
        self.assertFalse(result.success)

    def test_all_non_toggle_commands_have_dry_run_mapping(self):
        executor = ActionExecutor(dry_run=True)
        executor.execute(command("resume control"))
        for name in CommandName:
            if name in {CommandName.PAUSE_CONTROL, CommandName.RESUME_CONTROL}:
                continue
            phrase_by_name = {
                "move_left": "move left",
                "move_right": "move right",
                "move_up": "move up",
                "move_down": "move down",
                "left_click": "click",
                "double_click": "double click",
                "right_click": "right click",
                "scroll_up": "scroll up",
                "scroll_down": "scroll down",
                "open_browser": "open browser",
                "new_tab": "new tab",
                "close_tab": "close tab",
            }
            result = executor.execute(command(phrase_by_name[name.value]))
            self.assertTrue(result.success, name)

    def test_start_enabled_allows_live_action(self):
        executor = ActionExecutor(start_enabled=True)
        self.assertFalse(executor.paused)

    def test_live_movement_reports_observed_coordinates(self):
        class FakeAutomation:
            def __init__(self):
                self.point = (300, 200)

            def position(self):
                return Point(*self.point)

            def moveRel(self, dx, dy, duration):
                self.point = (self.point[0] + dx, self.point[1] + dy)

        executor = ActionExecutor(start_enabled=True, movement_pixels=180)
        executor._pyautogui = FakeAutomation()
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute(command("move left"))
        self.assertTrue(result.success)
        self.assertIn("(300, 200)", result.message)
        self.assertIn("(120, 200)", result.message)

    def test_live_movement_detects_silent_failure(self):
        class BlockedAutomation:
            def position(self):
                return Point(300, 200)

            def moveRel(self, dx, dy, duration):
                return None

        executor = ActionExecutor(start_enabled=True)
        executor._pyautogui = BlockedAutomation()
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute(command("move right"))
        self.assertFalse(result.success)
        self.assertIn("cursor stayed", result.message)

    def test_click_enable_moves_to_unique_interactive_control_and_presses(self):
        class FakeAutomation:
            def __init__(self):
                self.point = Point(0, 0)
                self.clicked = False

            def size(self):
                return Size(1470, 956)

            def moveTo(self, x, y, duration):
                self.point = Point(x, y)

            def position(self):
                return self.point

            def click(self):
                self.clicked = True

        class FakeLocator:
            def __init__(self):
                self.pressed = False

            def find(self, label):
                return [
                    InteractiveControl(
                        element=object(),
                        label="Enable",
                        role="AXButton",
                        app_name="Test App",
                        pid=123,
                        x=560,
                        y=380,
                        width=160,
                        height=80,
                    )
                ]

            def perform_default_action(self, control):
                self.pressed = True
                return True

        executor = ActionExecutor(start_enabled=True)
        automation = FakeAutomation()
        executor._pyautogui = automation
        locator = FakeLocator()
        executor._controls = locator
        with patch.object(executor, "_live_control_permission", return_value=None):
            action = interpret_screen_text_action("click enable")
            assert action is not None
            result = executor.execute_screen_text(action)
        self.assertTrue(result.success)
        self.assertEqual(automation.point, Point(640, 420))
        self.assertTrue(locator.pressed)
        self.assertFalse(automation.clicked)

    def test_click_enable_refuses_ambiguous_matches(self):
        class FakeAutomation:
            def size(self):
                return Size(1470, 956)

        class FakeLocator:
            def find(self, label):
                return [
                    InteractiveControl(
                        object(),
                        "Enable",
                        "AXButton",
                        "Test App",
                        123,
                        80,
                        80,
                        40,
                        40,
                    ),
                    InteractiveControl(
                        object(),
                        "Enable",
                        "AXButton",
                        "Test App",
                        123,
                        480,
                        480,
                        40,
                        40,
                    ),
                ]

        executor = ActionExecutor(start_enabled=True)
        executor._pyautogui = FakeAutomation()
        executor._controls = FakeLocator()
        with patch.object(executor, "_live_control_permission", return_value=None):
            action = interpret_screen_text_action("click enable")
            assert action is not None
            result = executor.execute_screen_text(action)
        self.assertFalse(result.success)
        self.assertIn("ambiguous", result.message)

    def test_single_click_on_finder_icon_does_not_invoke_axopen(self):
        class FakeAutomation:
            def __init__(self):
                self.point = Point(0, 0)
                self.clicked = False

            def moveTo(self, x, y, duration):
                self.point = Point(x, y)

            def position(self):
                return self.point

            def click(self):
                self.clicked = True

        class FinderLocator:
            def __init__(self):
                self.default_action_called = False

            def find(self, label):
                return [
                    InteractiveControl(
                        element=object(),
                        label="Projects",
                        role="AXImage",
                        app_name="Finder",
                        pid=123,
                        x=1378,
                        y=585,
                        width=64,
                        height=64,
                        action="AXOpen",
                    )
                ]

            def perform_default_action(self, control):
                self.default_action_called = True
                return True

        executor = ActionExecutor(start_enabled=True)
        automation = FakeAutomation()
        locator = FinderLocator()
        executor._pyautogui = automation
        executor._controls = locator
        action = interpret_screen_text_action("click projects")
        assert action is not None
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute_screen_text(action)
        self.assertTrue(result.success)
        self.assertEqual(automation.point, Point(1410, 617))
        self.assertTrue(automation.clicked)
        self.assertFalse(locator.default_action_called)

    def test_dynamic_double_right_and_hover_actions(self):
        class FakeAutomation:
            def __init__(self):
                self.point = Point(0, 0)
                self.operation = None

            def size(self):
                return Size(1470, 956)

            def moveTo(self, x, y, duration):
                self.point = Point(x, y)

            def position(self):
                return self.point

            def doubleClick(self, interval):
                self.operation = "double"

            def rightClick(self):
                self.operation = "right"

        class FakeLocator:
            def find(self, label):
                return [
                    InteractiveControl(
                        element=object(),
                        label=label.title(),
                        role="AXButton",
                        app_name="Test App",
                        pid=123,
                        x=600,
                        y=360,
                        width=200,
                        height=80,
                    )
                ]

            def perform_default_action(self, control):
                return True

        cases = (
            ("double click settings", "double"),
            ("right click downloads", "right"),
            ("move to sign in", None),
        )
        for phrase, expected_operation in cases:
            with self.subTest(phrase=phrase):
                executor = ActionExecutor(start_enabled=True)
                automation = FakeAutomation()
                executor._pyautogui = automation
                executor._controls = FakeLocator()
                action = interpret_screen_text_action(phrase)
                assert action is not None
                with patch.object(
                    executor,
                    "_live_control_permission",
                    return_value=None,
                ):
                    result = executor.execute_screen_text(action)
                self.assertTrue(result.success)
                self.assertEqual(automation.point, Point(700, 400))
                self.assertEqual(automation.operation, expected_operation)

    def test_local_button_moves_cursor_and_invokes_registered_control(self):
        class FakeAutomation:
            def __init__(self):
                self.point = Point(0, 0)

            def moveTo(self, x, y, duration):
                self.point = Point(x, y)

            def position(self):
                return self.point

        invoked = []
        executor = ActionExecutor(start_enabled=True)
        executor._pyautogui = FakeAutomation()
        action = interpret_screen_text_action("click enable")
        assert action is not None
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute_local_control(
                action,
                label="Enable",
                center=(240, 180),
                activate=lambda: invoked.append("Enable"),
            )
        self.assertTrue(result.success)
        self.assertEqual(executor._pyautogui.point, Point(240, 180))
        self.assertEqual(invoked, ["Enable"])

    def test_ordinary_visible_text_uses_ocr_after_semantic_controls_miss(self):
        class FakeAutomation:
            def __init__(self):
                self.point = Point(100, 100)
                self.clicked = False

            def size(self):
                return Size(1000, 800)

            def position(self):
                return self.point

            def moveTo(self, x, y, duration):
                self.point = Point(x, y)

            def click(self):
                self.clicked = True

        class NoSemanticControls:
            def find(self, label):
                return []

        class FakeScreenText:
            def find(self, label, **kwargs):
                self.excluded = kwargs["excluded_rectangles"]
                return [
                    ScreenTextMatch(
                        text="Projects",
                        confidence=96,
                        x=850,
                        y=140,
                        width=100,
                        height=30,
                    )
                ]

            def is_desktop_point(self, x, y):
                return True

        executor = ActionExecutor(start_enabled=True)
        executor._pyautogui = FakeAutomation()
        executor._controls = NoSemanticControls()
        screen_text = FakeScreenText()
        executor._screen_text = screen_text
        action = interpret_screen_text_action("click projects")
        assert action is not None
        exclusion = ((10, 10, 400, 600),)
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute_screen_text(
                action,
                excluded_rectangles=exclusion,
            )
        self.assertTrue(result.success)
        self.assertEqual(executor._pyautogui.point, Point(850, 140))
        self.assertTrue(executor._pyautogui.clicked)
        self.assertEqual(screen_text.excluded, exclusion)

    def test_ocr_receives_conflicting_desktop_icon_exclusion(self):
        class FakeAutomation:
            def size(self):
                return Size(1000, 800)

            def position(self):
                return Point(0, 0)

        finder_exclusion = (700, 100, 900, 220)

        class NoExactControl:
            def find_with_ocr_exclusions(self, label):
                self.label = label
                return [], (finder_exclusion,)

        class NoScreenMatch:
            def find(self, label, **kwargs):
                self.label = label
                self.excluded = kwargs["excluded_rectangles"]
                return []

        executor = ActionExecutor(start_enabled=True)
        executor._pyautogui = FakeAutomation()
        controls = NoExactControl()
        screen_text = NoScreenMatch()
        executor._controls = controls
        executor._screen_text = screen_text
        action = interpret_screen_text_action("click project")
        assert action is not None
        voice_window = (10, 20, 300, 500)
        with patch.object(executor, "_live_control_permission", return_value=None):
            result = executor.execute_screen_text(
                action,
                excluded_rectangles=(voice_window,),
            )
        self.assertFalse(result.success)
        self.assertEqual(controls.label, "project")
        self.assertEqual(screen_text.label, "project")
        self.assertEqual(
            screen_text.excluded,
            (voice_window, finder_exclusion),
        )


if __name__ == "__main__":
    unittest.main()
