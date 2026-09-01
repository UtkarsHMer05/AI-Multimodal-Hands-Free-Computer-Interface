"""Tkinter application for the voice-controlled computer interface."""

from __future__ import annotations

import argparse
import csv
import os
import random
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    X,
    Button,
    Frame,
    Label,
    StringVar,
    Text,
    Tk,
)
from tkinter import messagebox

from .accessibility_controls import normalize_control_text
from .actions import ActionExecutor, ActionResult
from .camera_control import CameraPointerController
from .commands import (
    COMMANDS,
    CommandName,
    VoiceCommand,
    evaluation_commands,
    interpret_command,
    interpret_screen_text_action,
)
from .evaluation import EvaluationSession
from .parakeet_speech import ParakeetMicrophoneListener, default_helper_path
from .speech import VoskMicrophoneListener, ensure_model
from .text_matching import target_comparison_key
from .window_visibility import intersection_area, visible_regions


class VoiceCursorApp:
    EVALUATION_TIMEOUT_MS = 12_000

    def __init__(
        self,
        root: Tk,
        *,
        dry_run: bool,
        model_path: Path | None,
        movement_pixels: int,
        start_enabled: bool,
        input_device: int | str | None,
        speech_engine: str,
    ):
        self.root = root
        self.root.title("Voice Cursor HCI")
        self.root.geometry("820x760")
        self.root.minsize(720, 680)

        self.dry_run = dry_run
        self.executor = ActionExecutor(
            dry_run=dry_run,
            movement_pixels=movement_pixels,
            start_enabled=start_enabled and not dry_run,
            on_click_feedback=self._threadsafe_click_feedback,
        )
        self.model_path = model_path
        self.input_device = input_device
        self.speech_engine = speech_engine
        self.stop_event = threading.Event()
        self.evaluation: EvaluationSession | None = None
        self.evaluation_accepting_result = False
        self.evaluation_timeout_id: str | None = None
        self.screen_action_in_progress = False
        self.camera_controller = CameraPointerController()
        self.local_button_targets: list[
            tuple[Button, str, tuple[str, ...]]
        ] = []
        self.session_log = self._create_session_log()

        self.status_text = StringVar(value="Starting...")
        self.control_text = StringVar(
            value="ENABLED" if not self.executor.paused else "PAUSED"
        )
        self.transcript_text = StringVar(value="—")
        initial_feedback = (
            f"Live control is enabled. Direction commands move {movement_pixels} pixels."
            if not self.executor.paused
            else 'Say "resume control" or use the Enable button.'
        )
        self.feedback_text = StringVar(value=initial_feedback)
        self.evaluation_text = StringVar(value="Evaluation is not running")
        self.camera_status_text = StringVar(value="Camera control is off")
        self.tongue_status_text = StringVar(value="Tongue clicks are off")
        self.blink_status_text = StringVar(value="Blink clicks are off")

        self._build_interface(dry_run=dry_run, movement_pixels=movement_pixels)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._start_listener()

    def _build_interface(self, *, dry_run: bool, movement_pixels: int) -> None:
        heading = Label(
            self.root,
            text="AI-Based Voice and Camera-Controlled Computer Interface",
            font=("TkDefaultFont", 19, "bold"),
            pady=14,
        )
        heading.pack(fill=X)

        mode = "DRY RUN — no computer actions will occur" if dry_run else "LIVE CONTROL"
        Label(
            self.root,
            text=mode,
            fg="#8b1a1a" if not dry_run else "#225c2d",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(pady=(0, 10))

        status_frame = Frame(self.root, padx=18, pady=8)
        status_frame.pack(fill=X)
        Label(status_frame, text="Recognizer:", width=12, anchor="w").pack(side=LEFT)
        Label(status_frame, textvariable=self.status_text, anchor="w").pack(
            side=LEFT, fill=X, expand=True
        )

        control_frame = Frame(self.root, padx=18, pady=8)
        control_frame.pack(fill=X)
        Label(control_frame, text="Control:", width=12, anchor="w").pack(side=LEFT)
        self.control_label = Label(
            control_frame,
            textvariable=self.control_text,
            fg="#1f6b32" if not self.executor.paused else "#9b1c1c",
            font=("TkDefaultFont", 12, "bold"),
            anchor="w",
        )
        self.control_label.pack(side=LEFT)
        self._project_button(
            control_frame,
            text="Enable",
            command=self.enable_control,
        ).pack(
            side=LEFT, padx=(24, 6)
        )
        self._project_button(
            control_frame,
            text="Pause",
            command=self.pause_control,
        ).pack(side=LEFT)
        self._project_button(
            control_frame,
            text="Test Cursor",
            command=self.test_cursor_control,
            aliases=("cursor test",),
        ).pack(side=LEFT, padx=(12, 0))

        transcript_frame = Frame(self.root, padx=18, pady=8)
        transcript_frame.pack(fill=X)
        Label(transcript_frame, text="Heard:", width=12, anchor="w").pack(side=LEFT)
        Label(
            transcript_frame,
            textvariable=self.transcript_text,
            font=("TkDefaultFont", 12),
            anchor="w",
        ).pack(side=LEFT, fill=X, expand=True)

        Label(
            self.root,
            textvariable=self.feedback_text,
            bg="#edf3f8",
            anchor="w",
            padx=14,
            pady=10,
        ).pack(fill=X, padx=18, pady=8)

        camera_frame = Frame(self.root, padx=18, pady=8)
        camera_frame.pack(fill=X)
        Label(camera_frame, text="Camera:", width=12, anchor="w").pack(side=LEFT)
        Label(
            camera_frame,
            textvariable=self.camera_status_text,
            anchor="w",
        ).pack(side=LEFT, fill=X, expand=True)

        camera_buttons = Frame(self.root, padx=18)
        camera_buttons.pack(fill=X, pady=(0, 8))
        self._project_button(
            camera_buttons,
            text="Start Head Tracking",
            command=lambda: self.start_camera_control("head"),
            aliases=("head tracking", "start head control"),
        ).pack(side=LEFT)
        self._project_button(
            camera_buttons,
            text="Start Eye Gaze",
            command=lambda: self.start_camera_control("gaze"),
            aliases=("eye gaze", "start gaze control"),
        ).pack(side=LEFT, padx=6)
        self._project_button(
            camera_buttons,
            text="Recalibrate Camera",
            command=self.recalibrate_camera_control,
            aliases=("recalibrate gaze", "recalibrate head"),
        ).pack(side=LEFT)
        self._project_button(
            camera_buttons,
            text="Stop Camera",
            command=self.stop_camera_control,
        ).pack(side=LEFT, padx=6)

        tongue_frame = Frame(self.root, padx=18)
        tongue_frame.pack(fill=X, pady=(0, 8))
        Label(tongue_frame, text="Tongue:", width=12, anchor="w").pack(side=LEFT)
        Label(
            tongue_frame,
            textvariable=self.tongue_status_text,
            anchor="w",
        ).pack(side=LEFT, fill=X, expand=True)
        self._project_button(
            tongue_frame,
            text="Calibrate Tongue Clicks",
            command=self.calibrate_tongue_control,
            aliases=("calibrate tongue", "tongue calibration"),
        ).pack(side=LEFT, padx=6)
        self._project_button(
            tongue_frame,
            text="Disable Tongue",
            command=self.disable_tongue_control,
            aliases=("stop tongue", "disable tongue clicks"),
        ).pack(side=LEFT)

        blink_frame = Frame(self.root, padx=18)
        blink_frame.pack(fill=X, pady=(0, 4))
        Label(blink_frame, text="Blink:", width=12, anchor="w").pack(side=LEFT)
        Label(
            blink_frame,
            textvariable=self.blink_status_text,
            anchor="w",
        ).pack(side=LEFT, fill=X, expand=True)

        blink_buttons = Frame(self.root, padx=18)
        blink_buttons.pack(fill=X, pady=(0, 8))
        self._project_button(
            blink_buttons,
            text="Calibrate Blink Clicks",
            command=self.calibrate_blink_control,
            aliases=("calibrate blink", "blink calibration"),
        ).pack(side=LEFT)
        self._project_button(
            blink_buttons,
            text="Disable Blink",
            command=self.disable_blink_control,
            aliases=("stop blink", "disable blink clicks"),
        ).pack(side=LEFT, padx=6)
        self._project_button(
            blink_buttons,
            text="Calibrate Both",
            command=self.calibrate_both_gestures,
            aliases=("calibrate both clicks", "calibrate tongue and blink"),
        ).pack(side=LEFT)

        evaluation_frame = Frame(self.root, padx=18, pady=8)
        evaluation_frame.pack(fill=X)
        self._project_button(
            evaluation_frame,
            text="Start Guided Evaluation",
            command=self.start_evaluation,
            aliases=(
                "start evaluation",
                "test evaluation",
                "test evaluations",
            ),
        ).pack(side=LEFT)
        self._project_button(
            evaluation_frame,
            text="Cancel Evaluation",
            command=self.cancel_evaluation,
        ).pack(side=LEFT, padx=8)
        Label(
            evaluation_frame,
            textvariable=self.evaluation_text,
            anchor="w",
            font=("TkDefaultFont", 11, "bold"),
        ).pack(side=LEFT, padx=12, fill=X, expand=True)

        commands_text = "  •  ".join(command.label for command in COMMANDS)
        Label(
            self.root,
            text=(
                f"Direction step: {movement_pixels} pixels\n"
                f"Supported commands\n{commands_text}"
                "\nInteractive controls: click <name>  •  double click <name>  •  "
                "right click <name>  •  move to <name>"
                "\nTongue after calibration: 1 gesture = single click  •  "
                "2 = double click  •  3 = triple click"
                "\nBlink after calibration: 2 rapid blinks = single click  •  "
                "4 rapid blinks = double click"
            ),
            justify=LEFT,
            wraplength=730,
            anchor="w",
            padx=18,
            pady=8,
        ).pack(fill=X)

        Label(self.root, text="Session log", anchor="w", padx=18).pack(fill=X)
        self.log_widget = Text(self.root, height=9, state="disabled", wrap="word")
        self.log_widget.pack(fill=BOTH, expand=True, padx=18, pady=(4, 16))
        startup_state = "enabled" if not self.executor.paused else "paused"
        self._append_log(f"Application started with control {startup_state}")

    def _project_button(
        self,
        parent,
        *,
        text: str,
        command,
        aliases: tuple[str, ...] = (),
    ) -> Button:
        """Create and register a real button; labels/transcripts never enter this list."""
        button = Button(parent, text=text, command=command)
        self.local_button_targets.append((button, text, aliases))
        return button

    def _start_listener(self) -> None:
        thread = threading.Thread(target=self._listener_worker, daemon=True)
        thread.start()

    def _listener_worker(self) -> None:
        try:
            if self.speech_engine in {"auto", "parakeet"}:
                if default_helper_path().is_file():
                    try:
                        listener = ParakeetMicrophoneListener(
                            device=self.input_device
                        )
                        listener.run(
                            stop_event=self.stop_event,
                            on_result=lambda text: self.root.after(
                                0, self._handle_recognized_text, text
                            ),
                            on_partial=lambda text: None,
                            on_status=self._threadsafe_status,
                        )
                        return
                    except Exception as exc:
                        if self.stop_event.is_set():
                            return
                        self._threadsafe_status(
                            f"MacParakeet unavailable ({exc}); falling back to Vosk…"
                        )
                elif self.speech_engine == "parakeet":
                    self._threadsafe_status(
                        "MacParakeet helper is not compiled; falling back to Vosk…"
                    )

            model_path = self.model_path or ensure_model(
                on_status=self._threadsafe_status
            )
            listener = VoskMicrophoneListener(
                model_path=model_path,
                device=self.input_device,
            )
            listener.run(
                stop_event=self.stop_event,
                on_result=lambda text: self.root.after(
                    0, self._handle_recognized_text, text
                ),
                on_partial=lambda text: self.root.after(
                    0, self._handle_partial_text, text
                ),
                on_status=self._threadsafe_status,
            )
        except Exception as exc:
            self._threadsafe_status(f"Startup failed: {exc}")

    def _threadsafe_status(self, message: str) -> None:
        try:
            self.root.after(0, self.status_text.set, message)
        except RuntimeError:
            pass

    def _handle_partial_text(self, text: str) -> None:
        # Partial hypotheses naturally change while a person is speaking.
        # Display only finalized recognition results so the UI is stable.
        return

    def _handle_recognized_text(self, text: str) -> None:
        self.transcript_text.set(text)

        if self.screen_action_in_progress:
            return
        if self.evaluation is not None and self.evaluation_accepting_result:
            self._record_evaluation_result(text)
            return
        if self.evaluation is not None:
            return

        screen_action = interpret_screen_text_action(text)
        if screen_action is not None:
            self.screen_action_in_progress = True
            self.feedback_text.set(
                f'Finding a button or visible text named "{screen_action.label}"…'
            )
            self._append_log(
                "Searching interactive controls, then the visible screen while "
                "excluding only visible Voice Cursor content"
            )
            self.root.after(
                10,
                self._execute_screen_action,
                text,
                screen_action,
            )
            return

        command = interpret_command(text)
        if command is None:
            self.feedback_text.set(f'Not a supported command: "{text}"')
            self._record_session(text, "", "unrecognized")
            self._append_log(f'Unrecognized: "{text}"')
            return

        result = self.executor.execute(command)
        self.feedback_text.set(result.message)
        self._sync_control_indicator()
        result_name = "success" if result.success else "ignored/error"
        self._record_session(text, command.name.value, result_name)
        self._append_log(f'{command.label}: {result.message}')

    def _execute_screen_action(self, text, screen_action) -> None:
        local_matches = self._matching_project_buttons(screen_action.label)
        if len(local_matches) > 1:
            names = ", ".join(item[1] for item in local_matches)
            result = ActionResult(
                False,
                f"Several project buttons match: {names}. Nothing was clicked.",
            )
        elif len(local_matches) == 1:
            button, button_label, _aliases = local_matches[0]
            button.update_idletasks()
            center = (
                button.winfo_rootx() + button.winfo_width() // 2,
                button.winfo_rooty() + button.winfo_height() // 2,
            )
            result = self.executor.execute_local_control(
                screen_action,
                label=button_label,
                center=center,
                activate=button.invoke,
            )
        else:
            result = self.executor.execute_screen_text(
                screen_action,
                excluded_rectangles=self._visible_voice_cursor_rectangles(),
            )
        result_name = "success" if result.success else "ignored/error"
        command_name = f"{screen_action.kind.value}:{screen_action.label}"
        self._record_session(text, command_name, result_name)
        self._append_log(f"{command_name}: {result.message}")
        self.feedback_text.set(result.message)
        self.screen_action_in_progress = False

    def _voice_cursor_rectangle(self) -> tuple[int, int, int, int]:
        """Return the project window bounds with padding for OCR exclusion."""
        self.root.update_idletasks()
        left = self.root.winfo_rootx() - 12
        top = self.root.winfo_rooty() - 45
        right = left + self.root.winfo_width() + 24
        bottom = top + self.root.winfo_height() + 57
        return (left, top, right, bottom)

    def _visible_voice_cursor_rectangles(
        self,
    ) -> tuple[tuple[int, int, int, int], ...]:
        """Exclude only project-window regions not covered by another app.

        Finder or browser windows can sit in front of Voice Cursor while still
        overlapping its screen coordinates. Excluding the entire project
        rectangle would incorrectly discard OCR words in those foreground
        windows. Quartz supplies front-to-back window order, allowing the
        covered areas to be subtracted from the exclusion safely.
        """
        project_rectangle = self._voice_cursor_rectangle()
        try:
            import Quartz

            options = (
                Quartz.kCGWindowListOptionOnScreenOnly
                | Quartz.kCGWindowListExcludeDesktopElements
            )
            windows = Quartz.CGWindowListCopyWindowInfo(
                options,
                Quartz.kCGNullWindowID,
            ) or []
            own_pid = os.getpid()
            candidates: list[tuple[int, int]] = []
            parsed_windows: list[
                tuple[int, int, float, tuple[int, int, int, int]]
            ] = []

            for index, window in enumerate(windows):
                try:
                    pid = int(window.get(Quartz.kCGWindowOwnerPID, 0))
                    layer = int(window.get(Quartz.kCGWindowLayer, -1))
                    alpha = float(window.get(Quartz.kCGWindowAlpha, 1.0))
                    bounds = window.get(Quartz.kCGWindowBounds, {})
                    left = round(float(bounds.get("X", 0)))
                    top = round(float(bounds.get("Y", 0)))
                    width = round(float(bounds.get("Width", 0)))
                    height = round(float(bounds.get("Height", 0)))
                except (TypeError, ValueError):
                    continue
                if width < 1 or height < 1:
                    continue
                rectangle = (left, top, left + width, top + height)
                parsed_windows.append((index, pid, alpha, rectangle))
                if pid == own_pid and 0 <= layer <= 19 and alpha > 0:
                    area = intersection_area(project_rectangle, rectangle)
                    if area > 0:
                        candidates.append((area, index))

            if not candidates:
                return (project_rectangle,)
            _area, own_window_index = max(candidates)
            foreground = tuple(
                rectangle
                for index, pid, alpha, rectangle in parsed_windows
                if index < own_window_index and pid != own_pid and alpha > 0
            )
            return visible_regions(project_rectangle, foreground)
        except Exception:
            # Fail safely by preserving the original full-window exclusion.
            return (project_rectangle,)

    def _matching_project_buttons(
        self,
        spoken_label: str,
    ) -> list[tuple[Button, str, tuple[str, ...]]]:
        target = target_comparison_key(spoken_label)
        if not target:
            return []

        exact = []
        for item in self.local_button_targets:
            _button, label, aliases = item
            names = (label, *aliases)
            normalized_names = [target_comparison_key(name) for name in names]
            if target in normalized_names:
                exact.append(item)
        return exact

    def enable_control(self) -> None:
        command = next(
            item for item in COMMANDS if item.name == CommandName.RESUME_CONTROL
        )
        result = self.executor.execute(command)
        self.feedback_text.set(result.message)
        self._sync_control_indicator()
        self._append_log(result.message)

    def pause_control(self) -> None:
        if self.camera_controller.running:
            self.stop_camera_control()
        command = next(
            item for item in COMMANDS if item.name == CommandName.PAUSE_CONTROL
        )
        result = self.executor.execute(command)
        self.feedback_text.set(result.message)
        self._sync_control_indicator()
        self._append_log(result.message)

    def test_cursor_control(self) -> None:
        result = self.executor.verify_cursor_control()
        self.feedback_text.set(result.message)
        self._append_log(result.message)

    def start_camera_control(self, mode: str) -> None:
        if self.dry_run:
            message = "Camera pointer control is disabled in dry-run mode."
            self.camera_status_text.set(message)
            self._append_log(message)
            return
        if self.executor.paused:
            message = "Enable live control before starting camera pointer movement."
            self.camera_status_text.set(message)
            self.feedback_text.set(message)
            self._append_log(message)
            return
        permission = self.executor._live_control_permission()
        if permission is not None:
            self.camera_status_text.set(permission.message)
            self.feedback_text.set(permission.message)
            self._append_log(permission.message)
            return
        label = "head tracking" if mode == "head" else "eye-gaze tracking"
        self.camera_status_text.set(f"Starting {label}…")
        self.camera_controller.start(
            mode,
            on_status=self._threadsafe_camera_status,
            on_tongue_status=self._threadsafe_tongue_status,
            on_blink_status=self._threadsafe_blink_status,
            on_click_feedback=self._threadsafe_click_feedback,
        )
        self._append_log(
            f"Starting {label}; move the pointer to a screen corner to stop safely"
        )

    def stop_camera_control(self) -> None:
        self.camera_controller.stop()
        self.camera_status_text.set("Camera control is off")
        self.tongue_status_text.set(
            "Calibration saved; restart the camera to resume"
            if self.camera_controller.tongue_calibrated
            else "Tongue clicks are off"
        )
        self.blink_status_text.set(
            "Calibration saved; restart the camera to resume"
            if self.camera_controller.blink_calibrated
            else "Blink clicks are off"
        )
        self._append_log("Camera pointer control stopped")

    def recalibrate_camera_control(self) -> None:
        if not self.camera_controller.running:
            message = "Start Head Tracking or Start Eye Gaze before recalibrating."
            self.camera_status_text.set(message)
            self._append_log(message)
            return
        self.camera_controller.recalibrate()
        self._append_log("Camera pointer control recalibration started")

    def _threadsafe_camera_status(self, message: str) -> None:
        try:
            self.root.after(0, self.camera_status_text.set, message)
            self.root.after(0, self._append_log, f"Camera: {message}")
        except RuntimeError:
            pass

    def calibrate_tongue_control(self) -> None:
        if not self.camera_controller.running:
            message = "Start Head Tracking or Start Eye Gaze before tongue calibration."
            self.tongue_status_text.set(message)
            self.feedback_text.set(message)
            self._append_log(message)
            return
        try:
            self.camera_controller.calibrate_tongue()
            self._append_log("In-app tongue calibration started")
        except RuntimeError as exc:
            self.tongue_status_text.set(str(exc))

    def disable_tongue_control(self) -> None:
        self.camera_controller.disable_tongue()
        self._append_log("In-app tongue clicks disabled")

    def _threadsafe_tongue_status(self, message: str) -> None:
        try:
            self.root.after(0, self.tongue_status_text.set, message)
            self.root.after(0, self._append_log, f"Tongue: {message}")
        except RuntimeError:
            return

    def calibrate_blink_control(self) -> None:
        if not self.camera_controller.running:
            message = "Start Head Tracking or Start Eye Gaze before blink calibration."
            self.blink_status_text.set(message)
            self.feedback_text.set(message)
            self._append_log(message)
            return
        try:
            self.camera_controller.calibrate_blink()
            self._append_log("In-app blink calibration started")
        except RuntimeError as exc:
            self.blink_status_text.set(str(exc))

    def disable_blink_control(self) -> None:
        self.camera_controller.disable_blink()
        self._append_log("In-app blink clicks disabled")

    def calibrate_both_gestures(self) -> None:
        if not self.camera_controller.running:
            message = "Start Head Tracking or Start Eye Gaze before calibration."
            self.tongue_status_text.set(message)
            self.blink_status_text.set(message)
            self.feedback_text.set(message)
            self._append_log(message)
            return
        try:
            self.camera_controller.calibrate_both()
            self._append_log("Sequential tongue and blink calibration started")
        except RuntimeError as exc:
            self.blink_status_text.set(str(exc))

    def _threadsafe_blink_status(self, message: str) -> None:
        try:
            self.root.after(0, self.blink_status_text.set, message)
            self.root.after(0, self._append_log, f"Blink: {message}")
        except RuntimeError:
            return

    def _threadsafe_click_feedback(self, action: str, x: int, y: int) -> None:
        try:
            self.root.after(0, self._show_click_ring, action, x, y)
        except RuntimeError:
            pass

    def _show_click_ring(self, action: str, x: int, y: int) -> None:
        """Launch a click-through indicator that cannot activate Voice Cursor."""
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "voice_cursor.click_overlay_worker",
                    action,
                    str(x),
                    str(y),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            pass

    def _sync_control_indicator(self) -> None:
        if self.executor.paused:
            self.control_text.set("PAUSED")
            self.control_label.configure(fg="#9b1c1c")
        else:
            self.control_text.set("ENABLED")
            self.control_label.configure(fg="#1f6b32")

    def start_evaluation(self) -> None:
        if self.evaluation is not None:
            messagebox.showinfo("Evaluation", "An evaluation is already running.")
            return

        commands = list(evaluation_commands())
        random.shuffle(commands)
        self.evaluation = EvaluationSession(tuple(commands))
        self.evaluation_accepting_result = False
        self.pause_control()
        self._append_log("Guided evaluation started; actions will not be executed")
        self._show_evaluation_prompt()

    def _show_evaluation_prompt(self) -> None:
        if self.evaluation is None:
            return
        if self.evaluation.complete:
            self._finish_evaluation()
            return

        target = self.evaluation.current
        assert target is not None
        trial_number = self.evaluation.index + 1
        total = len(self.evaluation.commands)
        self.evaluation_text.set(
            f'Trial {trial_number}/{total}: Say “{target.phrases[0]}”'
        )
        self.transcript_text.set("—")
        self.evaluation.start_current_trial()
        self.evaluation_accepting_result = True
        self._cancel_evaluation_timeout()
        self.evaluation_timeout_id = self.root.after(
            self.EVALUATION_TIMEOUT_MS, self._evaluation_timed_out
        )

    def _record_evaluation_result(self, text: str) -> None:
        if self.evaluation is None:
            return
        self.evaluation_accepting_result = False
        self._cancel_evaluation_timeout()
        self.evaluation.record(text)
        trial = self.evaluation.trials[-1]
        verdict = "correct" if trial.correct else "incorrect"
        self._append_log(
            f'Evaluation: expected {trial.target}, heard "{text}" — {verdict}'
        )
        self.root.after(650, self._show_evaluation_prompt)

    def _evaluation_timed_out(self) -> None:
        self.evaluation_timeout_id = None
        if self.evaluation is None:
            return
        self.evaluation_accepting_result = False
        target = self.evaluation.current
        self.evaluation.record_timeout(
            elapsed=self.EVALUATION_TIMEOUT_MS / 1_000
        )
        self._append_log(f"Evaluation: {target.label if target else 'trial'} timed out")
        self.root.after(650, self._show_evaluation_prompt)

    def _finish_evaluation(self) -> None:
        if self.evaluation is None:
            return
        output_dir = Path(__file__).resolve().parent.parent / "evaluation_results"
        output_path = self.evaluation.export_csv(output_dir)
        summary = self.evaluation.summary()
        self.evaluation_text.set(
            f"Completed: {summary['accuracy_percent']:.1f}% accuracy, "
            f"{summary['average_response_seconds']:.2f}s average"
        )
        self._append_log(f"Evaluation saved to {output_path}")
        messagebox.showinfo(
            "Evaluation complete",
            (
                f"Accuracy: {summary['accuracy_percent']:.1f}%\n"
                f"Average response time: "
                f"{summary['average_response_seconds']:.2f} seconds\n\n"
                f"Results saved to:\n{output_path}"
            ),
        )
        self.evaluation = None
        self.evaluation_accepting_result = False

    def cancel_evaluation(self) -> None:
        if self.evaluation is None:
            return
        self._cancel_evaluation_timeout()
        self.evaluation = None
        self.evaluation_accepting_result = False
        self.evaluation_text.set("Evaluation cancelled")
        self._append_log("Guided evaluation cancelled")

    def _cancel_evaluation_timeout(self) -> None:
        if self.evaluation_timeout_id is not None:
            self.root.after_cancel(self.evaluation_timeout_id)
            self.evaluation_timeout_id = None

    def _append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.configure(state="normal")
        self.log_widget.insert(END, f"[{timestamp}] {message}\n")
        self.log_widget.see(END)
        self.log_widget.configure(state="disabled")

    def _create_session_log(self) -> Path:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = log_dir / f"session_{timestamp}.csv"
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            csv.writer(csv_file).writerow(
                ["timestamp", "recognized_text", "command", "result"]
            )
        return path

    def _record_session(self, text: str, command: str, result: str) -> None:
        with self.session_log.open("a", newline="", encoding="utf-8") as csv_file:
            csv.writer(csv_file).writerow(
                [datetime.now().isoformat(timespec="seconds"), text, command, result]
            )

    def close(self) -> None:
        self._cancel_evaluation_timeout()
        self.camera_controller.stop()
        self.stop_event.set()
        self.root.destroy()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline voice-controlled cursor and basic computer actions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Recognize and log commands without controlling the computer",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        help="Use an existing unpacked Vosk model instead of auto-downloading one",
    )
    parser.add_argument(
        "--movement-pixels",
        type=int,
        default=180,
        help="Cursor movement distance per command (default: 180)",
    )
    parser.add_argument(
        "--start-enabled",
        action="store_true",
        help="Start live control enabled so movement commands work immediately",
    )
    parser.add_argument(
        "--input-device",
        help=(
            "Microphone device index or part of its name. By default the built-in "
            "Mac microphone is preferred."
        ),
    )
    parser.add_argument(
        "--speech-engine",
        choices=("auto", "parakeet", "vosk"),
        default="auto",
        help=(
            "Speech recognizer to use. 'auto' prefers the installed MacParakeet "
            "helper and falls back to Vosk (default: auto)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.movement_pixels < 1:
        raise SystemExit("--movement-pixels must be at least 1")
    if args.model_path is not None and not args.model_path.is_dir():
        raise SystemExit(f"Model folder not found: {args.model_path}")

    root = Tk()
    VoiceCursorApp(
        root,
        dry_run=args.dry_run,
        model_path=args.model_path,
        movement_pixels=args.movement_pixels,
        start_enabled=args.start_enabled,
        input_device=args.input_device,
        speech_engine=args.speech_engine,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
