# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Build ``agy`` CLI argv without the sandbox + skip-permissions footgun.

Default: ``--sandbox`` plus ``proceed-in-sandbox`` / ``deny: unsandboxed``.
``--unsafe-skip-permissions`` emits ``--dangerously-skip-permissions`` only
after refusing root, refusing a sandbox combo, and refusing a non-git cwd
unless allowlisted. See research-notes.md F11 and antigravity-cli#36.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agyloop.domain.errors import UnsafeSkipPermissionsError
from agyloop.domain.permission import DEFAULT_USER_PERMISSION_MODE, UserPermissionMode

ISSUE_36_URL = "https://github.com/google-antigravity/antigravity-cli/issues/36"
UNSAFE_SKIP_WARNING = (
    "WARNING: --unsafe-skip-permissions maps to agy's "
    "--dangerously-skip-permissions, which defeats --sandbox "
    f"(antigravity-cli#36). {ISSUE_36_URL}"
)
DEFAULT_PRINT_TIMEOUT = "24h0m0s"
_ALLOWLIST_ENV = "AGYLOOP_UNSAFE_SKIP_ALLOWLIST"


def _unsafe_refusal(reason: str) -> UnsafeSkipPermissionsError:
    return UnsafeSkipPermissionsError(f"{reason}\n{UNSAFE_SKIP_WARNING}")


@dataclass(frozen=True, slots=True)
class AgyCliInvocation:
    argv: tuple[str, ...]
    settings: dict[str, Any]
    warning: str | None = None


def _effective_uid() -> int:
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None:
        return 1
    return int(geteuid())


def _is_git_repo(cwd: Path) -> bool:
    current = cwd.resolve()
    for candidate in (current, *current.parents):
        git = candidate / ".git"
        if git.is_dir() or git.is_file():
            return True
    return False


def _allowlist_paths(allowlist: Sequence[str] | None) -> list[Path]:
    if allowlist is not None:
        raw = list(allowlist)
    else:
        env = os.environ.get(_ALLOWLIST_ENV, "")
        raw = [part for part in env.replace(":", ",").split(",") if part.strip()]
    return [Path(item).expanduser().resolve() for item in raw]


def _is_allowlisted(cwd: Path, allowlist: Sequence[str] | None) -> bool:
    resolved = cwd.resolve()
    for allowed in _allowlist_paths(allowlist):
        if resolved == allowed or allowed in resolved.parents:
            return True
    return False


def _build_permission_settings(
    *,
    permission_mode: UserPermissionMode,
    workspace: Path,
) -> dict[str, Any]:
    """Build agy CLI permission settings for the given mode.

    Maps agyloop permission modes to agy settings.json format:
    - autonomous: workspace-scoped allows + destructive denies (most permissive)
    - scoped: workspace-scoped allows + destructive denies (no blanket allow)
    - safe: restrictive (not fully implemented here, treated as scoped)
    - yolo: unrestricted (not recommended, treated as autonomous)
    """
    resolved_workspace = str(workspace.resolve())
    if permission_mode in ("autonomous", "yolo"):
        # Autonomous: allow workspace-scoped commands, deny only destructive ones
        return {
            "toolPermission": "ask",
            "permissions": {
                "allow": [
                    f"command(cwd={resolved_workspace})",
                    f"edit(path={resolved_workspace}/*)",
                    f"write(path={resolved_workspace}/*)",
                    f"read(path={resolved_workspace}/*)",
                ],
                "deny": ["command(rm -rf)", "command(mkfs)", "command(dd if=)"],
            },
        }
    # scoped or safe: workspace-scoped, no blanket allow
    return {
        "toolPermission": "ask",
        "permissions": {
            "allow": [
                f"command(cwd={resolved_workspace})",
                f"edit(path={resolved_workspace}/*)",
                f"write(path={resolved_workspace}/*)",
                f"read(path={resolved_workspace}/*)",
            ],
            "deny": ["command(rm -rf)", "command(mkfs)", "command(dd if=)"],
        },
    }


def validate_unsafe_skip_permissions(
    *,
    cwd: Path,
    sandbox: bool = False,
    allowlist: Sequence[str] | None = None,
) -> None:
    """Refuse the CLI skip-permissions opt-in when it would be a footgun."""
    if sandbox:
        raise _unsafe_refusal(
            "--unsafe-skip-permissions refuses to combine with --sandbox; "
            f"that combination defeats the sandbox ({ISSUE_36_URL})"
        )
    if _effective_uid() == 0:
        raise _unsafe_refusal("--unsafe-skip-permissions refuses to run as root (euid 0)")
    if not _is_git_repo(cwd) and not _is_allowlisted(cwd, allowlist):
        raise _unsafe_refusal(
            "--unsafe-skip-permissions refuses to run outside a git repository "
            "unless the directory is allowlisted"
        )


def build_agy_argv(
    *,
    prompt: str,
    cwd: Path | None = None,
    conversation_id: str | None = None,
    model: str | None = None,
    sandbox: bool | None = None,
    unsafe_skip_permissions: bool = False,
    allowlist: Sequence[str] | None = None,
    print_timeout: str = DEFAULT_PRINT_TIMEOUT,
    permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
) -> AgyCliInvocation:
    """Construct an ``agy -p`` invocation. Never emits skip-permissions with sandbox."""
    workspace = Path.cwd() if cwd is None else cwd
    use_sandbox = (not unsafe_skip_permissions) if sandbox is None else sandbox
    if unsafe_skip_permissions:
        validate_unsafe_skip_permissions(
            cwd=workspace,
            sandbox=use_sandbox,
            allowlist=allowlist,
        )

    argv: list[str] = ["agy", "-p", prompt, "--print-timeout", print_timeout]
    if conversation_id:
        argv.extend(["--conversation", conversation_id])
    if model:
        argv.extend(["--model", model])

    warning: str | None = None
    settings: dict[str, Any]
    if unsafe_skip_permissions:
        argv.append("--dangerously-skip-permissions")
        settings = {}
        warning = UNSAFE_SKIP_WARNING
    else:
        # Build settings based on permission_mode
        settings = _build_permission_settings(
            permission_mode=permission_mode,
            workspace=workspace,
        )
    if use_sandbox:
        argv.append("--sandbox")

    if "--dangerously-skip-permissions" in argv and "--sandbox" in argv:
        raise _unsafe_refusal(
            "refusing to emit --dangerously-skip-permissions together with "
            f"--sandbox ({ISSUE_36_URL})"
        )

    return AgyCliInvocation(argv=tuple(argv), settings=settings, warning=warning)
