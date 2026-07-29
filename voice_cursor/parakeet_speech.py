"""Low-latency microphone recognition using the installed MacParakeet model."""

from __future__ import annotations

import json
import math
import os
import queue
import select
import subprocess
import sys
import tempfile
import wave
from array import array
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

from .speech import InputDeviceConfig, input_device_candidates

StatusCallback = Callable[[str], None]
TextCallback = Callable[[str], None]


def default_helper_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "parakeet_helper"
        / "bin"
        / "voice-cursor-parakeet"
    )


def pcm16_rms(audio: bytes) -> float:
    """Return the RMS level of little-endian signed 16-bit PCM."""
    samples = array("h")
    samples.frombytes(audio)
    if not samples:
        return 0.0
    if os.sys.byteorder != "little":
        samples.byteswap()
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


@dataclass
class UtteranceSegmenter:
    """Split continuous PCM into phrases using an adaptive energy threshold."""

    sample_rate: int
    silence_seconds: float = 0.7
    minimum_seconds: float = 0.3
    maximum_seconds: float = 8.0
    calibration_seconds: float = 0.8

    def __post_init__(self) -> None:
        self.noise_floor = 180.0
        self.calibration_samples = 0
        self.active = False
        self.speech_samples = 0
        self.silence_samples = 0
        self.chunks: list[bytes] = []
        self.pre_roll: deque[bytes] = deque()
        self.pre_roll_samples = 0

    @property
    def calibrated(self) -> bool:
        return self.calibration_samples >= int(
            self.calibration_seconds * self.sample_rate
        )

    @property
    def threshold(self) -> float:
        return max(420.0, self.noise_floor * 3.2)

    def feed(self, audio: bytes) -> bytes | None:
        frame_count = len(audio) // 2
        if frame_count < 1:
            return None
        level = pcm16_rms(audio)

        if not self.calibrated:
            self._update_noise(level, weight=0.12)
            self.calibration_samples += frame_count
            return None

        is_speech = level >= self.threshold
        if not self.active:
            if not is_speech:
                self._update_noise(level, weight=0.025)
                self._append_pre_roll(audio, frame_count)
                return None
            self.active = True
            self.chunks = [*self.pre_roll, audio]
            self.speech_samples = self.pre_roll_samples + frame_count
            self.silence_samples = 0
            self.pre_roll.clear()
            self.pre_roll_samples = 0
            return None

        self.chunks.append(audio)
        self.speech_samples += frame_count
        if is_speech:
            self.silence_samples = 0
        else:
            self.silence_samples += frame_count

        enough_audio = self.speech_samples >= int(
            self.minimum_seconds * self.sample_rate
        )
        ended = self.silence_samples >= int(
            self.silence_seconds * self.sample_rate
        )
        too_long = self.speech_samples >= int(
            self.maximum_seconds * self.sample_rate
        )
        if enough_audio and (ended or too_long):
            utterance = b"".join(self.chunks)
            self._reset_after_utterance()
            return utterance
        return None

    def _append_pre_roll(self, audio: bytes, frame_count: int) -> None:
        self.pre_roll.append(audio)
        self.pre_roll_samples += frame_count
        maximum = int(0.25 * self.sample_rate)
        while self.pre_roll and self.pre_roll_samples > maximum:
            removed = self.pre_roll.popleft()
            self.pre_roll_samples -= len(removed) // 2

    def _update_noise(self, level: float, *, weight: float) -> None:
        self.noise_floor = (1.0 - weight) * self.noise_floor + weight * level

    def _reset_after_utterance(self) -> None:
        self.active = False
        self.speech_samples = 0
        self.silence_samples = 0
        self.chunks = []
        self.pre_roll.clear()
        self.pre_roll_samples = 0


class ParakeetHelper:
    """Keep FluidAudio and Parakeet loaded in one long-running Swift process."""

    def __init__(self, helper_path: Path | None = None):
        self.helper_path = Path(helper_path or default_helper_path())
        self.process: subprocess.Popen[str] | None = None

    def start(self, *, timeout: float = 60.0) -> None:
        if not self.helper_path.is_file():
            raise RuntimeError(
                f"Compiled Parakeet helper was not found at {self.helper_path}"
            )
        environment = os.environ.copy()
        environment["MACPARAKEET_TELEMETRY"] = "0"
        environment["DO_NOT_TRACK"] = "1"
        self.process = subprocess.Popen(
            [str(self.helper_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=environment,
        )
        response = self._read_response(timeout)
        if response.get("type") != "ready":
            raise RuntimeError(response.get("message") or "Parakeet did not become ready")

    def transcribe(self, audio_path: Path, *, timeout: float = 15.0) -> str:
        process = self.process
        if (
            process is None
            or process.poll() is not None
            or process.stdin is None
        ):
            raise RuntimeError("The Parakeet helper is not running")
        process.stdin.write(f"{audio_path}\n")
        process.stdin.flush()
        response = self._read_response(timeout)
        if response.get("type") == "error":
            raise RuntimeError(response.get("message") or "Parakeet failed")
        if response.get("type") != "result":
            raise RuntimeError("Parakeet returned an invalid response")
        return str(response.get("text") or "").strip()

    def close(self) -> None:
        process = self.process
        self.process = None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def _read_response(self, timeout: float) -> dict:
        process = self.process
        if process is None or process.stdout is None:
            raise RuntimeError("The Parakeet helper is not running")
        readable, _, _ = select.select([process.stdout], [], [], timeout)
        if not readable:
            raise RuntimeError("Parakeet recognition timed out")
        line = process.stdout.readline()
        if not line:
            raise RuntimeError("The Parakeet helper stopped unexpectedly")
        try:
            return json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Parakeet returned unreadable output") from exc


class ParakeetMicrophoneListener:
    """Recognize completed microphone utterances with a warm Parakeet model."""

    def __init__(
        self,
        *,
        device: int | str | None = None,
        helper_path: Path | None = None,
    ):
        self.device = device
        self.helper = ParakeetHelper(helper_path)

    def run(
        self,
        *,
        stop_event: Event,
        on_result: TextCallback,
        on_partial: TextCallback,
        on_status: StatusCallback,
    ) -> None:
        import sounddevice as sd

        on_status("Loading MacParakeet model once (first start takes about 20s)…")
        self.helper.start()
        try:
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
                            config=config,
                            stop_event=stop_event,
                            on_result=on_result,
                            on_status=on_status,
                        )
                        if stop_event.is_set():
                            return
                    except Exception as exc:
                        on_status(
                            f'Microphone "{config.name}" failed: {exc}. '
                            "Trying another input…"
                        )
                if not stop_event.is_set():
                    stop_event.wait(1.0)
        finally:
            self.helper.close()

    def _listen_on_device(
        self,
        *,
        sd,
        config: InputDeviceConfig,
        stop_event: Event,
        on_result: TextCallback,
        on_status: StatusCallback,
    ) -> None:
        if sys.platform == "darwin":
            self._listen_with_isolated_worker(
                config=config,
                stop_event=stop_event,
                on_result=on_result,
                on_status=on_status,
            )
            return

        audio_queue: queue.Queue[bytes] = queue.Queue(maxsize=120)
        segmenter = UtteranceSegmenter(config.sample_rate)

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
                f'Calibrating background noise on "{config.name}"—stay quiet briefly'
            )
            announced_ready = False
            while not stop_event.is_set():
                try:
                    audio = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                utterance = segmenter.feed(audio)
                if segmenter.calibrated and not announced_ready:
                    announced_ready = True
                    on_status(
                        f'Listening with MacParakeet on "{config.name}" '
                        f"at {config.sample_rate / 1000:g} kHz"
                    )
                if utterance is None:
                    continue

                on_status("Recognizing with MacParakeet…")
                text = self._transcribe_pcm(utterance, config.sample_rate)
                if text:
                    on_result(text)
                while True:
                    try:
                        audio_queue.get_nowait()
                    except queue.Empty:
                        break
                on_status(
                    f'Listening with MacParakeet on "{config.name}" '
                    f"at {config.sample_rate / 1000:g} kHz"
                )

    def _listen_with_isolated_worker(
        self,
        *,
        config: InputDeviceConfig,
        stop_event: Event,
        on_result: TextCallback,
        on_status: StatusCallback,
    ) -> None:
        """Read PCM from a child process so native CoreAudio aborts are contained."""
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "voice_cursor.microphone_worker",
                "--device-index",
                str(config.index),
                "--sample-rate",
                str(config.sample_rate),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        segmenter = UtteranceSegmenter(config.sample_rate)
        announced_ready = False
        pending = b""
        on_status(
            f'Calibrating background noise on "{config.name}"—stay quiet briefly'
        )
        try:
            if process.stdout is None:
                raise RuntimeError("The isolated microphone worker has no audio pipe")
            descriptor = process.stdout.fileno()
            while not stop_event.is_set():
                readable, _, _ = select.select([descriptor], [], [], 0.2)
                if not readable:
                    if process.poll() is not None:
                        raise RuntimeError(self._microphone_worker_error(process))
                    continue

                audio = os.read(descriptor, 16_384)
                if not audio:
                    raise RuntimeError(self._microphone_worker_error(process))
                audio = pending + audio
                even_length = len(audio) - (len(audio) % 2)
                pending = audio[even_length:]
                audio = audio[:even_length]
                if not audio:
                    continue

                utterance = segmenter.feed(audio)
                if segmenter.calibrated and not announced_ready:
                    announced_ready = True
                    on_status(
                        f'Listening with MacParakeet on "{config.name}" '
                        f"at {config.sample_rate / 1000:g} kHz"
                    )
                if utterance is None:
                    continue

                on_status("Recognizing with MacParakeet…")
                text = self._transcribe_pcm(utterance, config.sample_rate)
                if text:
                    on_result(text)
                self._drain_microphone_pipe(descriptor)
                on_status(
                    f'Listening with MacParakeet on "{config.name}" '
                    f"at {config.sample_rate / 1000:g} kHz"
                )
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)

    @staticmethod
    def _drain_microphone_pipe(descriptor: int) -> None:
        for _ in range(32):
            readable, _, _ = select.select([descriptor], [], [], 0)
            if not readable:
                return
            if not os.read(descriptor, 16_384):
                return

    @staticmethod
    def _microphone_worker_error(process: subprocess.Popen[bytes]) -> str:
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            return "isolated microphone worker stopped sending audio"
        detail = ""
        if process.stderr is not None:
            try:
                detail = process.stderr.read().decode(
                    "utf-8",
                    errors="replace",
                ).strip()
            except Exception:
                detail = ""
        if detail:
            last_line = detail.splitlines()[-1]
            return f"isolated microphone worker stopped: {last_line}"
        return (
            "isolated microphone worker stopped unexpectedly"
            if process.returncode in (None, 0)
            else f"isolated microphone worker exited with code {process.returncode}"
        )

    def _transcribe_pcm(self, audio: bytes, sample_rate: int) -> str:
        path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix="voice-cursor-parakeet-",
                suffix=".wav",
                delete=False,
            ) as temporary:
                path = Path(temporary.name)
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(sample_rate)
                output.writeframes(audio)
            return self.helper.transcribe(path)
        finally:
            if path is not None:
                path.unlink(missing_ok=True)
