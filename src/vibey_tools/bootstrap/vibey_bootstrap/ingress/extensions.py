"""Extension allowlist gate (cheapest, runs first in the classifier pipeline)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath

_DEFAULT_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".zip", ".gz"})


class ExtensionAllowlist:
    def __init__(self, extensions: Iterable[str] = _DEFAULT_EXTENSIONS) -> None:
        normalized: set[str] = set()
        for ext in extensions:
            if not ext:
                continue
            e = ext.lower()
            if not e.startswith("."):
                e = "." + e
            normalized.add(e)
        self._allowed = frozenset(normalized)

    @property
    def allowed(self) -> frozenset[str]:
        return self._allowed

    def _suffix(self, filename: str) -> str:
        if not filename:
            return ""
        return PurePosixPath(filename).suffix.lower()

    def allows(self, filename: str) -> bool:
        return self._suffix(filename) in self._allowed

    def reject_reason(self, filename: str) -> str | None:
        suffix = self._suffix(filename)
        if suffix in self._allowed:
            return None
        return f"unsupported_extension: {suffix or '(none)'}"


__all__ = ["ExtensionAllowlist"]
