"""Example 15 — Attachment classifier (4-gate pipeline).

Gate order is fixed: extension → MIME → size → magic-byte. Earlier gates
are cheaper and short-circuit later ones. Magic-byte is the final
authority; when bytes disagree with the extension, the bytes win
(``attachment.mismatched_extension`` bumps to surface the lie).

Key invariants:
- Pipeline order is non-negotiable — reordering creates DoS vectors.
- An ``.exe`` named ``report.pdf`` with PDF MIME + PDF magic bytes is
  still rejected at the extension gate.
- Bytes are authoritative — a real PDF named ``report.zip`` passes with
  ``extension_mismatch=True`` so monitoring catches the spike.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.ingress import AttachmentClassifier


def main() -> None:
    _reset_counters()
    classifier = AttachmentClassifier()

    cases = [
        # (name, content_type, size, content, narrative)
        (
            "report.pdf",
            "application/pdf",
            1024,
            b"%PDF-1.7" + b"x" * 100,
            "happy path",
        ),
        (
            "evil.exe",
            "application/pdf",
            1024,
            b"%PDF-1.7" + b"x" * 100,
            "attacker renames .exe → .pdf",
        ),
        (
            "weird.pdf",
            "application/x-msdownload",
            1024,
            b"%PDF-1.7",
            "PDF extension + executable MIME",
        ),
        (
            "report.pdf",
            "application/pdf",
            1024,
            b"NOPE-not-a-pdf",
            "extension+MIME lie; bytes catch it",
        ),
        (
            "report.zip",
            "application/octet-stream",
            1024,
            b"%PDF-1.7",
            "real PDF named .zip (mismatch flag)",
        ),
        (
            "huge.pdf",
            "application/pdf",
            200 * 1024 * 1024,
            b"%PDF-1.7",
            "exceeds size cap",
        ),
    ]

    print("classifier verdicts:")
    for name, mime, size, content, narrative in cases:
        r = classifier.classify(
            filename=name,
            content_type=mime,
            size_bytes=size,
            content=content,
        )
        verdict = "ACCEPT" if r.allowed else "REJECT"
        details = f"kind={r.kind!s}"
        if r.reject_reason:
            details += f" reason={r.reject_reason}"
        if r.extension_mismatch:
            details += " ⚠ extension_mismatch"
        print(f"  {verdict:6} {name:14} {details}  // {narrative}")

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(
        f"  attachment.rejected.unsupported_type   : {counters.get('attachment.rejected.unsupported_type', 0)}"
    )
    print(
        f"  attachment.rejected.mime               : {counters.get('attachment.rejected.mime', 0)}"
    )
    print(
        f"  attachment.rejected.size_cap           : {counters.get('attachment.rejected.size_cap', 0)}"
    )
    print(
        f"  attachment.rejected.magic_byte         : {counters.get('attachment.rejected.magic_byte', 0)}"
    )
    print(
        f"  attachment.mismatched_extension        : {counters.get('attachment.mismatched_extension', 0)}"
    )
    print(
        f"  attachment.classified.pdf              : {counters.get('attachment.classified.pdf', 0)}"
    )


if __name__ == "__main__":
    main()


# ── Expected output ──
# classifier verdicts:
#   ACCEPT report.pdf      kind=pdf  // happy path
#   REJECT evil.exe        kind=None reason=unsupported_extension: .exe  // attacker renames .exe → .pdf
#   REJECT weird.pdf       kind=None reason=mime: application/x-msdownload  // PDF extension + executable MIME
#   REJECT report.pdf      kind=None reason=magic_byte: unknown signature  // extension+MIME lie; bytes catch it
#   ACCEPT report.zip      kind=pdf ⚠ extension_mismatch  // real PDF named .zip (mismatch flag)
#   REJECT huge.pdf        kind=None reason=size_cap: ...  // exceeds size cap
#
# verified:
#   attachment.rejected.unsupported_type   : 1
#   attachment.rejected.mime               : 1
#   attachment.rejected.size_cap           : 1
#   attachment.rejected.magic_byte         : 1
#   attachment.mismatched_extension        : 1
#   attachment.classified.pdf              : 2
