"""Offline Vosk model management and streaming microphone recognition."""

from __future__ import annotations

import json
import queue
import shutil
import ssl
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from .commands import (
    interpret_command,
    interpret_screen_text_action,
    recognition_phrases,
)

MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"

StatusCallback = Callable[[str], None]
TextCallback = Callable[[str], None]


@dataclass(frozen=True)
class InputDeviceConfig:
    index: int
    name: str
    sample_rate: int


def default_model_root() -> Path:
    return Path(__file__).resolve().parent.parent / ".models"


def ensure_model(
    model_root: Path | None = None,
    *,
    on_status: StatusCallback | None = None,
) -> Path:
    """Return the local model path, downloading the 40 MB model if required."""
    root = Path(model_root) if model_root else default_model_root()
    model_path = root / MODEL_NAME
    if model_path.is_dir():
        return model_path

    status = on_status or (lambda _message: None)
    root.mkdir(parents=True, exist_ok=True)
    status("Downloading the speech model (about 40 MB)...")

    with tempfile.TemporaryDirectory(prefix="voice-cursor-model-") as temp_dir:
        archive = Path(temp_dir) / f"{MODEL_NAME}.zip"
        import certifi

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with (
            urllib.request.urlopen(MODEL_URL, context=ssl_context) as response,
            archive.open("wb") as archive_file,
        ):
            shutil.copyfileobj(response, archive_file)
        status("Extracting the speech model...")
        with zipfile.ZipFile(archive) as zipped:
            _safe_extract(zipped, root)

    if not model_path.is_dir():
        raise RuntimeError("The downloaded Vosk model did not contain the expected folder")

    status("Speech model is ready")
    return model_path


def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    """Extract an archive while rejecting path traversal."""
    destination = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if destination != target and destination not in target.parents:
            raise RuntimeError(f"Unsafe path in model archive: {member.filename}")
    archive.extractall(destination)


class VoskMicrophoneListener:
    """Continuously recognize speech and recover from macOS device failures."""

    def __init__(
        self,
        *,
        model_path: Path,
        device: int | str | None = None,
    ):
        self.model_path = Path(model_path)
        self.device = device

    def run(
        self,
        *,
        stop_event: Event,
        on_result: TextCallback,
        on_partial: TextCallback,
        on_status: StatusCallback,
    ) -> None:
        try:
            import sounddevice as sd
            from vosk import Model, SetLogLevel

            SetLogLevel(-1)
            on_status("Loading offline speech model...")
            model = Model(str(self.model_path))
            while not stop_event.is_set():
                candidates = input_device_candidates(sd, self.device)
                if not candidates:
                    on_status(
                        "No microphone input device is available; retrying in 1 second"
                    )
                    stop_event.wait(1.0)
                    continue

                for config in candidates:
                    if stop_event.is_set():
                        return
                    try:
                        self._listen_on_device(
                            sd=sd,
                            model=model,
                            config=config,
                            stop_event=stop_event,
                            on_result=on_result,
                            on_partial=on_partial,
                            on_status=on_status,
                        )
                        if stop_event.is_set():
                            return
                    except Exception as exc:
                        on_status(
                            f'Microphone "{config.name}" failed: {exc}. '
                            "Trying another input..."
                        )

                if not stop_event.is_set():
                    on_status(
                        "No microphone stream could stay open; retrying in 1 second"
                    )
                    stop_event.wait(1.0)
        except Exception as exc:
            on_status(f"Speech recognition stopped: {exc}")

    @staticmethod
    def _listen_on_device(
        *,
        sd,
        model,
        config: InputDeviceConfig,
        stop_event: Event,
        on_result: TextCallback,
        on_partial: TextCallback,
        on_status: StatusCallback,
    ) -> None:
        from vosk import KaldiRecognizer

        fixed_recognizer = KaldiRecognizer(
            model,
            config.sample_rate,
            json.dumps(recognition_phrases()),
        )
        free_recognizer = KaldiRecognizer(model, config.sample_rate)
        fixed_recognizer.SetWords(False)
        free_recognizer.SetWords(False)
        audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=60)

        def audio_callback(indata, _frames, _time, status) -> None:
            if status:
                on_status(f"Microphone status: {status}")
            try:
                audio_queue.put_nowait(bytes(indata))
            except queue.Full:
                pass

        with sd.RawInputStream(
            samplerate=config.sample_rate,
            blocksize=0,
            device=config.index,
            dtype="int16",
            channels=1,
            latency="high",
            callback=audio_callback,
        ):
            on_status(
                f'Listening on "{config.name}" at '
                f"{config.sample_rate / 1000:g} kHz"
            )
            while not stop_event.is_set():
                try:
                    audio = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                fixed_complete = fixed_recognizer.AcceptWaveform(audio)
                free_complete = free_recognizer.AcceptWaveform(audio)
                if fixed_complete or free_complete:
                    fixed_text = (
                        json.loads(fixed_recognizer.Result())
                        .get("text", "")
                        .strip()
                        if fixed_complete
                        else ""
                    )
                    free_text = (
                        json.loads(free_recognizer.Result()).get("text", "").strip()
                        if free_complete
                        else ""
                    )
                    text = choose_recognition_text(fixed_text, free_text)
                    if text:
                        on_result(text)
                else:
                    free_partial = json.loads(
                        free_recognizer.PartialResult()
                    ).get("partial", "")
                    fixed_partial = json.loads(
                        fixed_recognizer.PartialResult()
                    ).get("partial", "")
                    partial = free_partial or fixed_partial
                    on_partial(partial)


def choose_recognition_text(fixed_text: str, free_text: str) -> str:
    """Prefer dynamic free speech, then a valid constrained core command."""
    if free_text and interpret_screen_text_action(free_text) is not None:
        return free_text
    if fixed_text and interpret_command(fixed_text) is not None:
        return fixed_text
    return free_text or fixed_text


def input_device_candidates(sd, requested: int | str | None) -> list[InputDeviceConfig]:
    """Return usable input devices, preferring the built-in Mac microphone."""
    devices = list(sd.query_devices())
    candidates = [
        InputDeviceConfig(
            index=index,
            name=str(device["name"]),
            sample_rate=int(device["default_samplerate"] or 48_000),
        )
        for index, device in enumerate(devices)
        if int(device["max_input_channels"]) > 0
    ]

    if requested is not None:
        requested_text = str(requested).strip()
        if requested_text.isdigit():
            requested_index = int(requested_text)
            return [item for item in candidates if item.index == requested_index]
        lowered = requested_text.lower()
        exact = [item for item in candidates if item.name.lower() == lowered]
        return exact or [item for item in candidates if lowered in item.name.lower()]

    try:
        default_index = int(sd.default.device[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        default_index = -1

    def priority(item: InputDeviceConfig) -> tuple[int, int]:
        name = item.name.lower()
        if "macbook" in name and "microphone" in name:
            return (0, item.index)
        if "built-in" in name and ("microphone" in name or "input" in name):
            return (0, item.index)
        if any(
            virtual in name
            for virtual in ("steam", "blackhole", "aggregate", "virtual")
        ):
            return (30, item.index)
        if item.index == default_index:
            return (10, item.index)
        return (20, item.index)

    return sorted(candidates, key=priority)


def install_model_to(custom_path: Path, source_path: Path) -> None:
    """Copy a prepared model to a custom location (used for manual setups)."""
    if custom_path.exists():
        raise FileExistsError(custom_path)
    shutil.copytree(source_path, custom_path)
