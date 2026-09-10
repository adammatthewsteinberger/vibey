# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""SessionCatalog over agyloop's `.agyloop/runs` registry.

There is no vendor API to enumerate Antigravity conversations we did not
create (F6). This catalog lists only runs this process wrote.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agyloop.domain.session import SessionRef
from agyloop.infrastructure.rundir import RunDirectory, list_run_directories


class RunRegistryCatalog:
    def most_recent(self, cwd: str) -> SessionRef | None:
        root = Path(cwd)
        resumable = [
            directory
            for directory in list_run_directories(root)
            if directory.read_meta().conversation_id
        ]
        return _to_session_ref(resumable[-1]) if resumable else None

    def list_all(self, cwd: str | None = None) -> list[SessionRef]:
        root = Path(cwd) if cwd is not None else Path.cwd()
        return [_to_session_ref(directory) for directory in list_run_directories(root)]


def _to_session_ref(directory: RunDirectory) -> SessionRef:
    meta = directory.read_meta()
    session_id = meta.conversation_id or meta.run_id
    last_modified: datetime | None = None
    if meta.started_at:
        try:
            last_modified = datetime.fromisoformat(meta.started_at)
        except ValueError:
            last_modified = None
    preview = None
    plan_text = directory.read_plan_text()
    if plan_text:
        preview = plan_text.strip().splitlines()[0][:200] if plan_text.strip() else None
    return SessionRef(
        session_id=session_id,
        cwd=meta.cwd,
        last_modified=last_modified,
        first_prompt_preview=preview,
    )
