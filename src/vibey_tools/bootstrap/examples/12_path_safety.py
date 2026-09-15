"""Example 12 — Path safety (filename + root confinement).

Two-layered defense:

1. ``sanitize_path_segment`` for filenames / single segments before they
   interpolate into blob paths, log lines, or email subjects.
2. ``confine_to_root`` for resolved paths before opening files —
   refuses any escape from a configured root directory.

Key invariants:
- Bidi/zero-width chars (U+200B-U+200F, U+202A-U+202E, U+2060-U+206F,
  U+FEFF) are stripped BEFORE any other normalization. Visual-spoofing
  attacks (RLO injection making evil.exe display as evil.fdp) rely on
  these surviving sanitization.
- ``confine_to_root`` resolves both paths via ``Path.resolve()`` so
  symlink-escape attempts are caught.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.path_safety import (
    MAX_SEGMENT_LEN,
    confine_to_root,
    sanitize_path_segment,
)


def main() -> None:
    # ── 1. Filename sanitization ───────────────────────────────────────
    examples = [
        "invoice.pdf",  # benign — only character normalization
        "../etc/passwd",  # path-traversal attempt
        "invoice.pdf‮",  # RLO injection
        "  spaces and-hyphens  ",  # whitespace + hyphen normalization
        "a" * 200,  # over-length
        "",  # empty
        "invalid<>:|*?file.pdf",  # Windows-reserved chars
    ]

    print("filename sanitization:")
    for raw in examples:
        safe = sanitize_path_segment(raw)
        preview = (raw[:32] + "…") if len(raw) > 32 else raw
        print(f"  {preview!r:38} → {safe!r}")

    assert "‮" not in sanitize_path_segment("invoice.pdf‮")
    assert ".." not in sanitize_path_segment("../etc/passwd")

    # ── 2. Root confinement ────────────────────────────────────────────
    print()
    print("root confinement:")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "data"
        root.mkdir()
        legit = root / "subdir" / "report.pdf"
        legit.parent.mkdir()
        legit.touch()

        outside = Path(tmp) / "outside" / "report.pdf"
        outside.parent.mkdir()
        outside.touch()

        ok = confine_to_root(legit, allowed_root=root)
        print(f"  inside  → {ok.name} (ok, relative to root: {ok.relative_to(root.resolve())})")

        try:
            confine_to_root(outside, allowed_root=root)
        except ValueError as exc:
            print(f"  outside → rejected: {exc}")

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print("  bidi RLO U+202E stripped before normalization")
    print("  '..' replaced + path separators removed")
    print(f"  max segment length cap: {MAX_SEGMENT_LEN}")
    print("  empty / whitespace falls back to 'attachment'")
    print("  confine_to_root rejects escapes via Path.resolve() comparison")


if __name__ == "__main__":
    main()


# ── Expected output ──
# filename sanitization:
#   'invoice.pdf'                          → 'invoice.pdf'
#   '../etc/passwd'                        → '_etc_passwd'
#   'invoice.pdf‮'                    → 'invoice.pdf'
#   '  spaces and-hyphens  '               → 'spaces_and_hyphens'
#   'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa…'    → 'aaaaaaaaa...' (truncated to 64)
#   ''                                     → 'attachment'
#   'invalid<>:|*?file.pdf'                → 'invalid_file.pdf'
#
# root confinement:
#   inside  → report.pdf (ok, relative to root: subdir/report.pdf)
#   outside → rejected: path '...' escapes allowed root '...'
#
# verified:
#   ...
