# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run-scoped resource store under `.claudeloop/runs/<id>/resources/`."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ResourceSnapshot:
    attachments: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    connectors: dict[str, Any] = field(default_factory=dict)
    github: dict[str, Any] = field(default_factory=dict)
    web_search: bool = False
    deep_research: bool = False
    permission_mode: str = "bypass"
    cwd: str | None = None
    cli_system_prompt_append: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachments": list(self.attachments),
            "folders": list(self.folders),
            "skills": list(self.skills),
            "plugins": list(self.plugins),
            "connectors": dict(self.connectors),
            "github": dict(self.github),
            "web_search": self.web_search,
            "deep_research": self.deep_research,
            "permission_mode": self.permission_mode,
            "cwd": self.cwd,
            "cli_system_prompt_append": self.cli_system_prompt_append,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceSnapshot:
        return cls(
            attachments=[str(x) for x in data.get("attachments", [])],
            folders=[str(x) for x in data.get("folders", [])],
            skills=[str(x) for x in data.get("skills", [])],
            plugins=[str(x) for x in data.get("plugins", [])],
            connectors=dict(data.get("connectors") or {}),
            github=dict(data.get("github") or {}),
            web_search=bool(data.get("web_search", False)),
            deep_research=bool(data.get("deep_research", False)),
            permission_mode=str(data.get("permission_mode") or "bypass"),
            cwd=data.get("cwd"),
            cli_system_prompt_append=str(data.get("cli_system_prompt_append") or ""),
        )


class RunResourceStore:
    """Filesystem CRUD for run-scoped attachments, folders, skills, plugins, MCP."""

    def __init__(self, resources_root: Path) -> None:
        self.root = resources_root
        self.attachments_dir = resources_root / "attachments"
        self.artifacts_dir = resources_root.parent / "artifacts"
        self.memories_dir = resources_root.parent / "memories"
        self.research_dir = resources_root / "research"
        self.folders_path = resources_root / "folders.json"
        self.skills_path = resources_root / "skills.json"
        self.plugins_path = resources_root / "plugins.json"
        self.connectors_path = resources_root / "connectors.json"
        self.github_path = resources_root / "github.json"
        self.manifest_path = resources_root / "manifest.toml"
        self.memories_index = self.memories_dir / "index.json"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        self.memories_dir.mkdir(exist_ok=True)
        self.research_dir.mkdir(exist_ok=True)
        for path, default in (
            (self.folders_path, []),
            (self.skills_path, []),
            (self.plugins_path, []),
            (self.connectors_path, {}),
            (self.github_path, {}),
            (self.memories_index, {"items": []}),
        ):
            if not path.is_file():
                path.write_text(json.dumps(default, indent=2) + "\n", encoding="utf-8")

    def snapshot(self) -> ResourceSnapshot:
        self.ensure()
        flags = _read_json_dict(self.root / "flags.json")
        return ResourceSnapshot(
            attachments=sorted(p.name for p in self.attachments_dir.iterdir() if p.is_file()),
            folders=_read_json_list(self.folders_path),
            skills=_read_json_list(self.skills_path),
            plugins=_read_json_list(self.plugins_path),
            connectors=_read_json_dict(self.connectors_path),
            github=_read_json_dict(self.github_path),
            web_search=bool(flags.get("web_search")),
            deep_research=bool(flags.get("deep_research")),
            permission_mode=str(flags.get("permission_mode") or "bypass"),
            cwd=flags.get("cwd"),
            cli_system_prompt_append=str(flags.get("cli_system_prompt_append") or ""),
        )

    def write_manifest(self) -> None:
        snap = self.snapshot()
        lines = [
            "# claudeloop run resource manifest (auto-generated)",
            f'permission_mode = "{snap.permission_mode}"',
            f"web_search = {str(snap.web_search).lower()}",
            f"deep_research = {str(snap.deep_research).lower()}",
        ]
        if snap.cwd:
            lines.append(f'cwd = "{snap.cwd}"')
        for key, values in (
            ("attachments", snap.attachments),
            ("folders", snap.folders),
            ("skills", snap.skills),
            ("plugins", snap.plugins),
        ):
            lines.append(f"{key} = {json.dumps(values)}")
        lines.append(f"connectors = {json.dumps(snap.connectors)}")
        lines.append(f"github = {json.dumps(snap.github)}")
        self.manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def set_flag(self, **kwargs: Any) -> None:
        self.ensure()
        flags = _read_json_dict(self.root / "flags.json")
        flags.update({k: v for k, v in kwargs.items() if v is not None})
        (self.root / "flags.json").write_text(json.dumps(flags, indent=2) + "\n", encoding="utf-8")
        self.write_manifest()

    def attach(self, source: Path) -> Path:
        self.ensure()
        source = source.expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"attachment not found: {source}")
        dest = self.attachments_dir / source.name
        if source.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
        else:
            shutil.copy2(source, dest)
        self.write_manifest()
        return dest

    def unattach(self, name: str) -> None:
        self.ensure()
        target = self.attachments_dir / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.is_file():
            target.unlink()
        else:
            raise FileNotFoundError(f"attachment not found: {name}")
        self.write_manifest()

    def add_folder(self, path: str) -> None:
        folders = _read_json_list(self.folders_path)
        resolved = str(Path(path).expanduser().resolve())
        if resolved not in folders:
            folders.append(resolved)
            self.folders_path.write_text(json.dumps(folders, indent=2) + "\n", encoding="utf-8")
            self.write_manifest()

    def remove_folder(self, path: str) -> None:
        folders = _read_json_list(self.folders_path)
        resolved = str(Path(path).expanduser().resolve())
        folders = [f for f in folders if f != resolved and f != path]
        self.folders_path.write_text(json.dumps(folders, indent=2) + "\n", encoding="utf-8")
        self.write_manifest()

    def add_skill(self, skill: str) -> None:
        _append_unique_json_list(self.skills_path, skill)
        self.write_manifest()

    def remove_skill(self, skill: str) -> None:
        _remove_from_json_list(self.skills_path, skill)
        self.write_manifest()

    def add_plugin(self, plugin: str) -> None:
        _append_unique_json_list(self.plugins_path, plugin)
        self.write_manifest()

    def remove_plugin(self, plugin: str) -> None:
        _remove_from_json_list(self.plugins_path, plugin)
        self.write_manifest()

    def set_connector(self, name: str, config: dict[str, Any]) -> None:
        data = _read_json_dict(self.connectors_path)
        data[name] = config
        self.connectors_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.write_manifest()

    def remove_connector(self, name: str) -> None:
        data = _read_json_dict(self.connectors_path)
        data.pop(name, None)
        self.connectors_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.write_manifest()

    def list_connectors(self) -> dict[str, Any]:
        return _read_json_dict(self.connectors_path)

    def update_github(self, **kwargs: Any) -> None:
        data = _read_json_dict(self.github_path)
        data.update(kwargs)
        self.github_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.write_manifest()

    # --- memories ---
    def list_memories(self) -> list[dict[str, str]]:
        self.ensure()
        index = _read_json_dict(self.memories_index)
        return list(index.get("items") or [])

    def get_memory(self, name: str) -> str:
        path = self.memories_dir / f"{name}.md"
        if not path.is_file():
            raise FileNotFoundError(f"memory not found: {name}")
        return path.read_text(encoding="utf-8")

    def set_memory(self, name: str, body: str) -> Path:
        self.ensure()
        safe = _safe_name(name)
        path = self.memories_dir / f"{safe}.md"
        path.write_text(body, encoding="utf-8")
        index = _read_json_dict(self.memories_index)
        items = [i for i in (index.get("items") or []) if i.get("name") != safe]
        items.append({"name": safe, "path": str(path.name)})
        index["items"] = items
        self.memories_index.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        return path

    def remove_memory(self, name: str) -> None:
        safe = _safe_name(name)
        path = self.memories_dir / f"{safe}.md"
        if path.is_file():
            path.unlink()
        index = _read_json_dict(self.memories_index)
        index["items"] = [i for i in (index.get("items") or []) if i.get("name") != safe]
        self.memories_index.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    def memory_prompt_append(self) -> str:
        chunks: list[str] = []
        for item in self.list_memories():
            name = str(item.get("name") or "")
            if not name:
                continue
            try:
                chunks.append(f"### Memory: {name}\n{self.get_memory(name)}")
            except FileNotFoundError:
                continue
        if not chunks:
            return ""
        return "\n\n## Claudeloop run memories\n\n" + "\n\n".join(chunks)

    # --- artifacts ---
    def list_artifacts(self) -> list[str]:
        self.ensure()
        return sorted(p.name for p in self.artifacts_dir.iterdir() if p.is_file())

    def get_artifact(self, name: str) -> Path:
        path = self.artifacts_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"artifact not found: {name}")
        return path

    def put_artifact(self, name: str, source: Path) -> Path:
        self.ensure()
        dest = self.artifacts_dir / _safe_name(name)
        shutil.copy2(source.expanduser().resolve(), dest)
        return dest

    def remove_artifact(self, name: str) -> None:
        path = self.artifacts_dir / name
        if path.is_file():
            path.unlink()
        else:
            raise FileNotFoundError(f"artifact not found: {name}")

    def start_research(self, query: str) -> Path:
        self.ensure()
        from datetime import datetime, timezone

        research_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.research_dir / f"{research_id}.jsonl"
        record = {
            "id": research_id,
            "query": query,
            "status": "started",
            "at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        self.set_flag(deep_research=True)
        return path

    def research_status(self) -> list[dict[str, Any]]:
        self.ensure()
        rows: list[dict[str, Any]] = []
        for path in sorted(self.research_dir.glob("*.jsonl")):
            first = path.read_text(encoding="utf-8").splitlines()[:1]
            if first:
                rows.append(json.loads(first[0]))
        return rows


def _safe_name(name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_." else "_" for c in name.strip())
    if not cleaned:
        raise ValueError("name must not be blank")
    return cleaned


def _read_json_list(path: Path) -> list[str]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(x) for x in data]
    return []


def _read_json_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return dict(data)
    return {}


def _append_unique_json_list(path: Path, value: str) -> None:
    items = _read_json_list(path)
    if value not in items:
        items.append(value)
        path.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


def _remove_from_json_list(path: Path, value: str) -> None:
    items = [x for x in _read_json_list(path) if x != value]
    path.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
