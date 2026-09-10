# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from claudeloop.domain.control import (
    PromptNowCommand,
    SetPresetCommand,
    StopCommand,
    WindDownCommand,
    stop_outranks,
)
from claudeloop.domain.stop_summary import StopSummaryInput, render_stop_summary
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.git_savepoints import GitSavePointStore
from claudeloop.infrastructure.lock import FileSessionLock
from claudeloop.infrastructure.rundir import RunDirectory, resolve_run_directory, runs_root_for


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-m", "init")


def test_stop_outranks_prompts() -> None:
    cmds = stop_outranks([PromptNowCommand(text="x"), StopCommand(), PromptNowCommand(text="y")])
    assert cmds == [StopCommand()]


def test_file_run_control_roundtrip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(StopCommand())
    control.enqueue(PromptNowCommand(text="hello"))
    # Stop was enqueued first but stop_outranks collapses when both present
    polled = control.poll()
    assert polled == [StopCommand()]


def test_file_run_control_preset_roundtrip(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(SetPresetCommand(preset="high"))
    polled = control.poll()
    assert polled == [SetPresetCommand(preset="high")]


def test_run_directory_create_and_resolve(tmp_path: Path) -> None:
    cwd = tmp_path / "proj"
    cwd.mkdir()
    directory = RunDirectory.create(runs_root_for(cwd), cwd=cwd)
    assert directory.meta_path.is_file()
    resolved = resolve_run_directory(cwd, directory.read_meta().run_id)
    assert resolved.root == directory.root


def test_session_lock_acquire_release(tmp_path: Path) -> None:
    lock = FileSessionLock(tmp_path / "locks")
    assert lock.acquire("sess-1") is True
    assert lock.acquire("sess-1") is False
    lock.release("sess-1")
    assert lock.acquire("sess-1") is True
    lock.release("sess-1")


def test_git_savepoints_create_list_unwind(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)

    index = tmp_path / "savepoints.jsonl"
    store = GitSavePointStore(cwd=repo, index_path=index)
    run_id = "run1"
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    p1 = store.create(run_id=run_id, label="t1", message="first")
    assert p1 is not None
    (repo / "a.txt").write_text("three\n", encoding="utf-8")
    p2 = store.create(run_id=run_id, label="t2", message="second")
    assert p2 is not None
    points = store.list_points(run_id)
    assert len(points) == 2
    result = store.unwind(run_id=run_id, to="1", backup=True)
    assert result.to.n == 1
    assert result.backup_ref is not None
    assert (repo / "a.txt").read_text(encoding="utf-8") == "two\n"


def test_git_savepoints_unchanged_tree_ref_tags_without_empty_commit(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    store = GitSavePointStore(cwd=repo, index_path=tmp_path / "savepoints.jsonl")
    run_id = "run-wait"
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    commits_before = int(_git(repo, "rev-list", "--count", "HEAD").stdout.strip())

    p1 = store.create(run_id=run_id, label="turn-1", message="after turn 1")
    p2 = store.create(run_id=run_id, label="turn-2", message="after turn 2")
    assert p1 is not None and p2 is not None
    assert p1.sha == head_before
    assert p2.sha == head_before
    assert p1.ref != p2.ref
    assert p2.n == 2
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == head_before
    assert int(_git(repo, "rev-list", "--count", "HEAD").stdout.strip()) == commits_before
    assert _git(repo, "rev-parse", p1.ref).stdout.strip() == head_before
    assert _git(repo, "rev-parse", p2.ref).stdout.strip() == head_before

    (repo / "a.txt").write_text("changed\n", encoding="utf-8")
    p3 = store.create(
        run_id=run_id,
        label="turn-3",
        attempt=3,
        summary="Updated a.txt",
        remaining_work=("more",),
        verdict_name="Continue",
    )
    assert p3 is not None
    assert p3.sha != head_before
    assert int(_git(repo, "rev-list", "--count", "HEAD").stdout.strip()) == commits_before + 1
    msg = _git(repo, "log", "-1", "--format=%B", p3.sha).stdout
    assert msg.startswith("chore(claudeloop): turn 3 —")
    assert "Run: run-wait" in msg
    assert "Attempt: 3" in msg


def test_git_savepoints_excludes_claudeloop_control_plane(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    store = GitSavePointStore(cwd=repo, index_path=tmp_path / "savepoints.jsonl")
    control = repo / ".claudeloop" / "runs" / "x"
    control.mkdir(parents=True)
    (control / "meta.json").write_text("{}\n", encoding="utf-8")
    head_before = _git(repo, "rev-parse", "HEAD").stdout.strip()
    p1 = store.create(run_id="r", label="t1", attempt=1, summary="noise only")
    assert p1 is not None
    assert p1.sha == head_before
    assert int(_git(repo, "rev-list", "--count", "HEAD").stdout.strip()) == 1

    (repo / "real.txt").write_text("hi\n", encoding="utf-8")
    (control / "meta.json").write_text('{"x":1}\n', encoding="utf-8")
    p2 = store.create(run_id="r", label="t2", attempt=2, summary="real change")
    assert p2 is not None
    assert p2.sha != head_before
    names = _git(repo, "show", "--name-only", "--format=", p2.sha).stdout.strip().splitlines()
    assert "real.txt" in names
    assert not any(n.startswith(".claudeloop/") for n in names)


def test_render_stop_summary_includes_sections() -> None:
    md = render_stop_summary(
        StopSummaryInput(
            run_id="r1",
            session_id="s1",
            reason="stopped by operator",
            turns_spent=2,
            dollars_spent=0.5,
            last_summary="did stuff",
            remaining_plan_items=("item a",),
            remaining_work=("more",),
            git_changes="abc commit",
            latest_savepoint="#1",
            events_path="/tmp/events.jsonl",
            resume_hint="resume please",
        )
    )
    assert "stopped by operator" in md
    assert "item a" in md
    assert "resume please" in md


def test_file_run_control_wind_down_command(tmp_path: Path) -> None:
    control = FileRunControl(tmp_path / "inbox")
    control.enqueue(WindDownCommand(reason="test wind down"))
    polled = control.poll()
    assert len(polled) == 1
    assert isinstance(polled[0], WindDownCommand)
    assert polled[0].reason == "test wind down"


def test_file_run_control_skips_corrupt_command_file(tmp_path: Path) -> None:
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    # Write a corrupt JSON file
    (inbox / "corrupt.cmd.json").write_text("{invalid json", encoding="utf-8")
    # Write a valid command
    control = FileRunControl(inbox)
    control.enqueue(StopCommand())

    polled = control.poll()
    # Should get the valid command, corrupt file should be skipped
    assert polled == [StopCommand()]
    # Corrupt file should still exist (not deleted)
    assert (inbox / "corrupt.cmd.json").exists()


def test_command_to_payload_unsupported_type_raises() -> None:
    from claudeloop.infrastructure.control import _command_to_payload

    class UnsupportedCommand:
        pass

    with pytest.raises(TypeError, match="unsupported control command"):
        _command_to_payload(UnsupportedCommand())  # type: ignore[arg-type]


def test_payload_to_command_unknown_type_raises() -> None:
    from claudeloop.infrastructure.control import _payload_to_command

    with pytest.raises(ValueError, match="unknown control command type"):
        _payload_to_command({"type": "unknown_command_type"})
