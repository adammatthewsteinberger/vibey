# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/redact.py — recursive redaction of secrets."""

from __future__ import annotations

from claudeloop.infrastructure.redact import REDACTED_VALUE, redact, redact_string


def test_redact_string_sk_ant_token() -> None:
    value = "my key is sk-ant-abcdefghijklmnopqrstuvwxyz"
    result = redact_string(value)
    assert "sk-ant-" not in result
    assert REDACTED_VALUE in result


def test_redact_string_sk_token() -> None:
    value = "key=sk-abcdefghijklmnopqrstuvwxyz"
    result = redact_string(value)
    assert "sk-" not in result
    assert REDACTED_VALUE in result


def test_redact_string_bearer_token() -> None:
    value = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    result = redact_string(value)
    assert "eyJ" not in result
    assert REDACTED_VALUE in result


def test_redact_string_no_secrets() -> None:
    value = "hello world"
    assert redact_string(value) == value


def test_redact_dict_secret_keys() -> None:
    data = {"api_key": "secret123", "name": "test"}
    result = redact(data)
    assert result["api_key"] == REDACTED_VALUE
    assert result["name"] == "test"


def test_redact_dict_case_insensitive_key_matching() -> None:
    data = {"Authorization": "secret", "X-Api-Key": "key123"}
    result = redact(data)
    assert result["Authorization"] == REDACTED_VALUE
    assert result["X-Api-Key"] == REDACTED_VALUE


def test_redact_nested_dict() -> None:
    data = {"outer": {"password": "s3cret", "ok": "fine"}}
    result = redact(data)
    assert result["outer"]["password"] == REDACTED_VALUE
    assert result["outer"]["ok"] == "fine"


def test_redact_list() -> None:
    data = [{"api_key": "secret"}, "normal"]
    result = redact(data)
    assert result[0]["api_key"] == REDACTED_VALUE
    assert result[1] == "normal"


def test_redact_tuple() -> None:
    data = ({"secret": "val"}, "text")
    result = redact(data)
    assert isinstance(result, tuple)
    assert result[0]["secret"] == REDACTED_VALUE
    assert result[1] == "text"


def test_redact_string_in_value() -> None:
    data = {"msg": "token is sk-ant-AAAABBBBCCCCDDDDEEEEFFFFF"}
    result = redact(data)
    assert "sk-ant-" not in result["msg"]


def test_redact_non_string_non_container() -> None:
    assert redact(42) == 42
    assert redact(3.14) == 3.14
    assert redact(None) is None
    assert redact(True) is True


def test_redact_all_secret_key_names() -> None:
    for key in [
        "api_key",
        "apikey",
        "authorization_token",
        "access_token",
        "refresh_token",
        "client_secret",
        "secret_value",
        "secret",
        "password",
        "authorization",
        "x-api-key",
        "x_api_key",
        "anthropic_api_key",
        "bearer",
    ]:
        data = {key: "should-be-redacted"}
        result = redact(data)
        assert result[key] == REDACTED_VALUE, f"key {key!r} was not redacted"


def test_redact_list_of_strings_with_credentials() -> None:
    data = ["sk-abcdefghijklmnopqrstuvwxyz", "normal-value"]
    result = redact(data)
    assert REDACTED_VALUE in result[0]
    assert result[1] == "normal-value"
