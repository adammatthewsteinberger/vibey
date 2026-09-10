# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from cursorloop.infrastructure.config import load_config


def test_only_cursorloop_and_cursor_env_vars_are_read(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-be-ignored")
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_real")
    monkeypatch.setenv("CURSORLOOP_MAX_WAIT", "3600")
    config = load_config()
    assert config.api_key == "crsr_real"
    assert config.max_wait_seconds == 3600
    assert "ANTHROPIC_API_KEY" not in config.observed_env


def test_billing_lexicon_is_overridable_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("CURSORLOOP_BILLING_LEXICON", "wallet_empty,no_funds")
    assert load_config().billing_terms == ("wallet_empty", "no_funds")
