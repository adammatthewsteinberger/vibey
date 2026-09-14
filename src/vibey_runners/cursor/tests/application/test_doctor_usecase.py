# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cursorloop.application.usecases.doctor import explain_error_payload


def test_explain_error_payload_classifies_billing_from_json(tmp_path: Path) -> None:
    path = tmp_path / "err.json"
    path.write_text(
        json.dumps(
            {
                "error_type": "RateLimitError",
                "error_code": "usage_limit_reached",
                "proto_error_code": "usage_limit_reached",
                "error_message": "You're out of usage.",
                "http_status": 402,
                "is_retryable": False,
                "retry_after": None,
                "run_status": "error",
                "result_text": "add credits",
            }
        ),
        encoding="utf-8",
    )
    assert explain_error_payload(path) == "CreditsExhausted"


def test_explain_error_payload_rejects_non_object_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        explain_error_payload(path)


def test_explain_error_payload_coerces_message_and_result_aliases(tmp_path: Path) -> None:
    path = tmp_path / "aliases.json"
    path.write_text(
        json.dumps(
            {
                "message": "payment required",
                "result": "add credits",
                "run_status": "error",
                "http_status": "not-an-int",
                "is_retryable": "not-a-bool",
            }
        ),
        encoding="utf-8",
    )
    assert explain_error_payload(path) == "CreditsExhausted"
