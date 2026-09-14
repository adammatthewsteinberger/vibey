# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Git-backed save points under refs/cursorloop/<run_id>/<n>."""

from __future__ import annotations

import json
import subprocess  # nosec B404 — fixed argv git subcommands, never shell=True
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

_CONTROL_PLANE_DIR = ".cursorloop"


@dataclass(frozen=True, slots=True)
class SavePointRef:
    n: int
    ref: str
    sha: str
    label: str
    created_at: str


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
        message: str = "",
        attempt: int | None = None,
        verdict_name: str = "Continue",
        summary: str = "",
        remaining_work: tuple[str, ...] = (),
    ) -> SavePointRef | None:
        del attempt, verdict_name, summary, remaining_work
        if not self._is_git_repo():
            return None
        self._run(["git", "add", "-A"])
        self._run(["git", "reset", "-q", "--", _CONTROL_PLANE_DIR], check=False)
        has_staged = self._run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0
        if has_staged:
            subject = f"chore(cursorloop): {message or label}"
            self._run(["git", "commit", "--no-verify", "-m", subject])
        sha = self._run(["git", "rev-parse", "HEAD"]).stdout.strip()
        n = self._next_n(run_id)
        ref = f"refs/cursorloop/{run_id}/{n}"
        self._run(["git", "update-ref", ref, sha])
        point = SavePointRef(
            n=n,
            ref=ref,
            sha=sha,
            label=label,
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(point)) + "\n")
        return point

    def list_points(self, run_id: str) -> list[SavePointRef]:
        out: list[SavePointRef] = []
        if not self._index_path.is_file():
            return out
        for line in self._index_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if str(data.get("ref", "")).startswith(f"refs/cursorloop/{run_id}/"):
                out.append(SavePointRef(**{k: data[k] for k in SavePointRef.__dataclass_fields__}))
        return out

    def unwind(self, *, run_id: str, to: str, backup: bool) -> object:
        del run_id, backup
        self._run(["git", "reset", "--hard", to])
        return {"sha": to}

    def changes_since(self, since_sha: str | None) -> str:
        if since_sha is None:
            result = self._run(["git", "status", "--porcelain"], check=False)
            return result.stdout
        result = self._run(["git", "diff", "--stat", since_sha], check=False)
        return result.stdout

    def _next_n(self, run_id: str) -> int:
        return len(self.list_points(run_id)) + 1

    def _is_git_repo(self) -> bool:
        return self._run(["git", "rev-parse", "--is-inside-work-tree"], check=False).returncode == 0

    def _run(self, argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # nosec B603
            argv,
            cwd=self._cwd,
            capture_output=True,
            text=True,
            check=check,
        )
