"""Show a non-activating, click-through macOS click indicator."""

from __future__ import annotations

import argparse


def show(action: str, x: int, y: int) -> int:
    from AppKit import (
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSBackingStoreBuffered,
        NSBezierPath,
        NSColor,
        NSFont,
        NSFontAttributeName,
        NSForegroundColorAttributeName,
        NSMakeRect,
        NSPanel,
        NSScreen,
        NSString,
        NSWindowCollectionBehaviorCanJoinAllSpaces,
        NSWindowCollectionBehaviorFullScreenAuxiliary,
        NSWindowCollectionBehaviorStationary,
        NSWindowStyleMaskBorderless,
        NSWindowStyleMaskNonactivatingPanel,
    )
    from Foundation import NSDate, NSRunLoop
    from PyObjCTools import AppHelper
    import objc

    label = {
        "single": "1",
        "double": "2",
        "triple": "3",
        "right": "R",
    }.get(action, "1")
    color_values = {
        "1": (0.086, 0.514, 1.0),
        "2": (0.949, 0.549, 0.094),
        "3": (0.690, 0.263, 0.859),
        "R": (0.859, 0.231, 0.263),
    }
    red, green, blue = color_values[label]
    ring_color = NSColor.colorWithSRGBRed_green_blue_alpha_(
        red,
        green,
        blue,
        1.0,
    )

    class RingView(objc.lookUpClass("NSView")):
        diameter = 34.0
        opacity = 1.0

        def isOpaque(self):
            return False

        def drawRect_(self, _rect):
            bounds = self.bounds()
            inset = (bounds.size.width - self.diameter) / 2.0
            circle = NSBezierPath.bezierPathWithOvalInRect_(
                NSMakeRect(
                    inset,
                    inset,
                    self.diameter,
                    self.diameter,
                )
            )
            ring_color.colorWithAlphaComponent_(self.opacity).setStroke()
            circle.setLineWidth_(5.0)
            circle.stroke()

            attributes = {
                NSFontAttributeName: NSFont.boldSystemFontOfSize_(17),
                NSForegroundColorAttributeName: ring_color.colorWithAlphaComponent_(
                    self.opacity
                ),
            }
            text = NSString.stringWithString_(label)
            size = text.sizeWithAttributes_(attributes)
            text.drawAtPoint_withAttributes_(
                (
                    (bounds.size.width - size.width) / 2.0,
                    (bounds.size.height - size.height) / 2.0,
                ),
                attributes,
            )

    application = NSApplication.sharedApplication()
    application.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    screen = NSScreen.mainScreen()
    if screen is None:
        return 1
    screen_height = screen.frame().size.height
    size = 82.0
    panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(
            x - size / 2.0,
            screen_height - y - size / 2.0,
            size,
            size,
        ),
        NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
        NSBackingStoreBuffered,
        False,
    )
    panel.setOpaque_(False)
    panel.setBackgroundColor_(NSColor.clearColor())
    panel.setHasShadow_(False)
    panel.setIgnoresMouseEvents_(True)
    panel.setHidesOnDeactivate_(False)
    panel.setCollectionBehavior_(
        NSWindowCollectionBehaviorCanJoinAllSpaces
        | NSWindowCollectionBehaviorFullScreenAuxiliary
        | NSWindowCollectionBehaviorStationary
    )
    view = RingView.alloc().initWithFrame_(NSMakeRect(0, 0, size, size))
    panel.setContentView_(view)
    panel.orderFrontRegardless()

    frames = (
        (34.0, 1.0),
        (44.0, 0.88),
        (56.0, 0.72),
        (68.0, 0.52),
        (76.0, 0.28),
    )
    run_loop = NSRunLoop.currentRunLoop()
    for diameter, opacity in frames:
        view.diameter = diameter
        view.opacity = opacity
        view.setNeedsDisplay_(True)
        view.displayIfNeeded()
        run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.075))
    panel.orderOut_(None)
    NSApp().terminate_(None)
    AppHelper.stopEventLoop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("single", "double", "triple", "right"))
    parser.add_argument("x", type=int)
    parser.add_argument("y", type=int)
    arguments = parser.parse_args()
    return show(arguments.action, arguments.x, arguments.y)


if __name__ == "__main__":
    raise SystemExit(main())
