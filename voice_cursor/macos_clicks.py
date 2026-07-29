"""Reliable native multi-click mouse events for macOS."""

from __future__ import annotations

import time
from collections.abc import Callable


def post_left_click_sequence(
    x: int,
    y: int,
    count: int,
    *,
    interval: float = 0.10,
    press_duration: float = 0.025,
    quartz=None,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Post one macOS click sequence with explicit click-state values.

    Finder and AppKit controls use ``kCGMouseEventClickState`` to distinguish a
    genuine double/triple click from several unrelated single clicks. PyAutoGUI
    does not populate that field, so repeated PyAutoGUI clicks can select a
    Finder item without opening it.
    """
    if count not in {1, 2, 3}:
        raise ValueError("click count must be 1, 2, or 3")
    if quartz is None:
        import Quartz as quartz

    point = (float(x), float(y))
    for click_state in range(1, count + 1):
        down = quartz.CGEventCreateMouseEvent(
            None,
            quartz.kCGEventLeftMouseDown,
            point,
            quartz.kCGMouseButtonLeft,
        )
        quartz.CGEventSetIntegerValueField(
            down,
            quartz.kCGMouseEventClickState,
            click_state,
        )
        quartz.CGEventPost(quartz.kCGHIDEventTap, down)
        sleep(press_duration)

        up = quartz.CGEventCreateMouseEvent(
            None,
            quartz.kCGEventLeftMouseUp,
            point,
            quartz.kCGMouseButtonLeft,
        )
        quartz.CGEventSetIntegerValueField(
            up,
            quartz.kCGMouseEventClickState,
            click_state,
        )
        quartz.CGEventPost(quartz.kCGHIDEventTap, up)
        if click_state < count:
            sleep(interval)
