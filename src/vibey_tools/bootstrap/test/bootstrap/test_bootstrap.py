"""Tests for ``vibey_bootstrap.bootstrap``."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from vibey_bootstrap.bootstrap import (
    _reset_bootstrap_state,
    bootstrap_initialized,
    ensure_bootstrap,
    load_local_settings,
)


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_bootstrap_state()
    yield
    _reset_bootstrap_state()


def test_ensure_bootstrap_idempotent_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    ensure_bootstrap()
    assert bootstrap_initialized() is True
    ensure_bootstrap()  # no-op
    assert bootstrap_initialized() is True


def test_ensure_bootstrap_mock_short_circuits_initialize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    with patch(
        "vibey_bootstrap.services.application_bootstrap.initialize_application"
    ) as fake_init:
        ensure_bootstrap()
    fake_init.assert_not_called()


def test_load_local_settings_skips_underscore_keys(tmp_path: Path) -> None:
    p = tmp_path / "local.settings.json"
    p.write_text(json.dumps({"Values": {"_COMMENT": "x", "FOO_TEST": "bar"}}))
    os.environ.pop("FOO_TEST", None)
    os.environ.pop("_COMMENT", None)
    loaded = load_local_settings(p)
    assert os.environ.get("FOO_TEST") == "bar"
    assert "_COMMENT" not in os.environ
    assert loaded == 1


def test_load_local_settings_never_overrides_existing(tmp_path: Path) -> None:
    p = tmp_path / "local.settings.json"
    p.write_text(json.dumps({"Values": {"PRESERVED_KEY_TEST": "fromfile"}}))
    os.environ["PRESERVED_KEY_TEST"] = "preserved"
    try:
        load_local_settings(p)
        assert os.environ["PRESERVED_KEY_TEST"] == "preserved"
    finally:
        os.environ.pop("PRESERVED_KEY_TEST", None)


def test_load_local_settings_missing_file_silent() -> None:
    assert load_local_settings("/tmp/nonexistent.json") == 0


def test_load_local_settings_bad_json_silent(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json")
    assert load_local_settings(p) == 0
