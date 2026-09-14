# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Git-backed save points under ``refs/codexloop/<run_id>/<n>``."""

from __future__ import annotations

import json
import subprocess  # nosec B404 — argv lists are fixed git subcommands, never shell=True
from datetime import UTC, datetime
from pathlib import Path

from codexloop.domain.errors import ConfigurationError
from codexloop.domain.savepoint import SavePointRef, UnwindResult
from codexloop.domain.savepoint_message import format_savepoint_commit_message

_CONTROL_PLANE_DIR = ".codexloop"


class GitSavePointStore:
    def __init__(self, *, cwd: Path, index_path: Path) -> None:
        self._cwd = cwd
        self._index_path = index_path
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._index_path.exists():
            self._index_path.touch()

    def create(
        self,
        *,
        run_id: str,
        label: str,
        message: str | None = None,
        attempt: int | None = None,
        verdict_name: str = "Continue",
        summary: str = "",
        remaining_work: tuple[str, ...] = (),
    ) -> SavePointRef | None:
        if not self._is_git_repo():
            return None
        self._run(["git", "add", "-A"])
        self._run(["git", "reset", "-q", "--", _CONTROL_PLANE_DIR], check=False)
        has_staged = self._run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0
        changed_paths = self._staged_paths() if has_staged else ()
        turn_n = attempt if attempt is not None else self._next_n(run_id)
        subject: str | None = None
        if has_staged:
            subject, body = format_savepoint_commit_message(
                run_id=run_id,
                attempt=turn_n,
                verdict_name=verdict_name,
                summary=summary or message or "",
                remaining_work=remaining_work,
                changed_paths=changed_paths,
                label=label,
            )
            self._run(
                ["git", "commit", "--no-verify", "-m", subject, "-m", body],
            )
        sha = self._run(["git", "rev-parse", "HEAD"]).stdout.strip()
        n = self._next_n(run_id)
        ref = f"refs/codexloop/{run_id}/{n}"
        self._run(["git", "update-ref", ref, sha])
        point = SavePointRef(
            n=n,
            ref=ref,
            sha=sha,
            label=label,
            at=datetime.now(UTC),
            plan_item=None,
            committed=has_staged,
        )
        self._append_index(
            point,
            committed=has_staged,
            subject=subject,
            path_count=len(changed_paths),
        )
        return point

    def list_points(self, run_id: str) -> list[SavePointRef]:
        if not self._index_path.is_file():
            return []
        points: list[SavePointRef] = []
        for line in self._index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if data.get("run_id") and data["run_id"] != run_id:
                continue
            points.append(
                SavePointRef(
                    n=int(data["n"]),
                    ref=str(data["ref"]),
                    sha=str(data["sha"]),
                    label=str(data["label"]),
                    at=datetime.fromisoformat(data["at"]),
                    plan_item=data.get("plan_item"),
                    committed=bool(data.get("committed", False)),
                )
            )
        return points

    def unwind(self, *, run_id: str, to: str, backup: bool, live: bool = False) -> UnwindResult:
        if live:
            raise ConfigurationError("unwind refuses while a run is live")
        points = self.list_points(run_id)
        target = self._resolve_target(points, to)
        backup_ref: str | None = None
        if backup:
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            backup_ref = f"refs/codexloop/backup/{run_id}/{stamp}"
            head = self._run(["git", "rev-parse", "HEAD"]).stdout.strip()
            self._run(["git", "update-ref", backup_ref, head])
        self._run(["git", "reset", "--hard", target.sha])
        return UnwindResult(to=target, backup_ref=backup_ref, restored_sha=target.sha)

    def _next_n(self, run_id: str) -> int:
        existing = self.list_points(run_id)
        return (existing[-1].n + 1) if existing else 1

    def _staged_paths(self) -> tuple[str, ...]:
        result = self._run(["git", "diff", "--cached", "--name-only", "-z"], check=False)
        if result.returncode != 0 or not result.stdout:
            return ()
        return tuple(p for p in result.stdout.split("\0") if p)

    def _append_index(
        self,
        point: SavePointRef,
        *,
        committed: bool = False,
        subject: str | None = None,
        path_count: int = 0,
    ) -> None:
        parts = point.ref.split("/")
        run_id = parts[2] if len(parts) >= 4 else ""
        entry = {
            "run_id": run_id,
            "n": point.n,
            "ref": point.ref,
            "sha": point.sha,
            "label": point.label,
            "at": point.at.isoformat(),
            "plan_item": point.plan_item,
            "committed": committed,
            "subject": subject,
            "path_count": path_count,
        }
        with self._index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def _resolve_target(self, points: list[SavePointRef], to: str) -> SavePointRef:
        # Numeric save-point indexes (``1``, ``2``, …) are accepted, but a
        # shortened SHA can be all digits (e.g. ``4158599``). Prefer an exact
        # index hit, then fall through to SHA/ref/label matching.
        if to.isdigit():
            n = int(to)
            for point in points:
                if point.n == n:
                    return point
        for point in points:
            if point.ref == to or point.sha.startswith(to) or point.label == to:
                return point
        if to.isdigit():
            raise ValueError(f"no save point numbered {int(to)}")
        raise ValueError(f"no save point matching {to!r}")

    def _is_git_repo(self) -> bool:
        result = self._run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
        return result.returncode == 0 and result.stdout.strip() == "true"

    def _run(self, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # nosec B603
            args,
            cwd=self._cwd,
            check=check,
            capture_output=True,
            text=True,
        )


__all__ = ["GitSavePointStore"]
