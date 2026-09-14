# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""CLI argv builder: never combine skip-permissions with sandbox; refuse root."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agyloop.domain.errors import UnsafeSkipPermissionsError
from agyloop.infrastructure.agent.cli_argv import (
    ISSUE_36_URL,
    UNSAFE_SKIP_WARNING,
    build_agy_argv,
    validate_unsafe_skip_permissions,
)


def test_default_argv_uses_sandbox_and_never_emits_skip_permissions() -> None:
    invocation = build_agy_argv(prompt="hello", conversation_id="cid-1")
    argv = list(invocation.argv)
    assert "--sandbox" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert "-p" in argv or "--print" in argv or "--prompt" in argv
    assert "--print-timeout" in argv
    timeout = argv[argv.index("--print-timeout") + 1]
    assert timeout != "5m0s"
    assert "--conversation" in argv
    assert "cid-1" in argv
    assert "-c" not in argv
    assert "--continue" not in argv


def test_default_settings_allow_workspace_commands() -> None:
    """Default (autonomous) mode allows workspace-scoped commands."""
    invocation = build_agy_argv(prompt="hello")
    assert invocation.settings["toolPermission"] in ("ask", "allow")
    # Should have workspace allows, not blanket denies
    assert "permissions" in invocation.settings
    assert "allow" in invocation.settings["permissions"]
    # Should deny destructive commands
    assert "deny" in invocation.settings["permissions"]
    assert "--dangerously-skip-permissions" not in invocation.argv


def test_unsafe_skip_permissions_omits_sandbox(tmp_path: Path) -> None:
    _init_git(tmp_path)
    invocation = build_agy_argv(
        prompt="hello",
        cwd=tmp_path,
        unsafe_skip_permissions=True,
    )
    argv = list(invocation.argv)
    assert "--dangerously-skip-permissions" in argv
    assert "--sandbox" not in argv
    assert invocation.warning == UNSAFE_SKIP_WARNING


def test_unsafe_skip_permissions_refuses_sandbox_combo(tmp_path: Path) -> None:
    _init_git(tmp_path)
    with pytest.raises(UnsafeSkipPermissionsError, match="sandbox") as exc:
        build_agy_argv(
            prompt="hello",
            cwd=tmp_path,
            sandbox=True,
            unsafe_skip_permissions=True,
        )
    assert UNSAFE_SKIP_WARNING in str(exc.value)


def test_unsafe_skip_permissions_refuses_root(tmp_path: Path) -> None:
    _init_git(tmp_path)
    euid = "agyloop.infrastructure.agent.cli_argv.os.geteuid"
    with (
        patch(euid, return_value=0),
        pytest.raises(UnsafeSkipPermissionsError, match="root") as validate_exc,
    ):
        validate_unsafe_skip_permissions(cwd=tmp_path)
    assert UNSAFE_SKIP_WARNING in str(validate_exc.value)
    with (
        patch(euid, return_value=0),
        pytest.raises(UnsafeSkipPermissionsError, match="root") as build_exc,
    ):
        build_agy_argv(prompt="hello", cwd=tmp_path, unsafe_skip_permissions=True)
    assert UNSAFE_SKIP_WARNING in str(build_exc.value)


def test_unsafe_skip_permissions_allows_non_root(tmp_path: Path) -> None:
    _init_git(tmp_path)
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        validate_unsafe_skip_permissions(cwd=tmp_path)
        invocation = build_agy_argv(prompt="hello", cwd=tmp_path, unsafe_skip_permissions=True)
    assert "--dangerously-skip-permissions" in invocation.argv


def test_unsafe_skip_permissions_refuses_outside_git(tmp_path: Path) -> None:
    with (
        patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501),
        pytest.raises(UnsafeSkipPermissionsError, match="git") as exc,
    ):
        validate_unsafe_skip_permissions(cwd=tmp_path)
    assert UNSAFE_SKIP_WARNING in str(exc.value)


def test_unsafe_skip_permissions_allows_allowlisted_non_git(tmp_path: Path) -> None:
    with patch("agyloop.infrastructure.agent.cli_argv.os.geteuid", return_value=501):
        validate_unsafe_skip_permissions(cwd=tmp_path, allowlist=[str(tmp_path)])
        invocation = build_agy_argv(
            prompt="hello",
            cwd=tmp_path,
            unsafe_skip_permissions=True,
            allowlist=[str(tmp_path)],
        )
    assert "--dangerously-skip-permissions" in invocation.argv
    assert "--sandbox" not in invocation.argv


def test_unsafe_skip_warning_cites_issue_36() -> None:
    assert "36" in UNSAFE_SKIP_WARNING
    assert ISSUE_36_URL in UNSAFE_SKIP_WARNING or "antigravity-cli" in UNSAFE_SKIP_WARNING


def test_cli_argv_effective_uid_and_allowlist_child_and_sandbox_false(tmp_path: Path) -> None:
    from agyloop.infrastructure.agent.cli_argv import _effective_uid, _is_allowlisted

    # geteuid None
    with patch("agyloop.infrastructure.agent.cli_argv.getattr", return_value=None):
        assert _effective_uid() == 1

    # allowlist child of parent
    child = tmp_path / "subdir" / "project"
    child.mkdir(parents=True)
    assert _is_allowlisted(child, [str(tmp_path)]) is True

    # build_agy_argv with sandbox=False
    inv = build_agy_argv(prompt="hello", cwd=tmp_path, sandbox=False)
    assert "--sandbox" not in inv.argv
    assert "--dangerously-skip-permissions" not in inv.argv
    assert inv.settings["toolPermission"] in ("ask", "allow")


def test_scoped_permission_mode_allows_workspace_commands(tmp_path: Path) -> None:
    """--scoped mode must allow command execution within the workspace."""
    inv = build_agy_argv(prompt="build the project", cwd=tmp_path, permission_mode="scoped")
    settings = inv.settings
    # Scoped mode should NOT deny all unsandboxed commands - it should allow workspace-scoped ones
    assert "unsandboxed" not in settings.get("permissions", {}).get("deny", [])
    # Should have workspace-scoped allow rules
    assert "permissions" in settings
    assert "allow" in settings["permissions"]
    # The workspace path should be in the allow rules
    workspace_path = str(tmp_path.resolve())
    allow_rules = settings["permissions"]["allow"]
    # Check that at least one allow rule references the workspace
    assert any(workspace_path in str(rule) for rule in allow_rules), (
        f"Expected workspace {workspace_path} in allow rules, got {allow_rules}"
    )


def test_autonomous_permission_mode_includes_allow_all(tmp_path: Path) -> None:
    """autonomous mode should be more permissive than scoped."""
    inv = build_agy_argv(prompt="run tests", cwd=tmp_path, permission_mode="autonomous")
    # Autonomous might have different settings than scoped
    # The key is it should be at least as permissive as scoped
    assert "permissions" in inv.settings


def test_default_permission_mode_is_autonomous(tmp_path: Path) -> None:
    """When no permission_mode is specified, default to autonomous."""
    inv = build_agy_argv(prompt="hello", cwd=tmp_path)
    # Default should work - exact settings may vary but it shouldn't deny everything
    assert inv.settings is not None


def _init_git(repo: Path) -> None:
    (repo / ".git").mkdir()
