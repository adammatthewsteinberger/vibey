# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/chat_meta.py — ChatMeta and ChatMetaStore."""

from __future__ import annotations

import json
from pathlib import Path

from claudeloop.infrastructure.chat_meta import ChatMeta, ChatMetaStore


def test_chatmeta_defaults() -> None:
    meta = ChatMeta(session_id="s1")
    assert meta.session_id == "s1"
    assert meta.alias is None
    assert meta.pinned is False
    assert meta.unread is False
    assert meta.project is None
    assert meta.share_token is None
    assert meta.updated_at  # non-empty


def test_chatmeta_to_dict() -> None:
    meta = ChatMeta(session_id="s1", alias="my-chat", pinned=True)
    d = meta.to_dict()
    assert d["session_id"] == "s1"
    assert d["alias"] == "my-chat"
    assert d["pinned"] is True


def test_chatmeta_from_dict_full() -> None:
    data = {
        "session_id": "abc",
        "alias": "test",
        "pinned": True,
        "unread": True,
        "project": "proj",
        "share_token": "tok",
        "updated_at": "2024-01-01T00:00:00+00:00",
    }
    meta = ChatMeta.from_dict(data)
    assert meta.session_id == "abc"
    assert meta.alias == "test"
    assert meta.pinned is True
    assert meta.unread is True
    assert meta.project == "proj"
    assert meta.share_token == "tok"
    assert meta.updated_at == "2024-01-01T00:00:00+00:00"


def test_chatmeta_from_dict_minimal() -> None:
    meta = ChatMeta.from_dict({"session_id": 42})
    assert meta.session_id == "42"
    assert meta.pinned is False
    assert meta.unread is False
    assert meta.updated_at  # auto-generated


def test_store_creates_root(tmp_path: Path) -> None:
    root = tmp_path / "chats"
    ChatMetaStore(root)
    assert root.is_dir()


def test_store_get_missing_returns_default(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    meta = store.get("nonexistent")
    assert meta.session_id == "nonexistent"
    assert meta.alias is None


def test_store_save_and_get(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    meta = ChatMeta(session_id="s1", alias="hello")
    store.save(meta)
    loaded = store.get("s1")
    assert loaded.session_id == "s1"
    assert loaded.alias == "hello"


def test_store_list_all(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    store.save(ChatMeta(session_id="a"))
    store.save(ChatMeta(session_id="b"))
    all_meta = store.list_all()
    ids = [m.session_id for m in all_meta]
    assert "a" in ids
    assert "b" in ids


def test_store_delete_existing(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    store.save(ChatMeta(session_id="s1"))
    assert store.delete("s1") is True
    loaded = store.get("s1")
    assert loaded.alias is None  # default, not saved


def test_store_delete_missing(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    assert store.delete("nope") is False


def test_store_rename(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    store.save(ChatMeta(session_id="s1"))
    result = store.rename("s1", "new-name")
    assert result.alias == "new-name"
    assert store.get("s1").alias == "new-name"


def test_store_set_pinned(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    result = store.set_pinned("s1", True)
    assert result.pinned is True
    assert store.get("s1").pinned is True
    store.set_pinned("s1", False)
    assert store.get("s1").pinned is False


def test_store_set_unread(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    result = store.set_unread("s1", True)
    assert result.unread is True
    assert store.get("s1").unread is True


def test_store_set_project(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    result = store.set_project("s1", "my-project")
    assert result.project == "my-project"
    assert store.get("s1").project == "my-project"


def test_store_share(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    bundle_dir = tmp_path / "bundles"
    result = store.share("s1", bundle_dir=bundle_dir)
    assert "share_token" in result
    assert "bundle_path" in result
    assert bundle_dir.is_dir()
    bundle_path = Path(result["bundle_path"])
    assert bundle_path.is_file()
    bundle_data = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle_data["session_id"] == "s1"
    assert bundle_data["share_token"] == result["share_token"]


def test_store_share_reuses_existing_token(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    bundle_dir = tmp_path / "bundles"
    r1 = store.share("s1", bundle_dir=bundle_dir)
    r2 = store.share("s1", bundle_dir=bundle_dir)
    assert r1["share_token"] == r2["share_token"]


def test_store_path_sanitization(tmp_path: Path) -> None:
    store = ChatMetaStore(tmp_path / "chats")
    store.save(ChatMeta(session_id="a/b..c"))
    files = list((tmp_path / "chats").glob("*.json"))
    assert len(files) == 1
    assert "/" not in files[0].name
    assert ".." not in files[0].stem
