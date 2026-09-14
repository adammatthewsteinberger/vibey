# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""``AgentGateway`` backed by a live ``agy`` CLI subprocess.

Uses ``build_agy_argv`` so the default is ``--sandbox`` plus
``proceed-in-sandbox`` / ``deny: unsandboxed``. ``--unsafe-skip-permissions``
is valid on this path after the usual gates. Never ``shell=True``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # nosec B404 — argv lists from build_agy_argv, never shell=True
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agyloop.application.dto import TurnOutcome
from agyloop.domain.capacity import Available
from agyloop.domain.classify import TurnSignals, classify
from agyloop.domain.errors import AgentConfigError
from agyloop.domain.model_profile import ModelEffortProfile
from agyloop.domain.permission import DEFAULT_USER_PERMISSION_MODE, UserPermissionMode
from agyloop.infrastructure.agent.cli_argv import AgyCliInvocation, build_agy_argv
from agyloop.infrastructure.agent.translate import outcome_from_exception

AgyProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


def execute_agy(
    invocation: AgyCliInvocation,
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Run one ``agy`` argv list. Settings are exported for the child, not argv."""
    env = os.environ.copy()
    if invocation.settings:
        env["AGYLOOP_AGY_SETTINGS"] = json.dumps(invocation.settings)
        settings_path = cwd / ".agyloop" / "cli-settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(invocation.settings, indent=2) + "\n", encoding="utf-8")
        env["AGYLOOP_AGY_SETTINGS_FILE"] = str(settings_path)
    return subprocess.run(  # nosec B603
        list(invocation.argv),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


class AgyCliAgentGateway:
    """One live ``agy -p`` session. Conversation id is passed via ``--conversation``."""

    def __init__(
        self,
        *,
        cwd: str,
        conversation_id: str | None = None,
        model: str | None = None,
        unsafe_skip_permissions: bool = False,
        print_timeout: str | None = None,
        runner: AgyProcessRunner | None = None,
        permission_mode: UserPermissionMode = DEFAULT_USER_PERMISSION_MODE,
    ) -> None:
        self._cwd = Path(cwd)
        self._conversation_id = conversation_id
        self._model = model
        self._unsafe_skip_permissions = unsafe_skip_permissions
        self._print_timeout = print_timeout
        self._runner = runner or execute_agy
        self._permission_mode = permission_mode

    def resolve_tool_approval(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        del request_id, allow, reason
        return False

    async def set_profile(self, profile: ModelEffortProfile) -> None:
        self._model = profile.model

    async def set_permission_mode(self, mode: str) -> None:
        if mode in ("autonomous", "scoped", "safe", "yolo"):
            self._permission_mode = mode  # type: ignore[assignment]

    async def set_cwd(self, cwd: str) -> None:
        self._cwd = Path(cwd)

    async def set_session_resources(self, **kwargs: Any) -> None:
        del kwargs

    async def send_turn(self, prompt_text: str) -> TurnOutcome:
        if self._runner is execute_agy and shutil.which("agy") is None:
            raise AgentConfigError("agy CLI not found on PATH; install it or use --gateway sdk")
        kwargs: dict[str, Any] = {
            "prompt": prompt_text,
            "cwd": self._cwd,
            "conversation_id": self._conversation_id,
            "model": self._model,
            "unsafe_skip_permissions": self._unsafe_skip_permissions,
            "permission_mode": self._permission_mode,
        }
        if self._print_timeout is not None:
            kwargs["print_timeout"] = self._print_timeout
        invocation = build_agy_argv(**kwargs)
        result = self._runner(invocation, cwd=self._cwd)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        combined = "\n".join(part for part in (stdout, stderr) if part)
        if result.returncode != 0:
            outcome = outcome_from_exception(
                RuntimeError(combined or f"agy exited {result.returncode}"),
                output_text=combined,
                session_id=self._conversation_id,
            )
            if isinstance(classify(outcome.signals), Available):
                raise AgentConfigError(combined or f"agy exited {result.returncode}")
            return outcome
        printed = stdout or stderr
        if not printed:
            raise AgentConfigError("agy exited 0 with empty print (stdout and stderr were blank)")
        return TurnOutcome(
            signals=TurnSignals(),
            verdict=None,
            output_text=printed,
            session_id=self._conversation_id,
        )

    async def close(self) -> None:
        return None
