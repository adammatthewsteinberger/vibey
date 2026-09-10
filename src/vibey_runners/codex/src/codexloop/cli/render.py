# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Human-readable rendering of CLI results."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from codexloop.application.dto import RunResult
from codexloop.domain.session import ThreadRef


def render_result(result: RunResult) -> str:
    status = "done" if result.success else result.reason
    thread = result.thread_id or "-"
    return f"{status}  turns={result.turns}  thread={thread}"


def render_threads(threads: Sequence[ThreadRef]) -> str:
    if not threads:
        return "No threads recorded."
    return "\n".join(
        f"{ref.thread_id}\t{ref.model}\t{ref.cwd}\t{ref.started_at.isoformat()}" for ref in threads
    )


def render_runs(records: Sequence[Mapping[str, object]]) -> str:
    if not records:
        return "No runs."
    return "\n".join(str(record.get("run_id", "-")) for record in records)


def render_status(record: Mapping[str, object] | None) -> str:
    if record is None:
        return "No runs."
    return json.dumps(dict(record), indent=2, default=str)


def render_logs(text: str) -> str:
    return text if text else "No logs."
