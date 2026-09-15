"""Scaffold CLI tests."""

from __future__ import annotations

from pathlib import Path

from vibey_bootstrap.contrib.scaffold import list_templates, main, scaffold


def test_list_templates_includes_helm() -> None:
    names = list_templates()
    assert any(n.startswith("helm/") for n in names)


def test_scaffold_substitutes_vars(tmp_path: Path) -> None:
    dest = scaffold(
        "helm/worker/Chart.yaml.template",
        tmp_path,
        {"app_name": "my-worker"},
    )
    assert dest.read_text().count("my-worker") >= 1


def test_main_version() -> None:
    assert main(["version"]) == 0


def test_main_azbootstrap_alias_warns_once_and_delegates(capsys) -> None:
    from vibey_bootstrap.contrib import scaffold as mod

    mod._ALIAS_WARNED = False
    try:
        assert mod.main_azbootstrap(["version"]) == 0
        assert mod.main_azbootstrap(["version"]) == 0
    finally:
        mod._ALIAS_WARNED = False
    captured = capsys.readouterr()
    assert captured.err.count("deprecated alias") == 1
    assert "vibey-bootstrap" in captured.err
