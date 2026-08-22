# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.infrastructure.ledger.redact import REDACTED, contains_secret, redact_payload


def test_sensitive_key_name_is_redacted_regardless_of_value() -> None:
    payload = {"api_key": "anything", "note": "fine"}
    result = redact_payload(payload)
    assert result["api_key"] == REDACTED
    assert result["note"] == "fine"


def test_openai_style_secret_key_is_redacted_in_free_text() -> None:
    payload = {"text": "use sk-abcdefghijklmnopqrstuvwx to authenticate"}
    result = redact_payload(payload)
    assert "sk-abcdefghijklmnopqrstuvwx" not in result["text"]
    assert REDACTED in result["text"]


def test_aws_access_key_id_is_redacted() -> None:
    payload = {"text": "key is AKIAABCDEFGHIJKLMNOP"}
    result = redact_payload(payload)
    assert "AKIAABCDEFGHIJKLMNOP" not in result["text"]


def test_github_token_is_redacted() -> None:
    payload = {"text": "ghp_" + "a" * 40}
    result = redact_payload(payload)
    assert "ghp_" + "a" * 40 not in result["text"]


def test_slack_token_is_redacted() -> None:
    payload = {"text": "xoxb-1234567890-abcdefghij"}
    result = redact_payload(payload)
    assert "xoxb-1234567890-abcdefghij" not in result["text"]


def test_bearer_token_is_redacted() -> None:
    payload = {"header": "Authorization: Bearer abcdefghij1234567890"}
    result = redact_payload(payload)
    assert "abcdefghij1234567890" not in result["header"]


def test_nested_mapping_is_redacted() -> None:
    payload = {"outer": {"password": "hunter2", "safe": "ok"}}
    result = redact_payload(payload)
    assert result["outer"]["password"] == REDACTED
    assert result["outer"]["safe"] == "ok"


def test_list_of_strings_is_redacted() -> None:
    payload = {"lines": ["clean line", "token is sk-" + "x" * 20]}
    result = redact_payload(payload)
    assert result["lines"][0] == "clean line"
    assert "sk-" + "x" * 20 not in result["lines"][1]


def test_non_string_values_pass_through_unchanged() -> None:
    payload = {"count": 5, "ok": True, "ratio": 1.5, "nothing": None}
    result = redact_payload(payload)
    assert result == payload


def test_clean_payload_is_unchanged() -> None:
    payload = {"summary": "added the outbox table", "cost_usd": 0.01}
    assert redact_payload(payload) == payload
    assert contains_secret(payload) is False


def test_contains_secret_detects_a_planted_secret() -> None:
    payload = {"detail": "sk-" + "y" * 20}
    assert contains_secret(payload) is True
