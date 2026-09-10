# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Run-scoped resource store under `.agyloop/runs/<id>/resources/`."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _read_json_list(path: Path) -> list[str]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@dataclass
class ResourceSnapshot:
    attachments: list[str] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)
    permission_mode: str = "autonomous"
    cwd: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachments": list(self.attachments),
            "folders": list(self.folders),
            "permission_mode": self.permission_mode,
            "cwd": self.cwd,
        }


class RunResourceStore:
    def __init__(self, resources_root: Path) -> None:
        self.root = resources_root
        self.attachments_dir = resources_root / "attachments"
        self.folders_path = resources_root / "folders.json"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(exist_ok=True)
        if not self.folders_path.is_file():
            _write_json(self.folders_path, [])

    def snapshot(self) -> ResourceSnapshot:
        self.ensure()
        flags = {}
        flags_path = self.root / "flags.json"
        if flags_path.is_file():
            loaded = json.loads(flags_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                flags = loaded
        return ResourceSnapshot(
            attachments=sorted(path.name for path in self.attachments_dir.iterdir()),
            folders=_read_json_list(self.folders_path),
            permission_mode=str(flags.get("permission_mode") or "autonomous"),
            cwd=flags.get("cwd") if isinstance(flags.get("cwd"), str) else None,
        )

    def set_flag(self, **kwargs: Any) -> None:
        self.ensure()
        path = self.root / "flags.json"
        flags: dict[str, Any] = {}
        if path.is_file():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                flags = loaded
        flags.update({key: value for key, value in kwargs.items() if value is not None})
        _write_json(path, flags)

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

    def add_folder(self, value: str) -> None:
        self.ensure()
        folders = _read_json_list(self.folders_path)
        resolved = str(Path(value).expanduser().resolve())
        if resolved not in folders:
            folders.append(resolved)
        _write_json(self.folders_path, folders)

    def remove_folder(self, value: str) -> None:
        self.ensure()
        folders = _read_json_list(self.folders_path)
        resolved = str(Path(value).expanduser().resolve())
        folders = [item for item in folders if item not in {value, resolved}]
        _write_json(self.folders_path, folders)


class ResourcePortAdapter:
    def __init__(self, store: RunResourceStore) -> None:
        self._store = store
        self._store.ensure()

    def apply_mutate(
        self, *, action: str, kind: str, value: str, name: str | None = None
    ) -> dict[str, Any]:
        kind_l = kind.lower()
        if kind_l == "attachment":
            if action == "add":
                dest = self._store.attach(Path(value))
                return {"path": str(dest)}
            if action == "rm":
                self._store.unattach(name or Path(value).name)
                return {"removed": name or Path(value).name}
        if kind_l in {"folder", "add-dir", "add_dir"}:
            if action == "add":
                self._store.add_folder(value)
                return {"folder": value}
            if action == "rm":
                self._store.remove_folder(value)
                return {"removed": value}
        raise ValueError(f"unsupported resource mutate {action}/{kind}")

    def gateway_payload(self) -> dict[str, Any]:
        snap = self._store.snapshot()
        return {"add_dirs": list(snap.folders)}

    def set_permission_mode(self, mode: str) -> None:
        self._store.set_flag(permission_mode=mode)

    def set_cwd(self, path: str) -> None:
        self._store.set_flag(cwd=str(Path(path).expanduser().resolve()))
