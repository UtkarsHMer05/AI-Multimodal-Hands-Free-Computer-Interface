"""Optional head- and eye-gaze-based pointer control."""

from __future__ import annotations

import json
import math
import os
import select
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock, Thread, current_thread
from types import ModuleType
from typing import Callable, Literal

from .macos_clicks import post_left_click_sequence
from .window_activation import activate_application_at_point

TrackingMode = Literal["head", "gaze"]
StatusCallback = Callable[[str], None]
ClickFeedbackCallback = Callable[[str, int, int], None]

FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)


def default_face_model_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / ".models"
        / "face_landmarker.task"
    )


def ensure_face_model(
    model_path: Path | None = None,
    *,
    on_status: StatusCallback | None = None,
) -> Path:
    path = Path(model_path or default_face_model_path())
    if path.is_file() and path.stat().st_size > 1_000_000:
        return path
    status = on_status or (lambda _message: None)
    status("Downloading the 3.6 MB MediaPipe face-landmark model once…")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        import certifi

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with tempfile.NamedTemporaryFile(
            prefix="face-landmarker-",
            suffix=".task",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            with urllib.request.urlopen(
                FACE_MODEL_URL,
                timeout=30,
                context=ssl_context,
            ) as response:
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
        if temporary_path.stat().st_size < 1_000_000:
            raise RuntimeError("The downloaded face model is incomplete")
        os.replace(temporary_path, path)
        return path
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


@dataclass
class RelativePointerMapper:
    """Map calibrated head/gaze signals to smooth joystick-like cursor motion."""

    mode: TrackingMode
    maximum_speed: float = 34.0
    smoothing: float = 0.32

    def __post_init__(self) -> None:
        self.neutral_x = 0.0
        self.neutral_y = 0.0
        self.filtered_x = 0.0
        self.filtered_y = 0.0
        self.filter_initialized = False
        self.calibration: list[tuple[float, float]] = []

    @property
    def calibrated(self) -> bool:
        return len(self.calibration) >= 24

    def reset(self) -> None:
        self.neutral_x = 0.0
        self.neutral_y = 0.0
        self.filtered_x = 0.0
        self.filtered_y = 0.0
        self.filter_initialized = False
        self.calibration.clear()

    def update(self, x: float, y: float) -> tuple[int, int] | None:
        if not self.calibrated:
            self.calibration.append((x, y))
            if self.calibrated:
                ordered_x = sorted(item[0] for item in self.calibration)
                ordered_y = sorted(item[1] for item in self.calibration)
                middle = len(self.calibration) // 2
                self.neutral_x = ordered_x[middle]
                self.neutral_y = ordered_y[middle]
            return None

        if not self.filter_initialized:
            self.filtered_x = x
            self.filtered_y = y
            self.filter_initialized = True
        else:
            self.filtered_x += self.smoothing * (x - self.filtered_x)
            self.filtered_y += self.smoothing * (y - self.filtered_y)

        dead_zone = 0.022 if self.mode == "head" else 0.035
        full_scale = 0.115 if self.mode == "head" else 0.18
        dx = self._velocity(self.filtered_x - self.neutral_x, dead_zone, full_scale)
        dy = self._velocity(self.filtered_y - self.neutral_y, dead_zone, full_scale)
        return dx, dy

    def _velocity(
        self,
        displacement: float,
        dead_zone: float,
        full_scale: float,
    ) -> int:
        magnitude = abs(displacement)
        if magnitude <= dead_zone:
            return 0
        strength = min(1.0, (magnitude - dead_zone) / (full_scale - dead_zone))
        speed = self.maximum_speed * math.pow(strength, 1.35)
        return round(math.copysign(speed, displacement))


@dataclass
class TongueGestureDetector:
    """Calibrate tongue appearance and turn deliberate gestures into clicks."""

    calibration_frames: int = 28
    sequence_timeout_seconds: float = 0.70
    minimum_gesture_seconds: float = 0.12

    def __post_init__(self) -> None:
        self.phase = "off"
        self.neutral_samples: list[tuple[float, ...]] = []
        self.tongue_samples: list[tuple[float, ...]] = []
        self.neutral_center: tuple[float, ...] | None = None
        self.tongue_center: tuple[float, ...] | None = None
        self.direction: tuple[float, ...] | None = None
        self.direction_norm = 0.0
        self.present_frames = 0
        self.absent_frames = 0
        self.gesture_started: float | None = None
        self.pending_taps = 0
        self.last_tap_at = 0.0
        self.cooldown_until = 0.0
        self.phase_ready_at = 0.0

    @property
    def calibrated(self) -> bool:
        return self.phase in {"arming", "ready"}

    @property
    def freeze_pointer(self) -> bool:
        return (
            self.phase in {"neutral", "tongue_wait", "tongue", "arming"}
            or self.gesture_started is not None
            or self.present_frames > 0
            or self.pending_taps > 0
        )

    def start_calibration(self) -> str:
        self.phase = "neutral"
        self.neutral_samples.clear()
        self.tongue_samples.clear()
        self._reset_gesture()
        self._reset_sequence()
        return "Calibration 1/2: close your mouth and look at the screen centre"

    def disable(self) -> None:
        self.phase = "off"
        self._reset_gesture()
        self._reset_sequence()

    def update(
        self,
        features: tuple[float, ...],
        *,
        now: float,
    ) -> tuple[str | None, str | None]:
        """Return `(click_action, status_message)` for one camera frame."""
        if self.phase == "off":
            return None, None
        if self.phase == "neutral":
            self.neutral_samples.append(features)
            if len(self.neutral_samples) >= self.calibration_frames:
                self.phase = "tongue_wait"
                self.phase_ready_at = now + 1.2
                return (
                    None,
                    "Calibration 2/2: now stick your tongue out and hold it steady",
                )
            return None, None
        if self.phase == "tongue_wait":
            if now < self.phase_ready_at:
                return None, None
            self.phase = "tongue"
        if self.phase == "tongue":
            self.tongue_samples.append(features)
            if len(self.tongue_samples) >= self.calibration_frames:
                if not self._finish_calibration():
                    self.phase = "off"
                    return (
                        None,
                        "Tongue calibration failed—use brighter front lighting "
                        "and try again",
                    )
                self.phase = "arming"
                self.absent_frames = 0
                return (
                    None,
                    "Calibration complete—retract your tongue to arm clicks",
                )
            return None, None

        likelihood = self._likelihood(features)
        if self.phase == "arming":
            if likelihood <= 0.38:
                self.absent_frames += 1
            else:
                self.absent_frames = 0
            if self.absent_frames >= 5:
                self.phase = "ready"
                self.absent_frames = 0
                return (
                    None,
                    "Tongue clicks active: 1 gesture = single, 2 = double, 3 = triple",
                )
            return None, None

        if likelihood >= 0.64:
            self.present_frames += 1
            self.absent_frames = 0
        elif likelihood <= 0.38:
            self.absent_frames += 1
            self.present_frames = 0

        if self.gesture_started is None:
            if now >= self.cooldown_until and self.present_frames >= 3:
                self.gesture_started = now
                return None, None
            if (
                self.pending_taps > 0
                and now - self.last_tap_at >= self.sequence_timeout_seconds
            ):
                return self._emit_sequence(now)
            return None, None

        duration = now - self.gesture_started
        if self.absent_frames < 3:
            return None, None

        if duration < self.minimum_gesture_seconds:
            self._reset_gesture()
            return None, "Tongue gesture was too brief and was ignored"

        self.pending_taps = min(3, self.pending_taps + 1)
        self.last_tap_at = now
        count = self.pending_taps
        self._reset_gesture()
        if count >= 3:
            return self._emit_sequence(now)
        return (
            None,
            f"Tongue gesture {count} detected—waiting briefly for another",
        )

    def _emit_sequence(self, now: float) -> tuple[str, str]:
        count = self.pending_taps
        action = {1: "single", 2: "double", 3: "triple"}[count]
        label = {1: "single-click", 2: "double-click", 3: "triple-click"}[count]
        self._reset_sequence()
        self.cooldown_until = now + 0.30
        return action, f"{count} tongue gesture{'s' if count != 1 else ''}: {label}"

    def _finish_calibration(self) -> bool:
        neutral = self._median_vector(self.neutral_samples)
        tongue = self._median_vector(self.tongue_samples)
        direction = tuple(
            tongue_value - neutral_value
            for neutral_value, tongue_value in zip(neutral, tongue)
        )
        norm = sum(value * value for value in direction)
        if math.sqrt(norm) < 0.035:
            return False
        self.neutral_center = neutral
        self.tongue_center = tongue
        self.direction = direction
        self.direction_norm = norm
        return True

    def _likelihood(self, features: tuple[float, ...]) -> float:
        neutral = self.neutral_center
        direction = self.direction
        if neutral is None or direction is None or self.direction_norm <= 0:
            return 0.0
        projection = sum(
            (value - base) * axis
            for value, base, axis in zip(features, neutral, direction)
        )
        return max(0.0, min(1.0, projection / self.direction_norm))

    @staticmethod
    def _median_vector(samples: list[tuple[float, ...]]) -> tuple[float, ...]:
        return tuple(
            sorted(sample[index] for sample in samples)[len(samples) // 2]
            for index in range(len(samples[0]))
        )

    def _reset_gesture(self) -> None:
        self.present_frames = 0
        self.absent_frames = 0
        self.gesture_started = None

    def _reset_sequence(self) -> None:
        self.pending_taps = 0
        self.last_tap_at = 0.0


class CameraPointerController:
    """Run camera inference out of process and apply its pointer movements."""

    def __init__(self, *, camera_index: int = 0):
        self.camera_index = camera_index
        self.mode: TrackingMode | None = None
        self._process: subprocess.Popen[str] | None = None
        self._thread: Thread | None = None
        self._stop_event = Event()
        self._lock = Lock()
        self._mapper: RelativePointerMapper | None = None
        self._on_status: StatusCallback = lambda _message: None
        self._on_tongue_status: StatusCallback = lambda _message: None
        self._on_click_feedback: ClickFeedbackCallback = (
            lambda _action, _x, _y: None
        )
        self._tongue = TongueGestureDetector()
        self._no_face_reported = False

    @property
    def running(self) -> bool:
        process = self._process
        return process is not None and process.poll() is None

    @property
    def tongue_calibrated(self) -> bool:
        return self._tongue.calibrated

    def start(
        self,
        mode: TrackingMode,
        *,
        on_status: StatusCallback,
        on_tongue_status: StatusCallback | None = None,
        on_click_feedback: ClickFeedbackCallback | None = None,
    ) -> None:
        if mode not in {"head", "gaze"}:
            raise ValueError(f"Unsupported camera-control mode: {mode}")
        self.stop()
        self.mode = mode
        self._on_status = on_status
        self._on_tongue_status = on_tongue_status or (lambda _message: None)
        self._on_click_feedback = on_click_feedback or (
            lambda _action, _x, _y: None
        )
        self._stop_event.clear()
        self._mapper = RelativePointerMapper(mode=mode)
        self._no_face_reported = False
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        if self._tongue.calibrated:
            self._tongue_status(
                (
                    "Tongue clicks active: 1 gesture = single, 2 = double, 3 = triple"
                    if self._tongue.phase == "ready"
                    else "Calibration saved—retract your tongue to arm clicks"
                )
            )

    def recalibrate(self) -> None:
        mapper = self._mapper
        if mapper is not None:
            mapper.reset()
            self._status("Recalibrating—look at the screen centre and stay still")

    def calibrate_tongue(self) -> None:
        if not self.running:
            raise RuntimeError("Start Head Tracking or Start Eye Gaze first")
        self._tongue_status(self._tongue.start_calibration())

    def disable_tongue(self) -> None:
        self._tongue.disable()
        self._tongue_status("Tongue clicks are off")

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
        thread = self._thread
        if (
            thread is not None
            and thread is not current_thread()
            and thread.is_alive()
        ):
            thread.join(timeout=3)
        self._thread = None
        self.mode = None

    def _run(self) -> None:
        try:
            model_path = ensure_face_model(on_status=self._status)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "voice_cursor.camera_worker",
                    "--model-path",
                    str(model_path),
                    "--camera-index",
                    str(self.camera_index),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
            with self._lock:
                self._process = process
            self._status("Starting the FaceTime camera and MediaPipe…")
            if process.stdout is None:
                raise RuntimeError("Camera worker output is unavailable")
            last_message = time.monotonic()
            while not self._stop_event.is_set():
                readable, _, _ = select.select([process.stdout], [], [], 0.5)
                if not readable:
                    if process.poll() is not None:
                        break
                    if time.monotonic() - last_message > 12:
                        raise RuntimeError(
                            "the camera returned no frames. Unlock the Mac, close "
                            "other camera apps, and allow Terminal under System "
                            "Settings → Privacy & Security → Camera"
                        )
                    continue
                line = process.stdout.readline()
                if not line:
                    break
                last_message = time.monotonic()
                self._handle_message(json.loads(line))
            if not self._stop_event.is_set() and process.poll() not in (None, 0):
                raise RuntimeError("The camera tracking worker stopped")
        except Exception as exc:
            if not self._stop_event.is_set():
                self._status(f"Camera control stopped: {exc}")
        finally:
            with self._lock:
                process = self._process
                self._process = None
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)

    def _handle_message(self, message: dict) -> None:
        message_type = message.get("type")
        if message_type == "ready":
            label = "head" if self.mode == "head" else "eye gaze"
            self._status(
                f"Calibrating {label} control—look at the screen centre and stay still"
            )
            return
        if message_type == "no_face":
            if not self._no_face_reported:
                self._no_face_reported = True
                self._status("No face detected—face the camera in even lighting")
            return
        if message_type == "error":
            raise RuntimeError(str(message.get("message") or "Camera error"))
        if message_type != "metrics":
            return

        self._no_face_reported = False
        mapper = self._mapper
        if mapper is None or self.mode is None:
            return
        features = tuple(float(value) for value in message["tongue_features"])
        tongue_action, tongue_status = self._tongue.update(
            features,
            now=time.monotonic(),
        )
        if tongue_status is not None:
            self._tongue_status(tongue_status)

        prefix = "head" if self.mode == "head" else "gaze"
        movement = mapper.update(
            float(message[f"{prefix}_x"]),
            float(message[f"{prefix}_y"]),
        )
        if movement is None:
            if mapper.calibrated:
                label = "Head" if self.mode == "head" else "Eye-gaze"
                self._status(
                    f"{label} control active • Recalibrate if the cursor drifts"
                )
            self._perform_tongue_action(tongue_action)
            return
        dx, dy = movement
        if self._tongue.freeze_pointer:
            dx = 0
            dy = 0
        try:
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0
            if dx != 0 or dy != 0:
                pyautogui.moveRel(dx, dy, duration=0)
            self._perform_tongue_action(tongue_action, automation=pyautogui)
        except Exception as exc:
            self._stop_event.set()
            raise RuntimeError(
                f"cursor movement failed ({exc}); camera control was stopped"
            ) from exc

    def _perform_tongue_action(self, action: str | None, *, automation=None) -> None:
        if action is None:
            return
        if automation is None:
            import pyautogui as automation

            automation.FAILSAFE = True
            automation.PAUSE = 0
        real_macos_automation = (
            isinstance(automation, ModuleType) and sys.platform == "darwin"
        )
        fixed_point = automation.position()
        if isinstance(automation, ModuleType):
            activation = activate_application_at_point(
                int(fixed_point.x),
                int(fixed_point.y),
            )
            if activation.changed:
                time.sleep(0.12)
        if action == "single":
            automation.click()
        elif action == "double":
            if real_macos_automation:
                post_left_click_sequence(
                    int(fixed_point.x),
                    int(fixed_point.y),
                    2,
                )
            else:
                automation.doubleClick(interval=0.12)
        elif action == "triple":
            if real_macos_automation:
                post_left_click_sequence(
                    int(fixed_point.x),
                    int(fixed_point.y),
                    3,
                )
            else:
                automation.click(clicks=3, interval=0.12)
        else:
            return
        try:
            final_point = automation.position()
            self._on_click_feedback(
                action,
                int(final_point.x),
                int(final_point.y),
            )
        except Exception:
            pass

    def _status(self, message: str) -> None:
        self._on_status(message)

    def _tongue_status(self, message: str) -> None:
        self._on_tongue_status(message)
