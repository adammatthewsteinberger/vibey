# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

from claudeloop.infrastructure.config import RunnerConfig, load_config


def test_defaults_when_nothing_set(tmp_path: Path) -> None:
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config == RunnerConfig()


def test_file_overrides_defaults(tmp_path: Path) -> None:
    (tmp_path / "claudeloop.toml").write_text('max_turns = 5\nlog_level = "DEBUG"\n')
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config.max_turns == 5
    assert config.log_level == "DEBUG"


def test_home_config_applies_then_cwd_config_overrides_it(tmp_path: Path) -> None:
    home = tmp_path / "home"
    cwd = tmp_path / "cwd"
    (home / ".config" / "claudeloop").mkdir(parents=True)
    (home / ".config" / "claudeloop" / "config.toml").write_text(
        'max_turns = 1\nlog_level = "DEBUG"\n'
    )
    cwd.mkdir()
    (cwd / "claudeloop.toml").write_text("max_turns = 2\n")

    config = load_config(cwd=cwd, home=home)
    assert config.max_turns == 2  # cwd config wins over home config
    assert config.log_level == "DEBUG"  # but home config still applies where cwd is silent


def test_env_overrides_file(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "claudeloop.toml").write_text("max_turns = 5\n")
    monkeypatch.setenv("CLAUDELOOP_MAX_TURNS", "9")
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config.max_turns == 9


def test_cli_overrides_env_and_file(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "claudeloop.toml").write_text("max_turns = 5\n")
    monkeypatch.setenv("CLAUDELOOP_MAX_TURNS", "9")
    config = load_config(cwd=tmp_path, home=tmp_path, cli_overrides={"max_turns": 42})
    assert config.max_turns == 42


def test_cli_overrides_with_none_values_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "claudeloop.toml").write_text("max_turns = 5\n")
    config = load_config(cwd=tmp_path, home=tmp_path, cli_overrides={"max_turns": None})
    assert config.max_turns == 5  # None means "not provided", not "clear it"


def test_env_bool_coercion(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CLAUDELOOP_RETRY_WATCHDOG", "true")
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config.retry_watchdog is True


def test_env_float_coercion(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("CLAUDELOOP_MAX_DOLLARS", "12.5")
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config.max_dollars == 12.5


def test_env_str_coercion_passes_through_unchanged(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A field whose type hint is plain `str` (neither bool/float/int) hits
    _coerce's final fallback branch: the raw env string is returned as-is."""
    monkeypatch.setenv("CLAUDELOOP_LOG_LEVEL", "DEBUG")
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config.log_level == "DEBUG"


def test_unknown_keys_in_file_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "claudeloop.toml").write_text('not_a_real_field = "x"\nmax_turns = 3\n')
    config = load_config(cwd=tmp_path, home=tmp_path)
    assert config.max_turns == 3


def test_missing_file_is_not_an_error(tmp_path: Path) -> None:
    config = load_config(cwd=tmp_path / "does-not-exist", home=tmp_path)
    assert config == RunnerConfig()


def test_aliases_returns_model_aliases() -> None:
    config = RunnerConfig(model_low="low-model", model_medium="mid-model", model_high="high-model")
    aliases = config.aliases()
    assert aliases.low == "low-model"
    assert aliases.medium == "mid-model"
    assert aliases.high == "high-model"


def test_resolved_profile_calls_resolve() -> None:
    config = RunnerConfig(model="claude-opus", effort="high")
    profile = config.resolved_profile()
    assert profile.model == "claude-opus"
    assert profile.effort == "high"


def test_effective_log_chatter_from_config() -> None:
    config = RunnerConfig(log_chatter="full")
    assert config.effective_log_chatter() == "full"


def test_effective_log_chatter_invalid_raises() -> None:
    import pytest

    config = RunnerConfig(log_chatter="invalid")
    with pytest.raises(ValueError, match="invalid log_chatter"):
        config.effective_log_chatter()


def test_effective_log_chatter_debug_level_returns_full() -> None:
    config = RunnerConfig(log_level="DEBUG")
    assert config.effective_log_chatter() == "full"


def test_effective_log_chatter_default_is_summary() -> None:
    config = RunnerConfig()
    assert config.effective_log_chatter() == "summary"


def test_effective_partial_messages_explicit_true() -> None:
    config = RunnerConfig(include_partial_messages=True)
    assert config.effective_partial_messages() is True


def test_effective_partial_messages_explicit_false() -> None:
    config = RunnerConfig(include_partial_messages=False)
    assert config.effective_partial_messages() is False


def test_effective_partial_messages_defaults_to_stream_ui() -> None:
    config = RunnerConfig(stream_ui=True)
    assert config.effective_partial_messages() is True
