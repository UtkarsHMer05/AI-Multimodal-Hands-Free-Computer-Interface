"""Activate the visible macOS application under a screen point."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ActivationResult:
    app_name: str | None
    pid: int | None
    changed: bool


def window_owner_at_point(
    windows,
    x: int,
    y: int,
    *,
    quartz,
) -> tuple[int | None, str | None]:
    """Select the frontmost normal application window containing a point."""
    ignored_owners = {
        "Window Server",
        "Dock",
        "SystemUIServer",
        "Control Center",
        "Notification Center",
    }
    for window in windows or []:
        try:
            layer = int(window.get(quartz.kCGWindowLayer, -1))
            alpha = float(window.get(quartz.kCGWindowAlpha, 1.0))
            bounds = window.get(quartz.kCGWindowBounds, {})
            left = float(bounds.get("X", 0))
            top = float(bounds.get("Y", 0))
            width = float(bounds.get("Width", 0))
            height = float(bounds.get("Height", 0))
            pid = int(window.get(quartz.kCGWindowOwnerPID, 0))
            owner = str(window.get(quartz.kCGWindowOwnerName) or "")
        except (TypeError, ValueError):
            continue
        contains_point = (
            left <= x <= left + width and top <= y <= top + height
        )
        if owner in ignored_owners and contains_point:
            return None, None
        if (
            layer != 0
            or alpha <= 0
            or width < 20
            or height < 20
            or pid <= 0
            or not contains_point
        ):
            continue
        return pid, owner
    return None, None


def activate_application_at_point(x: int, y: int) -> ActivationResult:
    """Bring the normal application window under `(x, y)` to the front."""
    try:
        import Quartz
        from AppKit import (
            NSApplicationActivateAllWindows,
            NSApplicationActivateIgnoringOtherApps,
            NSRunningApplication,
            NSWorkspace,
        )
    except ImportError:
        return ActivationResult(None, None, False)

    options = (
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements
    )
    windows = Quartz.CGWindowListCopyWindowInfo(
        options,
        Quartz.kCGNullWindowID,
    )
    target_pid, target_name = window_owner_at_point(
        windows,
        x,
        y,
        quartz=Quartz,
    )

    if target_pid is None:
        return ActivationResult(None, None, False)

    workspace = NSWorkspace.sharedWorkspace()
    frontmost = workspace.frontmostApplication()
    frontmost_pid = (
        int(frontmost.processIdentifier())
        if frontmost is not None
        else None
    )
    if target_pid == frontmost_pid:
        return ActivationResult(target_name, target_pid, False)

    application = NSRunningApplication.runningApplicationWithProcessIdentifier_(
        target_pid
    )
    if application is None:
        return ActivationResult(target_name, target_pid, False)
    activated = bool(
        application.activateWithOptions_(
            NSApplicationActivateAllWindows
            | NSApplicationActivateIgnoringOtherApps
        )
    )
    if activated:
        deadline = time.monotonic() + 0.45
        while time.monotonic() < deadline:
            current = workspace.frontmostApplication()
            if (
                current is not None
                and int(current.processIdentifier()) == target_pid
            ):
                break
            time.sleep(0.02)
    return ActivationResult(target_name, target_pid, activated)
