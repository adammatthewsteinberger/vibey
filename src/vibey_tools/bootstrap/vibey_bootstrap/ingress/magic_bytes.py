"""Magic-byte classifier (authoritative — final gate in the pipeline).

When the extension says PDF and the bytes say something else, the bytes win.
This catches `evil.exe` renamed to `report.pdf` with the right MIME — the
extension and MIME gates can be lied to; the leading bytes cannot.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

ClassifiedKind = Literal["pdf", "zip", "gzip", "png", "jpeg", "reject"]

_SIGNATURES: dict[ClassifiedKind, tuple[bytes, ...]] = {
    "pdf": (b"%PDF-",),
    "zip": (b"PK\x03\x04",),
    "gzip": (b"\x1f\x8b",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpeg": (b"\xff\xd8\xff",),
}

_EXTENSION_TO_KIND: dict[str, ClassifiedKind] = {
    ".pdf": "pdf",
    ".zip": "zip",
    ".gz": "gzip",
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
}


def classify_bytes(
    content: bytes,
    *,
    allowed: tuple[ClassifiedKind, ...] = ("pdf", "zip"),
) -> ClassifiedKind:
    """Match the leading bytes against the signature table.

    Returns the first matched kind that's in ``allowed``; otherwise ``"reject"``.
    """
    if not isinstance(content, (bytes, bytearray)):
        return "reject"
    head = bytes(content[:16])
    for kind, sigs in _SIGNATURES.items():
        if kind not in allowed:
            continue
        for sig in sigs:
            if head.startswith(sig):
                return kind
    return "reject"


def extension_matches_kind(filename: str, kind: ClassifiedKind) -> bool:
    """Audit helper — is the filename's extension consistent with the bytes?"""
    if not filename or kind == "reject":
        return False
    suffix = PurePosixPath(filename).suffix.lower()
    expected = _EXTENSION_TO_KIND.get(suffix)
    return expected == kind


__all__ = ["ClassifiedKind", "classify_bytes", "extension_matches_kind"]
