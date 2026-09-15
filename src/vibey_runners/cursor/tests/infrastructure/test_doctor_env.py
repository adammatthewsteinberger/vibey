# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.doctor_env import (
    check_bridge_binary,
    check_cursor_me,
    check_git_repository,
    check_managed_hooks_state,
    check_mcp_oauth_readiness,
    check_model_in_catalog,
    check_setting_sources,
    run_doctor,
)


def test_an_mcp_server_needing_oauth_is_a_fatal_finding(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"linear": {"url": "https://mcp.linear.app/mcp"}}}'
    )
    findings = check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset())
    assert [f.name for f in findings if f.level == "fail"] == ["mcp-oauth:linear"]


def test_a_saved_login_clears_the_finding(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"linear": {"url": "https://mcp.linear.app/mcp"}}}'
    )
    findings = check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset({"linear"}))
    assert all(f.level != "fail" for f in findings)


def test_service_account_keys_cannot_fall_back_to_user_auth(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"linear": {"url": "https://mcp.linear.app/mcp"}}}'
    )
    findings = check_mcp_oauth_readiness(
        workspace=tmp_path, saved_logins=frozenset({"linear"}), is_service_account=True
    )
    assert any(f.level == "fail" for f in findings)


def test_doctor_never_prints_mcp_env_or_headers(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"gh": {"command": "npx", "env": {"GITHUB_TOKEN": "ghp_secret"}}}}'
    )
    rendered = "\n".join(
        f.detail for f in check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset())
    )
    assert "ghp_secret" not in rendered


def test_cursor_me_pass_and_fail() -> None:
    ok = check_cursor_me(
        api_key="k",
        me_fn=lambda **kwargs: SimpleNamespace(user_email="a@b.c"),
    )
    assert ok.level == "pass"
    assert "a@b.c" in ok.detail

    def boom(**kwargs: object) -> None:
        raise RuntimeError("revoked")

    bad = check_cursor_me(api_key="k", me_fn=boom)
    assert bad.level == "fail"


def test_bridge_binary_missing_and_present() -> None:
    missing = check_bridge_binary(which=lambda name: None)
    assert missing.level == "fail"
    # Real binary on this machine when available.
    present = check_bridge_binary()
    assert present.level in {"pass", "fail"}


def test_model_catalog_and_router(tmp_path: Path) -> None:
    del tmp_path
    models = [SimpleNamespace(id="composer-2.5"), SimpleNamespace(id="auto-smart")]
    findings = check_model_in_catalog(
        profile=SHIPPED_PRESETS["composer"],
        api_key="k",
        models_fn=lambda **kwargs: models,
    )
    assert any(f.level == "pass" and f.name == "models-catalog" for f in findings)

    router = check_model_in_catalog(
        profile=SHIPPED_PRESETS["router-balanced"],
        api_key="k",
        models_fn=lambda **kwargs: models,
    )
    assert any(f.name == "router-availability" and f.level == "pass" for f in router)


def test_setting_sources_reports_coupling() -> None:
    hermetic = check_setting_sources(sources=None)
    assert hermetic.level == "pass"
    project = check_setting_sources(sources=("project",))
    assert project.level == "warn"
    assert "MCP" in project.detail


def test_git_and_hooks_checks(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(".cursorloop/\n", encoding="utf-8")
    git = check_git_repository(tmp_path)
    assert git.level in {"pass", "warn"}
    hooks = check_managed_hooks_state(tmp_path)
    assert hooks.level == "pass"
    # Stale backup without install → fail
    state = tmp_path / ".cursorloop"
    state.mkdir()
    (state / "hooks.json.original").write_text("{}", encoding="utf-8")
    stale = check_managed_hooks_state(tmp_path)
    assert stale.level == "fail"


def test_run_doctor_offline_skips_live(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(".cursorloop/\n", encoding="utf-8")
    findings = run_doctor(workspace=tmp_path, api_key="k", live=False, which=lambda name: None)
    names = {f.name for f in findings}
    assert "cursor-api-key" in names
    assert "cursor-sdk-bridge" in names
    assert "cursor-me" not in names
    assert "models-catalog" not in names
