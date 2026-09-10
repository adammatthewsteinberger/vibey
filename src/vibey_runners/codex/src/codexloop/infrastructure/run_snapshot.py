# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Writes ``<run_dir>/snapshots/latest.json`` — the always-current run
snapshot.

Distinct from ``infrastructure/snapshot.py``, which archives a *worktree*
into a timestamped directory on explicit ``codexloop snapshot``. This one
is cheap run *state*, rewritten at every turn boundary, so an external
reader can answer "where is this run right now?" without parsing the
whole event stream.

That reader is the reason the file has a fixed name: orchestrators poll a
stable path. ``RunSnapshotSink`` was declared as a port with no
implementation and no caller until this module; the gap made every
codexloop run look snapshot-less from the outside.

The write is atomic (temp file + ``os.replace``) because a poller can
read at any instant, and a half-written JSON file is worse than a stale
one.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

SCHEMA_VERSION = 1


class RunDirSnapshotSink:
    """Persists run state to ``<run_dir>/snapshots/latest.json``."""

    def __init__(self, snapshots_dir: Path) -> None:
        self._dir = snapshots_dir

    def write(self, snapshot: Mapping[str, object]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {"schema_version": SCHEMA_VERSION}
        payload.update(snapshot)
        target = self._dir / "latest.json"
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
        os.replace(tmp, target)
