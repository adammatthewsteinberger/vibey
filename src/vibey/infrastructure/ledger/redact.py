# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Redaction on write, ported in spirit from the *loop family: secrets must
never reach the ledger column, because the ledger is replicated into every
receiving worktree's .vibey/handoff/ledger.jsonl and read by whichever
engine is rotated in next. Pure text transform -- no I/O, safe to unit test
without a database, and applied by the ledger repository immediately
before a payload is persisted."""

import re
from collections.abc import Mapping

REDACTED = "[REDACTED]"

_SENSITIVE_KEY_NAMES = re.compile(
    r"(api[_-]?key|secret|password|passwd|token|auth[_-]?header|private[_-]?key|access[_-]?key)",
    re.IGNORECASE,
)

# Vendor-shaped credential patterns, independent of the field name they
# appear under (a secret pasted into free text is still a secret).
_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),  # OpenAI / Anthropic-style secret keys
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),  # GitHub personal access token
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),  # Slack tokens
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),  # Google API key
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{10,}"),
)


def _redact_string(value: str) -> str:
    redacted = value
    for pattern in _VALUE_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def _redact_value(key: str | None, value: object) -> object:
    if key is not None and _SENSITIVE_KEY_NAMES.search(key):
        return REDACTED
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, Mapping):
        return redact_payload(value)
    if isinstance(value, list | tuple):
        return [_redact_value(None, item) for item in value]
    return value


def redact_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """Recursively redacts sensitive key names and vendor-shaped secret
    patterns found anywhere in the payload, including inside nested
    mappings, lists, and free text."""
    return {key: _redact_value(key, value) for key, value in payload.items()}


def contains_secret(payload: Mapping[str, object]) -> bool:
    """True if redact_payload would change anything -- useful for a fast
    assertion in tests without diffing the whole structure."""
    return redact_payload(payload) != dict(payload)


__all__ = ["REDACTED", "contains_secret", "redact_payload"]
