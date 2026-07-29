"""Supported voice commands and deterministic phrase matching."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum


class CommandName(str, Enum):
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    LEFT_CLICK = "left_click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    OPEN_BROWSER = "open_browser"
    NEW_TAB = "new_tab"
    CLOSE_TAB = "close_tab"
    PAUSE_CONTROL = "pause_control"
    RESUME_CONTROL = "resume_control"


class ScreenActionKind(str, Enum):
    CLICK = "screen_click"
    DOUBLE_CLICK = "screen_double_click"
    RIGHT_CLICK = "screen_right_click"
    HOVER = "screen_hover"


@dataclass(frozen=True)
class VoiceCommand:
    name: CommandName
    label: str
    phrases: tuple[str, ...]


@dataclass(frozen=True)
class ScreenTextAction:
    kind: ScreenActionKind
    label: str


COMMANDS: tuple[VoiceCommand, ...] = (
    VoiceCommand(CommandName.MOVE_LEFT, "Move left", ("move left", "go left")),
    VoiceCommand(CommandName.MOVE_RIGHT, "Move right", ("move right", "go right")),
    VoiceCommand(CommandName.MOVE_UP, "Move up", ("move up", "go up")),
    VoiceCommand(CommandName.MOVE_DOWN, "Move down", ("move down", "go down")),
    VoiceCommand(CommandName.LEFT_CLICK, "Click", ("click", "left click")),
    VoiceCommand(CommandName.DOUBLE_CLICK, "Double click", ("double click",)),
    VoiceCommand(CommandName.RIGHT_CLICK, "Right click", ("right click",)),
    VoiceCommand(CommandName.SCROLL_UP, "Scroll up", ("scroll up",)),
    VoiceCommand(CommandName.SCROLL_DOWN, "Scroll down", ("scroll down",)),
    VoiceCommand(CommandName.OPEN_BROWSER, "Open browser", ("open browser",)),
    VoiceCommand(CommandName.NEW_TAB, "New tab", ("new tab", "open new tab")),
    VoiceCommand(CommandName.CLOSE_TAB, "Close tab", ("close tab",)),
    VoiceCommand(
        CommandName.PAUSE_CONTROL,
        "Pause control",
        ("pause control", "disable control"),
    ),
    VoiceCommand(
        CommandName.RESUME_CONTROL,
        "Resume control",
        ("resume control", "enable control"),
    ),
)

COMMAND_BY_NAME = {command.name: command for command in COMMANDS}


def normalize_phrase(text: str) -> str:
    """Normalize speech-recognition output for exact command matching."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for prefix in ("please ", "computer "):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
    return normalized


_PHRASE_TO_COMMAND = {
    normalize_phrase(phrase): command
    for command in COMMANDS
    for phrase in command.phrases
}


def interpret_command(text: str) -> VoiceCommand | None:
    """Return an exact or clearly dominant fixed-vocabulary command match."""
    normalized = normalize_phrase(text)
    exact = _PHRASE_TO_COMMAND.get(normalized)
    if exact is not None:
        return exact
    if len(normalized) < 5:
        return None

    ranked = sorted(
        (
            (
                SequenceMatcher(None, normalized, phrase).ratio(),
                command,
            )
            for phrase, command in _PHRASE_TO_COMMAND.items()
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    if not ranked or ranked[0][0] < 0.84:
        return None
    if len(ranked) > 1 and ranked[0][0] - ranked[1][0] < 0.08:
        return None
    return ranked[0][1]


def interpret_screen_text_action(text: str) -> ScreenTextAction | None:
    """Parse actions such as 'click Submit' or 'double click Sign In'."""
    normalized = normalize_phrase(text)
    patterns = (
        (r"^(?:double click)(?: on)? (.+)$", ScreenActionKind.DOUBLE_CLICK),
        (r"^(?:right click)(?: on)? (.+)$", ScreenActionKind.RIGHT_CLICK),
        (r"^(?:click|press)(?: on)? (.+)$", ScreenActionKind.CLICK),
        (r"^(?:move to|hover over|hover on) (.+)$", ScreenActionKind.HOVER),
    )
    for pattern, kind in patterns:
        matched = re.match(pattern, normalized)
        if matched is None:
            continue
        label = matched.group(1).strip()
        if label.startswith("the "):
            label = label[4:].strip()
        if 1 <= len(label.split()) <= 8:
            return ScreenTextAction(kind=kind, label=label)
    return None


def recognition_phrases() -> list[str]:
    """Return the constrained Vosk grammar used by the recognizer."""
    phrases = sorted(_PHRASE_TO_COMMAND)
    return [*phrases, "[unk]"]


def evaluation_commands() -> tuple[VoiceCommand, ...]:
    """Core commands used by evaluation, excluding state toggles."""
    return tuple(
        command
        for command in COMMANDS
        if command.name
        not in {CommandName.PAUSE_CONTROL, CommandName.RESUME_CONTROL}
    )
