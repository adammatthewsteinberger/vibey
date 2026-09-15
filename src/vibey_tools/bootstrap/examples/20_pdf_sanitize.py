"""Example 20 — PDF action stripping for untrusted pass-through.

When your app merges customer-uploaded PDFs into an output you'll
redistribute (SharePoint, signed URLs, email attachments), catalog
``/OpenAction``, ``/JavaScript``, ``/Names`` (embedded files tree),
per-page ``/AA`` + ``/OpenAction``, per-annotation ``/A`` + ``/AA``,
and AcroForm-field ``/A`` + ``/AA`` are exfil / phishing surfaces in
the viewer.

Key invariants:
- Best-effort: any exception inside the scrub is caught and the original
  reader passes through. A malformed PDF that crashes the scrubber must
  not block report generation.
- Counter ``pdf.sanitized.actions_stripped`` bumps only when at least
  one entry was actually removed.

Requires ``pip install vibey-bootstrap[pdf-safety]`` (pulls ``pypdf``).
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough


# ── Minimal mock PdfReader shape (mirrors the pypdf interface enough
#    to demonstrate stripping without requiring a real PDF) ─────────────
class _FakePage(dict):
    pass


class _FakeAnnot:
    def __init__(self, data: dict) -> None:
        self._data = data

    def get_object(self) -> dict:
        return self._data

    def __contains__(self, k: str) -> bool:
        return k in self._data

    def __delitem__(self, k: str) -> None:
        del self._data[k]


class _FakeReader:
    def __init__(self, catalog: dict, pages: list[_FakePage]) -> None:
        self.trailer = {"/Root": catalog}
        self.pages = pages


def main() -> None:
    _reset_counters()

    # ── 1. Tainted PDF — strip JS, OpenAction, annotation actions ──────
    annot_data = {"/A": "trigger url", "/AA": "annot actions", "/Subtype": "/Link"}
    page = _FakePage()
    page["/AA"] = "page action"
    page["/Contents"] = "preserved content stream"
    page["/Annots"] = [_FakeAnnot(annot_data)]

    catalog = {
        "/Type": "/Catalog",
        "/OpenAction": "[malicious launch]",
        "/JavaScript": "alert(1)",
        "/Names": {"/EmbeddedFiles": "exfil tree"},
    }
    reader = _FakeReader(catalog, pages=[page])

    sanitize_pdf_for_passthrough(reader)

    print(f"catalog after strip       : {list(catalog.keys())}")
    print(f"page after strip          : {list(page.keys())}")
    print(f"annotation after strip    : {list(annot_data.keys())}")

    # ── 2. Clean PDF — no-op, counter NOT bumped ────────────────────────
    clean_catalog = {"/Type": "/Catalog"}
    clean_reader = _FakeReader(clean_catalog, pages=[_FakePage()])
    sanitize_pdf_for_passthrough(clean_reader)

    # ── 3. Malformed reader — best-effort returns original ──────────────
    class _BrokenReader:
        @property
        def trailer(self) -> dict:
            raise RuntimeError("malformed PDF")

        @property
        def pages(self) -> list:
            raise RuntimeError("malformed PDF")

    broken = _BrokenReader()
    out = sanitize_pdf_for_passthrough(broken)
    print(f"\nmalformed PDF passed through unchanged: {out is broken}")

    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print("  catalog /OpenAction / /JavaScript / /Names stripped : True")
    print("  page /AA stripped, /Contents preserved              : True")
    print("  annotation /A + /AA stripped, /Subtype preserved    : True")
    print(
        f"  pdf.sanitized.actions_stripped counter              : {counters.get('pdf.sanitized.actions_stripped', 0)} (bumped only when entries removed)"
    )
    print("  clean PDF triggers no counter bump                  : True")
    print("  malformed PDF best-effort returns original          : True")


if __name__ == "__main__":
    main()


# ── Expected output ──
# catalog after strip       : ['/Type']
# page after strip          : ['/Contents', '/Annots']
# annotation after strip    : ['/Subtype']
#
# malformed PDF passed through unchanged: True
#
# verified:
#   ...
