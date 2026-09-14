# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Git-backed save points under refs/claudeloop/<run_id>/<n>."""

from __future__ import annotations

import json
import subprocess  # nosec B404 — argv lists are fixed git subcommands, never shell=True
from datetime import datetime, timezone
from pathlib import Path

from claudeloop.domain.savepoint import SavePointRef, UnwindResult
from claudeloop.domain.savepoint_message import format_savepoint_commit_message

_CONTROL_PLANE_DIR = ".claudeloop"


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
        # Never commit control-plane state into the project history, even when
        # a host repo forgot to gitignore `.claudeloop/`.
        self._run(["git", "reset", "-q", "--", _CONTROL_PLANE_DIR], check=False)
        # Only commit when the index differs from HEAD. Unchanged trees still
        # get a numbered refs/claudeloop/<run_id>/<n> pointing at current HEAD
        # — no empty commits on wait/poll turns.
        has_staged = self._run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0
        changed_paths = self._staged_paths() if has_staged else ()
        turn_n = attempt if attempt is not None else self._next_n(run_id)
        subject: str | None = None
        if has_staged:
            if message is not None and attempt is None and not summary and not remaining_work:
                # Legacy single-line callers (tests): keep a simple subject.
                subject = f"chore(claudeloop): {message}"
                body = f"Run: {run_id}\nLabel: {label}\n"
            else:
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
                [
                    "git",
                    "commit",
                    "--no-verify",
                    "-m",
                    subject,
                    "-m",
                    body,
                ],
            )
        sha = self._run(["git", "rev-parse", "HEAD"]).stdout.strip()
        n = self._next_n(run_id)
        ref = f"refs/claudeloop/{run_id}/{n}"
        self._run(["git", "update-ref", ref, sha])
        point = SavePointRef(
            n=n,
            ref=ref,
            sha=sha,
            label=label,
            at=datetime.now(timezone.utc),
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

    def unwind(self, *, run_id: str, to: str, backup: bool) -> UnwindResult:
        points = self.list_points(run_id)
        target = self._resolve_target(points, to)
        backup_ref: str | None = None
        if backup:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_ref = f"refs/claudeloop/backup/{run_id}/{stamp}"
            head = self._run(["git", "rev-parse", "HEAD"]).stdout.strip()
            self._run(["git", "update-ref", backup_ref, head])
        self._run(["git", "reset", "--hard", target.sha])
        return UnwindResult(to=target, backup_ref=backup_ref, restored_sha=target.sha)

    def changes_since(self, since_sha: str | None) -> str:
        if not self._is_git_repo():
            return ""
        if since_sha:
            result = self._run(["git", "log", "--oneline", f"{since_sha}..HEAD"], check=False)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        result = self._run(["git", "status", "--short"], check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    def _next_n(self, run_id: str) -> int:
        existing = self.list_points(run_id)
        return (existing[-1].n + 1) if existing else 1

    def _staged_paths(self) -> tuple[str, ...]:
        result = self._run(
            ["git", "diff", "--cached", "--name-only", "-z"],
            check=False,
        )
        if result.returncode != 0 or not result.stdout:
            return ()
        parts = [p for p in result.stdout.split("\0") if p]
        return tuple(parts)

    def _append_index(
        self,
        point: SavePointRef,
        *,
        committed: bool = False,
        subject: str | None = None,
        path_count: int = 0,
    ) -> None:
        # Infer run_id from ref: refs/claudeloop/<run_id>/<n>
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
        with self._index_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _resolve_target(self, points: list[SavePointRef], to: str) -> SavePointRef:
        # A SHA prefix can itself be all-digit (no a-f characters), so digits
        # alone don't prove `to` is a savepoint number -- only try the number
        # lookup, and fall through to ref/sha/label matching either way, so
        # a numeric-looking SHA prefix still resolves correctly.
        if to.isdigit():
            n = int(to)
            for point in points:
                if point.n == n:
                    return point
        for point in points:
            if point.ref == to or point.sha.startswith(to) or point.label == to:
                return point
        raise ValueError(f"no save point matching {to!r}")

    def _is_git_repo(self) -> bool:
        result = self._run(["git", "rev-parse", "--is-inside-work-tree"], check=False)
        return result.returncode == 0 and result.stdout.strip() == "true"

    def _run(self, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        # Fixed argv only (git + literal subcommands); cwd is the project worktree.
        return subprocess.run(  # nosec B603
            args,
            cwd=self._cwd,
            check=check,
            capture_output=True,
            text=True,
        )
