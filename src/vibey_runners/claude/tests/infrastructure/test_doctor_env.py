# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/doctor_env.py — RealDoctorEnvironment adapter."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from claudeloop.infrastructure.doctor_env import RealDoctorEnvironment


def test_find_claude_cli_when_not_in_path() -> None:
    """find_claude_cli returns None when claude is not in PATH."""
    env = RealDoctorEnvironment()
    with patch("shutil.which", return_value=None):
        assert env.find_claude_cli() is None


def test_find_claude_cli_when_in_path() -> None:
    """find_claude_cli returns path when claude is in PATH."""
    env = RealDoctorEnvironment()
    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        assert env.find_claude_cli() == "/usr/local/bin/claude"


def test_claude_cli_version_success() -> None:
    """claude_cli_version returns version string when command succeeds."""
    env = RealDoctorEnvironment()
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "claude 1.2.3\n"
    with patch("subprocess.run", return_value=mock_result):
        version = env.claude_cli_version("/path/to/claude")
        assert version == "claude 1.2.3"


def test_claude_cli_version_non_zero_exit() -> None:
    """claude_cli_version returns None when command exits non-zero."""
    env = RealDoctorEnvironment()
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        assert env.claude_cli_version("/path/to/claude") is None


def test_claude_cli_version_timeout() -> None:
    """claude_cli_version returns None on timeout."""
    env = RealDoctorEnvironment()
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 10)):
        assert env.claude_cli_version("/path/to/claude") is None


def test_claude_cli_version_oserror() -> None:
    """claude_cli_version returns None on OSError."""
    env = RealDoctorEnvironment()
    with patch("subprocess.run", side_effect=OSError("Command not found")):
        assert env.claude_cli_version("/path/to/claude") is None


def test_claude_cli_version_empty_output() -> None:
    """claude_cli_version returns None when output is empty."""
    env = RealDoctorEnvironment()
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result):
        assert env.claude_cli_version("/path/to/claude") is None


def test_is_authenticated_via_api_key(monkeypatch) -> None:
    """is_authenticated returns True when ANTHROPIC_API_KEY is set."""
    env = RealDoctorEnvironment()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    assert env.is_authenticated() is True


def test_is_authenticated_via_auth_token(monkeypatch) -> None:
    """is_authenticated returns True when ANTHROPIC_AUTH_TOKEN is set."""
    env = RealDoctorEnvironment()
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    assert env.is_authenticated() is True


def test_is_authenticated_via_claude_auth_status(monkeypatch) -> None:
    """is_authenticated checks claude auth status when no env vars set."""
    env = RealDoctorEnvironment()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"loggedIn": True})

    with (
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", return_value=mock_result),
    ):
        assert env.is_authenticated() is True


def test_is_authenticated_via_credentials_file(tmp_path: Path, monkeypatch) -> None:
    """is_authenticated checks .claude/.credentials.json as fallback."""
    env = RealDoctorEnvironment()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    # Create fake credentials file
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    claude_dir = fake_home / ".claude"
    claude_dir.mkdir()
    creds_file = claude_dir / ".credentials.json"
    creds_file.write_text("{}", encoding="utf-8")

    with (
        patch("pathlib.Path.home", return_value=fake_home),
        patch.object(env, "find_claude_cli", return_value=None),
    ):
        assert env.is_authenticated() is True


def test_is_authenticated_false_when_nothing_found(tmp_path: Path, monkeypatch) -> None:
    """is_authenticated returns False when no auth method found."""
    env = RealDoctorEnvironment()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    fake_home = tmp_path / "home"
    fake_home.mkdir()

    with (
        patch("pathlib.Path.home", return_value=fake_home),
        patch.object(env, "find_claude_cli", return_value=None),
    ):
        assert env.is_authenticated() is False


def test_is_authenticated_claude_auth_not_logged_in(monkeypatch) -> None:
    """is_authenticated handles claude auth status returning loggedIn: false."""
    env = RealDoctorEnvironment()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({"loggedIn": False})

    fake_home = Path("/nonexistent")
    with (
        patch("pathlib.Path.home", return_value=fake_home),
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", return_value=mock_result),
    ):
        assert env.is_authenticated() is False


def test_is_authenticated_claude_auth_invalid_json(monkeypatch) -> None:
    """is_authenticated handles invalid JSON from claude auth status."""
    env = RealDoctorEnvironment()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "not json"

    fake_home = Path("/nonexistent")
    with (
        patch("pathlib.Path.home", return_value=fake_home),
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", return_value=mock_result),
    ):
        assert env.is_authenticated() is False


def test_configured_mcp_servers_no_claude_cli() -> None:
    """configured_mcp_servers returns empty list when claude CLI not found."""
    env = RealDoctorEnvironment()
    with patch.object(env, "find_claude_cli", return_value=None):
        assert env.configured_mcp_servers() == []


def test_configured_mcp_servers_command_fails() -> None:
    """configured_mcp_servers returns empty list when mcp list fails."""
    env = RealDoctorEnvironment()
    mock_result = Mock()
    mock_result.returncode = 1

    with (
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", return_value=mock_result),
    ):
        assert env.configured_mcp_servers() == []


def test_configured_mcp_servers_timeout() -> None:
    """configured_mcp_servers returns empty list on timeout."""
    env = RealDoctorEnvironment()
    with (
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 60)),
    ):
        assert env.configured_mcp_servers() == []


def test_configured_mcp_servers_oserror() -> None:
    """configured_mcp_servers returns empty list on OSError."""
    env = RealDoctorEnvironment()
    with (
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", side_effect=OSError("Command failed")),
    ):
        assert env.configured_mcp_servers() == []


def test_configured_mcp_servers_success() -> None:
    """configured_mcp_servers parses server names from colon-delimited output."""
    env = RealDoctorEnvironment()
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "server1: connected\nserver2: connected\nserver3: error\n"

    with (
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", return_value=mock_result),
    ):
        servers = env.configured_mcp_servers()
        assert "server1" in servers
        assert "server2" in servers
        assert "server3" in servers


def test_configured_mcp_servers_skips_blank_and_no_colon_lines() -> None:
    """configured_mcp_servers skips blank lines and lines without colons."""
    env = RealDoctorEnvironment()
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "server1: ok\n\nno-colon-line\nserver2: ok\n"

    with (
        patch.object(env, "find_claude_cli", return_value="/usr/bin/claude"),
        patch("subprocess.run", return_value=mock_result),
    ):
        servers = env.configured_mcp_servers()
        assert servers == ["server1", "server2"]


def test_anthropic_sdk_version_returns_version() -> None:
    """anthropic_sdk_version returns the anthropic module version."""
    env = RealDoctorEnvironment()
    result = env.anthropic_sdk_version()
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0


def test_api_surface_method_count_returns_int() -> None:
    """api_surface_method_count returns an integer count."""
    env = RealDoctorEnvironment()
    count = env.api_surface_method_count()
    assert count is None or isinstance(count, int)


def test_anthropic_sdk_version_import_error() -> None:
    """anthropic_sdk_version returns None when anthropic module cannot be imported."""
    import sys
    from unittest.mock import patch

    env = RealDoctorEnvironment()
    # Mock the import to raise ImportError
    with (
        patch.dict(sys.modules, {"anthropic": None}),
        patch("builtins.__import__", side_effect=ImportError("no module")),
    ):
        result = env.anthropic_sdk_version()
        assert result is None


def test_api_surface_method_count_import_error() -> None:
    """api_surface_method_count returns None when introspect module cannot be imported."""
    import sys
    from unittest.mock import patch

    env = RealDoctorEnvironment()
    # Mock sys.modules to make introspect unavailable
    with patch.dict(sys.modules, {"claudeloop.infrastructure.api.introspect": None}):
        result = env.api_surface_method_count()
        assert result is None
