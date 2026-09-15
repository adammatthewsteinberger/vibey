"""_reset_transports is gated on AZURE_BOOTSTRAP_ALLOW_RESET=1."""

from __future__ import annotations

import pytest

import vibey_bootstrap.transports as transports


def test_reset_requires_allow_flag(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError):
        transports._reset_transports()


def test_reset_clears_and_reregisters_builtins() -> None:
    # Allowed (top-level conftest sets the flag); builtins are re-registered.
    transports.register_transport("ephemeral", lambda: None)
    transports._reset_transports()
    names = set(transports.list_transports())
    assert names == {
        "console",
        "app_insights",
        "sumo_logic",
        "panther",
        "file",
        "blob",
        "sql",
        "nosql",
        "adx",
        "event_hubs",
    }
    assert "ephemeral" not in names
