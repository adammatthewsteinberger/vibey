"""MIME allowlist gate (advisory — magic-byte gate is the real authority)."""

from __future__ import annotations

from collections.abc import Iterable

_DEFAULT_MIMES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/zip",
        "application/x-zip-compressed",
        "application/x-gzip",
        "application/gzip",
        "application/octet-stream",
    }
)


class MimeAllowlist:
    def __init__(self, allowed: Iterable[str] = _DEFAULT_MIMES) -> None:
        self._allowed = frozenset(m.lower() for m in allowed if m)

    @property
    def allowed(self) -> frozenset[str]:
        return self._allowed

    def allows(self, content_type: str | None) -> bool:
        if content_type is None:
            return False
        return content_type.split(";", 1)[0].strip().lower() in self._allowed

    def reject_reason(self, content_type: str | None) -> str | None:
        if self.allows(content_type):
            return None
        return f"mime: {content_type or '(none)'}"


__all__ = ["MimeAllowlist"]
