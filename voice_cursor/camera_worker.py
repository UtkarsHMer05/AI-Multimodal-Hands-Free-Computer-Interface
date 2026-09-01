"""Camera/MediaPipe worker for head and eye-gaze measurements."""

from __future__ import annotations

import argparse
import json
import sys
import time
import math
from pathlib import Path


def _mean_point(landmarks, indexes: tuple[int, ...]) -> tuple[float, float]:
    count = len(indexes)
    return (
        sum(float(landmarks[index].x) for index in indexes) / count,
        sum(float(landmarks[index].y) for index in indexes) / count,
    )


def _eye_ratio(
    landmarks,
    *,
    iris: tuple[int, ...],
    corners: tuple[int, int],
    lids: tuple[int, int],
) -> tuple[float, float]:
    iris_x, iris_y = _mean_point(landmarks, iris)
    left = min(float(landmarks[index].x) for index in corners)
    right = max(float(landmarks[index].x) for index in corners)
    top = min(float(landmarks[index].y) for index in lids)
    bottom = max(float(landmarks[index].y) for index in lids)
    return (
        (iris_x - left) / max(right - left, 1e-6),
        (iris_y - top) / max(bottom - top, 1e-6),
    )


def _point_distance(landmarks, first: int, second: int) -> float:
    dx = float(landmarks[first].x) - float(landmarks[second].x)
    dy = float(landmarks[first].y) - float(landmarks[second].y)
    return math.hypot(dx, dy)


def eye_openness(landmarks) -> float:
    """Return scale-independent openness averaged across both eyes."""
    right_width = max(_point_distance(landmarks, 33, 133), 1e-6)
    left_width = max(_point_distance(landmarks, 362, 263), 1e-6)
    right_gap = (
        _point_distance(landmarks, 159, 145)
        + _point_distance(landmarks, 158, 153)
    ) / (2.0 * right_width)
    left_gap = (
        _point_distance(landmarks, 386, 374)
        + _point_distance(landmarks, 385, 380)
    ) / (2.0 * left_width)
    return (right_gap + left_gap) / 2.0


def tongue_features(rgb_frame, landmarks) -> list[float]:
    """Measure calibrated tongue evidence inside and below the mouth region."""
    import numpy as np

    height, width = rgb_frame.shape[:2]
    left_corner = landmarks[61]
    right_corner = landmarks[291]
    upper_inner = landmarks[13]
    lower_inner = landmarks[14]
    lower_outer = landmarks[17]

    left = min(float(left_corner.x), float(right_corner.x))
    right = max(float(left_corner.x), float(right_corner.x))
    mouth_width = max((right - left) * width, 4.0)
    horizontal_padding = 0.12 * mouth_width
    x1 = max(0, round(left * width + horizontal_padding))
    x2 = min(width, round(right * width - horizontal_padding))
    upper_y = min(float(upper_inner.y), float(lower_inner.y)) * height
    lower_y = max(float(lower_inner.y), float(lower_outer.y)) * height
    y1 = max(0, round(upper_y))
    y2 = min(height, round(lower_y + 0.48 * mouth_width))
    if x2 - x1 < 3 or y2 - y1 < 3:
        return [0.0] * 5

    pixels = rgb_frame[y1:y2, x1:x2].astype(np.float32)
    red = pixels[:, :, 0]
    green = pixels[:, :, 1]
    blue = pixels[:, :, 2]
    maximum = np.maximum(np.maximum(red, green), blue)
    minimum = np.minimum(np.minimum(red, green), blue)
    saturation = (maximum - minimum) / np.maximum(maximum, 1.0)
    redness = np.maximum(0.0, red - (green + blue) / 2.0) / 255.0
    valid = maximum > 35
    if not np.any(valid):
        return [0.0] * 5

    valid_redness = redness[valid]
    valid_saturation = saturation[valid]
    pink_fraction = np.mean(
        (valid_redness > 0.23) & (valid_saturation > 0.18)
    )
    mouth_open = abs(float(lower_inner.y) - float(upper_inner.y))
    mouth_open /= max(right - left, 1e-6)
    return [
        float(np.mean(valid_redness)),
        float(np.quantile(valid_redness, 0.80)),
        float(pink_fraction),
        float(np.mean(valid_saturation)),
        float(min(1.0, mouth_open)),
    ]


def measurements(landmarks) -> dict[str, float]:
    """Convert MediaPipe's mirrored face landmarks into stable control signals."""
    xs = [float(item.x) for item in landmarks]
    ys = [float(item.y) for item in landmarks]
    face_center_x = (min(xs) + max(xs)) / 2.0
    face_center_y = (min(ys) + max(ys)) / 2.0
    nose = landmarks[1]
    # Combining face translation with the nose position responds to both moving
    # the head sideways and turning the face toward a screen edge.
    head_x = (face_center_x + float(nose.x)) / 2.0
    head_y = (face_center_y + float(nose.y)) / 2.0

    right_eye = _eye_ratio(
        landmarks,
        iris=(468, 469, 470, 471, 472),
        corners=(33, 133),
        lids=(159, 145),
    )
    left_eye = _eye_ratio(
        landmarks,
        iris=(473, 474, 475, 476, 477),
        corners=(362, 263),
        lids=(386, 374),
    )
    return {
        "head_x": head_x,
        "head_y": head_y,
        "gaze_x": (right_eye[0] + left_eye[0]) / 2.0,
        "gaze_y": (right_eye[1] + left_eye[1]) / 2.0,
        "eye_openness": eye_openness(landmarks),
    }


def run(*, model_path: Path, camera_index: int) -> int:
    import cv2
    import mediapipe as mp

    capture = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture.set(cv2.CAP_PROP_FPS, 24)
    if not capture.isOpened():
        print(
            json.dumps(
                {
                    "type": "error",
                    "message": (
                        "The camera could not be opened. Allow Terminal under "
                        "System Settings → Privacy & Security → Camera."
                    ),
                }
            ),
            flush=True,
        )
        return 1

    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.55,
        min_face_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    started = time.monotonic()
    last_emitted = 0.0
    try:
        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
            print(json.dumps({"type": "ready"}), flush=True)
            while True:
                ok, frame = capture.read()
                if not ok:
                    print(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "The camera stopped returning video frames.",
                            }
                        ),
                        flush=True,
                    )
                    return 1

                now = time.monotonic()
                if now - last_emitted < 1.0 / 24.0:
                    continue
                last_emitted = now
                mirrored = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(mirrored, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp_ms = max(0, round((now - started) * 1_000))
                result = landmarker.detect_for_video(image, timestamp_ms)
                if not result.face_landmarks:
                    print(json.dumps({"type": "no_face"}), flush=True)
                    continue
                values = measurements(result.face_landmarks[0])
                values["tongue_features"] = tongue_features(
                    rgb,
                    result.face_landmarks[0],
                )
                print(
                    json.dumps({"type": "metrics", **values}, separators=(",", ":")),
                    flush=True,
                )
    except (BrokenPipeError, KeyboardInterrupt):
        return 0
    except Exception as exc:
        print(
            json.dumps({"type": "error", "message": str(exc)}),
            flush=True,
        )
        return 1
    finally:
        capture.release()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--camera-index", type=int, default=0)
    arguments = parser.parse_args()
    return run(
        model_path=arguments.model_path,
        camera_index=arguments.camera_index,
    )


if __name__ == "__main__":
    raise SystemExit(main())
