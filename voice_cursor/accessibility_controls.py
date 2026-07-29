"""Find genuine interactive macOS controls through the Accessibility API."""

from __future__ import annotations

import re
from dataclasses import dataclass


class AccessibilityControlError(RuntimeError):
    """Raised when interactive controls cannot be inspected safely."""


def normalize_control_text(text: str) -> str:
    """Normalize a spoken or accessibility label for safe comparison."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


@dataclass(frozen=True)
class InteractiveControl:
    element: object
    label: str
    role: str
    app_name: str
    pid: int
    x: int
    y: int
    width: int
    height: int
    similarity: float = 1.0
    action: str = "AXPress"

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


class AccessibilityControlLocator:
    """Search visible apps for pressable controls while ignoring plain text."""

    EXCLUDED_ROLES = {
        "AXStaticText",
        "AXTextField",
        "AXTextArea",
        "AXScrollArea",
        "AXWindow",
        "AXApplication",
    }

    def __init__(self, *, excluded_pid: int | None = None, max_nodes: int = 8_000):
        self.excluded_pid = excluded_pid
        self.max_nodes = max_nodes

    def find(self, label: str) -> list[InteractiveControl]:
        matches, _exclusions = self.find_with_ocr_exclusions(label)
        return matches

    def find_with_ocr_exclusions(
        self,
        label: str,
    ) -> tuple[list[InteractiveControl], tuple[tuple[int, int, int, int], ...]]:
        """Return exact matches plus desktop icons OCR must not reinterpret."""
        target = normalize_control_text(label)
        if not target:
            return [], ()
        controls = self.interactive_controls()

        exact = [
            control
            for control in controls
            if normalize_control_text(control.label) == target
        ]
        conflicts = tuple(
            (
                control.x - 70,
                control.y - 8,
                control.x + control.width + 70,
                control.y + control.height + 70,
            )
            for control in controls
            if control.app_name == "Finder"
            and control.role == "AXImage"
            and normalize_control_text(control.label) != target
        )
        return self._deduplicate(exact), conflicts

    def interactive_controls(self) -> list[InteractiveControl]:
        try:
            import ApplicationServices as AS
            import Quartz
            from AppKit import NSWorkspace
        except ImportError as exc:
            raise AccessibilityControlError(
                "The macOS accessibility bridge is missing. Reinstall the project "
                "dependencies."
            ) from exc

        if not AS.AXIsProcessTrusted():
            raise AccessibilityControlError(
                "Accessibility permission is required for semantic button targeting."
            )

        visible_apps = self._visible_application_pids(Quartz)
        finder = next(
            (
                app
                for app in NSWorkspace.sharedWorkspace().runningApplications()
                if str(app.localizedName() or "") == "Finder"
            ),
            None,
        )
        if finder is not None:
            finder_pid = int(finder.processIdentifier())
            if all(pid != finder_pid for pid, _name in visible_apps):
                visible_apps.append((finder_pid, "Finder"))
        if not visible_apps:
            raise AccessibilityControlError(
                "No visible target application windows were found."
            )

        seen: set[str] = set()
        controls: list[InteractiveControl] = []
        for pid, app_name in visible_apps:
            if len(seen) >= self.max_nodes:
                break
            root = AS.AXUIElementCreateApplication(pid)
            windows = self._attribute(AS, root, AS.kAXWindowsAttribute) or []
            focused_window = self._attribute(
                AS,
                root,
                AS.kAXFocusedWindowAttribute,
            )
            starts = []
            if focused_window is not None:
                starts.append(focused_window)
            starts.extend(
                window for window in windows if repr(window) != repr(focused_window)
            )
            if app_name == "Finder":
                starts.append(root)

            for start in starts:
                if self._attribute(AS, start, AS.kAXMinimizedAttribute) is True:
                    continue
                stack: list[tuple[object, int]] = [(start, 0)]
                while stack and len(seen) < self.max_nodes:
                    element, depth = stack.pop()
                    marker = repr(element)
                    if marker in seen:
                        continue
                    seen.add(marker)

                    role = self._attribute(AS, element, AS.kAXRoleAttribute)
                    actions = self._actions(AS, element)
                    open_action = getattr(AS, "kAXOpenAction", "AXOpen")
                    default_action = (
                        AS.kAXPressAction
                        if AS.kAXPressAction in actions
                        else (
                            open_action
                            if open_action in actions
                            else None
                        )
                    )
                    if (
                        isinstance(role, str)
                        and role not in self.EXCLUDED_ROLES
                        and default_action is not None
                    ):
                        label = self._control_label(AS, element)
                        bounds = self._bounds(AS, element)
                        if label and bounds is not None:
                            x, y, width, height = bounds
                            controls.append(
                                InteractiveControl(
                                    element=element,
                                    label=label,
                                    role=role,
                                    app_name=app_name,
                                    pid=pid,
                                    x=x,
                                    y=y,
                                    width=width,
                                    height=height,
                                    action=default_action,
                                )
                            )

                    if depth >= 60:
                        continue
                    children = self._attribute(
                        AS,
                        element,
                        AS.kAXChildrenAttribute,
                    )
                    if children:
                        stack.extend((child, depth + 1) for child in children)

        return self._deduplicate(controls)

    def _visible_application_pids(self, Quartz) -> list[tuple[int, str]]:
        """Return visible normal-window owners in front-to-back order."""
        options = (
            Quartz.kCGWindowListOptionOnScreenOnly
            | Quartz.kCGWindowListExcludeDesktopElements
        )
        window_info = Quartz.CGWindowListCopyWindowInfo(
            options,
            Quartz.kCGNullWindowID,
        )
        applications: list[tuple[int, str]] = []
        seen_pids: set[int] = set()
        for window in window_info or []:
            try:
                pid = int(window.get(Quartz.kCGWindowOwnerPID, 0))
                layer = int(window.get(Quartz.kCGWindowLayer, -1))
                alpha = float(window.get(Quartz.kCGWindowAlpha, 1.0))
                bounds = window.get(Quartz.kCGWindowBounds, {})
                width = float(bounds.get("Width", 0))
                height = float(bounds.get("Height", 0))
            except (TypeError, ValueError):
                continue
            if (
                pid <= 0
                or (
                    self.excluded_pid is not None
                    and pid == self.excluded_pid
                )
                or pid in seen_pids
                # Normal windows use layer 0, while macOS dialogs/sheets and
                # always-on-top application windows use layers up to 19.
                # Higher layers are system UI such as the menu bar/overlays.
                or layer < 0
                or layer > 19
                or alpha <= 0
                or width < 20
                or height < 20
            ):
                continue
            name = str(
                window.get(Quartz.kCGWindowOwnerName)
                or f"Application {pid}"
            )
            seen_pids.add(pid)
            applications.append((pid, name))
        return applications

    @staticmethod
    def perform_default_action(control: InteractiveControl) -> bool:
        try:
            import ApplicationServices as AS

            return (
                AS.AXUIElementPerformAction(control.element, control.action) == 0
            )
        except Exception:
            return False

    @staticmethod
    def _attribute(AS, element, attribute):
        try:
            error, value = AS.AXUIElementCopyAttributeValue(
                element,
                attribute,
                None,
            )
            return value if error == 0 else None
        except Exception:
            return None

    @staticmethod
    def _actions(AS, element) -> tuple[str, ...]:
        try:
            error, actions = AS.AXUIElementCopyActionNames(element, None)
            return tuple(actions) if error == 0 and actions else ()
        except Exception:
            return ()

    @classmethod
    def _control_label(cls, AS, element) -> str:
        attributes = (
            AS.kAXTitleAttribute,
            AS.kAXDescriptionAttribute,
            AS.kAXHelpAttribute,
            AS.kAXValueAttribute,
        )
        for attribute in attributes:
            value = cls._attribute(AS, element, attribute)
            if isinstance(value, str) and normalize_control_text(value):
                return value.strip()
        return ""

    @classmethod
    def _bounds(cls, AS, element) -> tuple[int, int, int, int] | None:
        position_value = cls._attribute(AS, element, AS.kAXPositionAttribute)
        size_value = cls._attribute(AS, element, AS.kAXSizeAttribute)
        if position_value is None or size_value is None:
            return None
        try:
            position_ok, position = AS.AXValueGetValue(
                position_value,
                AS.kAXValueCGPointType,
                None,
            )
            size_ok, size = AS.AXValueGetValue(
                size_value,
                AS.kAXValueCGSizeType,
                None,
            )
        except Exception:
            return None
        if not position_ok or not size_ok or size.width <= 0 or size.height <= 0:
            return None
        return (
            round(position.x),
            round(position.y),
            round(size.width),
            round(size.height),
        )

    @staticmethod
    def _deduplicate(
        controls: list[InteractiveControl],
    ) -> list[InteractiveControl]:
        deduplicated: list[InteractiveControl] = []
        for control in controls:
            duplicate = any(
                normalize_control_text(existing.label)
                == normalize_control_text(control.label)
                and abs(existing.center[0] - control.center[0]) <= 3
                and abs(existing.center[1] - control.center[1]) <= 3
                for existing in deduplicated
            )
            if not duplicate:
                deduplicated.append(control)
        return deduplicated
