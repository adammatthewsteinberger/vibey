# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for API JSON payload loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from codexloop.infrastructure.api.json_io import load_json_payload


def test_inline_json() -> None:
    assert load_json_payload(inline='{"model":"gpt-4o"}', json_file=None) == {"model": "gpt-4o"}


def test_json_file(tmp_path: Path) -> None:
    path = tmp_path / "body.json"
    path.write_text('{"n": 1}', encoding="utf-8")
    assert load_json_payload(inline=None, json_file=path) == {"n": 1}


def test_at_path_indirection(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text('{"ok": true}', encoding="utf-8")
    pointer = tmp_path / "pointer.json"
    pointer.write_text(f"@{real}", encoding="utf-8")
    assert load_json_payload(inline=None, json_file=pointer) == {"ok": True}


def test_rejects_both() -> None:
    with pytest.raises(ValueError, match="only one"):
        load_json_payload(inline="{}", json_file=Path("x.json"))


def test_rejects_non_object() -> None:
    with pytest.raises(TypeError, match="object"):
        load_json_payload(inline="[]", json_file=None)
