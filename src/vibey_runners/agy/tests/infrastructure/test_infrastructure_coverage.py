# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from google.antigravity.types import (
    AntigravityConnectionError,
)

from agyloop.infrastructure.agent.catalog import _to_session_ref
from agyloop.infrastructure.agent.cli_argv import (
    AgyCliInvocation,
    _is_allowlisted,
    build_agy_argv,
)
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway
from agyloop.infrastructure.agent.gateway_cli import execute_agy
from agyloop.infrastructure.agent.gemini_rewrite import GeminiRewriteProxy
from agyloop.infrastructure.agent.harness_retarget import (
    HarnessSession,
    _apply_sdk_monkeypatches,
    _kill_process_tree,
    apply_binary_path_monkeypatch,
    copy_harness_siblings,
    overwrite_site_packages_harness,
    prepare_harness,
    smoke_check_harness,
    stock_harness_path,
    write_patched_copy,
)
from agyloop.infrastructure.config import _from_file, load_config
from agyloop.infrastructure.events import JsonlRunEventSink
from agyloop.infrastructure.git_savepoints import GitSavePointStore
from agyloop.infrastructure.rundir import RunDirectory, runs_root_for
from agyloop.infrastructure.snapshot import _load_savepoints
from agyloop.infrastructure.state_bus import FileStateBus
from agyloop.infrastructure.stream_ui import StreamApp, follow_events_plain


def test_catalog_coverage_branches(tmp_path: Path) -> None:
    directory = RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)
    # Test _to_session_ref with started_at=None and empty plan
    with patch.object(directory, "read_meta") as mock_meta:
        meta = MagicMock()
        meta.conversation_id = "c1"
        meta.run_id = "r1"
        meta.started_at = None
        meta.cwd = str(tmp_path)
        mock_meta.return_value = meta
        with patch.object(directory, "read_plan_text", return_value="   \n\n"):
            ref = _to_session_ref(directory)
            assert ref.last_modified is None
            assert ref.first_prompt_preview is None


def test_cli_argv_coverage_branches(tmp_path: Path) -> None:
    # _is_allowlisted with non-matching allowlist path
    other_path = tmp_path / "other"
    other_path.mkdir()
    target_path = tmp_path / "target"
    target_path.mkdir()
    assert not _is_allowlisted(target_path, [str(other_path)])

    # build_agy_argv with bypassed validation to hit line 136 guard
    with (
        patch("agyloop.infrastructure.agent.cli_argv.validate_unsafe_skip_permissions"),
        pytest.raises(Exception, match="refusing to emit --dangerously-skip-permissions"),
    ):
        build_agy_argv(
            prompt="hello",
            cwd=target_path,
            sandbox=True,
            unsafe_skip_permissions=True,
        )


@pytest.mark.asyncio
async def test_gateway_ensure_started_raises() -> None:
    gw = AntigravityAgentGateway(cwd="/tmp")
    with (
        patch.object(
            gw, "_ensure_started", side_effect=AntigravityConnectionError("connection failed")
        ),
        pytest.raises(AntigravityConnectionError),
    ):
        await gw.send_turn("prompt")


def test_gateway_cli_empty_settings(tmp_path: Path) -> None:
    inv = AgyCliInvocation(argv=("python3", "-c", "print('ok')"), settings={})
    res = execute_agy(inv, cwd=tmp_path)
    assert res.returncode == 0
    assert res.stdout.strip() == "ok"


def test_gemini_rewrite_proxy_stop_and_socket_branches() -> None:
    proxy = GeminiRewriteProxy(listen_port=0)
    # Stop when httpd and thread are None
    proxy.stop()
    assert proxy._httpd is None
    assert proxy._thread is None

    # Test non-socket socket instance
    with patch(
        "agyloop.infrastructure.agent.gemini_rewrite.ThreadingHTTPServer"
    ) as mock_server_cls:
        mock_server = MagicMock()
        mock_server.socket = "not-a-socket"
        mock_server.server_address = ("127.0.0.1", 12345)
        mock_server_cls.return_value = mock_server
        p = GeminiRewriteProxy(listen_port=0)
        url = p.start()
        assert "12345" in url
        p.stop()


def test_harness_retarget_coverage_branches(tmp_path: Path) -> None:
    # stock_harness_path error handling
    with patch.dict("sys.modules", {"google.antigravity.types": None}):
        assert stock_harness_path() is None

    # copy_harness_siblings when target exists with same size
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stock_bin = bin_dir / "localharness"
    stock_bin.write_bytes(b"bin-data")
    sibling = bin_dir / "sibling.txt"
    sibling.write_bytes(b"sibling-data")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    target_sibling = dest_dir / "sibling.txt"
    target_sibling.write_bytes(b"sibling-data")

    copied = copy_harness_siblings(stock_bin, dest_dir)
    assert copied == []

    # write_patched_copy when dest already has patched bytes
    dest_bin = dest_dir / "localharness"
    write_patched_copy(stock_bin, dest_bin)
    write_patched_copy(stock_bin, dest_bin)

    # _kill_process_tree when killpg/getpgid are None
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    with patch("os.killpg", None):
        _kill_process_tree(mock_proc)
        mock_proc.kill.assert_called_once()

    # smoke_check_harness when marker stamp does not match
    dest_file = tmp_path / "dummy_exe"
    dest_file.write_bytes(b"dummy")
    marker = dest_file.with_name(dest_file.name + ".verified")
    marker.write_text("wrong-stamp\n", encoding="utf-8")
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.communicate.return_value = (b"", b"")
        proc.returncode = 0
        mock_popen.return_value = proc
        assert smoke_check_harness(dest_file) is None

    # smoke_check_harness when the process exits during the poll window but
    # the follow-up communicate() to collect stderr itself times out (a
    # grandchild still holding the pipe open) -- treated as unrunnable
    # rather than raising.
    dest_file2 = tmp_path / "dummy_exe2"
    dest_file2.write_bytes(b"dummy2")
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock()
        proc.poll.return_value = 0
        proc.pid = 999999999
        proc.communicate.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=1.0)
        mock_popen.return_value = proc
        reason = smoke_check_harness(dest_file2)
        assert reason == "exit_hung:process_exited_but_communicate_timed_out"

    # HarnessSession.close with proxy and previous_harness_path
    session = HarnessSession(
        set_harness_path=True,
        previous_harness_path="/prev/path",
        proxy=MagicMock(),
    )
    session.close()
    assert os.environ.get("ANTIGRAVITY_HARNESS_PATH") == "/prev/path"
    os.environ.pop("ANTIGRAVITY_HARNESS_PATH", None)

    # prepare_harness with copy_patch_failed (binary_contains_withdrawn is True on dest)
    with (
        patch.dict(
            "os.environ", {"AGYLOOP_SKIP_HARNESS_RETARGET": "0", "ANTIGRAVITY_HARNESS_PATH": ""}
        ),
        patch("agyloop.infrastructure.agent.harness_retarget._active", None),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
            return_value=stock_bin,
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.binary_contains_withdrawn",
            side_effect=[True, True, True],
        ),
        patch("agyloop.infrastructure.agent.harness_retarget.write_patched_copy"),
        patch("agyloop.infrastructure.agent.harness_retarget._maybe_start_proxy"),
    ):
        sess = prepare_harness()
        assert "copy_patch_failed" in sess.notes
        sess.close()

    # prepare_harness with NO_SITE_PACKAGES_ENV == "1"
    with (
        patch.dict(
            "os.environ",
            {
                "AGYLOOP_SKIP_HARNESS_RETARGET": "0",
                "ANTIGRAVITY_HARNESS_PATH": "",
                "AGYLOOP_NO_SITE_PACKAGES_PATCH": "1",
            },
        ),
        patch("agyloop.infrastructure.agent.harness_retarget._active", None),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
            return_value=stock_bin,
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.binary_contains_withdrawn",
            side_effect=[True, True, True],
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.write_patched_copy",
            side_effect=OSError("copy fail"),
        ),
        patch("agyloop.infrastructure.agent.harness_retarget._maybe_start_proxy"),
    ):
        sess = prepare_harness()
        assert sess is not None
        sess.close()

    # prepare_harness with site_packages_overwrite and binary_contains_withdrawn still True
    with (
        patch.dict(
            "os.environ",
            {
                "AGYLOOP_SKIP_HARNESS_RETARGET": "0",
                "ANTIGRAVITY_HARNESS_PATH": "",
                "AGYLOOP_NO_SITE_PACKAGES_PATCH": "0",
            },
        ),
        patch("agyloop.infrastructure.agent.harness_retarget._active", None),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
            return_value=stock_bin,
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.binary_contains_withdrawn",
            side_effect=[True, True, True, True],
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.write_patched_copy",
            side_effect=OSError("copy fail"),
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.overwrite_site_packages_harness",
            return_value=Path("/dummy/backup"),
        ),
        patch("agyloop.infrastructure.agent.harness_retarget._maybe_start_proxy"),
    ):
        sess = prepare_harness()
        assert "site_packages_overwrite" in sess.notes
        sess.close()

    # prepare_harness where still_withdrawn is False
    with (
        patch.dict(
            "os.environ",
            {
                "AGYLOOP_SKIP_HARNESS_RETARGET": "0",
                "ANTIGRAVITY_HARNESS_PATH": "",
                "AGYLOOP_NO_SITE_PACKAGES_PATCH": "1",
            },
        ),
        patch("agyloop.infrastructure.agent.harness_retarget._active", None),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.stock_harness_path",
            return_value=stock_bin,
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.binary_contains_withdrawn",
            side_effect=[True, False],
        ),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.write_patched_copy",
            side_effect=OSError("copy fail"),
        ),
    ):
        sess = prepare_harness()
        assert sess is not None
        sess.close()

    # _apply_sdk_monkeypatches when original_models is not callable and restores is empty
    dummy_mod = ModuleType("dummy_conn")
    dummy_mod._get_default_binary_path_external = None  # type: ignore[attr-defined]
    dummy_mod.build_models_proto = "not-callable"  # type: ignore[attr-defined]
    with patch.dict(
        "sys.modules", {"google.antigravity.connections.local.local_connection": dummy_mod}
    ):
        sess = HarnessSession()
        _apply_sdk_monkeypatches(sess, patched_binary=None)
        assert sess.monkeypatch_restore is None

    # apply_binary_path_monkeypatch restore when original is None
    stub_mod = ModuleType("stub_mod")
    restore_fn = apply_binary_path_monkeypatch(stub_mod, patched_binary=tmp_path / "bin")
    assert getattr(stub_mod, "_get_default_binary_path_external", None) is not None
    assert stub_mod._get_default_binary_path_external() == str(tmp_path / "bin")  # type: ignore[attr-defined]
    restore_fn()
    assert not hasattr(stub_mod, "_get_default_binary_path_external")

    # overwrite_site_packages_harness when backup exists
    stock_f = tmp_path / "stock_f"
    stock_f.write_bytes(b"hello")
    backup_f = stock_f.with_name(stock_f.name + ".agyloop-bak")
    backup_f.write_bytes(b"hello")
    with (
        patch.dict("os.environ", {"AGYLOOP_NO_SITE_PACKAGES_PATCH": "0"}),
        patch(
            "agyloop.infrastructure.agent.harness_retarget.patch_harness_bytes",
            return_value=b"patched",
        ),
    ):
        res = overwrite_site_packages_harness(stock_f)
        assert res == backup_f

    # overwrite_site_packages_harness backup verification failure
    stock_f2 = tmp_path / "stock_f2"
    stock_f2.write_bytes(b"data")
    with (
        patch.dict("os.environ", {"AGYLOOP_NO_SITE_PACKAGES_PATCH": "0"}),
        patch.object(Path, "is_file", return_value=False),
        patch.object(Path, "write_bytes"),
        patch.object(Path, "chmod"),
        patch.object(Path, "read_bytes", side_effect=[b"data", b"corrupted"]),
        pytest.raises(OSError, match="backup failed verification"),
    ):
        overwrite_site_packages_harness(stock_f2)


def test_config_coverage_branches(tmp_path: Path) -> None:
    # _from_file with unknown model alias and unknown top-level keys
    cfg_file = tmp_path / "test.toml"
    cfg_file.write_text(
        """
[model]
unknown_alias = "val"
low = "gemini-2.5-flash"

[run]
unknown_run_key = 123

[unknown_section]
foo = "bar"

unknown_root = "baz"
""",
        encoding="utf-8",
    )
    res = _from_file(cfg_file)
    assert res.get("model_low") == "gemini-2.5-flash"
    assert "unknown_root" not in res

    # load_config with cli_overrides containing only None
    cfg = load_config(cwd=tmp_path, cli_overrides={"model": None, "max_turns": None})
    assert cfg is not None


def test_events_coverage_branches(tmp_path: Path) -> None:
    sink = JsonlRunEventSink(tmp_path / "events.jsonl", run_id="r1")
    # bind with all None
    sink.bind()
    # emit with trace_id, turn_id, session_id, payload all None
    sink.emit("test_event", None)

    # bind with specific fields
    sink.bind(session_id="s1", attempt=2, phase="RUNNING", trace_id="t1", turn_id="turn1")
    sink.emit("test_event2", {"key": "val"})

    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2


def test_git_savepoints_list_points_no_index(tmp_path: Path) -> None:
    store = GitSavePointStore(cwd=tmp_path, index_path=tmp_path / "index.jsonl")
    store._index_path.unlink(missing_ok=True)
    # Index path does not exist
    assert store.list_points("r1") == []


def test_snapshot_load_savepoints_empty_file(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty_savepoints.jsonl"
    empty_file.touch()
    assert _load_savepoints(empty_file) == []


def test_state_bus_existing_file(tmp_path: Path) -> None:
    bus_file = tmp_path / "bus.jsonl"
    bus_file.write_text("existing\n", encoding="utf-8")
    status_file = tmp_path / "status.json"
    bus = FileStateBus(status_path=status_file, bus_path=bus_file, run_id="r1")
    bus.publish("test", {"state": 1})
    assert status_file.is_file()


def test_stream_ui_coverage_branches(tmp_path: Path) -> None:
    # follow_events_plain with non-existent file and follow=False
    follow_events_plain(tmp_path / "nonexistent.jsonl", follow=False)

    # follow_events_plain with empty file (empty chunk)
    empty_f = tmp_path / "empty_events.jsonl"
    empty_f.touch()
    follow_events_plain(empty_f, follow=False)

    # follow_events_plain with non-chatter events
    events_f = tmp_path / "events.jsonl"
    events_f.write_text(
        json.dumps({"event_type": "other.event", "payload": {}})
        + "\n"
        + json.dumps({"event_type": None, "payload": {}})
        + "\n",
        encoding="utf-8",
    )
    follow_events_plain(events_f, follow=False)

    # StreamApp with replay=False
    app = StreamApp(events_path=events_f, follow=True, replay=False)
    with patch.object(app, "set_interval"):
        app.on_mount()

    # StreamApp _drain with chatter.delta empty text, chatter.assistant empty body (saw_delta=False), unknown event
    rich_events = tmp_path / "rich_events.jsonl"
    rich_events.write_text(
        json.dumps({"event_type": "chatter.delta", "payload": {"text": ""}})
        + "\n"
        + json.dumps({"event_type": "chatter.prompt", "payload": {"text": "hello"}})
        + "\n"
        + json.dumps({"event_type": "chatter.assistant", "payload": {"text": ""}})
        + "\n"
        + json.dumps({"event_type": "custom.event", "payload": {}})
        + "\n"
        + json.dumps({"event_type": None, "payload": {}})
        + "\n",
        encoding="utf-8",
    )
    app2 = StreamApp(events_path=rich_events, follow=True)
    mock_log = MagicMock()
    with patch.object(app2, "query_one", return_value=mock_log):
        app2._drain(follow=True)
        assert mock_log.write.called
