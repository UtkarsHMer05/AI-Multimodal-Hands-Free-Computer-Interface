"""Find ordinary visible words with a local whole-screen OCR fallback."""

from __future__ import annotations

import csv
import ctypes
import io
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .text_matching import normalize_target_text, target_comparison_key


class ScreenTextError(RuntimeError):
    """Raised when whole-screen OCR cannot be completed."""


@dataclass(frozen=True)
class ScreenTextMatch:
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int
    similarity: float = 1.0

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        return (
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.x + self.width // 2,
            self.y + self.height // 2,
        )


def normalize_screen_text(text: str) -> str:
    return normalize_target_text(text)


class ScreenTextLocator:
    """Capture the main display and locate exact visible text."""

    def __init__(self, *, minimum_confidence: float = 35.0):
        self.minimum_confidence = minimum_confidence

    def find(
        self,
        label: str,
        *,
        screen_width: int,
        screen_height: int,
        excluded_rectangles: tuple[tuple[int, int, int, int], ...] = (),
    ) -> list[ScreenTextMatch]:
        target = normalize_screen_text(label)
        if not target or len(target.split()) > 8:
            return []
        if not self._screen_capture_trusted():
            raise ScreenTextError(
                "Screen Recording permission is required for visual text search. "
                "Open System Settings → Privacy & Security → Screen & System "
                "Audio Recording, enable Terminal, then restart Voice Cursor."
            )
        tesseract = shutil.which("tesseract")
        if tesseract is None:
            raise ScreenTextError(
                "Tesseract OCR is not installed. Install it with "
                "'brew install tesseract'."
            )

        with tempfile.TemporaryDirectory(prefix="voice-cursor-screen-") as directory:
            screenshot = Path(directory) / "main-display.png"
            self._capture_main_display(screenshot)
            outputs = []
            last_error = ""
            for page_mode in ("11", "3", "6"):
                completed = subprocess.run(
                    [
                        tesseract,
                        str(screenshot),
                        "stdout",
                        "--psm",
                        page_mode,
                        "tsv",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if completed.returncode == 0:
                    outputs.append(completed.stdout)
                else:
                    last_error = completed.stderr.strip()

        candidates: list[ScreenTextMatch] = []
        for output in outputs:
            candidates.extend(
                self.matches_from_tsv(
                    output,
                    target,
                    screen_width=screen_width,
                    screen_height=screen_height,
                    minimum_confidence=self.minimum_confidence,
                    excluded_rectangles=excluded_rectangles,
                )
            )
        candidates = self._deduplicate(candidates)
        if candidates:
            candidates.sort(
                key=lambda item: (item.similarity, item.confidence),
                reverse=True,
            )
            best = candidates[0]
            return [
                item
                for item in candidates
                if best.similarity - item.similarity < 0.08
            ]
        if not outputs and last_error:
            raise ScreenTextError(f"Screen OCR failed: {last_error}")
        return []

    @staticmethod
    def is_desktop_point(x: int, y: int) -> bool:
        """Return true when a point is not covered by an app window."""
        try:
            import Quartz

            options = (
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements
            )
            windows = Quartz.CGWindowListCopyWindowInfo(
                options,
                Quartz.kCGNullWindowID,
            )
            for window in windows or []:
                layer = int(window.get(Quartz.kCGWindowLayer, -1))
                alpha = float(window.get(Quartz.kCGWindowAlpha, 1.0))
                bounds = window.get(Quartz.kCGWindowBounds, {})
                left = float(bounds.get("X", 0))
                top = float(bounds.get("Y", 0))
                right = left + float(bounds.get("Width", 0))
                bottom = top + float(bounds.get("Height", 0))
                if (
                    0 <= layer <= 19
                    and alpha > 0
                    and left <= x <= right
                    and top <= y <= bottom
                ):
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def matches_from_tsv(
        tsv_text: str,
        label: str,
        *,
        screen_width: int,
        screen_height: int,
        minimum_confidence: float = 35.0,
        excluded_rectangles: tuple[tuple[int, int, int, int], ...] = (),
    ) -> list[ScreenTextMatch]:
        rows = list(csv.DictReader(io.StringIO(tsv_text), delimiter="\t"))
        page = next((row for row in rows if row.get("level") == "1"), None)
        if page is None:
            raise ScreenTextError("OCR did not return screen dimensions.")
        try:
            image_width = int(page["width"])
            image_height = int(page["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ScreenTextError("OCR returned invalid screen dimensions.") from exc
        if image_width < 1 or image_height < 1:
            raise ScreenTextError("The captured screen has invalid dimensions.")

        scale_x = screen_width / image_width
        scale_y = screen_height / image_height
        target = normalize_screen_text(label)
        target_key = target_comparison_key(target)
        matches: list[ScreenTextMatch] = []
        lines: dict[tuple[str, str, str, str], list[dict[str, object]]] = {}

        for row in rows:
            if row.get("level") != "5":
                continue
            word = normalize_screen_text(row.get("text", ""))
            try:
                confidence = float(row["conf"])
                left = int(row["left"])
                top = int(row["top"])
                width = int(row["width"])
                height = int(row["height"])
            except (KeyError, TypeError, ValueError):
                continue
            if not word or width < 1 or height < 1:
                continue
            key = (
                row.get("page_num", ""),
                row.get("block_num", ""),
                row.get("par_num", ""),
                row.get("line_num", ""),
            )
            lines.setdefault(key, []).append(
                {
                    "normalized": word,
                    "original": row.get("text", ""),
                    "confidence": confidence,
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height,
                }
            )

        for words in lines.values():
            # OCR may split one visual word into several tokens ("back end")
            # or combine several spoken words into one token ("backend").
            # Compare every short consecutive group using the same
            # whitespace-insensitive key used for accessibility controls.
            for count in range(1, min(8, len(words)) + 1):
                for index in range(0, len(words) - count + 1):
                    group = words[index : index + count]
                    candidate = " ".join(
                        str(word["normalized"]) for word in group
                    )
                    if target_comparison_key(candidate) != target_key:
                        continue
                    confidence = (
                        sum(float(word["confidence"]) for word in group) / count
                    )
                    if confidence < minimum_confidence:
                        continue
                    left = min(int(word["left"]) for word in group)
                    top = min(int(word["top"]) for word in group)
                    right = max(
                        int(word["left"]) + int(word["width"])
                        for word in group
                    )
                    bottom = max(
                        int(word["top"]) + int(word["height"])
                        for word in group
                    )
                    x = round(((left + right) / 2) * scale_x)
                    y = round(((top + bottom) / 2) * scale_y)
                    logical_width = max(1, round((right - left) * scale_x))
                    logical_height = max(1, round((bottom - top) * scale_y))
                    bounds = (
                        x - logical_width // 2,
                        y - logical_height // 2,
                        x + logical_width // 2,
                        y + logical_height // 2,
                    )
                    if any(
                        ScreenTextLocator._rectangles_intersect(bounds, excluded)
                        for excluded in excluded_rectangles
                    ):
                        continue
                    matches.append(
                        ScreenTextMatch(
                            text=" ".join(
                                str(word["original"]) for word in group
                            ),
                            confidence=confidence,
                            x=x,
                            y=y,
                            width=logical_width,
                            height=logical_height,
                            similarity=1.0,
                        )
                    )
        return matches

    @staticmethod
    def _rectangles_intersect(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> bool:
        return not (
            first[2] < second[0]
            or first[0] > second[2]
            or first[3] < second[1]
            or first[1] > second[3]
        )

    @staticmethod
    def _deduplicate(matches: list[ScreenTextMatch]) -> list[ScreenTextMatch]:
        result: list[ScreenTextMatch] = []
        for match in sorted(
            matches,
            key=lambda item: (item.similarity, item.confidence),
            reverse=True,
        ):
            if any(
                target_comparison_key(existing.text)
                == target_comparison_key(match.text)
                and abs(existing.x - match.x) <= 8
                and abs(existing.y - match.y) <= 8
                for existing in result
            ):
                continue
            result.append(match)
        return result

    @staticmethod
    def _capture_main_display(output_path: Path) -> None:
        completed = subprocess.run(
            ["/usr/sbin/screencapture", "-x", "-D", "1", str(output_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0 or not output_path.is_file():
            detail = completed.stderr.strip() or "no screenshot was produced"
            raise ScreenTextError(f"Screen capture failed: {detail}")

    @staticmethod
    def _screen_capture_trusted() -> bool:
        try:
            core_graphics = ctypes.CDLL(
                "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
            )
            preflight = core_graphics.CGPreflightScreenCaptureAccess
            preflight.restype = ctypes.c_bool
            preflight.argtypes = []
            return bool(preflight())
        except (AttributeError, OSError):
            return True
