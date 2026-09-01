"""Safe execution of the supported computer-control actions."""

from __future__ import annotations

import ctypes
import platform
import time
import webbrowser
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from .accessibility_controls import (
    AccessibilityControlError,
    AccessibilityControlLocator,
)
from .commands import (
    CommandName,
    ScreenActionKind,
    ScreenTextAction,
    VoiceCommand,
)
from .macos_clicks import post_left_click_sequence
from .screen_text import ScreenTextError, ScreenTextLocator
from .window_activation import activate_application_at_point


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str


class ActionExecutor:
    """Map recognized commands to operating-system actions.

    Control starts paused. In dry-run mode, commands are reported but no mouse,
    keyboard, or browser action is performed.
    """

    def __init__(
        self,
        *,
        dry_run: bool = False,
        movement_pixels: int = 180,
        start_enabled: bool = False,
        on_click_feedback: Callable[[str, int, int], None] | None = None,
    ):
        self.dry_run = dry_run
        self.movement_pixels = movement_pixels
        self.paused = not start_enabled
        self._pyautogui = None
        self._on_click_feedback = on_click_feedback or (
            lambda _action, _x, _y: None
        )
        self._controls = AccessibilityControlLocator()
        self._screen_text = ScreenTextLocator()

    def _automation(self):
        if self._pyautogui is None:
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.08
            self._pyautogui = pyautogui
        return self._pyautogui

    def execute(self, command: VoiceCommand) -> ActionResult:
        if command.name == CommandName.PAUSE_CONTROL:
            self.paused = True
            return ActionResult(True, "Control paused")

        if command.name == CommandName.RESUME_CONTROL:
            permission = self._live_control_permission()
            if permission is not None:
                self.paused = True
                return permission
            self.paused = False
            suffix = " (dry run)" if self.dry_run else ""
            return ActionResult(True, f"Control enabled{suffix}")

        if self.paused:
            return ActionResult(False, "Ignored while control is paused")

        if self.dry_run:
            return ActionResult(True, f"Dry run: {command.label}")

        try:
            return self._perform(command)
        except Exception as exc:  # OS permissions and automation errors
            return ActionResult(False, f"Action failed: {exc}")

    def execute_screen_text(
        self,
        action: ScreenTextAction,
        *,
        excluded_rectangles: tuple[tuple[int, int, int, int], ...] = (),
    ) -> ActionResult:
        """Target a semantic control, then fall back to whole-screen OCR."""
        if self.paused:
            return ActionResult(False, "Ignored while control is paused")
        if self.dry_run:
            return ActionResult(
                True,
                f'Dry run: {action.kind.value} visible "{action.label}"',
            )
        permission = self._live_control_permission()
        if permission is not None:
            return permission
        try:
            return self._act_on_interactive_control(
                action,
                excluded_rectangles=excluded_rectangles,
            )
        except Exception as exc:
            return ActionResult(False, f"Screen action failed: {exc}")

    def execute_local_control(
        self,
        action: ScreenTextAction,
        *,
        label: str,
        center: tuple[int, int],
        activate: Callable[[], object],
    ) -> ActionResult:
        """Operate a registered button in the Voice Cursor Tk window."""
        if self.paused:
            return ActionResult(False, "Ignored while control is paused")
        if self.dry_run:
            return ActionResult(
                True,
                f'Dry run: {action.kind.value} button "{label}"',
            )
        permission = self._live_control_permission()
        if permission is not None:
            return permission
        try:
            automation = self._automation()
            target_x, target_y = center
            automation.moveTo(target_x, target_y, duration=0.35)
            observed = automation.position()
            if (
                abs(observed.x - target_x) > 20
                or abs(observed.y - target_y) > 20
            ):
                return ActionResult(
                    False,
                    f'Found button "{label}" at ({target_x}, {target_y}), but '
                    f"the cursor stopped at ({observed.x}, {observed.y}).",
                )

            if action.kind == ScreenActionKind.CLICK:
                self._prepare_click(automation)
                activate()
                verb = "Clicked"
                click_kind = "single"
            elif action.kind == ScreenActionKind.DOUBLE_CLICK:
                self._prepare_click(automation)
                activate()
                activate()
                verb = "Double-clicked"
                click_kind = "double"
            elif action.kind == ScreenActionKind.RIGHT_CLICK:
                self._prepare_click(automation)
                automation.rightClick()
                verb = "Right-clicked"
                click_kind = "right"
            elif action.kind == ScreenActionKind.HOVER:
                verb = "Moved to"
                click_kind = None
            else:
                return ActionResult(
                    False,
                    f"Unsupported screen action: {action.kind.value}",
                )
            self._notify_click(click_kind, automation)
            return ActionResult(
                True,
                f'{verb} project button "{label}" at ({target_x}, {target_y})',
            )
        except Exception as exc:
            return ActionResult(False, f"Project button action failed: {exc}")

    def verify_cursor_control(self) -> ActionResult:
        """Move the pointer briefly and restore it, verifying actual OS control."""
        if self.dry_run:
            return ActionResult(
                False,
                "Cursor test is unavailable in dry-run mode. Restart without --dry-run.",
            )

        permission = self._live_control_permission()
        if permission is not None:
            return permission

        try:
            automation = self._automation()
            start = automation.position()
            automation.moveRel(40, 0, duration=0.2)
            after = automation.position()
            if after == start:
                automation.moveRel(-40, 0, duration=0.2)
                after = automation.position()
            automation.moveTo(start.x, start.y, duration=0.2)
            if after == start:
                return ActionResult(
                    False,
                    "Cursor did not move. Allow the launching app under macOS "
                    "System Settings → Privacy & Security → Accessibility.",
                )
            return ActionResult(
                True,
                f"Cursor test passed: ({start.x}, {start.y}) → "
                f"({after.x}, {after.y}) → restored",
            )
        except Exception as exc:
            return ActionResult(False, f"Cursor test failed: {exc}")

    def _perform(self, command: VoiceCommand) -> ActionResult:
        automation = self._automation()
        step = self.movement_pixels
        action = command.name

        if action == CommandName.MOVE_LEFT:
            return self._move_cursor(-step, 0, command.label)
        elif action == CommandName.MOVE_RIGHT:
            return self._move_cursor(step, 0, command.label)
        elif action == CommandName.MOVE_UP:
            return self._move_cursor(0, -step, command.label)
        elif action == CommandName.MOVE_DOWN:
            return self._move_cursor(0, step, command.label)
        elif action == CommandName.LEFT_CLICK:
            self._prepare_click(automation)
            automation.click()
            self._notify_click("single", automation)
        elif action == CommandName.DOUBLE_CLICK:
            self._prepare_click(automation)
            self._double_click(automation)
            self._notify_click("double", automation)
        elif action == CommandName.RIGHT_CLICK:
            self._prepare_click(automation)
            automation.rightClick()
            self._notify_click("right", automation)
        elif action == CommandName.SCROLL_UP:
            automation.scroll(4)
        elif action == CommandName.SCROLL_DOWN:
            automation.scroll(-4)
        elif action == CommandName.OPEN_BROWSER:
            webbrowser.open("about:blank")
        elif action == CommandName.NEW_TAB:
            automation.hotkey(self._modifier_key(), "t")
        elif action == CommandName.CLOSE_TAB:
            automation.hotkey(self._modifier_key(), "w")
        else:
            return ActionResult(False, f"No action is configured for {command.label}")

        return ActionResult(True, f"Completed: {command.label}")

    def _act_on_interactive_control(
        self,
        action: ScreenTextAction,
        *,
        excluded_rectangles: tuple[tuple[int, int, int, int], ...] = (),
    ) -> ActionResult:
        label = action.label
        automation = self._automation()
        semantic_exclusions: tuple[tuple[int, int, int, int], ...] = ()
        try:
            find_with_exclusions = getattr(
                self._controls,
                "find_with_ocr_exclusions",
                None,
            )
            if find_with_exclusions is None:
                matches = self._controls.find(label)
            else:
                matches, semantic_exclusions = find_with_exclusions(label)
        except AccessibilityControlError:
            matches = []

        if not matches:
            return self._act_on_visible_screen_text(
                action,
                excluded_rectangles=(
                    *excluded_rectangles,
                    *semantic_exclusions,
                ),
            )
        if len(matches) > 1:
            coordinates = ", ".join(
                f"({item.center[0]}, {item.center[1]})" for item in matches[:4]
            )
            return ActionResult(
                False,
                f'Found {len(matches)} interactive "{label}" controls at '
                f"{coordinates}. Nothing was clicked because the target is ambiguous.",
            )

        target = matches[0]
        target_x, target_y = target.center
        automation.moveTo(target_x, target_y, duration=0.35)
        observed = automation.position()
        if abs(observed.x - target_x) > 20 or abs(observed.y - target_y) > 20:
            return ActionResult(
                False,
                f'Found the interactive "{target.label}" control at '
                f"({target_x}, {target_y}), but the "
                f"cursor stopped at ({observed.x}, {observed.y}). Check "
                "Accessibility permission.",
            )

        if action.kind == ScreenActionKind.CLICK:
            self._prepare_click(automation)
            if (
                target.action != "AXPress"
                or not self._controls.perform_default_action(target)
            ):
                automation.click()
            verb = "Clicked"
            click_kind = "single"
        elif action.kind == ScreenActionKind.DOUBLE_CLICK:
            self._prepare_click(automation)
            self._double_click(automation)
            verb = "Double-clicked"
            click_kind = "double"
        elif action.kind == ScreenActionKind.RIGHT_CLICK:
            self._prepare_click(automation)
            automation.rightClick()
            verb = "Right-clicked"
            click_kind = "right"
        elif action.kind == ScreenActionKind.HOVER:
            verb = "Moved to"
            click_kind = None
        else:
            return ActionResult(False, f"Unsupported screen action: {action.kind.value}")
        self._notify_click(click_kind, automation)

        return ActionResult(
            True,
            f'{verb} interactive {target.role} "{target.label}" in '
            f"{target.app_name} at ({target_x}, {target_y})"
            + (
                f" using {target.similarity * 100:.0f}% speech/control similarity"
                if target.similarity < 1.0
                else ""
            ),
        )

    def _act_on_visible_screen_text(
        self,
        action: ScreenTextAction,
        *,
        excluded_rectangles: tuple[tuple[int, int, int, int], ...],
    ) -> ActionResult:
        automation = self._automation()
        size = automation.size()
        try:
            matches = self._screen_text.find(
                action.label,
                screen_width=size.width,
                screen_height=size.height,
                excluded_rectangles=excluded_rectangles,
            )
        except ScreenTextError as exc:
            return ActionResult(False, str(exc))
        if not matches:
            return ActionResult(
                False,
                f'No button or visible screen text matching "{action.label}" '
                "was found outside visible Voice Cursor content.",
            )

        current = automation.position()
        matches.sort(
            key=lambda item: (
                0
                if self._screen_text.is_desktop_point(item.x, item.y)
                else 1,
                -item.similarity,
                -item.height,
                -item.confidence,
                (item.x - current.x) ** 2 + (item.y - current.y) ** 2,
            )
        )
        target = matches[0]
        automation.moveTo(target.x, target.y, duration=0.4)
        observed = automation.position()
        if abs(observed.x - target.x) > 20 or abs(observed.y - target.y) > 20:
            return ActionResult(
                False,
                f'Found visible text "{target.text}" at ({target.x}, {target.y}), '
                f"but the cursor stopped at ({observed.x}, {observed.y}).",
            )

        if action.kind == ScreenActionKind.CLICK:
            self._prepare_click(automation)
            automation.click()
            verb = "Clicked"
            click_kind = "single"
        elif action.kind == ScreenActionKind.DOUBLE_CLICK:
            self._prepare_click(automation)
            self._double_click(automation)
            verb = "Double-clicked"
            click_kind = "double"
        elif action.kind == ScreenActionKind.RIGHT_CLICK:
            self._prepare_click(automation)
            automation.rightClick()
            verb = "Right-clicked"
            click_kind = "right"
        elif action.kind == ScreenActionKind.HOVER:
            verb = "Moved to"
            click_kind = None
        else:
            return ActionResult(
                False,
                f"Unsupported screen action: {action.kind.value}",
            )
        self._notify_click(click_kind, automation)

        selection = (
            f"; selected the best of {len(matches)} visible matches"
            if len(matches) > 1
            else ""
        )
        fuzzy = (
            f" using {target.similarity * 100:.0f}% speech/text similarity"
            if target.similarity < 1.0
            else ""
        )
        return ActionResult(
            True,
            f'{verb} visible text "{target.text}" at ({target.x}, {target.y})'
            f"{selection}{fuzzy}",
        )

    def _notify_click(self, action: str | None, automation) -> None:
        if action is None:
            return
        try:
            point = automation.position()
            self._on_click_feedback(action, int(point.x), int(point.y))
        except Exception:
            pass

    @staticmethod
    def _prepare_click(automation) -> None:
        """Activate the visible target app so the first click is not consumed."""
        if not isinstance(automation, ModuleType):
            return
        try:
            point = automation.position()
            result = activate_application_at_point(int(point.x), int(point.y))
            if result.changed:
                time.sleep(0.12)
        except Exception:
            pass

    @staticmethod
    def _double_click(automation) -> None:
        """Send a genuine AppKit/Finder-compatible double-click on macOS."""
        if platform.system() == "Darwin" and isinstance(automation, ModuleType):
            point = automation.position()
            post_left_click_sequence(int(point.x), int(point.y), 2)
            return
        automation.doubleClick(interval=0.12)

    def _move_cursor(self, dx: int, dy: int, label: str) -> ActionResult:
        automation = self._automation()
        before = automation.position()
        automation.moveRel(dx, dy, duration=0.3)
        after = automation.position()
        if after == before:
            return ActionResult(
                False,
                f"{label} was recognized, but the cursor stayed at "
                f"({before.x}, {before.y}). It may be at the screen edge, or "
                "macOS Accessibility permission may be blocking control.",
            )
        return ActionResult(
            True,
            f"{label}: cursor ({before.x}, {before.y}) → ({after.x}, {after.y})",
        )

    def _live_control_permission(self) -> ActionResult | None:
        if self.dry_run or platform.system() != "Darwin":
            return None
        trusted = self._macos_accessibility_trusted()
        if trusted is not False:
            return None
        return ActionResult(
            False,
            "macOS Accessibility permission is required. Open System Settings → "
            "Privacy & Security → Accessibility, enable Terminal (or the app used "
            "to launch Voice Cursor), then restart Voice Cursor.",
        )

    @staticmethod
    def _macos_accessibility_trusted() -> bool | None:
        """Return macOS Accessibility trust, or None when it cannot be queried."""
        try:
            application_services = ctypes.CDLL(
                "/System/Library/Frameworks/ApplicationServices.framework/"
                "ApplicationServices"
            )
            check_trust = application_services.AXIsProcessTrusted
            check_trust.restype = ctypes.c_bool
            check_trust.argtypes = []
            return bool(check_trust())
        except (AttributeError, OSError):
            return None

    @staticmethod
    def _modifier_key() -> str:
        return "command" if platform.system() == "Darwin" else "ctrl"
