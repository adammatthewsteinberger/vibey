# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Composition root wiring for adaptive wait, --no-probe, and the loud notifier."""

import inspect
from pathlib import Path

import pytest
from google.antigravity.types import BuiltinTools

from agyloop.bootstrap import build_runner, parse_gateway
from agyloop.infrastructure.agent.gateway import AntigravityAgentGateway
from agyloop.infrastructure.agent.gateway_cli import AgyCliAgentGateway
from agyloop.infrastructure.agent.probe import AntigravityCapacityProbe
from agyloop.infrastructure.agent.probe_cli import AgyCliCapacityProbe
from agyloop.infrastructure.control import FileRunControl
from agyloop.infrastructure.git_savepoints import GitSavePointStore
from agyloop.infrastructure.notify import StderrNotifier
from agyloop.infrastructure.snapshot import RunSnapshotBuilder


def test_build_runner_wires_no_probe_and_stderr_notifier(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, no_probe=True)
    assert context.runner._no_probe is True
    assert context.runner._wait_policy.no_probe is True
    assert isinstance(context.runner._notifier, StderrNotifier)
    assert isinstance(context.runner._control, FileRunControl)
    assert isinstance(context.runner._save_points, GitSavePointStore)
    assert isinstance(context.runner._snapshots, RunSnapshotBuilder)
    assert context.runner._ramp == 0


def test_build_runner_strict_autonomy_disables_ask_question(tmp_path: Path) -> None:
    source = inspect.getsource(build_runner)
    assert "del strict_autonomy" not in source
    context = build_runner(cwd=tmp_path, strict_autonomy=True)
    assert isinstance(context.gateway, AntigravityAgentGateway)
    cfg = context.gateway._config()
    assert BuiltinTools.ASK_QUESTION in (cfg.capabilities.disabled_tools or [])


def test_build_runner_passes_google_api_key_into_sdk_gateway(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    context = build_runner(cwd=tmp_path, no_probe=True)
    assert isinstance(context.gateway, AntigravityAgentGateway)
    assert context.gateway._api_key == "test-google-key"
    assert context.gateway._config().api_key == "test-google-key"


def test_build_runner_cli_gateway_and_ramp(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, gateway="cli", ramp=4, no_probe=True)
    assert isinstance(context.gateway, AgyCliAgentGateway)
    assert context.runner._ramp == 4
    assert parse_gateway("SDK") == "sdk"
    assert parse_gateway("cli") == "cli"


def test_cli_gateway_gets_a_cli_probe_not_the_sdk_harness(tmp_path: Path) -> None:
    """--gateway cli must not boot the Antigravity harness for the preflight probe.

    Regression: bootstrap consulted the gateway kind when building the turn
    gateway and forgot it when building the probe, so `--gateway cli` still
    spawned the local harness and died with
    `RuntimeError: Failed to read length from stdout` before turn one.
    """
    context = build_runner(cwd=tmp_path, gateway="cli")
    assert isinstance(context.gateway, AgyCliAgentGateway)
    assert isinstance(context.runner._probe, AgyCliCapacityProbe)
    assert not isinstance(context.runner._probe, AntigravityCapacityProbe)


def test_cli_gateway_never_constructs_the_antigravity_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _explode(*args: object, **kwargs: object) -> None:
        raise AssertionError("--gateway cli must never construct the SDK Agent")

    monkeypatch.setattr("agyloop.infrastructure.agent.probe.Agent", _explode)
    context = build_runner(cwd=tmp_path, gateway="cli")
    assert isinstance(context.runner._probe, AgyCliCapacityProbe)


def test_sdk_gateway_still_gets_the_sdk_probe(tmp_path: Path) -> None:
    context = build_runner(cwd=tmp_path, gateway="sdk")
    assert isinstance(context.gateway, AntigravityAgentGateway)
    assert isinstance(context.runner._probe, AntigravityCapacityProbe)


@pytest.mark.parametrize("gateway", ["sdk", "cli"])
def test_no_probe_beats_the_transport_choice(tmp_path: Path, gateway: str) -> None:
    context = build_runner(cwd=tmp_path, gateway=gateway, no_probe=True)
    assert not isinstance(context.runner._probe, AntigravityCapacityProbe | AgyCliCapacityProbe)
    assert context.runner._wait_policy.no_probe is True
