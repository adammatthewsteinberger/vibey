"""Tests for ``vibey_bootstrap.path_safety``."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibey_bootstrap.path_safety import (
    MAX_SEGMENT_LEN,
    confine_to_root,
    sanitize_path_segment,
)


class TestSanitizeSegment:
    def test_strips_rlo_override(self) -> None:
        out = sanitize_path_segment("invoice.pdf‮")
        assert "‮" not in out

    def test_strips_zero_width(self) -> None:
        out = sanitize_path_segment("a​b")
        assert out == "ab"

    def test_collapses_dotdot(self) -> None:
        out = sanitize_path_segment("../etc/passwd")
        assert ".." not in out
        assert "/" not in out

    def test_truncates_to_max(self) -> None:
        out = sanitize_path_segment("x" * 200)
        assert len(out) <= MAX_SEGMENT_LEN

    def test_falls_back_to_placeholder(self) -> None:
        assert sanitize_path_segment("   ") == "attachment"
        assert sanitize_path_segment("") == "attachment"

    def test_custom_placeholder(self) -> None:
        assert sanitize_path_segment("", empty_placeholder="report") == "report"

    def test_replaces_forbidden_chars(self) -> None:
        out = sanitize_path_segment("foo/bar:baz")
        for c in '/:*?<>|"':
            assert c not in out

    def test_non_string_returns_placeholder(self) -> None:
        assert sanitize_path_segment(None) == "attachment"  # type: ignore[arg-type]
        assert sanitize_path_segment(42) == "attachment"  # type: ignore[arg-type]


class TestConfineToRoot:
    def test_accepts_subpath(self, tmp_path: Path) -> None:
        root = tmp_path / "data"
        root.mkdir()
        inside = root / "subdir" / "file.pdf"
        inside.parent.mkdir(parents=True)
        inside.touch()
        out = confine_to_root(inside, allowed_root=root)
        assert out.is_relative_to(root.resolve())

    def test_rejects_escape(self, tmp_path: Path) -> None:
        root = tmp_path / "data"
        root.mkdir()
        outside = tmp_path / "outside" / "file.pdf"
        outside.parent.mkdir()
        outside.touch()
        with pytest.raises(ValueError, match="escapes allowed root"):
            confine_to_root(outside, allowed_root=root)

    def test_rejects_dotdot_traversal(self, tmp_path: Path) -> None:
        root = tmp_path / "data"
        root.mkdir()
        target = root / "subdir" / ".." / ".." / "etc"
        with pytest.raises(ValueError):
            confine_to_root(target, allowed_root=root)
