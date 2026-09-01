#!/usr/bin/env python3
"""Assert parity between the website TypeScript port and the Python engine.

Compares, on a shared battery of utterances:
  - interpret_command          <-> interpretCommand
  - interpret_screen_text_action <-> interpretScreenTextAction
  - difflib SequenceMatcher    <-> similarityRatio (JS port)
  - target_comparison_key      <-> targetComparisonKey
  - target_texts_match         <-> targetTextsMatch

Usage:  python3 scripts/verify_port_parity.py
Exit code 0 means every case matches.
"""

from __future__ import annotations

import json
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "website"
BUILD = WEB / ".parity"

sys.path.insert(0, str(ROOT))
from voice_cursor.commands import (  # noqa: E402
    interpret_command,
    interpret_screen_text_action,
)
from voice_cursor.text_matching import (  # noqa: E402
    target_comparison_key,
    target_texts_match,
)

UTTERANCES = [
    # exact phrases and aliases
    "move left", "go left", "Move Right", "MOVE UP", "go down", "click",
    "left click", "double click", "right click", "scroll up", "scroll down",
    "open browser", "new tab", "open new tab", "close tab", "pause control",
    "disable control", "resume control", "enable control",
    # prefixes and punctuation
    "Please move left", "computer, click", "PLEASE  SCROLL UP!",
    "computer new tab", "move... left", "double-click", "Please, right click",
    "Computer, open browser",
    # fuzzy near-misses
    "muv left", "move lift", "mov left", "move leftt", "scroll upp",
    "sroll down", "close the tab", "close tabs", "newtab", "open browsers",
    "klick", "right-click it", "move left a bit", "double click it",
    "moved left", "moves left", "scrol down", "clik",
    # non-commands
    "hello world", "what time is it", "a", "ok", "", "search the web",
    "stop", "move diagonally", "triple click", "drag file", "type hello",
    "clicks", "moving left",
    # screen-target actions
    "click Enable", "click the Submit button", "double click Sign In",
    "double click on Downloads", "right click Downloads", "press Submit",
    "click on Sign In", "move to Sign In", "hover over Sign In",
    "hover on trash", "press the Enable button", "click BACK-END",
    "click back end", "click Projects", "click welcome",
    "move to the Sign In link", "right click on the Projects folder",
    "click one two three four five six seven eight nine ten",
    "click the", "press", "move to", "click  ",
]

RATIO_PAIRS = [
    ("move left", "move left"), ("move lift", "move left"),
    ("move lift", "mve lft"), ("close the tab", "close tab"),
    ("a b c d", "a b c d e"), ("abcd", "abcd abcd"), (" abcd", "abcd abcd"),
    ("kitten", "sitting"), ("aaaa", "aa"), ("abc", "acb"),
    ("scroll upp", "scroll up"), ("scroll down", "scroll dawn"),
    ("open browser", "open browsers"), ("new tab", "newtab"),
    ("click", "click"), ("click", "clicks"), ("move left", "left move"),
    ("right click", "click right"), ("double click", "double-click"),
    ("press submit", "press Submit"), ("1234", "4321"),
    ("q w e r t y", "q w e r t"), (" Sign In", "Sign In "),
    ("backend", "back end"), ("BACKEND", "back-end"),
    ("zzz", "zzzzzzz"), ("identical strings", "identical strings"),
    ("", ""), ("", "a"), ("abc", ""), ("xyz", "abc"),
    ("move up or down", "move down"), ("tab", "close tab"),
    ("click Enable", "click"), ("Sign In", "sign in"),
    ("download folder", "Downloads"), ("open the browser now", "open browser"),
    ("new browser tab", "new tab"), ("pause it", "pause control"),
    ("resume control now", "resume control"), ("enable control", "enable control"),
]

TARGET_PAIRS = [
    ("backend", "back end"), ("BACK-END", "backend"), ("project", "projects"),
    ("Sign In", "signin"), (" Sign  In ", "sign-in"), ("", "x"), ("  ", "x"),
    ("Projects", "projects"), ("Submit", "Submits"), ("Downloads", "downloads"),
    ("HCI Project", "HCI-project"), ("HCI Project", "HCI projects"),
    ("trash", "Trash"), ("enable", "Enable"), ("enable", "Enabled"),
    ("back end", "back-end"), ("BACKEND", "back end"), ("src", "SRC"),
    ("backend folder", "backendfolder"), ("backend folder", "backend folders"),
]


def py_results() -> dict:
    def interpret(u: str) -> dict:
        command = interpret_command(u)
        screen = interpret_screen_text_action(u)
        return {
            "command": command.name.value if command else None,
            "screen": (
                {"kind": screen.kind.value, "label": screen.label}
                if screen
                else None
            ),
        }

    return {
        "utterances": [interpret(u) for u in UTTERANCES],
        "ratios": [
            SequenceMatcher(None, a, b).ratio() for a, b in RATIO_PAIRS
        ],
        "targetKeys": [target_comparison_key(a) for a, _ in TARGET_PAIRS],
        "targetMatches": [target_texts_match(a, b) for a, b in TARGET_PAIRS],
    }


def run(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(f"command failed: {' '.join(cmd)}")


def main() -> int:
    BUILD.mkdir(exist_ok=True)
    (BUILD / "battery.json").write_text(
        json.dumps(
            {"utterances": UTTERANCES, "ratioPairs": RATIO_PAIRS,
             "targetPairs": TARGET_PAIRS}
        )
    )

    # Compile the TS module and run the JS harness on the same battery.
    run(
        ["npx", "tsc", "src/lib/commands.ts", "--outDir", ".parity",
         "--module", "commonjs", "--target", "es2020", "--skipLibCheck",
         "--esModuleInterop"],
        WEB,
    )
    run(["node", "scripts/parity-harness.mjs"], WEB)

    ts = json.loads((BUILD / "ts-results.json").read_text())
    py = py_results()

    failures = 0

    for i, (want, got) in enumerate(zip(py["utterances"], ts["utterances"])):
        if want != got:
            failures += 1
            print(f"UTTERANCE MISMATCH {UTTERANCES[i]!r}: py={want} ts={got}")

    for i, (want, got) in enumerate(zip(py["ratios"], ts["ratios"])):
        if abs(want - got) > 1e-9:
            failures += 1
            print(f"RATIO MISMATCH {RATIO_PAIRS[i]!r}: py={want} ts={got}")

    for i, (want, got) in enumerate(zip(py["targetKeys"], ts["targetKeys"])):
        if want != got:
            failures += 1
            print(f"KEY MISMATCH {TARGET_PAIRS[i][0]!r}: py={want!r} ts={got!r}")

    for i, (want, got) in enumerate(
        zip(py["targetMatches"], ts["targetMatches"])
    ):
        if want != got:
            failures += 1
            print(f"MATCH MISMATCH {TARGET_PAIRS[i]!r}: py={want} ts={got}")

    total = len(UTTERANCES) + len(RATIO_PAIRS) + 2 * len(TARGET_PAIRS)
    print(f"parity check: {total - failures}/{total} cases match")
    if failures:
        print(f"FAILED: {failures} mismatches")
        return 1
    print("OK: TypeScript port matches the Python engine on every case")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
