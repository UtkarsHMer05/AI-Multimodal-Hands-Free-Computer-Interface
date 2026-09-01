"""Rectangle helpers for excluding only visible parts of the project window."""

from __future__ import annotations

Rectangle = tuple[int, int, int, int]


def intersection(first: Rectangle, second: Rectangle) -> Rectangle | None:
    """Return the positive-area intersection of two rectangles."""
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    if left >= right or top >= bottom:
        return None
    return (left, top, right, bottom)


def intersection_area(first: Rectangle, second: Rectangle) -> int:
    overlap = intersection(first, second)
    if overlap is None:
        return 0
    return (overlap[2] - overlap[0]) * (overlap[3] - overlap[1])


def subtract_rectangle(source: Rectangle, covering: Rectangle) -> list[Rectangle]:
    """Return non-overlapping pieces of ``source`` not covered by ``covering``."""
    overlap = intersection(source, covering)
    if overlap is None:
        return [source]

    left, top, right, bottom = source
    overlap_left, overlap_top, overlap_right, overlap_bottom = overlap
    pieces = [
        (left, top, right, overlap_top),
        (left, overlap_bottom, right, bottom),
        (left, overlap_top, overlap_left, overlap_bottom),
        (overlap_right, overlap_top, right, overlap_bottom),
    ]
    return [
        piece
        for piece in pieces
        if piece[0] < piece[2] and piece[1] < piece[3]
    ]


def visible_regions(
    source: Rectangle,
    foreground_rectangles: tuple[Rectangle, ...],
) -> tuple[Rectangle, ...]:
    """Return portions of ``source`` not hidden by foreground windows."""
    regions = [source]
    for covering in foreground_rectangles:
        next_regions: list[Rectangle] = []
        for region in regions:
            next_regions.extend(subtract_rectangle(region, covering))
        regions = next_regions
        if not regions:
            break
    return tuple(regions)
