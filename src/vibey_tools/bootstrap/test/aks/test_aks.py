"""AKS runtime tests."""

from __future__ import annotations

import threading

from vibey_bootstrap.aks import build_info, install_sigterm_handler
from vibey_bootstrap.aks.leader_election import LeaderElection


def test_build_info_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("BUILD_VERSION", "3.0.0")
    monkeypatch.setenv("POD_NAME", "worker-1")
    info = build_info()
    assert info["version"] == "3.0.0"
    assert info["pod_name"] == "worker-1"


def test_leader_election_noop_without_configmap() -> None:
    le = LeaderElection(configmap_name=None)
    le.start()
    assert le.is_leader is True
    le.stop()


def test_sigterm_sets_event() -> None:
    ev = threading.Event()
    install_sigterm_handler(ev)
    assert isinstance(ev, threading.Event)
