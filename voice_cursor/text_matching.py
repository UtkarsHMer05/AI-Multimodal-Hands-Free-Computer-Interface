"""Shared normalization for spoken labels and visible control text."""

from __future__ import annotations

import re


def normalize_target_text(text: str) -> str:
    """Return lowercase alphanumeric words separated by single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def target_comparison_key(text: str) -> str:
    """Return a key insensitive to case, whitespace, and separators.

    Removing only separators allows ``backend``, ``back end``, and
    ``BACK-END`` to match while keeping genuinely different spellings such as
    ``project`` and ``projects`` distinct.
    """
    return normalize_target_text(text).replace(" ", "")


def target_texts_match(first: str, second: str) -> bool:
    """Return whether two non-empty target labels have the same key."""
    first_key = target_comparison_key(first)
    return bool(first_key) and first_key == target_comparison_key(second)
