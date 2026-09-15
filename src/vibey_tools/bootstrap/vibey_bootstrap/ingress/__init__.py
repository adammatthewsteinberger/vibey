"""Tier 2 attachment / file-upload hardening.

Four gates, fixed order: extension → MIME → size → magic-byte. Use
:class:`AttachmentClassifier` to run the whole pipeline; each gate is
also independently usable for projects that need finer control.
"""

from vibey_bootstrap.ingress.classifier import AttachmentClassifier, ClassificationResult
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
from vibey_bootstrap.ingress.zip_safety import (
    MAX_ZIP_ENTRIES,
    MAX_ZIP_UNCOMPRESSED_BYTES,
    enforce_zip_safety_limits,
)

__all__ = [
    "AttachmentClassifier",
    "ClassificationResult",
    "ClassifiedKind",
    "DEFAULT_MAX_PDF_BYTES",
    "DEFAULT_MAX_ZIP_UNCOMPRESSED_BYTES",
    "ExtensionAllowlist",
    "MAX_ZIP_ENTRIES",
    "MAX_ZIP_UNCOMPRESSED_BYTES",
    "MimeAllowlist",
    "classify_bytes",
    "enforce_size_cap",
    "enforce_zip_safety_limits",
    "extension_matches_kind",
]
