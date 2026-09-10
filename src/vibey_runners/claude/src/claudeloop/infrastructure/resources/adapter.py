# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adapter: RunResourceStore → application RunResources port."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claudeloop.infrastructure.github_import import (
    import_github_issue,
    materialize_issue_attachment,
    parse_repo_ref,
)
from claudeloop.infrastructure.resources.store import RunResourceStore


class ResourcePortAdapter:
    def __init__(self, store: RunResourceStore) -> None:
        self._store = store
        self._store.ensure()
        self._dirty = True

    def apply_mutate(
        self, *, action: str, kind: str, value: str, name: str | None = None
    ) -> dict[str, Any]:
        kind_l = kind.lower()
        if kind_l == "attachment":
            if action == "add":
                dest = self._store.attach(Path(value))
                self._dirty = True
                return {"path": str(dest)}
            if action == "rm":
                self._store.unattach(name or Path(value).name)
                self._dirty = True
                return {"removed": name or Path(value).name}
        if kind_l == "folder":
            if action == "add":
                self._store.add_folder(value)
                self._dirty = True
                return {"folder": value}
            if action == "rm":
                self._store.remove_folder(value)
                self._dirty = True
                return {"removed": value}
        if kind_l == "skill":
            if action == "add":
                self._store.add_skill(value)
                self._dirty = True
                return {"skill": value}
            if action == "rm":
                self._store.remove_skill(value)
                self._dirty = True
                return {"removed": value}
        if kind_l == "plugin":
            if action == "add":
                self._store.add_plugin(value)
                self._dirty = True
                return {"plugin": value}
            if action == "rm":
                self._store.remove_plugin(value)
                self._dirty = True
                return {"removed": value}
        if kind_l in {"connector", "mcp"}:
            if action in {"add", "set"}:
                config = json.loads(value) if value.strip().startswith("{") else {"url": value}
                self._store.set_connector(name or "default", config)
                self._dirty = True
                return {"connector": name or "default"}
            if action == "rm":
                self._store.remove_connector(name or value)
                self._dirty = True
                return {"removed": name or value}
        if kind_l == "github":
            if action in {"add", "set"}:
                owner, repo, ref = parse_repo_ref(value)
                self._store.update_github(owner=owner, repo=repo, ref=ref, source=value)
                self._dirty = True
                return {"owner": owner, "repo": repo, "ref": ref}
            if action == "rm":
                self._store.update_github(cleared=True)
                self._dirty = True
                return {"cleared": True}
        if kind_l in {"github-issue", "issue"}:
            issue = import_github_issue(value)
            path = materialize_issue_attachment(issue, self._store.attachments_dir)
            self._store.update_github(
                last_issue={
                    "owner": issue.owner,
                    "repo": issue.repo,
                    "number": issue.number,
                    "url": issue.url,
                }
            )
            self._dirty = True
            return {
                "attachment": str(path),
                "prompt_fragment": issue.as_prompt_fragment(),
            }
        if kind_l == "memory":
            if action in {"add", "set"}:
                path = self._store.set_memory(name or "note", value)
                self._dirty = True
                return {"path": str(path)}
            if action == "rm":
                self._store.remove_memory(name or value)
                self._dirty = True
                return {"removed": name or value}
        if kind_l == "web-search":
            self._store.set_flag(web_search=action != "rm")
            self._dirty = True
            return {"web_search": action != "rm"}
        if kind_l == "research":
            if action == "add":
                path = self._store.start_research(value)
                self._dirty = True
                return {"research_path": str(path)}
            return {"status": self._store.research_status()}
        raise ValueError(f"unsupported resource mutate {action}/{kind}")

    def gateway_payload(self) -> dict[str, Any]:
        snap = self._store.snapshot()
        allowed: list[str] = []
        if snap.web_search:
            # Enable web search when the SDK/tool surface exposes it.
            allowed.append("WebSearch")

        # Combine CLI-provided system prompt append with memory-derived content
        chunks: list[str] = []
        if snap.cli_system_prompt_append.strip():
            chunks.append(snap.cli_system_prompt_append.strip())
        memory_append = self._store.memory_prompt_append()
        if memory_append.strip():
            chunks.append(memory_append.strip())
        system_prompt_append = "\n\n".join(chunks)

        payload: dict[str, Any] = {
            "add_dirs": list(snap.folders),
            "skills": list(snap.skills) or None,
            "plugins": list(snap.plugins),
            "mcp_servers": dict(snap.connectors) or None,
            "system_prompt_append": system_prompt_append,
            "allowed_tools": allowed or None,
        }
        self._dirty = False
        return payload

    def set_permission_mode(self, mode: str) -> None:
        self._store.set_flag(permission_mode=mode)

    def set_cwd(self, path: str) -> None:
        self._store.set_flag(cwd=str(Path(path).expanduser().resolve()))

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def store(self) -> RunResourceStore:
        return self._store
