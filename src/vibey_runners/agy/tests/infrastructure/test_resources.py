# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

import pytest

from agyloop.infrastructure.resources import (
    ResourcePortAdapter,
    ResourceSnapshot,
    RunResourceStore,
    _read_json_list,
    _write_json,
)


def test_json_list_helpers(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    assert _read_json_list(missing) == []

    not_list = tmp_path / "dict.json"
    _write_json(not_list, {"key": "value"})
    assert _read_json_list(not_list) == []

    valid_list = tmp_path / "list.json"
    _write_json(valid_list, ["item1", 123])
    assert _read_json_list(valid_list) == ["item1", "123"]


def test_resource_snapshot_to_dict() -> None:
    snap = ResourceSnapshot(
        attachments=["a.txt"],
        folders=["/tmp/f"],
        permission_mode="scoped",
        cwd="/tmp",
    )
    d = snap.to_dict()
    assert d["attachments"] == ["a.txt"]
    assert d["folders"] == ["/tmp/f"]
    assert d["permission_mode"] == "scoped"
    assert d["cwd"] == "/tmp"


def test_run_resource_store_lifecycle(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    store.ensure()
    assert store.attachments_dir.is_dir()
    assert store.folders_path.is_file()

    # Initial snapshot
    snap = store.snapshot()
    assert snap.attachments == []
    assert snap.folders == []
    assert snap.permission_mode == "autonomous"
    assert snap.cwd is None

    # Set flags
    store.set_flag(permission_mode="safe", cwd=str(tmp_path), other=None)
    snap2 = store.snapshot()
    assert snap2.permission_mode == "safe"
    assert snap2.cwd == str(tmp_path)

    # Attach file
    src_file = tmp_path / "file.txt"
    src_file.write_text("content", encoding="utf-8")
    dest_file = store.attach(src_file)
    assert dest_file.name == "file.txt"
    assert dest_file.is_file()

    # Attach nonexistent file
    with pytest.raises(FileNotFoundError, match="attachment not found"):
        store.attach(tmp_path / "nonexistent.txt")

    # Attach directory and overwrite directory
    src_dir = tmp_path / "src_dir"
    src_dir.mkdir()
    (src_dir / "sub.txt").write_text("sub", encoding="utf-8")
    dest_dir = store.attach(src_dir)
    assert dest_dir.is_dir()
    # Attach again to trigger rmtree and overwrite
    store.attach(src_dir)

    # Unattach file and dir
    store.unattach("file.txt")
    assert not dest_file.exists()
    store.unattach("src_dir")
    assert not dest_dir.exists()

    # Unattach missing
    with pytest.raises(FileNotFoundError, match="attachment not found"):
        store.unattach("missing.txt")

    # Folders: add and remove
    folder1 = tmp_path / "folder1"
    store.add_folder(str(folder1))
    # Add duplicate
    store.add_folder(str(folder1))
    assert str(folder1.resolve()) in store.snapshot().folders

    store.remove_folder(str(folder1))
    assert str(folder1.resolve()) not in store.snapshot().folders


def test_resource_port_adapter(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    adapter = ResourcePortAdapter(store)

    src_file = tmp_path / "data.txt"
    src_file.write_text("data", encoding="utf-8")

    # Attachment add & rm
    res_add = adapter.apply_mutate(action="add", kind="attachment", value=str(src_file))
    assert "data.txt" in res_add["path"]

    res_rm = adapter.apply_mutate(action="rm", kind="attachment", value="", name="data.txt")
    assert res_rm["removed"] == "data.txt"

    # Rm without explicit name
    dest = store.attach(src_file)
    res_rm2 = adapter.apply_mutate(action="rm", kind="attachment", value=str(dest))
    assert res_rm2["removed"] == "data.txt"

    # Folder / add-dir add & rm
    f_path = str(tmp_path / "dir1")
    adapter.apply_mutate(action="add", kind="folder", value=f_path)
    assert adapter.gateway_payload()["add_dirs"] == [str((tmp_path / "dir1").resolve())]

    adapter.apply_mutate(action="rm", kind="add-dir", value=f_path)
    assert adapter.gateway_payload()["add_dirs"] == []

    adapter.apply_mutate(action="add", kind="add_dir", value=f_path)
    adapter.apply_mutate(action="rm", kind="folder", value=f_path)

    # Unsupported mutate
    with pytest.raises(ValueError, match="unsupported resource mutate"):
        adapter.apply_mutate(action="unknown", kind="unknown", value="")
    with pytest.raises(ValueError, match="unsupported resource mutate"):
        adapter.apply_mutate(action="edit", kind="attachment", value="")
    with pytest.raises(ValueError, match="unsupported resource mutate"):
        adapter.apply_mutate(action="edit", kind="folder", value="")

    # set_permission_mode and set_cwd
    adapter.set_permission_mode("yolo")
    adapter.set_cwd(str(tmp_path))
    snap = store.snapshot()
    assert snap.permission_mode == "yolo"
    assert snap.cwd == str(tmp_path.resolve())


def test_flags_json_non_dict(tmp_path: Path) -> None:
    store = RunResourceStore(tmp_path / "resources")
    store.ensure()
    (store.root / "flags.json").write_text('"string json"', encoding="utf-8")
    snap = store.snapshot()
    assert snap.permission_mode == "autonomous"

    store.set_flag(permission_mode="safe")
    assert store.snapshot().permission_mode == "safe"
