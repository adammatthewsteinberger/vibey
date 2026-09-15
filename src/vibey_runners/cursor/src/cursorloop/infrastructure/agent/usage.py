# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Per-turn tokens and billed dollars from ``agent.get_usage()``.

``cost is None`` means UNKNOWN, never zero. Returning ``0.0`` for an
unsettled ``AgentUsage.cost`` would let a ``--max-cost`` cap run forever.
"""

from __future__ import annotations

from typing import Any


class CursorUsageReader:
    """``UsageReader`` over a durable Agent handle."""

    def __init__(self, agent: Any) -> None:
        self._agent = agent

    async def turn_tokens(self, run_id: str) -> int:
        usage = self._agent.get_usage(run_id=run_id)
        runs = getattr(usage, "runs", ()) or ()
        for item in runs:
            if getattr(item, "run_id", None) == run_id:
                inner = getattr(item, "usage", None)
                total = getattr(inner, "total_tokens", None) if inner is not None else None
                if isinstance(total, int) and not isinstance(total, bool):
                    return total
        inner = getattr(usage, "usage", None)
        total = getattr(inner, "total_tokens", None) if inner is not None else None
        return total if isinstance(total, int) and not isinstance(total, bool) else 0

    async def billed_cost_usd(self) -> float | None:
        usage = self._agent.get_usage()
        cost = getattr(usage, "cost", None)
        if cost is None:
            return None
        charged = getattr(cost, "charged_cents", None)
        if charged is None:
            return None
        return float(charged) / 100.0
