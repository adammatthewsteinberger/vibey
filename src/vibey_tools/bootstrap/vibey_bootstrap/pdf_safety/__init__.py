"""PDF action stripping for untrusted pass-through.

When an app merges customer-uploaded PDFs into an output that will be
redistributed, the catalog-level OpenAction, AcroForm-field actions, page
actions, and annotation actions are an exfiltration / phishing risk if the
viewer renders them. This module strips them in-place before
``writer.append(reader)``.

Best-effort: any exception inside the scrub is caught and the original
reader passes through. Reason: a malformed PDF that crashes the scrubber
must not block report generation — the ingress gates already classified
it as a valid PDF.
"""

from __future__ import annotations

import logging
from typing import Any

from vibey_bootstrap.counters import bump_counter

_logger = logging.getLogger(__name__)

_CATALOG_STRIP_KEYS = ("/OpenAction", "/AA", "/JavaScript", "/Names", "/URI")
_PAGE_STRIP_KEYS = ("/AA", "/OpenAction")
_ANNOT_STRIP_KEYS = ("/A", "/AA")
_FIELD_STRIP_KEYS = ("/A", "/AA")


def _strip_keys(obj: Any, keys: tuple[str, ...]) -> int:
    """Try to delete each key from a PDF dictionary; return count removed."""
    removed = 0
    if obj is None:
        return 0
    for key in keys:
        try:
            if key in obj:
                del obj[key]
                removed += 1
        except Exception:
            continue
    return removed


def sanitize_pdf_for_passthrough(reader: Any) -> Any:
    """Strip executable / network-bearing entries from a PdfReader.

    Mutates the reader in place AND returns it for ergonomic chaining.
    Best-effort: never raises; on any exception during scrub, returns the
    original reader unchanged and skips the counter bump.
    """
    try:
        removed_total = 0

        # Catalog-level scrub
        try:
            root = reader.trailer["/Root"]
            removed_total += _strip_keys(root, _CATALOG_STRIP_KEYS)
        except Exception:
            pass

        # AcroForm fields
        try:
            acroform = reader.trailer["/Root"].get("/AcroForm")
            if acroform is not None:
                fields = acroform.get("/Fields") or []
                for field in fields:
                    try:
                        removed_total += _strip_keys(field, _FIELD_STRIP_KEYS)
                    except Exception:
                        continue
        except Exception:
            pass

        # Per-page + per-annotation scrub
        try:
            for page in reader.pages:
                try:
                    removed_total += _strip_keys(page, _PAGE_STRIP_KEYS)
                    annots = page.get("/Annots")
                    if annots is None:
                        continue
                    for annot in annots:
                        try:
                            try:
                                annot_obj = annot.get_object()
                            except Exception:
                                annot_obj = annot
                            removed_total += _strip_keys(annot_obj, _ANNOT_STRIP_KEYS)
                        except Exception:
                            continue
                except Exception:
                    continue
        except Exception:
            pass

        if removed_total > 0:
            bump_counter("pdf.sanitized.actions_stripped")
    except Exception:
        _logger.exception("sanitize_pdf_for_passthrough: scrub raised; passing through")
    return reader


__all__ = ["sanitize_pdf_for_passthrough"]
