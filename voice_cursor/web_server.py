"""Local web dashboard for the Voice Cursor engine.

Serves the built website (website/out) and exposes a WebSocket bridge that
drives the same engine the Tk application uses:

- ActionExecutor       -> guarded real cursor actions on this Mac
- CameraController     -> MediaPipe head / eye-gaze / tongue / blink pipeline
- Parakeet/Vosk        -> the same continuous offline listener as the app
- interpret_command    -> the identical grammar dispatch used by the app

The browser page at /dashboard connects to ws://localhost:8757/bridge and
becomes a full remote control surface for the running engine. Everything
stays on this machine: no audio, video, or transcripts ever leave localhost.

Run:  python -m voice_cursor.web_server   (or ./run_website.command)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import struct
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable

import websockets

from voice_cursor.actions import ActionExecutor
from voice_cursor.camera_control import CameraPointerController
from voice_cursor.commands import (
    CommandName,
    interpret_command,
    interpret_screen_text_action,
)
from voice_cursor.parakeet_speech import ParakeetMicrophoneListener
from voice_cursor.speech import VoskMicrophoneListener


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "website" / "out"
VOICE_CURSOR_WINDOW_TITLE = "Voice Cursor Web Dashboard"
PORT = 8757


class EngineEvent:
    """A single engine event pushed to every connected dashboard client."""

    def __init__(self, kind: str, data: dict[str, Any] | None = None):
        self.kind = kind
        self.data = data or {}


class DashboardEngine:
    """Owns the real engine and broadcasts events to dashboard clients."""

    def __init__(self, *, dry_run: bool, speech_engine: str, movement_pixels: int):
        self.dry_run = dry_run
        self.speech_engine = speech_engine
        self.movement_pixels = movement_pixels
        self.lock = threading.Lock()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.clients: set = set()
        self.stop_event = threading.Event()
        self.listener_thread: threading.Thread | None = None
        self.executor = ActionExecutor(
            dry_run=dry_run,
            movement_pixels=movement_pixels,
            start_enabled=False,
            on_click_feedback=lambda action, x, y: self.broadcast(
                EngineEvent("click_feedback", {"action": action, "x": x, "y": y})
            ),
        )
        self.camera = CameraPointerController()
        self.transcript = ""
        self.feedback = "Control is paused. Say “resume control” or press Enable."
        self.logs: list[tuple[str, str]] = []
        self.status = "Idle"

    # ------------------------------------------------------------------ bus
    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def broadcast(self, event: EngineEvent) -> None:
        """Thread-safe broadcast; callable from engine threads."""
        loop = self.loop
        if loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._push(event), loop)

    async def _push(self, event: EngineEvent) -> None:
        if not self.clients:
            return
        message = json.dumps({"kind": event.kind, **event.data})
        dead = []
        for client in list(self.clients):
            try:
                await client.send(message)
            except Exception:
                dead.append(client)
        for client in dead:
            self.clients.discard(client)

    def emit(self, kind: str, **data: Any) -> None:
        self.broadcast(EngineEvent(kind, data))

    # --------------------------------------------------------------- engine
    def push_log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        with self.lock:
            self.logs.append((stamp, message))
            self.logs = self.logs[-200:]
        self.emit("log", time=stamp, message=message)

    def set_feedback(self, message: str) -> None:
        self.feedback = message
        self.emit("feedback", message=message)

    def set_status(self, message: str) -> None:
        self.status = message
        self.emit("status", message=message)

    def set_transcript(self, text: str) -> None:
        self.transcript = text
        self.emit("transcript", text=text)

    def handle_text(self, text: str) -> None:
        """The same dispatch as app.py _handle_recognized_text."""
        self.set_transcript(text)
        screen_action = interpret_screen_text_action(text)
        if screen_action is not None:
            self.set_feedback(
                f'Finding a button or visible text named "{screen_action.label}"…'
            )
            self.push_log(
                "Searching interactive controls, then the visible screen"
            )
            result = self.executor.execute_screen_text(screen_action)
            self.finish_action(text, f"{screen_action.kind.value}:{screen_action.label}", result)
            return
        command = interpret_command(text)
        if command is None:
            self.set_feedback(f'Not a supported command: "{text}"')
            self.push_log(f'Unrecognized: "{text}"')
            self.record_session(text, "", "unrecognized")
            return
        result = self.executor.execute(command)
        self.set_feedback(result.message)
        self.emit("paused", paused=self.executor.paused)
        self.finish_action(text, command.name.value, result)

    def finish_action(self, text: str, command_name: str, result) -> None:
        result_name = "success" if result.success else "ignored/error"
        self.record_session(text, command_name, result_name)
        self.push_log(f"{command_name}: {result.message}")
        self.set_feedback(result.message)

    def record_session(self, text: str, command: str, result: str) -> None:
        self.emit("session", text=text, command=command, result=result)

    # --------------------------------------------------------------- speech
    def start_listener(self) -> None:
        if self.listener_thread is not None and self.listener_thread.is_alive():
            return
        self.stop_event.clear()
        self.listener_thread = threading.Thread(
            target=self._listener_worker, daemon=True
        )
        self.listener_thread.start()

    def stop_listener(self) -> None:
        self.stop_event.set()
        self.listener_thread = None

    def _listener_worker(self) -> None:
        engine = self.speech_engine
        started = False
        if engine in {"auto", "parakeet"}:
            from voice_cursor.parakeet_speech import default_helper_path

            if default_helper_path().is_file():
                try:
                    listener = ParakeetMicrophoneListener(device=None)
                    listener.run(
                        stop_event=self.stop_event,
                        on_result=self.handle_text,
                        on_partial=lambda _text: None,
                        on_status=self.set_status,
                    )
                    started = True
                except Exception as exc:
                    if self.stop_event.is_set():
                        return
                    self.set_status(f"MacParakeet unavailable ({exc}); falling back to Vosk…")
        if not started and not self.stop_event.is_set():
            try:
                from voice_cursor.speech import ensure_model

                model_path = ensure_model(on_status=self.set_status)
                listener = VoskMicrophoneListener(model_path=model_path, device=None)
                listener.run(
                    stop_event=self.stop_event,
                    on_result=self.handle_text,
                    on_partial=lambda _text: None,
                    on_status=self.set_status,
                )
            except Exception as exc:
                if not self.stop_event.is_set():
                    self.set_status(f"Speech listener stopped: {exc}")

    # --------------------------------------------------------------- camera
    def start_camera(self, mode: str) -> None:
        if self.dry_run:
            self.emit("camera_status", message="Camera pointer control is disabled in dry-run mode.")
            return
        if self.executor.paused:
            self.emit(
                "camera_status",
                message="Enable live control before starting camera pointer movement.",
            )
            return
        label = "head tracking" if mode == "head" else "eye-gaze tracking"
        self.set_camera_status(f"Starting {label}…")
        self.camera.start(
            mode,
            on_status=lambda m: self.emit("camera_status", message=m),
            on_tongue_status=lambda m: self.emit("tongue_status", message=m),
            on_blink_status=lambda m: self.emit("blink_status", message=m),
            on_click_feedback=self._camera_click,
        )
        self.push_log(f"Starting {label}; move the pointer to a screen corner to stop safely")

    def _camera_click(self, action: str, x: int, y: int) -> None:
        self.emit("click_feedback", action=action, x=x, y=y)

    def stop_camera(self) -> None:
        self.camera.stop()
        self.set_camera_status("Camera control is off")

    def set_camera_status(self, message: str) -> None:
        self.emit("camera_status", message=message)

    def calibrate_tongue(self) -> None:
        try:
            self.camera.calibrate_tongue()
            self.emit("tongue_status", message="Tongue calibration started—follow the phases")
        except RuntimeError as exc:
            self.emit("tongue_status", message=str(exc))

    def disable_tongue(self) -> None:
        self.camera.disable_tongue()
        self.emit("tongue_status", message="Tongue clicks are off")

    def calibrate_blink(self) -> None:
        try:
            self.camera.calibrate_blink()
            self.emit("blink_status", message="Blink calibration started—follow the phases")
        except RuntimeError as exc:
            self.emit("blink_status", message=str(exc))

    def disable_blink(self) -> None:
        self.camera.disable_blink()
        self.emit("blink_status", message="Blink clicks are off")

    # -------------------------------------------------------------- actions
    def enable(self) -> None:
        command = interpret_command("resume control")
        assert command is not None
        result = self.executor.execute(command)
        self.set_feedback(result.message)
        self.emit("paused", paused=self.executor.paused)
        self.push_log(result.message)

    def pause(self) -> None:
        if self.camera.running:
            self.stop_camera()
        command = interpret_command("pause control")
        assert command is not None
        result = self.executor.execute(command)
        self.set_feedback(result.message)
        self.emit("paused", paused=self.executor.paused)
        self.push_log(result.message)

    def snapshot(self) -> dict[str, Any]:
        return {
            "kind": "snapshot",
            "paused": self.executor.paused,
            "listening": self.listener_thread is not None
            and self.listener_thread.is_alive(),
            "camera_running": self.camera.running,
            "camera_mode": self.camera.mode,
            "tongue_calibrated": self.camera.tongue_calibrated,
            "blink_calibrated": self.camera.blink_calibrated,
            "transcript": self.transcript,
            "feedback": self.feedback,
            "status": self.status,
            "logs": self.logs[-40:],
        }


# ---------------------------------------------------------------------------
# WebSocket protocol
# ---------------------------------------------------------------------------

# Module-level engine reference: the single dashboard server per process.
_engine: DashboardEngine | None = None


def get_engine() -> DashboardEngine:
    assert _engine is not None, "engine not initialized"
    return _engine


async def bridge_handler(websocket) -> None:
    engine = get_engine()
    engine.clients.add(websocket)
    try:
        await websocket.send(json.dumps(engine.snapshot()))
        async for raw in websocket:
            try:
                message = json.loads(raw)
            except (TypeError, ValueError):
                continue
            kind = message.get("kind")
            if kind == "text":
                engine.handle_text(str(message.get("text", "")))
            elif kind == "enable":
                engine.enable()
            elif kind == "pause":
                engine.pause()
            elif kind == "listen_start":
                engine.start_listener()
                engine.emit("listening", listening=True)
                engine.set_status("Listening…")
            elif kind == "listen_stop":
                engine.stop_listener()
                engine.emit("listening", listening=False)
                engine.set_status("Listener stopped")
            elif kind == "camera_start":
                engine.start_camera(str(message.get("mode", "head")))
                engine.emit("camera_running", running=engine.camera.running)
            elif kind == "camera_stop":
                engine.stop_camera()
                engine.emit("camera_running", running=False)
            elif kind == "camera_recalibrate":
                engine.camera.recalibrate()
            elif kind == "tongue_calibrate":
                engine.calibrate_tongue()
            elif kind == "tongue_disable":
                engine.disable_tongue()
            elif kind == "blink_calibrate":
                engine.calibrate_blink()
            elif kind == "blink_disable":
                engine.disable_blink()
            else:
                engine.push_log(f"Unknown bridge message: {kind}")
    except websockets.ConnectionClosed:
        pass
    finally:
        engine.clients.discard(websocket)
        # Safety parity: when the dashboard disconnects, voice control stops
        # but live-control state is preserved (pause/enabled unchanged).
        if not engine.clients and engine.listener_thread is not None:
            engine.stop_listener()
            engine.emit("listening", listening=False)


# ---------------------------------------------------------------------------
# Static file serving for website/out on the same port
# ---------------------------------------------------------------------------

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
    ".map": "application/json",
    ".json": "application/json",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}


def respond(status: int, body: bytes, content_type: str):
    from websockets.datastructures import Headers
    from websockets.http11 import Response

    headers = Headers(
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            (
                "Cache-Control",
                "no-store"
                if content_type.startswith("text/html")
                else "public, max-age=3600",
            ),
        ]
    )
    reason = {200: "OK", 403: "Forbidden", 404: "Not Found"}.get(status, "Error")
    return Response(status, reason, headers, body)


def serve_file(site_dir: Path, relative: str):
    target = (site_dir / relative).resolve()
    if not str(target).startswith(str(site_dir.resolve())) or not target.is_file():
        return respond(404, b"Not found", "text/plain")
    data = target.read_bytes()
    mime = MIME.get(target.suffix.lower(), "application/octet-stream")
    return respond(200, data, mime)


def make_process_request(site_dir: Path):
    async def process_request(connection, request):
        path = request.path
        if path.startswith("/bridge"):
            return None  # proceed with the WebSocket handshake
        clean = path.split("?", 1)[0].split("#", 1)[0].strip("/")
        if clean == "":
            return serve_file(site_dir, "index.html")
        if clean.endswith("/index.html"):
            clean = clean[: -len("index.html")].strip("/")
        target = (site_dir / clean).resolve()
        if not str(target).startswith(str(site_dir.resolve())):
            return respond(403, b"Forbidden", "text/plain")
        if target.is_file():
            return serve_file(site_dir, clean)
        if (target / "index.html").is_file():
            return serve_file(site_dir, f"{clean}/index.html")
        return respond(404, b"Not found", "text/plain")

    return process_request


async def main_async(args: argparse.Namespace) -> None:
    global _engine
    site_dir = Path(args.site_dir).resolve()
    if not (site_dir / "index.html").is_file():
        raise SystemExit(
            f"Website build not found at {site_dir}. Run: cd website && npm run build"
        )
    engine = DashboardEngine(
        dry_run=args.dry_run,
        speech_engine=args.speech_engine,
        movement_pixels=args.movement_pixels,
    )
    _engine = engine
    loop = asyncio.get_running_loop()
    engine.set_loop(loop)

    from websockets.asyncio.server import serve

    async with serve(
        bridge_handler,
        host=args.host,
        port=args.port,
        process_request=make_process_request(site_dir),
    ):
        url = f"http://localhost:{args.port}/"
        print(f"Voice Cursor dashboard: {url}")
        print("Press Ctrl+C to stop.")
        if args.open:
            webbrowser.open(f"{url}dashboard/")
        await asyncio.Future()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Voice Cursor web dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--site-dir", default=str(SITE))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--speech-engine", choices=("auto", "parakeet", "vosk"), default="auto")
    parser.add_argument("--movement-pixels", type=int, default=180)
    parser.add_argument("--open", action="store_true", help="Open the dashboard in the browser")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
