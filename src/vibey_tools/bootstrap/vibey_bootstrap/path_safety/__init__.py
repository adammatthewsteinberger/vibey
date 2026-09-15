"""Filename + path sanitization.

Two-layered defense:

- :func:`sanitize_path_segment` for filenames / single segments before they
  interpolate into blob paths, filesystem paths, email subjects, or log lines.
- :func:`confine_to_root` for resolved paths before opening files — refuses
  any escape from a configured root directory.

The bidi/zero-width regex is the live attack surface for visual-spoofing
filename attacks (RLO injection in particular). Strip first, then everything
else.
"""

from __future__ import annotations

import re
from pathlib import Path

# Bidi controls + zero-width marks + word joiner + BOM:
#   U+200B-U+200F, U+202A-U+202E, U+2060-U+206F, U+FEFF
# This regex INTENTIONALLY contains the bidi control chars it exists to
# match — the whole point of the module is to strip them. Bandit's B613
# "trojan source" check is a false positive here; this IS the defense.
_BIDI_AND_INVISIBLE_CHARS = re.compile(r"[​-‏‪-‮⁠-⁯﻿]")  # nosec B613
_FORBIDDEN_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_WHITESPACE_RUN = re.compile(r"\s+")
_UNDERSCORE_RUN = re.compile(r"_+")

MAX_SEGMENT_LEN = 64


def sanitize_path_segment(value: str, *, empty_placeholder: str = "attachment") -> str:
    """Normalize a single filename / path segment.

    Order matters: bidi/zero-width chars are stripped BEFORE any other
    normalization so a visual-spoofing attack can't hide other transformations.
    """
    if not isinstance(value, str):
        return empty_placeholder
    s = value.strip()
    if not s:
        return empty_placeholder

    s = _BIDI_AND_INVISIBLE_CHARS.sub("", s)
    s = _WHITESPACE_RUN.sub("_", s)
    s = s.replace("-", "_")
    s = _FORBIDDEN_FILENAME_CHARS.sub("_", s)
    s = s.replace("..", "_")
    s = _UNDERSCORE_RUN.sub("_", s)
    s = s.strip("_")
    if len(s) > MAX_SEGMENT_LEN:
        s = s[:MAX_SEGMENT_LEN].rstrip("_")
    return s or empty_placeholder


def confine_to_root(raw: str | Path, *, allowed_root: str | Path) -> Path:
    """Resolve ``raw`` and assert it's under ``allowed_root``.

    Both inputs are canonicalized via ``Path.expanduser().resolve()`` before
    comparison — protects against symlink escape and ``..`` traversal.
    """
    try:
        root = Path(allowed_root).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"allowed_root could not be resolved: {exc}") from exc
    try:
        candidate = Path(raw).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"path could not be resolved: {exc}") from exc

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path {str(candidate)!r} escapes allowed root {str(root)!r}") from exc
    return candidate


__all__ = ["MAX_SEGMENT_LEN", "confine_to_root", "sanitize_path_segment"]
