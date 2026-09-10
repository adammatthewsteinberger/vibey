# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import asyncio
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qwenloop import __version__
from qwenloop.cli.app import app
from qwenloop.domain.model import Backend, RunState, RunStatus, ServerInfo
from qwenloop.infrastructure.profiles import PORTABLE

runner = CliRunner()


def test_version() -> None:
    """Asserts the CLI reports the package's own version, not a literal.

    Hardcoding it meant every release broke this test: the bump moves
    pyproject.toml and __init__.py, the literal stays behind, and CI fails on
    `assert "0.1.0" in "qwenloop 0.2.0"` — a failure that says nothing about the
    CLI and everything about the test.
    """
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_union_commands_are_present() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("run", "resume", "doctor", "cloud", "api", "voice", "model", "server"):
        assert command in result.stdout


def test_model_list_does_not_download() -> None:
    listed = runner.invoke(app, ["model", "list"])
    assert listed.exit_code == 0
    assert "Q5_K_M" in listed.stdout


def test_local_equivalent() -> None:
    result = runner.invoke(app, ["cloud"])
    assert result.exit_code == 0
    assert "local qwenloop equivalent" in result.stdout


def test_identity_usage_and_controls(tmp_path: Path) -> None:
    assert runner.invoke(app, ["whoami"]).exit_code == 0
    assert runner.invoke(app, ["usage", "--cwd", str(tmp_path)]).exit_code == 0
    run_id = "abc"
    assert runner.invoke(app, ["stop", run_id, "--cwd", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["wind-down", run_id, "--cwd", str(tmp_path)]).exit_code == 0
    assert runner.invoke(app, ["prompt", run_id, "hello", "--cwd", str(tmp_path)]).exit_code == 0
    inbox = tmp_path / ".qwenloop" / "runs" / run_id / "control" / "inbox"
    assert len(list(inbox.glob("*.json"))) == 3


def test_model_inspection_validation_and_remove(tmp_path: Path) -> None:
    assert runner.invoke(app, ["model", "inspect"]).exit_code == 0
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "qwenloop.cli.app.ModelCache.verify",
            lambda *_args: (_ for _ in ()).throw(FileNotFoundError("missing")),
        )
        assert runner.invoke(app, ["model", "verify"]).exit_code != 0
    assert runner.invoke(app, ["model", "remove", "portable"]).exit_code != 0
    assert runner.invoke(app, ["model", "remove", "portable", "--yes"]).exit_code == 0
    bf16 = runner.invoke(app, ["model", "install", "--profile", "nvidia-bf16"])
    assert bf16.exit_code == 0
    assert "BF16" in bf16.stdout


def test_server_and_tool_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", True, True, 1)

    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return info

        async def start(self, _profile):  # type: ignore[no-untyped-def]
            return info

        async def health(self, _info):  # type: ignore[no-untyped-def]
            return True

        async def stop(self, _info):  # type: ignore[no-untyped-def]
            return None

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    monkeypatch.setattr("qwenloop.cli.app.VllmServer", Server)
    assert runner.invoke(app, ["server", "status"]).exit_code == 0
    assert runner.invoke(app, ["server", "start"]).exit_code == 0
    assert runner.invoke(app, ["server", "stop"]).exit_code == 0
    assert runner.invoke(app, ["tool", "approve", "read_file"]).exit_code == 0
    assert runner.invoke(app, ["tool", "deny", "shell"]).exit_code == 0


def test_doctor_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("shutil.which", lambda _name: None)
    assert runner.invoke(app, ["doctor"]).exit_code == 1
    monkeypatch.setattr("shutil.which", lambda _name: "/bin/tool")
    assert runner.invoke(app, ["doctor"]).exit_code == 0


@pytest.mark.parametrize(
    ("status", "expected"),
    [(RunStatus.COMPLETED, 0), (RunStatus.WINDING_DOWN, 75), (RunStatus.FAILED, 1)],
)
def test_run_statuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: RunStatus, expected: int
) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("do it")

    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", False, True)

        async def health(self, _info):  # type: ignore[no-untyped-def]
            return True

    class FakeRunner:
        def __init__(self, *_args):  # type: ignore[no-untyped-def]
            pass

        async def run(self, **kwargs):  # type: ignore[no-untyped-def]
            return RunState(str(kwargs["run_id"]), status=status)

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    monkeypatch.setattr("qwenloop.cli.app.AutonomousRunner", FakeRunner)
    result = runner.invoke(app, ["run", str(plan), "--cwd", str(tmp_path)])
    assert result.exit_code == expected


def test_run_start_and_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("do it")

    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return None

        async def start(self, _profile):  # type: ignore[no-untyped-def]
            raise OSError("missing")

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    result = runner.invoke(app, ["run", str(plan), "--cwd", str(tmp_path)])
    assert result.exit_code == 1
    assert "unavailable" in result.stderr


def test_run_waits_for_new_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("do it")
    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", True, False, 1)

    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return None

        async def start(self, _profile):  # type: ignore[no-untyped-def]
            return info

    class FakeRunner:
        def __init__(self, *_args):  # type: ignore[no-untyped-def]
            pass

        async def run(self, **_kwargs):  # type: ignore[no-untyped-def]
            return RunState("run", status=RunStatus.COMPLETED)

    async def ready(_server, value, **_kwargs):  # type: ignore[no-untyped-def]
        return value

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    monkeypatch.setattr("qwenloop.cli.app.AutonomousRunner", FakeRunner)
    monkeypatch.setattr("qwenloop.cli.app._wait_until_ready", ready)
    assert runner.invoke(app, ["run", str(plan), "--cwd", str(tmp_path)]).exit_code == 0


def test_server_start_reports_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    class Server:
        async def start(self, _profile):  # type: ignore[no-untyped-def]
            raise OSError("missing runtime")

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    result = runner.invoke(app, ["server", "start", "--backend", "llama.cpp"])
    assert result.exit_code == 1
    assert "unavailable" in result.stderr


def test_server_stop_when_nothing_is_running(monkeypatch: pytest.MonkeyPatch) -> None:
    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return None

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    monkeypatch.setattr("qwenloop.cli.app.VllmServer", Server)
    result = runner.invoke(app, ["server", "stop"])
    assert result.exit_code == 0
    assert "not running" in result.stdout


def test_wait_until_ready_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    import qwenloop.cli.app as module

    info = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", True, False, None)

    class Healthy:
        async def health(self, _info):  # type: ignore[no-untyped-def]
            return True

    assert asyncio.run(module._wait_until_ready(Healthy(), info, timeout_seconds=1)) is info

    class Unhealthy:
        async def health(self, _info):  # type: ignore[no-untyped-def]
            return False

    with pytest.raises(TimeoutError):
        asyncio.run(module._wait_until_ready(Unhealthy(), info, timeout_seconds=0))

    class EventuallyHealthy:
        def __init__(self) -> None:
            self.calls = 0

        async def health(self, _info):  # type: ignore[no-untyped-def]
            self.calls += 1
            return self.calls == 2

    assert (
        asyncio.run(module._wait_until_ready(EventuallyHealthy(), info, timeout_seconds=1)) is info
    )

    dead = ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", True, False, 999)

    def missing(_pid, _signal):  # type: ignore[no-untyped-def]
        raise ProcessLookupError

    monkeypatch.setattr(module.os, "kill", missing)
    with pytest.raises(RuntimeError, match="exited"):
        asyncio.run(module._wait_until_ready(Unhealthy(), dead, timeout_seconds=1))


def test_portable_install_is_explicit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "model.gguf"
    monkeypatch.setattr("qwenloop.cli.app.ModelCache.install", lambda *_args: target)
    result = runner.invoke(app, ["model", "install", "--profile", "portable"])
    assert result.exit_code == 0
    assert str(target) in result.stdout


def test_portable_install_reports_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args):  # type: ignore[no-untyped-def]
        raise ValueError("bad artifact")

    monkeypatch.setattr("qwenloop.cli.app.ModelCache.install", fail)
    result = runner.invoke(app, ["model", "install", "--profile", "portable"])
    assert result.exit_code != 0


def test_remove_existing_profile_is_recoverable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "models" / "portable"
    target.mkdir(parents=True)
    monkeypatch.setattr("qwenloop.cli.app.user_cache_path", lambda _name: tmp_path)
    result = runner.invoke(app, ["model", "remove", "portable", "--yes"])
    assert result.exit_code != 0
    assert "Trash" in result.output


def test_entry_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    import qwenloop.cli.app as module

    called: list[bool] = []
    monkeypatch.setattr(module, "app", lambda: called.append(True))
    assert module._nvidia_vram() == 0
    module.main()
    assert called == [True]


def test_nvidia_vram_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    import qwenloop.cli.app as module

    class Result:
        stdout = "40960\n2048\n"

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.shutil, "which", lambda _name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: Result())
    assert module._nvidia_vram() == 40960 * 1024 * 1024


def test_nvidia_vram_probe_without_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    import qwenloop.cli.app as module

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)
    assert module._nvidia_vram() == 0


@pytest.mark.parametrize("failure", [OSError("missing"), ValueError("bad")])
def test_nvidia_vram_probe_failure(monkeypatch: pytest.MonkeyPatch, failure: Exception) -> None:
    import qwenloop.cli.app as module

    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.shutil, "which", lambda _name: "/usr/bin/nvidia-smi")

    def fail(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise failure

    monkeypatch.setattr(module.subprocess, "run", fail)
    assert module._nvidia_vram() == 0


def test_run_rejects_storm_with_plan(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("do it")
    result = runner.invoke(app, ["run", str(plan), "--storm"])
    assert result.exit_code != 0
    assert "not both" in result.output


def test_run_requires_plan_when_not_storm() -> None:
    result = runner.invoke(app, ["run"])
    assert result.exit_code != 0
    assert "PLAN is required" in result.output


def test_discover_storm_repos_filters_uncloned_and_handles_gh_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import qwenloop.cli.app as module

    (tmp_path / "a" / ".git").mkdir(parents=True)
    (tmp_path / "b").mkdir()  # not cloned: no .git
    monkeypatch.setattr(module, "list_repo_names", lambda _owner: ["a", "b", "c"])
    assert module._discover_storm_repos("owner", tmp_path) == ["a"]
    monkeypatch.setattr(module, "list_repo_names", lambda _owner: None)
    assert module._discover_storm_repos("owner", tmp_path) == []


def test_storm_sweep_reports_per_repo_status_and_tally(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "a" / ".git").mkdir(parents=True)
    (tmp_path / "b" / ".git").mkdir(parents=True)

    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return ServerInfo(Backend.LLAMA_CPP, PORTABLE.name, "x", False, True)

        async def health(self, _info):  # type: ignore[no-untyped-def]
            return True

    class FakeRunner:
        def __init__(self, *_args):  # type: ignore[no-untyped-def]
            pass

        async def run(self, **kwargs):  # type: ignore[no-untyped-def]
            status = RunStatus.COMPLETED if kwargs["cwd"].name == "a" else RunStatus.FAILED
            return RunState(str(kwargs["run_id"]), status=status, turns=3)

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    monkeypatch.setattr("qwenloop.cli.app.AutonomousRunner", FakeRunner)
    monkeypatch.setattr("qwenloop.cli.app.list_repo_names", lambda _owner: ["a", "b"])
    monkeypatch.setattr("qwenloop.cli.app.list_open_issues", lambda _owner, _repo: None)
    monkeypatch.setattr("qwenloop.cli.app.list_open_pull_requests", lambda _owner, _repo: None)

    result = runner.invoke(
        app, ["run", "--storm", "--owner", "acme", "--repos-root", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert "a\tcompleted\t3" in result.stdout
    assert "b\tfailed\t3" in result.stdout
    assert "qwenstorm complete: 1/2 repos completed" in result.stdout


def test_storm_skips_repo_not_cloned_locally(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("qwenloop.cli.app.list_repo_names", lambda _owner: [])
    result = runner.invoke(
        app, ["run", "--storm", "--repos-root", str(tmp_path), "--repo", "missing"]
    )
    assert result.exit_code == 0
    assert "skip missing: not cloned" in result.stdout
    assert "qwenstorm complete: 0/0 repos completed" in result.stdout


def test_storm_continues_past_unavailable_repo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "a" / ".git").mkdir(parents=True)
    (tmp_path / "b" / ".git").mkdir(parents=True)

    class Server:
        def inspect(self, _profile):  # type: ignore[no-untyped-def]
            return None

        async def start(self, _profile):  # type: ignore[no-untyped-def]
            raise OSError("no runtime")

    monkeypatch.setattr("qwenloop.cli.app.LlamaCppServer", Server)
    monkeypatch.setattr("qwenloop.cli.app.list_open_issues", lambda _owner, _repo: None)
    monkeypatch.setattr("qwenloop.cli.app.list_open_pull_requests", lambda _owner, _repo: None)

    result = runner.invoke(
        app,
        ["run", "--storm", "--repos-root", str(tmp_path), "--repo", "a", "--repo", "b"],
    )
    assert result.exit_code == 0
    assert "a\tunavailable\tno runtime" in result.stdout
    assert "b\tunavailable\tno runtime" in result.stdout
    assert "qwenstorm complete: 0/2 repos completed" in result.stdout
