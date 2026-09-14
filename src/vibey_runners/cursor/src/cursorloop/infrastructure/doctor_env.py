# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Doctor findings — environment checks for unattended readiness."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404 — fixed argv, never shell=True
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from cursor_sdk import Cursor

from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile
from cursorloop.infrastructure.agent.hooks import ManagedHooks

Level = Literal["pass", "warn", "fail"]


@dataclass(frozen=True, slots=True)
class Finding:
    name: str
    level: Level
    detail: str
    remedy: str = ""


MeFn = Callable[..., Any]
ModelsFn = Callable[..., Sequence[Any]]


def _mcp_servers(workspace: Path) -> dict[str, Any]:
    path = workspace / ".cursor" / "mcp.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    servers = data.get("mcpServers", {})
    return servers if isinstance(servers, dict) else {}


def _needs_oauth(config: object) -> bool:
    if not isinstance(config, dict):
        return False
    return bool("url" in config and "command" not in config)


def _safe_detail(name: str, config: dict[str, Any]) -> str:
    kind = "url" if "url" in config else "command"
    return f"MCP server {name!r} ({kind}) needs a saved OAuth login for unattended runs"


def check_mcp_oauth_readiness(
    *,
    workspace: Path,
    saved_logins: frozenset[str],
    is_service_account: bool = False,
) -> list[Finding]:
    """Fail when a remote MCP server has no saved login the SDK can reuse."""
    findings: list[Finding] = []
    servers = _mcp_servers(workspace)
    for name, config in servers.items():
        if not isinstance(config, dict):
            continue
        # Never echo env/headers — only structural detail.
        if is_service_account and _needs_oauth(config):
            findings.append(
                Finding(
                    name=f"mcp-oauth:{name}",
                    level="fail",
                    detail=(
                        f"Service-account keys cannot fall back to user auth for "
                        f"MCP server {name!r}"
                    ),
                    remedy="Use a user API key with a saved MCP login, or remove the server.",
                )
            )
            continue
        if _needs_oauth(config) and name not in saved_logins:
            findings.append(
                Finding(
                    name=f"mcp-oauth:{name}",
                    level="fail",
                    detail=_safe_detail(name, config),
                    remedy=f"Open Cursor, sign in to MCP server {name!r}, then re-run doctor.",
                )
            )
        elif "command" in config:
            findings.append(
                Finding(
                    name=f"mcp-local:{name}",
                    level="pass",
                    detail=f"MCP server {name!r} uses a local command (no OAuth browser flow).",
                )
            )
    return findings


def check_api_key_present(api_key: str | None) -> Finding:
    if api_key:
        return Finding(name="cursor-api-key", level="pass", detail="CURSOR_API_KEY is set")
    return Finding(
        name="cursor-api-key",
        level="fail",
        detail="CURSOR_API_KEY is unset",
        remedy="Export CURSOR_API_KEY from the Cursor dashboard.",
    )


def check_cursor_me(
    *,
    api_key: str | None,
    me_fn: MeFn | None = None,
) -> Finding:
    """Verify the API key authenticates via Cursor.me()."""
    if not api_key:
        return Finding(
            name="cursor-me",
            level="fail",
            detail="Skipping Cursor.me() — no API key",
            remedy="Set CURSOR_API_KEY first.",
        )
    if me_fn is None:
        me_fn = Cursor.me
    try:
        user = me_fn(api_key=api_key)
    except Exception as exc:  # noqa: BLE001 — surface any auth/network failure
        return Finding(
            name="cursor-me",
            level="fail",
            detail=f"Cursor.me() failed: {type(exc).__name__}",
            remedy="Rotate or re-export CURSOR_API_KEY; confirm network access.",
        )
    email = getattr(user, "user_email", None) or getattr(user, "email", None) or ""
    label = str(email) if email else "authenticated user"
    return Finding(name="cursor-me", level="pass", detail=f"Authenticated as {label}")


def check_bridge_binary(*, which: Callable[[str], str | None] | None = None) -> Finding:
    """Confirm the bundled cursor-sdk-bridge binary is on PATH and runnable."""
    finder = which if which is not None else shutil.which
    path = finder("cursor-sdk-bridge")
    if not path:
        return Finding(
            name="cursor-sdk-bridge",
            level="fail",
            detail="cursor-sdk-bridge not found on PATH",
            remedy="Reinstall cursor-sdk or use the CLI-fallback gateway.",
        )
    try:
        completed = subprocess.run(  # nosec B603
            [path, "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except OSError as exc:
        return Finding(
            name="cursor-sdk-bridge",
            level="fail",
            detail=f"cursor-sdk-bridge failed to exec: {exc}",
            remedy="Check platform support / code-signing policy for the bridge binary.",
        )
    if completed.returncode != 0:
        return Finding(
            name="cursor-sdk-bridge",
            level="fail",
            detail="cursor-sdk-bridge --help exited non-zero",
            remedy="Reinstall cursor-sdk or inspect bridge binary permissions.",
        )
    return Finding(
        name="cursor-sdk-bridge",
        level="pass",
        detail=f"cursor-sdk-bridge available at {path}",
    )


def check_model_in_catalog(
    *,
    profile: ModelProfile,
    api_key: str | None,
    models_fn: ModelsFn | None = None,
) -> list[Finding]:
    """Ensure the selected model id appears in Cursor.models.list()."""
    if not api_key:
        return [
            Finding(
                name="models-catalog",
                level="fail",
                detail="Skipping models.list() — no API key",
                remedy="Set CURSOR_API_KEY first.",
            )
        ]
    if models_fn is None:
        models_fn = Cursor.models.list
    try:
        models = list(models_fn(api_key=api_key))
    except Exception as exc:  # noqa: BLE001
        return [
            Finding(
                name="models-catalog",
                level="fail",
                detail=f"Cursor.models.list() failed: {type(exc).__name__}",
                remedy="Confirm auth and retry; model ids are never trusted from a constant.",
            )
        ]
    ids = {str(getattr(m, "id", m)) for m in models}
    findings: list[Finding] = []
    if profile.model_id in ids:
        findings.append(
            Finding(
                name="models-catalog",
                level="pass",
                detail=f"Selected model {profile.model_id!r} is in the account catalog",
            )
        )
    else:
        findings.append(
            Finding(
                name="models-catalog",
                level="fail",
                detail=f"Selected model {profile.model_id!r} is not in Cursor.models.list()",
                remedy="Pick a catalog id via cursorloop models or change --model.",
            )
        )
    if profile.model_id == "auto-smart":
        findings.extend(_check_router_params(profile, ids))
    return findings


def _check_router_params(profile: ModelProfile, catalog_ids: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    if "auto-smart" not in catalog_ids:
        findings.append(
            Finding(
                name="router-availability",
                level="fail",
                detail="Router preset selected but auto-smart is absent from the catalog",
                remedy="Use a non-router profile or wait for auto-smart on the account.",
            )
        )
        return findings
    allowed = {"cost", "balanced", "intelligence"}
    optimize = dict(profile.params).get("optimize_for")
    if optimize is None:
        findings.append(
            Finding(
                name="router-availability",
                level="warn",
                detail="Router profile has no optimize_for param",
                remedy="Use a shipped router-* preset.",
            )
        )
    elif optimize not in allowed:
        findings.append(
            Finding(
                name="router-availability",
                level="fail",
                detail=f"optimize_for={optimize!r} is not in {sorted(allowed)}",
                remedy="Use cost, balanced, or intelligence.",
            )
        )
    else:
        findings.append(
            Finding(
                name="router-availability",
                level="pass",
                detail=f"Router optimize_for={optimize!r} is allowed",
            )
        )
    return findings


def check_setting_sources(*, sources: Sequence[str] | None) -> Finding:
    """Report what project/user setting_sources would load (skills AND MCP)."""
    chosen = tuple(sources) if sources else ()
    if not chosen:
        return Finding(
            name="setting-sources",
            level="pass",
            detail=(
                "Default setting_sources=None (hermetic): project skills and "
                "project MCP are NOT loaded"
            ),
            remedy="Pass --setting-sources project only if you accept project MCP too.",
        )
    parts = []
    if "project" in chosen:
        parts.append("project skills AND project MCP (.cursor/mcp.json)")
    if "user" in chosen:
        parts.append("user skills AND user MCP")
    return Finding(
        name="setting-sources",
        level="warn",
        detail="setting_sources will load: " + "; ".join(parts),
        remedy="Doctor cannot split skills from MCP — treat them as coupled.",
    )


def check_git_repository(workspace: Path) -> Finding:
    """Autonomy guardrail: workspace should be a non-root git checkout."""
    if workspace.resolve() == Path("/"):
        return Finding(
            name="git-root",
            level="fail",
            detail="Workspace is filesystem root — refusing autonomous runs",
            remedy="Run from a project directory.",
        )
    probe = workspace / ".git"
    if probe.exists():
        return Finding(name="git-repo", level="pass", detail="Workspace is a git repository")
    # Walk parents for .git (worktrees / subdirs)
    for parent in workspace.resolve().parents:
        if (parent / ".git").exists():
            return Finding(
                name="git-repo",
                level="pass",
                detail=f"Git repository found at {parent}",
            )
    return Finding(
        name="git-repo",
        level="warn",
        detail="Workspace is not inside a git repository",
        remedy="Initialize git so savepoints/unwind work.",
    )


def check_managed_hooks_state(workspace: Path) -> Finding:
    """Detect a stale managed hooks.json left by a crashed run."""
    state_dir = workspace / ".cursorloop"
    manager = ManagedHooks(workspace=workspace, state_dir=state_dir)
    backup = state_dir / "hooks.json.original"
    if manager.is_installed():
        return Finding(
            name="managed-hooks",
            level="warn",
            detail="Managed hooks appear installed (a run may still be active or crashed)",
            remedy="If no run is active, run `cursorloop reset` to restore hooks.json.",
        )
    if backup.is_file():
        return Finding(
            name="managed-hooks",
            level="fail",
            detail="Found hooks.json.original without an active managed install — likely a crash",
            remedy="Run `cursorloop reset` to restore .cursor/hooks.json.",
        )
    return Finding(
        name="managed-hooks",
        level="pass",
        detail="No stale managed-hooks state detected",
    )


def check_cloud_hooks_clean(*, cloud: bool, workspace: Path) -> Finding:
    """Cloud agents read hooks from the repo — warn on uncommitted hooks.json."""
    if not cloud:
        return Finding(
            name="cloud-hooks",
            level="pass",
            detail="Local run — cloud hooks dirty-check skipped",
        )
    hooks = workspace / ".cursor" / "hooks.json"
    if not hooks.is_file():
        return Finding(
            name="cloud-hooks",
            level="pass",
            detail="No .cursor/hooks.json for cloud to read",
        )
    result = subprocess.run(  # nosec B603 B607
        ["git", "status", "--porcelain", "--", str(hooks)],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return Finding(
            name="cloud-hooks",
            level="warn",
            detail="Could not ask git about .cursor/hooks.json",
            remedy="Ensure the workspace is a git repo before cloud runs.",
        )
    if result.stdout.strip():
        return Finding(
            name="cloud-hooks",
            level="fail",
            detail=".cursor/hooks.json has uncommitted changes; cloud agents read the repo copy",
            remedy="Commit or stash hooks.json before a cloud run.",
        )
    return Finding(
        name="cloud-hooks",
        level="pass",
        detail=".cursor/hooks.json is clean in git",
    )


def check_cursorloop_gitignored(workspace: Path) -> Finding:
    gitignore = workspace / ".gitignore"
    if not gitignore.is_file():
        return Finding(
            name="cursorloop-gitignore",
            level="warn",
            detail="No .gitignore; .cursorloop/ may be committed",
            remedy="Add '.cursorloop/' to .gitignore",
        )
    text = gitignore.read_text(encoding="utf-8")
    if ".cursorloop" in text:
        return Finding(
            name="cursorloop-gitignore",
            level="pass",
            detail=".cursorloop/ appears in .gitignore",
        )
    return Finding(
        name="cursorloop-gitignore",
        level="fail",
        detail=".cursorloop/ is not git-ignored",
        remedy="Add '.cursorloop/' to .gitignore (run state holds prompts/transcripts).",
    )


def resolve_profile(model: str | None) -> ModelProfile:
    if model and model in SHIPPED_PRESETS:
        return SHIPPED_PRESETS[model]
    if model:
        return ModelProfile(model_id=model)
    return SHIPPED_PRESETS["composer"]


def run_doctor(
    *,
    workspace: Path,
    saved_logins: frozenset[str] = frozenset(),
    is_service_account: bool = False,
    api_key: str | None = None,
    model: str | None = None,
    setting_sources: Sequence[str] | None = None,
    cloud: bool = False,
    live: bool = True,
    me_fn: MeFn | None = None,
    models_fn: ModelsFn | None = None,
    which: Callable[[str], str | None] | None = None,
) -> list[Finding]:
    """Run the full doctor checklist.

    ``live=False`` skips network/SDK calls (useful for unit tests of local checks).
    """
    key = api_key if api_key is not None else os.environ.get("CURSOR_API_KEY")
    profile = resolve_profile(model)
    findings: list[Finding] = [
        check_api_key_present(key),
        check_bridge_binary(which=which),
        check_setting_sources(sources=setting_sources),
        check_git_repository(workspace),
        check_managed_hooks_state(workspace),
        check_cloud_hooks_clean(cloud=cloud, workspace=workspace),
        check_cursorloop_gitignored(workspace),
    ]
    findings.extend(
        check_mcp_oauth_readiness(
            workspace=workspace,
            saved_logins=saved_logins,
            is_service_account=is_service_account,
        )
    )
    if live:
        findings.append(check_cursor_me(api_key=key, me_fn=me_fn))
        findings.extend(check_model_in_catalog(profile=profile, api_key=key, models_fn=models_fn))
    return findings


def findings_as_json(findings: list[Finding]) -> str:
    return json.dumps([asdict(f) for f in findings], indent=2) + "\n"
