"""Tests for ``vibey_bootstrap.logging.masking``."""

from __future__ import annotations

from vibey_bootstrap.logging.masking import (
    _looks_sensitive,
    _safe_repr,
    content_preview,
    mask_api_key,
    mask_bearer_token,
    mask_email_address,
    mask_secrets_in_dict,
    register_secret_keys,
    safe_json_dumps,
    sanitize_for_log,
)


class TestMaskApiKey:
    def test_none(self) -> None:
        assert mask_api_key(None) == "***"

    def test_empty(self) -> None:
        assert mask_api_key("") == "***"

    def test_short(self) -> None:
        assert mask_api_key("abc") == "***"

    def test_long(self) -> None:
        assert mask_api_key("abcdefgh") == "***efgh"


class TestMaskBearerToken:
    def test_bearer_prefix(self) -> None:
        assert mask_bearer_token("Bearer eyJabc") == "Bearer ***"

    def test_bearer_lowercase(self) -> None:
        assert mask_bearer_token("bearer eyJabc") == "Bearer ***"

    def test_no_bearer(self) -> None:
        assert mask_bearer_token("eyJabc") == "***"

    def test_none(self) -> None:
        assert mask_bearer_token(None) == "***"


class TestMaskEmailAddress:
    def test_short_local(self) -> None:
        assert mask_email_address("al@example.com") == "***@example.com"

    def test_truncated_local(self) -> None:
        assert mask_email_address("alice@example.com") == "***ce@example.com"

    def test_no_at(self) -> None:
        assert mask_email_address("no-at-sign") == "***"

    def test_empty_local(self) -> None:
        assert mask_email_address("@example.com") == "***@example.com"

    def test_none(self) -> None:
        assert mask_email_address(None) == "***"


class TestSanitizeForLog:
    def test_strips_every_control_char(self) -> None:
        for b in range(0x00, 0x20):
            assert sanitize_for_log(chr(b)) == "?", f"failed at byte {b:#x}"
        assert sanitize_for_log(chr(0x7F)) == "?"

    def test_preserves_normal_text(self) -> None:
        assert sanitize_for_log("hello world") == "hello world"

    def test_strips_newlines(self) -> None:
        assert sanitize_for_log("a\nb\rc\td") == "a?b?c?d"

    def test_truncates(self) -> None:
        out = sanitize_for_log("x" * 300, max_len=256)
        assert out.endswith("...[truncated]")
        assert out.startswith("x" * 256)

    def test_none(self) -> None:
        assert sanitize_for_log(None) == ""


class TestMaskSecretsInDict:
    def test_case_insensitive(self) -> None:
        masked = mask_secrets_in_dict(
            {"Authorization": "Bearer xyz", "Note": "ok", "X-API-Key": "abc"}
        )
        assert masked["Authorization"] == "***"
        assert masked["Note"] == "ok"
        assert masked["X-API-Key"] == "***"

    def test_keeps_falsy(self) -> None:
        masked = mask_secrets_in_dict({"api_key": "", "password": None})
        assert masked["api_key"] == ""
        assert masked["password"] is None

    def test_register_extends_allowlist(self) -> None:
        register_secret_keys("custom_secret_field")
        masked = mask_secrets_in_dict({"custom_secret_field": "live-value"})
        assert masked["custom_secret_field"] == "***"


class TestSafeRepr:
    def test_primitives(self) -> None:
        assert _safe_repr(None) == "None"
        assert _safe_repr(True) == "True"
        assert _safe_repr(42) == "42"

    def test_string_truncates(self) -> None:
        out = _safe_repr("x" * 500, max_len=50)
        assert len(out) <= 51
        assert out.endswith("…")

    def test_bytes(self) -> None:
        assert _safe_repr(b"\x00\x01") == "<bytes len=2>"

    def test_containers(self) -> None:
        assert _safe_repr([1, 2, 3]) == "<list len=3>"
        assert _safe_repr((1, 2)) == "<tuple len=2>"
        assert _safe_repr({1, 2, 3}) == "<set len=3>"
        assert _safe_repr({"a": 1}) == "<dict len=1>"

    def test_never_calls_heavy_repr(self) -> None:
        class Heavy:
            def __repr__(self) -> str:
                raise RuntimeError("expensive __repr__ raised")

        out = _safe_repr(Heavy())
        assert out == "<Heavy>"


class TestContentPreview:
    def test_bytes_decode(self) -> None:
        assert content_preview(b"hello") == "hello"

    def test_string_truncate(self) -> None:
        out = content_preview("a" * 1000, max_len=100)
        assert out.endswith("...[truncated]")


class TestSafeJsonDumps:
    def test_basic(self) -> None:
        assert safe_json_dumps({"a": 1}) == '{"a": 1}'

    def test_non_serializable_falls_back(self) -> None:
        class Obj:
            pass

        out = safe_json_dumps(Obj())
        assert isinstance(out, str)


class TestLooksSensitive:
    def test_substring_hits(self) -> None:
        assert _looks_sensitive("user_password")
        assert _looks_sensitive("API_KEY")
        assert _looks_sensitive("connection_string")
        assert _looks_sensitive("bearer_token")

    def test_safe_names_pass(self) -> None:
        assert not _looks_sensitive("user_id")
        assert not _looks_sensitive("operation")
