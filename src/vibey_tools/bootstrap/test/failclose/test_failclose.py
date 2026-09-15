"""Tests for ``vibey_bootstrap.failclose``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.failclose import (
    ConfigurationError,
    fail_open_env,
    optional_env,
    require_env,
)


def test_configuration_error_is_v1_alias() -> None:
    from vibey_bootstrap.models.exceptions import ConfigurationError as V1Class

    assert ConfigurationError is V1Class


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("X_TEST_ENV", raising=False)


def test_require_env_raises_on_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ConfigurationError):
        require_env("X_TEST_ENV")


def test_require_env_raises_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_TEST_ENV", "")
    with pytest.raises(ConfigurationError):
        require_env("X_TEST_ENV")


def test_require_env_strips_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_TEST_ENV", "  value  ")
    assert require_env("X_TEST_ENV") == "value"


def test_require_env_raises_on_whitespace_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_TEST_ENV", "   ")
    with pytest.raises(ConfigurationError):
        require_env("X_TEST_ENV")


def test_optional_env_default() -> None:
    assert optional_env("X_TEST_ENV", default="x") == "x"


def test_optional_env_reads_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_TEST_ENV", "  hello  ")
    assert optional_env("X_TEST_ENV") == "hello"


def test_fail_open_env_none_when_unset() -> None:
    assert fail_open_env("X_TEST_ENV") is None


def test_fail_open_env_none_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_TEST_ENV", "")
    assert fail_open_env("X_TEST_ENV") is None


def test_fail_open_env_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("X_TEST_ENV", "live")
    assert fail_open_env("X_TEST_ENV") == "live"
