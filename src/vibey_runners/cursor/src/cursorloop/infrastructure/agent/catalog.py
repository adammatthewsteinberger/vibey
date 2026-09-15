# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Resolved agent handles via ``client.agents.list/get/list_runs``.

Local persistence is workspace-scoped. Always pass ``cwd=`` on local list/get
and ``workspace=`` on bridge launch. Resuming from a mismatched cwd without
``allow_cwd_change`` is refused — otherwise the bridge silently finds nothing.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from cursor_sdk import CursorClient

from cursorloop.domain.session import AgentRef, runtime_from_id


def _parse_modified(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _ref_from_info(info: object, *, fallback_cwd: str) -> AgentRef:
    agent_id = str(getattr(info, "agent_id", "") or "")
    stored_cwd = str(getattr(info, "cwd", "") or "") or fallback_cwd
    runtime = getattr(info, "runtime", None)
    if not isinstance(runtime, str) or not runtime:
        runtime = runtime_from_id(agent_id)
    name = getattr(info, "name", None)
    summary = getattr(info, "summary", None)
    status = getattr(info, "status", None)
    return AgentRef(
        agent_id=agent_id,
        runtime=runtime,
        cwd=stored_cwd,
        name=name if isinstance(name, str) else None,
        summary=summary if isinstance(summary, str) else None,
        last_modified=_parse_modified(getattr(info, "last_modified", None)),
        status=status if isinstance(status, str) else None,
    )


class CursorAgentCatalog:
    """``AgentCatalog`` over the client's agents resource namespace."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @classmethod
    def connect(
        cls,
        workspace: str,
        *,
        launch_bridge: Callable[..., Any] | None = None,
    ) -> CursorAgentCatalog:
        if launch_bridge is None:
            launch_bridge = CursorClient.launch_bridge
        client = launch_bridge(workspace=workspace)
        return cls(client)

    def list_all(self, cwd: str | None = None) -> list[AgentRef]:
        agents = self._client.agents
        result = agents.list(runtime="local", cwd=cwd) if cwd is not None else agents.list()
        items = getattr(result, "items", result) or ()
        fallback = cwd if cwd is not None else "."
        return [_ref_from_info(item, fallback_cwd=fallback) for item in items]

    def most_recent(self, cwd: str) -> AgentRef | None:
        refs = self.list_all(cwd)
        if not refs:
            return None
        oldest = datetime.min.replace(tzinfo=UTC)
        return max(refs, key=lambda ref: ref.last_modified or oldest)

    def get(self, agent_id: str, *, cwd: str, allow_cwd_change: bool = False) -> AgentRef:
        info = self._client.agents.get(agent_id, cwd=cwd)
        ref = _ref_from_info(info, fallback_cwd=cwd)
        if ref.cwd != cwd and not allow_cwd_change:
            raise ValueError(
                f"agent {agent_id!r} cwd {ref.cwd!r} does not match {cwd!r}; "
                "pass allow_cwd_change to resume from a mismatched cwd"
            )
        return ref

    def list_runs(self, agent_id: str, *, cwd: str | None = None) -> list[object]:
        kwargs: dict[str, Any] = {}
        if cwd is not None:
            kwargs["cwd"] = cwd
        result = self._client.agents.list_runs(agent_id, **kwargs)
        items = getattr(result, "items", result) or ()
        return list(items)
