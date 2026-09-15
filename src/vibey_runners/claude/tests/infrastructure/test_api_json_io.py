# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Unit tests for ``--json`` / ``--json-file`` payload parsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claudeloop.infrastructure.api.json_io import load_json_payload


def test_load_json_payload_empty_when_neither_source_given() -> None:
    assert load_json_payload(inline=None, json_file=None) == {}


def test_load_json_payload_rejects_both_sources(tmp_path: Path) -> None:
    path = tmp_path / "body.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="only one of --json or --json-file"):
        load_json_payload(inline='{"a": 1}', json_file=path)


def test_load_json_payload_reads_inline_object() -> None:
    assert load_json_payload(inline='{"model": "claude"}', json_file=None) == {"model": "claude"}


def test_load_json_payload_rejects_non_object_top_level() -> None:
    with pytest.raises(TypeError, match="must be an object"):
        load_json_payload(inline="[1, 2]", json_file=None)


def test_load_json_payload_reads_json_file(tmp_path: Path) -> None:
    path = tmp_path / "body.json"
    path.write_text(json.dumps({"max_tokens": 10}), encoding="utf-8")
    assert load_json_payload(inline=None, json_file=path) == {"max_tokens": 10}


def test_load_json_payload_follows_at_path_indirection(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    real.write_text(json.dumps({"stream": True}), encoding="utf-8")
    pointer = tmp_path / "pointer.json"
    pointer.write_text(f"@{real}", encoding="utf-8")
    assert load_json_payload(inline=None, json_file=pointer) == {"stream": True}
