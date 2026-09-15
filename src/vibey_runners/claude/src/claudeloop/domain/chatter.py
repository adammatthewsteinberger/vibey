# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pure helpers for chatter field truncation and event payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CHATTER_FIELD_CAP_BYTES = 256 * 1024
SUMMARY_PREVIEW_BYTES = 512


@dataclass(frozen=True, slots=True)
class TruncatedText:
    text: str
    truncated: bool


def truncate_chatter(value: str, *, cap_bytes: int = CHATTER_FIELD_CAP_BYTES) -> TruncatedText:
    encoded = value.encode("utf-8")
    if len(encoded) <= cap_bytes:
        return TruncatedText(text=value, truncated=False)
    # Cut on a UTF-8 boundary.
    cut = encoded[:cap_bytes]
    while cut and (cut[-1] & 0xC0) == 0x80:
        cut = cut[:-1]
    return TruncatedText(text=cut.decode("utf-8", errors="ignore"), truncated=True)


def chatter_event_payload(
    text: str,
    *,
    mode: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build a chatter.* event payload, or None when mode is off.

    Summary mode still emits a short ``preview`` for console logs, but always
    includes full ``text`` (up to CHATTER_FIELD_CAP_BYTES) so stream-UI /
    event consumers are never capped at the preview size.
    """
    if mode == "off":
        return None
    full = truncate_chatter(text)
    payload: dict[str, Any] = {
        "text": full.text,
        "length": len(text),
        "truncated": full.truncated,
    }
    if mode == "summary":
        preview = truncate_chatter(text, cap_bytes=SUMMARY_PREVIEW_BYTES)
        payload["preview"] = preview.text
        payload["preview_truncated"] = preview.truncated or len(text) > len(preview.text)
    if extra:
        payload.update(extra)
    return payload
