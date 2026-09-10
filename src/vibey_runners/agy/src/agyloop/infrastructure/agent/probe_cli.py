# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capacity probe backed by the ``agy`` CLI, for ``--gateway cli``.

The SDK probe in ``probe.py`` boots the local Antigravity harness. Selecting
``--gateway cli`` is an explicit opt-out of that harness, so the probe must opt
out too -- otherwise a preflight probe exercises the very transport the operator
just declined, and a harness that cannot start kills the run before turn one.

Degrading ``--gateway cli`` to a no-op probe would be the cheaper fix, but it
silently loses capacity detection: every window and credits rejection would look
like ``Available``. One cheap ``agy -p`` through the same ``build_agy_argv``
guards and the same ``classify()`` ladder keeps the distinction intact.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from agyloop.application.dto import TurnOutcome
from agyloop.domain.capacity import Available
from agyloop.domain.classify import TurnSignals, classify
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.cli_argv import build_agy_argv
from agyloop.infrastructure.agent.gateway_cli import AgyProcessRunner, execute_agy
from agyloop.infrastructure.agent.translate import outcome_from_exception

PROBE_PROMPT = "Reply with the single word OK and nothing else."


class AgyCliCapacityProbe:
    """One throwaway ``agy -p``, no ``--conversation``, so the probe never
    pollutes or resumes the run's session."""

    def __init__(
        self,
        *,
        cwd: str,
        model: str | None = None,
        unsafe_skip_permissions: bool = False,
        print_timeout: str | None = None,
        runner: AgyProcessRunner | None = None,
    ) -> None:
        self._cwd = Path(cwd)
        self._model = model
        self._unsafe_skip_permissions = unsafe_skip_permissions
        self._print_timeout = print_timeout
        self._runner = runner or execute_agy

    def set_model(self, model: str | None) -> None:
        """Keep the probe on the run's model so a per-model spend limit is not
        masked by probing a cheaper one."""
        self._model = model

    async def probe(self) -> TurnOutcome:
        if self._runner is execute_agy and shutil.which("agy") is None:
            raise AgentConfigError("agy CLI not found on PATH; install it or use --gateway sdk")
        kwargs: dict[str, object] = {
            "prompt": PROBE_PROMPT,
            "cwd": self._cwd,
            "conversation_id": None,
            "model": self._model,
            "unsafe_skip_permissions": self._unsafe_skip_permissions,
        }
        if self._print_timeout is not None:
            kwargs["print_timeout"] = self._print_timeout
        invocation = build_agy_argv(**kwargs)  # type: ignore[arg-type]
        result = self._runner(invocation, cwd=self._cwd)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        combined = "\n".join(part for part in (stdout, stderr) if part)
        if result.returncode != 0:
            outcome = outcome_from_exception(
                RuntimeError(combined or f"agy exited {result.returncode}"),
                output_text=combined,
                session_id=None,
            )
            # A non-zero exit the ladder reads as Available is not capacity --
            # it is a broken invocation. Fail closed rather than reporting
            # headroom the account may not have.
            if isinstance(classify(outcome.signals), Available):
                raise AgentConfigError(combined or f"agy exited {result.returncode}")
            return outcome
        return TurnOutcome(
            signals=TurnSignals(),
            verdict=None,
            output_text=stdout or stderr,
            session_id=None,
        )
