# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/resources/store.py — RunResourceStore."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claudeloop.infrastructure.resources.store import (
    ResourceSnapshot,
    RunResourceStore,
    _read_json_dict,
    _read_json_list,
    _safe_name,
)


class TestResourceSnapshot:
    def test_defaults(self) -> None:
        snap = ResourceSnapshot()
        assert snap.attachments == []
        assert snap.connectors == {}
        assert snap.web_search is False
        assert snap.permission_mode == "bypass"

    def test_to_dict(self) -> None:
        snap = ResourceSnapshot(skills=["a"], web_search=True)
        d = snap.to_dict()
        assert d["skills"] == ["a"]
        assert d["web_search"] is True

    def test_from_dict_minimal(self) -> None:
        snap = ResourceSnapshot.from_dict({})
        assert snap.attachments == []
        assert snap.permission_mode == "bypass"

    def test_from_dict_full(self) -> None:
        snap = ResourceSnapshot.from_dict(
            {
                "attachments": ["f.txt"],
                "folders": ["/tmp"],
                "skills": ["s1"],
                "plugins": ["p1"],
                "connectors": {"c": {"url": "x"}},
                "github": {"owner": "o"},
                "web_search": True,
                "deep_research": True,
                "permission_mode": "manual",
                "cwd": "/home",
            }
        )
        assert snap.attachments == ["f.txt"]
        assert snap.web_search is True
        assert snap.permission_mode == "manual"

    def test_roundtrip(self) -> None:
        original = ResourceSnapshot(
            skills=["a", "b"],
            plugins=["p"],
            web_search=True,
        )
        restored = ResourceSnapshot.from_dict(original.to_dict())
        assert restored.skills == original.skills
        assert restored.web_search == original.web_search


class TestSafeName:
    def test_alphanumeric(self) -> None:
        assert _safe_name("hello") == "hello"

    def test_special_chars_replaced(self) -> None:
        assert _safe_name("a/b c") == "a_b_c"

    def test_blank_raises(self) -> None:
        with pytest.raises(ValueError, match="blank"):
            _safe_name("   ")

    def test_preserves_dashes_underscores_dots(self) -> None:
        assert _safe_name("my-note_v1.0") == "my-note_v1.0"


class TestRunResourceStore:
    def test_ensure_creates_directories(self, tmp_path: Path) -> None:
        root = tmp_path / "resources"
        store = RunResourceStore(root)
        (root.parent / "artifacts").mkdir(parents=True, exist_ok=True)
        (root.parent / "memories").mkdir(parents=True, exist_ok=True)
        store.ensure()
        assert root.is_dir()
        assert store.attachments_dir.is_dir()
        assert store.research_dir.is_dir()

    def test_snapshot_empty(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        snap = store.snapshot()
        assert snap.attachments == []
        assert snap.connectors == {}

    def test_attach_file(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        src = tmp_path / "note.txt"
        src.write_text("hello", encoding="utf-8")
        dest = store.attach(src)
        assert dest.is_file()
        assert dest.read_text(encoding="utf-8") == "hello"

    def test_attach_nonexistent_raises(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        with pytest.raises(FileNotFoundError):
            store.attach(tmp_path / "nonexistent")

    def test_unattach(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        src = tmp_path / "note.txt"
        src.write_text("hi", encoding="utf-8")
        store.attach(src)
        store.unattach("note.txt")
        assert not (store.attachments_dir / "note.txt").exists()

    def test_unattach_missing_raises(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        with pytest.raises(FileNotFoundError):
            store.unattach("nope")

    def test_add_and_remove_folder(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.add_folder("/tmp/test")
        snap = store.snapshot()
        assert any("/tmp/test" in f for f in snap.folders)
        store.remove_folder("/tmp/test")

    def test_add_and_remove_skill(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.add_skill("skill-a")
        assert "skill-a" in json.loads(store.skills_path.read_text(encoding="utf-8"))
        store.remove_skill("skill-a")
        assert "skill-a" not in json.loads(store.skills_path.read_text(encoding="utf-8"))

    def test_add_and_remove_plugin(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.add_plugin("p1")
        store.remove_plugin("p1")

    def test_set_and_remove_connector(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.set_connector("my-mcp", {"url": "http://localhost"})
        conns = store.list_connectors()
        assert "my-mcp" in conns
        store.remove_connector("my-mcp")
        assert "my-mcp" not in store.list_connectors()

    def test_memories_crud(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.set_memory("prefs", "be concise")
        assert store.get_memory("prefs") == "be concise"
        memories = store.list_memories()
        assert any(m.get("name") == "prefs" for m in memories)
        store.remove_memory("prefs")
        with pytest.raises(FileNotFoundError):
            store.get_memory("prefs")

    def test_memory_prompt_append(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        assert store.memory_prompt_append() == ""
        store.set_memory("note", "remember this")
        append = store.memory_prompt_append()
        assert "note" in append
        assert "remember this" in append

    def test_artifacts_crud(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        src = tmp_path / "data.json"
        src.write_text('{"key": "val"}', encoding="utf-8")
        store.put_artifact("data.json", src)
        assert "data.json" in store.list_artifacts()
        path = store.get_artifact("data.json")
        assert path.is_file()
        store.remove_artifact("data.json")
        assert "data.json" not in store.list_artifacts()

    def test_get_artifact_missing(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        with pytest.raises(FileNotFoundError):
            store.get_artifact("nope")

    def test_remove_artifact_missing(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        with pytest.raises(FileNotFoundError):
            store.remove_artifact("nope")

    def test_set_flag(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.set_flag(web_search=True)
        snap = store.snapshot()
        assert snap.web_search is True

    def test_update_github(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.update_github(owner="o", repo="r")
        snap = store.snapshot()
        assert snap.github.get("owner") == "o"

    def test_research_start_and_status(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.start_research("how does X work?")
        rows = store.research_status()
        assert len(rows) == 1
        assert rows[0]["query"] == "how does X work?"

    def test_write_manifest(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.write_manifest()
        assert store.manifest_path.is_file()
        content = store.manifest_path.read_text(encoding="utf-8")
        assert "permission_mode" in content

    def test_add_duplicate_skill_idempotent(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.add_skill("s1")
        store.add_skill("s1")
        skills = json.loads(store.skills_path.read_text(encoding="utf-8"))
        assert skills.count("s1") == 1

    def test_attach_directory_overwrites_existing(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()

        # Create a directory to attach
        source_dir = tmp_path / "source_dir"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1", encoding="utf-8")
        store.attach(source_dir)

        # Attach a new directory with the same name (should overwrite)
        source_dir2 = tmp_path / "source_dir"
        if source_dir2.exists():
            import shutil

            shutil.rmtree(source_dir2)
        source_dir2.mkdir()
        (source_dir2 / "file2.txt").write_text("content2", encoding="utf-8")
        result = store.attach(source_dir2)

        # Should contain file2.txt, not file1.txt
        assert (result / "file2.txt").exists()
        assert not (result / "file1.txt").exists()

    def test_memory_prompt_append_skips_blank_names(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.set_memory("real", "content")
        # Inject a blank-name entry directly -- list_memories() would return
        # it as-is, and memory_prompt_append() must skip it via `continue`
        # rather than rendering an empty "### Memory: " header.
        index = json.loads(store.memories_index.read_text(encoding="utf-8"))
        index["items"].insert(0, {"name": "", "path": ""})
        store.memories_index.write_text(json.dumps(index), encoding="utf-8")

        append = store.memory_prompt_append()
        assert "### Memory: \n" not in append
        assert "real" in append

    def test_memory_prompt_append_skips_missing_memory_file(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.set_memory("real", "content")
        # Reference a memory name in the index whose .md file was never
        # written (or was deleted out from under the index) -- get_memory()
        # raises FileNotFoundError, which memory_prompt_append() must
        # swallow and skip rather than propagate.
        index = json.loads(store.memories_index.read_text(encoding="utf-8"))
        index["items"].append({"name": "ghost", "path": "ghost.md"})
        store.memories_index.write_text(json.dumps(index), encoding="utf-8")

        append = store.memory_prompt_append()
        assert "ghost" not in append
        assert "real" in append

    def test_unattach_directory(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()

        # Attach a directory
        source_dir = tmp_path / "my_dir"
        source_dir.mkdir()
        (source_dir / "nested.txt").write_text("data", encoding="utf-8")
        store.attach(source_dir)

        # Unattach the directory
        store.unattach("my_dir")
        assert not (store.attachments_dir / "my_dir").exists()

    def test_add_duplicate_folder_is_idempotent(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.add_folder("/tmp/dup")
        store.add_folder("/tmp/dup")
        snap = store.snapshot()
        count = sum(1 for f in snap.folders if f.endswith("/dup"))
        assert count == 1

    def test_remove_memory_with_missing_file(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        store.set_memory("ephemeral", "content")
        mem_file = store.memories_dir / "ephemeral.md"
        mem_file.unlink()
        store.remove_memory("ephemeral")
        assert store.list_memories() == []

    def test_research_status_with_empty_jsonl(self, tmp_path: Path) -> None:
        root = tmp_path / "run" / "resources"
        (tmp_path / "run" / "artifacts").mkdir(parents=True)
        (tmp_path / "run" / "memories").mkdir(parents=True)
        store = RunResourceStore(root)
        store.ensure()
        (store.research_dir / "empty.jsonl").write_text("", encoding="utf-8")
        rows = store.research_status()
        assert rows == []


class TestReadJsonHelpers:
    def test_read_json_list_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert _read_json_list(tmp_path / "nope.json") == []

    def test_read_json_list_non_list_json_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "weird.json"
        path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
        assert _read_json_list(path) == []

    def test_read_json_dict_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert _read_json_dict(tmp_path / "nope.json") == {}

    def test_read_json_dict_non_dict_json_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "weird.json"
        path.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
        assert _read_json_dict(path) == {}
