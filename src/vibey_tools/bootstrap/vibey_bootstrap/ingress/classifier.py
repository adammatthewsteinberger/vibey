"""Attachment classifier — runs the four gates in fixed order.

Gate order: extension → MIME → size → magic-byte. Earlier gates are cheaper
and short-circuit later ones. Magic-byte is always the final authority;
on extension/magic-byte mismatch we pass through (bytes win) but bump
``attachment.mismatched_extension`` so dashboards can spot a spike of
attackers renaming files.
"""

from __future__ import annotations

from dataclasses import dataclass

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import OversizedAttachmentError
from vibey_bootstrap.ingress.extensions import ExtensionAllowlist
from vibey_bootstrap.ingress.magic_bytes import (
    ClassifiedKind,
    classify_bytes,
    extension_matches_kind,
)
from vibey_bootstrap.ingress.mime import MimeAllowlist
from vibey_bootstrap.ingress.size import (
    DEFAULT_MAX_PDF_BYTES,
    DEFAULT_MAX_ZIP_UNCOMPRESSED_BYTES,
    enforce_size_cap,
)


@dataclass
class ClassificationResult:
    allowed: bool
    kind: ClassifiedKind | None
    reject_reason: str | None
    extension_mismatch: bool = False


class AttachmentClassifier:
    def __init__(
        self,
        *,
        extension_allowlist: ExtensionAllowlist | None = None,
        mime_allowlist: MimeAllowlist | None = None,
        size_caps: dict[ClassifiedKind, int] | None = None,
        counter_namespace: str = "attachment",
        allowed_kinds: tuple[ClassifiedKind, ...] = ("pdf", "zip"),
    ) -> None:
        self._ext = extension_allowlist or ExtensionAllowlist()
        self._mime = mime_allowlist or MimeAllowlist()
        self._size_caps: dict[ClassifiedKind, int] = size_caps or {
            "pdf": DEFAULT_MAX_PDF_BYTES,
            "zip": DEFAULT_MAX_ZIP_UNCOMPRESSED_BYTES,
        }
        self._namespace = counter_namespace
        self._allowed_kinds = allowed_kinds

    def _reject(self, reason: str, gate: str) -> ClassificationResult:
        bump_counter(f"{self._namespace}.rejected.{gate}")
        return ClassificationResult(
            allowed=False,
            kind=None,
            reject_reason=reason,
        )

    def classify(
        self,
        *,
        filename: str,
        content_type: str | None,
        size_bytes: int,
        content: bytes,
    ) -> ClassificationResult:
        # 1. Extension
        ext_reason = self._ext.reject_reason(filename)
        if ext_reason:
            return self._reject(ext_reason, "unsupported_type")

        # 2. MIME (advisory)
        mime_reason = self._mime.reject_reason(content_type)
        if mime_reason:
            return self._reject(mime_reason, "mime")

        # 3. Magic-byte classification (also tells us the size cap to apply)
        kind = classify_bytes(content, allowed=self._allowed_kinds)
        if kind == "reject":
            return self._reject("magic_byte: unknown signature", "magic_byte")

        # 4. Size cap (now we know the kind)
        cap = self._size_caps.get(kind)
        if cap is not None:
            try:
                enforce_size_cap(
                    size_bytes=size_bytes,
                    cap_bytes=cap,
                    filename=filename,
                    counter_name=f"{self._namespace}.rejected.size_cap",
                )
            except OversizedAttachmentError as exc:
                return ClassificationResult(
                    allowed=False,
                    kind=None,
                    reject_reason=f"size_cap: {exc}",
                )

        # 5. Extension/kind audit — pass-through with flag
        extension_mismatch = not extension_matches_kind(filename, kind)
        if extension_mismatch:
            bump_counter(f"{self._namespace}.mismatched_extension")

        bump_counter(f"{self._namespace}.classified.{kind}")
        return ClassificationResult(
            allowed=True,
            kind=kind,
            reject_reason=None,
            extension_mismatch=extension_mismatch,
        )


__all__ = ["AttachmentClassifier", "ClassificationResult"]
