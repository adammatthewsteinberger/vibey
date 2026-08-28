# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Process/JSON integration with the independently versioned vibey-skills CLI."""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from vibey.application.dto import JobRecord
from vibey.application.interfaces import SkillsContextResult

_MODES = frozenset({"off", "shadow", "inject"})
_DEFAULT_BUDGET = 6_000
_MIN_BUDGET = 1_000
_MAX_BUDGET = 32_000


class VibeySkillsContextCompiler:
    """Build/reuse a local index and ask vibey-skills for one packet."""

    def __init__(
        self,
        *,
        mode: str,
        index_path: Path,
        budget: int = _DEFAULT_BUDGET,
        command: Sequence[str] | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        if mode not in _MODES - {"off"}:
            raise ValueError("skills context mode must be 'shadow' or 'inject'")
        if not _MIN_BUDGET <= budget <= _MAX_BUDGET:
            raise ValueError(
                f"skills context budget must be between {_MIN_BUDGET} and {_MAX_BUDGET}"
            )
        if timeout_seconds <= 0:
            raise ValueError("skills context timeout must be positive")
        self._mode = mode
        self._index_path = index_path
        self._budget = budget
        self._command = tuple(command or (sys.executable, "-m", "vibey_skills.cli"))
        if not self._command or any(not part for part in self._command):
            raise ValueError("skills context command must not be empty")
        self._timeout_seconds = timeout_seconds
        self._index_lock = asyncio.Lock()

    async def compile(self, *, job: object, worktree_path: Path) -> SkillsContextResult:
        if not isinstance(job, JobRecord):
            raise TypeError("skills context compiler requires a JobRecord")
        context_dir = worktree_path / ".vibey" / "context" / "skills"
        context_dir.mkdir(parents=True, exist_ok=True)
        request_path = context_dir / f"{job.id}.request.json"
        packet_path = context_dir / f"{job.id}.packet.md"
        manifest_path = context_dir / f"{job.id}.packet.json"
        request_path.write_text(
            json.dumps(
                _request_for(job, budget=self._budget),
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            await self._ensure_index()
            returncode, _stdout, stderr = await self._run(
                *self._command,
                "packet",
                "--request",
                str(request_path),
                "--index",
                str(self._index_path),
                "--budget",
                str(self._budget),
                "--output",
                str(packet_path),
                "--manifest",
                str(manifest_path),
            )
            manifest = _load_json_object(manifest_path)
            status = str(manifest.get("status", "error"))
            markdown = packet_path.read_text(encoding="utf-8") if packet_path.is_file() else ""
            provenance = _provenance(
                mode=self._mode,
                status=status,
                manifest=manifest,
                returncode=returncode,
                detail=stderr,
            )
            if returncode not in {0, 2}:
                return SkillsContextResult(self._mode, "error", "", provenance)
            return SkillsContextResult(self._mode, status, markdown, provenance)
        except (TimeoutError, OSError, ValueError) as exc:
            return SkillsContextResult(
                self._mode,
                "error",
                "",
                {
                    "mode": self._mode,
                    "status": "error",
                    "fallback": "existing_prompt",
                    "detail": _bounded(str(exc)),
                },
            )

    async def _ensure_index(self) -> None:
        async with self._index_lock:
            manifest = self._index_path / "manifest.json"
            database = self._index_path / "index.sqlite3"
            if manifest.is_file() and database.is_file():
                returncode, _stdout, _stderr = await self._run(
                    *self._command,
                    "index",
                    "inspect",
                    str(self._index_path),
                    "--json",
                )
                if returncode == 0:
                    return
            returncode, _stdout, stderr = await self._run(
                *self._command, "index", "build", "--output", str(self._index_path)
            )
            if returncode != 0:
                raise OSError(f"vibey-skills index build failed: {_bounded(stderr)}")

    async def _run(self, *argv: str) -> tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self._timeout_seconds
            )
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        return (
            process.returncode or 0,
            stdout.decode(errors="replace"),
            stderr.decode(errors="replace"),
        )


def compiler_from_config(
    config: Mapping[str, object], *, repo_path: Path
) -> VibeySkillsContextCompiler | None:
    raw = config.get("skills_context")
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError("skills_context project config must be an object")
    mode = str(raw.get("mode", "off"))
    if mode == "off":
        return None
    if mode not in _MODES:
        raise ValueError("skills_context.mode must be off, shadow, or inject")
    budget = raw.get("budget", _DEFAULT_BUDGET)
    if not isinstance(budget, int) or isinstance(budget, bool):
        raise ValueError("skills_context.budget must be an integer")
    timeout = raw.get("timeout_seconds", 120.0)
    if not isinstance(timeout, int | float) or isinstance(timeout, bool):
        raise ValueError("skills_context.timeout_seconds must be numeric")
    command_raw = raw.get("command")
    command: tuple[str, ...] | None = None
    if command_raw is not None:
        if not isinstance(command_raw, list) or not all(
            isinstance(value, str) and value for value in command_raw
        ):
            raise ValueError("skills_context.command must be a non-empty string list")
        command = tuple(command_raw)
    index_raw = raw.get("index_path")
    index_path = (
        Path(str(index_raw)).expanduser()
        if index_raw is not None
        else repo_path / ".vibey" / "skills-context" / "index"
    )
    if not index_path.is_absolute():
        index_path = repo_path / index_path
    return VibeySkillsContextCompiler(
        mode=mode,
        index_path=index_path,
        budget=budget,
        command=command,
        timeout_seconds=float(timeout),
    )


def _request_for(job: JobRecord, *, budget: int) -> dict[str, Any]:
    payload = job.payload
    verification = payload.get("verification")
    commands: list[str] = []
    if isinstance(verification, Mapping):
        raw_commands = verification.get("commands", ())
        if isinstance(raw_commands, Sequence) and not isinstance(raw_commands, str | bytes):
            commands = [str(value) for value in raw_commands]
    request: dict[str, Any] = {
        "schema_version": 1,
        "title": str(payload.get("title", job.work_item_id or job.kind)),
        "objective": str(payload.get("objective", payload.get("title", ""))),
        "phase": job.phase.value,
        "job_kind": job.kind,
        "commands": commands,
        "maximum_context_tokens": budget,
        "ranking_mode": "deterministic",
    }
    for field in (
        "requirements",
        "acceptance_criteria",
        "languages",
        "dependencies",
        "paths",
        "target_files",
        "changed_files",
        "required_plugins",
        "excluded_plugins",
        "required_skills",
        "excluded_skills",
    ):
        value = payload.get(field)
        if isinstance(value, Sequence) and not isinstance(value, str | bytes):
            request[field] = [str(item) for item in value]
    repair = payload.get("repair_detail")
    if isinstance(repair, str) and repair:
        request["prior_failure_class"] = "verification"
        request["error_summary"] = _bounded(repair)
    return request


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("vibey-skills packet manifest is not a JSON object")
    return value


def _provenance(
    *,
    mode: str,
    status: str,
    manifest: Mapping[str, object],
    returncode: int,
    detail: str,
) -> dict[str, object]:
    allowed = (
        "schema_version",
        "index_version",
        "skills_release",
        "corpus_sha256",
        "query_sha256",
        "packet_sha256",
        "packet_token_estimate",
        "maximum_context_tokens",
        "mandatory_token_estimate",
        "retrieved_token_estimate",
        "retrieval_latency_ns",
        "selected_plugins",
        "selected_skills",
        "fallback",
    )
    result: dict[str, object] = {
        "mode": mode,
        "status": status,
        "returncode": returncode,
    }
    result.update({key: manifest[key] for key in allowed if key in manifest})
    if detail.strip() and returncode not in {0, 2}:
        result["detail"] = _bounded(detail)
    return result


def _bounded(value: str, limit: int = 1_000) -> str:
    return value.strip()[:limit]
