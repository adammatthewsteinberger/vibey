# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json

import pytest

from cursorloop.domain.hooks_policy import (
    HOOK_SUCCESS_EXIT,
    MANAGED_EVENTS,
    allow_payload,
    preamble_injection_payload,
)


def test_managed_events_are_the_autonomy_set() -> None:
    assert MANAGED_EVENTS == (
        "preToolUse",
        "beforeShellExecution",
        "beforeMCPExecution",
        "beforeReadFile",
        "beforeSubmitPrompt",
        "stop",
    )


def test_allow_payload_is_permission_allow_for_every_managed_event() -> None:
    for event in MANAGED_EVENTS:
        payload = allow_payload(event)
        assert payload["permission"] == "allow"
        assert "deny" not in payload.values()
        assert "ask" not in payload.values()


def test_allow_payload_rejects_unmanaged_events() -> None:
    with pytest.raises(ValueError):
        allow_payload("sessionStart")


def test_preamble_injection_payload_carries_additional_context() -> None:
    payload = preamble_injection_payload("You are running autonomously.")
    assert payload["additional_context"] == "You are running autonomously."
    assert payload["permission"] == "allow"


def test_payloads_are_json_object_of_strings() -> None:
    allow = allow_payload("preToolUse")
    inject = preamble_injection_payload("preamble")
    for payload in (allow, inject):
        encoded = json.dumps(payload)
        decoded = json.loads(encoded)
        assert decoded == payload
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in payload.items())


def test_success_exit_is_never_the_blocking_code() -> None:
    """Exit 2 blocks the action. Autonomy hooks exist to ALLOW, so the
    domain builder must never advertise that exit."""
    assert HOOK_SUCCESS_EXIT == 0
    assert HOOK_SUCCESS_EXIT != 2
