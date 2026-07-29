"""Guided recognition evaluation and CSV result export."""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import monotonic

from .commands import VoiceCommand, interpret_command


@dataclass(frozen=True)
class EvaluationTrial:
    target: str
    recognized_text: str
    matched_command: str
    correct: bool
    response_time_seconds: float


class EvaluationSession:
    def __init__(self, commands: tuple[VoiceCommand, ...]):
        if not commands:
            raise ValueError("At least one evaluation command is required")
        self.commands = commands
        self.index = 0
        self.trials: list[EvaluationTrial] = []
        self._trial_started = monotonic()

    @property
    def complete(self) -> bool:
        return self.index >= len(self.commands)

    @property
    def current(self) -> VoiceCommand | None:
        return None if self.complete else self.commands[self.index]

    def start_current_trial(self) -> None:
        self._trial_started = monotonic()

    def record(self, recognized_text: str, *, elapsed: float | None = None) -> None:
        if self.complete:
            return
        target = self.commands[self.index]
        recognized = interpret_command(recognized_text)
        duration = monotonic() - self._trial_started if elapsed is None else elapsed
        self.trials.append(
            EvaluationTrial(
                target=target.label,
                recognized_text=recognized_text,
                matched_command=recognized.label if recognized else "Unrecognized",
                correct=recognized is not None and recognized.name == target.name,
                response_time_seconds=max(0.0, duration),
            )
        )
        self.index += 1

    def record_timeout(self, *, elapsed: float) -> None:
        self.record("", elapsed=elapsed)

    def summary(self) -> dict[str, float | int]:
        total = len(self.trials)
        correct = sum(trial.correct for trial in self.trials)
        times = [trial.response_time_seconds for trial in self.trials]
        return {
            "total_trials": total,
            "correct_trials": correct,
            "accuracy_percent": (correct / total * 100.0) if total else 0.0,
            "average_response_seconds": statistics.fmean(times) if times else 0.0,
        }

    def export_csv(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"evaluation_{timestamp}.csv"
        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "target_command",
                    "recognized_text",
                    "matched_command",
                    "correct",
                    "response_time_seconds",
                ]
            )
            for trial in self.trials:
                writer.writerow(
                    [
                        trial.target,
                        trial.recognized_text,
                        trial.matched_command,
                        trial.correct,
                        f"{trial.response_time_seconds:.3f}",
                    ]
                )

            summary = self.summary()
            writer.writerow([])
            writer.writerow(["summary_metric", "value"])
            for key, value in summary.items():
                writer.writerow([key, f"{value:.3f}" if isinstance(value, float) else value])

        return output_path
