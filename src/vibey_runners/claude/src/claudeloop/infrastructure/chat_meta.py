# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Native chat/session metadata under `.claudeloop/chats/`."""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ChatMeta:
    session_id: str
    alias: str | None = None
    pinned: bool = False
    unread: bool = False
    project: str | None = None
    share_token: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMeta:
        return cls(
            session_id=str(data["session_id"]),
            alias=data.get("alias"),
            pinned=bool(data.get("pinned", False)),
            unread=bool(data.get("unread", False)),
            project=data.get("project"),
            share_token=data.get("share_token"),
            updated_at=str(data.get("updated_at") or datetime.now(timezone.utc).isoformat()),
        )


class ChatMetaStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id)
        return self.root / f"{safe}.json"

    def get(self, session_id: str) -> ChatMeta:
        path = self._path(session_id)
        if path.is_file():
            return ChatMeta.from_dict(json.loads(path.read_text(encoding="utf-8")))
        return ChatMeta(session_id=session_id)

    def save(self, meta: ChatMeta) -> None:
        meta.updated_at = datetime.now(timezone.utc).isoformat()
        self._path(meta.session_id).write_text(
            json.dumps(meta.to_dict(), indent=2) + "\n", encoding="utf-8"
        )

    def list_all(self) -> list[ChatMeta]:
        rows: list[ChatMeta] = []
        for path in sorted(self.root.glob("*.json")):
            rows.append(ChatMeta.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        return rows

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if path.is_file():
            path.unlink()
            return True
        return False

    def rename(self, session_id: str, alias: str) -> ChatMeta:
        meta = self.get(session_id)
        meta.alias = alias
        self.save(meta)
        return meta

    def set_pinned(self, session_id: str, pinned: bool) -> ChatMeta:
        meta = self.get(session_id)
        meta.pinned = pinned
        self.save(meta)
        return meta

    def set_unread(self, session_id: str, unread: bool) -> ChatMeta:
        meta = self.get(session_id)
        meta.unread = unread
        self.save(meta)
        return meta

    def set_project(self, session_id: str, project: str) -> ChatMeta:
        meta = self.get(session_id)
        meta.project = project
        self.save(meta)
        return meta

    def share(self, session_id: str, *, bundle_dir: Path) -> dict[str, str]:
        meta = self.get(session_id)
        token = meta.share_token or secrets.token_urlsafe(16)
        meta.share_token = token
        self.save(meta)
        bundle_dir.mkdir(parents=True, exist_ok=True)
        bundle = bundle_dir / f"share-{token}.json"
        payload = {
            "session_id": session_id,
            "alias": meta.alias,
            "share_token": token,
            "note": (
                "Local share bundle only — Claude.ai share APIs are not wired. "
                "Distribute this redacted export path yourself."
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        bundle.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return {"share_token": token, "bundle_path": str(bundle)}
