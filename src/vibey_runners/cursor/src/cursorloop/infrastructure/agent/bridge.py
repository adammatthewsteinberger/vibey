# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Own the Cursor SDK bridge lifetime and create/resume durable agents.

``bootstrap`` calls this module so ``cursor_sdk`` stays inside infrastructure/
while the composition root still owns when the bridge starts and stops.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cursor_sdk import Agent, CursorClient

from cursorloop.domain.model_profile import ModelProfile
from cursorloop.infrastructure.agent.options import build_agent_options

LaunchBridge = Callable[..., Any]
_API_KEY_ENV = "CURSOR_API_KEY"


@dataclass(frozen=True, slots=True)
class LiveBridge:
    """Bridge client + durable agent created for one autonomous run."""

    client: Any
    agent: Any
    owns_client: bool = True
    # (touched, previous): restore CURSOR_API_KEY on close when we exported one.
    _api_key_env_backup: tuple[bool, str | None] = (False, None)

    def close(self) -> None:
        """Release resources.

        Agent close is primarily owned by ``CursorAgentGateway.close`` (runner
        ``finally``). This method still attempts agent close for callers that
        never entered the runner, but suppresses already-gone agents so the
        CLI ``built.close()`` path cannot crash after a successful turn.
        """
        closer = getattr(self.agent, "close", None)
        if callable(closer):
            with contextlib.suppress(Exception):
                closer()
        if self.owns_client:
            shutdown = getattr(self.client, "close", None)
            if callable(shutdown):
                with contextlib.suppress(Exception):
                    shutdown()
        _restore_api_key_env(self._api_key_env_backup)


def _export_api_key(api_key: str | None) -> tuple[bool, str | None]:
    """Export ``CURSOR_API_KEY`` for the SDK bridge; return a restore token."""
    if not api_key:
        return (False, None)
    previous = os.environ.get(_API_KEY_ENV)
    os.environ[_API_KEY_ENV] = api_key
    return (True, previous)


def _restore_api_key_env(backup: tuple[bool, str | None]) -> None:
    touched, previous = backup
    if not touched:
        return
    if previous is None:
        os.environ.pop(_API_KEY_ENV, None)
    else:
        os.environ[_API_KEY_ENV] = previous


def launch_bridge_client(
    workspace: Path,
    *,
    api_key: str | None = None,
    launch_bridge: LaunchBridge | None = None,
) -> tuple[Any, tuple[bool, str | None]]:
    """Start ``CursorClient.launch_bridge`` for ``workspace``.

    The SDK's ``launch_bridge`` does not accept an auth kwarg — it constructs
    ``CursorClient`` with ``allow_api_key_env_fallback=True`` and reads
    ``CURSOR_API_KEY``. When a key is supplied explicitly, export it into the
    process env before launching so the bridge can authenticate. The caller
    must restore via the returned backup token (``LiveBridge.close`` does).
    """
    backup = _export_api_key(api_key)
    launcher = launch_bridge if launch_bridge is not None else CursorClient.launch_bridge
    try:
        client = launcher(workspace=str(workspace), allow_api_key_env_fallback=True)
    except Exception:
        _restore_api_key_env(backup)
        raise
    return client, backup


def open_live_bridge(
    *,
    workspace: Path,
    profile: ModelProfile,
    api_key: str | None = None,
    resume_agent_id: str | None = None,
    client: Any | None = None,
    launch_bridge: LaunchBridge | None = None,
    create_agent: Callable[..., Any] | None = None,
    resume_agent: Callable[..., Any] | None = None,
) -> LiveBridge:
    """Launch (or reuse) a bridge client and create/resume a durable Agent."""
    owns_client = client is None
    if client is not None:
        live_client = client
        backup: tuple[bool, str | None] = (False, None)
    else:
        live_client, backup = launch_bridge_client(
            workspace, api_key=api_key, launch_bridge=launch_bridge
        )
    options = build_agent_options(profile=profile, cwd=str(workspace))
    create = create_agent if create_agent is not None else Agent.create
    resume = resume_agent if resume_agent is not None else Agent.resume
    create_kwargs: dict[str, Any] = {"options": options, "client": live_client}
    if api_key:
        create_kwargs["api_key"] = api_key
    try:
        if resume_agent_id:
            agent = resume(resume_agent_id, options=options, client=live_client)
        else:
            agent = create(**create_kwargs)
    except Exception:
        _restore_api_key_env(backup)
        if owns_client:
            shutdown = getattr(live_client, "close", None)
            if callable(shutdown):
                with contextlib.suppress(Exception):
                    shutdown()
        raise
    return LiveBridge(
        client=live_client,
        agent=agent,
        owns_client=owns_client,
        _api_key_env_backup=backup,
    )
