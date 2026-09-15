# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tool approval gate for Manual permission mode — never blocks on stdin."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from claude_agent_sdk.types import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)

Decision = Literal["allow", "deny"]


@dataclass
class PendingApproval:
    request_id: str
    tool_name: str
    input_summary: str
    created_at: float


class ToolApprovalGate:
    """Async approve/deny with timeout. Operator decisions arrive via control inbox."""

    def __init__(self, *, timeout_seconds: float = 30.0) -> None:
        self._timeout = timeout_seconds
        self._pending: dict[str, PendingApproval] = {}
        self._decisions: dict[str, tuple[Decision, str]] = {}
        self._events: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def resolve(self, request_id: str, *, allow: bool, reason: str = "") -> bool:
        if request_id not in self._pending and request_id not in self._decisions:
            # Still accept early decisions before the callback registers.
            self._decisions[request_id] = ("allow" if allow else "deny", reason)
            return True
        self._decisions[request_id] = ("allow" if allow else "deny", reason)
        return True

    def drain_events(self) -> list[dict[str, Any]]:
        events = list(self._events)
        self._events.clear()
        return events

    async def can_use_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        context: ToolPermissionContext,
    ) -> PermissionResultAllow | PermissionResultDeny:
        del context
        request_id = str(uuid.uuid4())
        summary = _summarize_input(tool_input)
        pending = PendingApproval(
            request_id=request_id,
            tool_name=tool_name,
            input_summary=summary,
            created_at=time.monotonic(),
        )
        async with self._lock:
            self._pending[request_id] = pending
            self._events.append(
                {
                    "type": "tool.approval_needed",
                    "request_id": request_id,
                    "tool_name": tool_name,
                    "input_summary": summary,
                    "timeout_seconds": self._timeout,
                }
            )

        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            decision = self._decisions.pop(request_id, None)
            if decision is not None:
                async with self._lock:
                    self._pending.pop(request_id, None)
                kind, reason = decision
                if kind == "allow":
                    return PermissionResultAllow()
                return PermissionResultDeny(
                    message=reason or "denied by operator",
                    interrupt=False,
                )
            await asyncio.sleep(0.1)

        async with self._lock:
            self._pending.pop(request_id, None)
            self._events.append(
                {
                    "type": "tool.approval_timeout",
                    "request_id": request_id,
                    "tool_name": tool_name,
                }
            )
        return PermissionResultDeny(
            message=(
                "tool approval timed out — denied to preserve autonomy "
                "(never block on a human). Use `claudeloop tool approve ID` sooner, "
                "or switch to bypass / accept-edits / auto."
            ),
            interrupt=False,
        )


def _summarize_input(tool_input: dict[str, Any]) -> str:
    text = str(tool_input)
    if len(text) > 200:
        return text[:197] + "..."
    return text
