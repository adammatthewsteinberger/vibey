"""`refresh_setting`, the enhanced config repository, and the scaffold CLI.

The common thread is precedence: a value already in ``os.environ`` — typically a local
override — must survive a Key Vault load, and a config source that goes away must not
take the process with it.
"""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock

import pytest

import vibey_bootstrap
from vibey_bootstrap.contrib import scaffold as scaffold_mod
from vibey_bootstrap.contrib.scaffold import list_templates, main, main_azbootstrap, scaffold
from vibey_bootstrap.repositories.enhanced_config_repository import EnhancedConfigRepository

# ═══════════════════════════════════════════════════════ refresh_setting


def test_refreshing_no_names_does_nothing():
    assert vibey_bootstrap.refresh_setting() is None


def test_refreshing_without_a_bootstrap_module_is_a_debug_no_op(monkeypatch, caplog):
    import builtins as py_builtins

    real_import = py_builtins.__import__

    def refuse(name, *a, **kw):
        if name == "vibey_bootstrap.services.application_bootstrap":
            raise ImportError("not available")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(py_builtins, "__import__", refuse)
    with caplog.at_level(logging.DEBUG, logger="vibey_bootstrap"):
        vibey_bootstrap.refresh_setting("LOG_LEVEL")
    assert "bootstrap module unavailable" in caplog.text


def test_refreshed_values_land_in_the_environment(monkeypatch, caplog):
    from vibey_bootstrap.services import application_bootstrap

    repo = MagicMock()
    repo.get_value.side_effect = lambda name: {"GOOD": "yes", "ABSENT": None, "BROKEN": None}.get(
        name
    )
    repo.get_value = MagicMock(
        side_effect=lambda name: (
            {"GOOD": "yes", "ABSENT": None}.get(name)
            if name != "BROKEN"
            else (_ for _ in ()).throw(RuntimeError("App Config is unreachable"))
        )
    )
    monkeypatch.setattr(application_bootstrap, "get_last_initialized_repo", lambda: repo)
    monkeypatch.delenv("GOOD", raising=False)

    with caplog.at_level(logging.WARNING, logger="vibey_bootstrap"):
        vibey_bootstrap.refresh_setting("GOOD", "ABSENT", "BROKEN", "", None)  # type: ignore[arg-type]

    assert os.environ["GOOD"] == "yes"
    assert "ABSENT" not in os.environ
    assert "failed to read BROKEN" in caplog.text
    del os.environ["GOOD"]


def test_refreshing_before_initialisation_is_a_debug_no_op(monkeypatch, caplog):
    from vibey_bootstrap.services import application_bootstrap

    monkeypatch.setattr(application_bootstrap, "get_last_initialized_repo", lambda: None)
    with caplog.at_level(logging.DEBUG, logger="vibey_bootstrap"):
        vibey_bootstrap.refresh_setting("LOG_LEVEL")
    assert "no cached repo" in caplog.text


# ══════════════════════════════════════════ enhanced config repository


@pytest.fixture
def repo() -> EnhancedConfigRepository:
    return EnhancedConfigRepository(app_config_connection_string=None)


def test_a_local_environment_value_survives_a_key_vault_load(repo, monkeypatch, caplog):
    monkeypatch.setenv("SHARED_KEY", "local override")
    secrets = MagicMock()
    secrets.list_secrets.return_value = {
        "SHARED_KEY": "from key vault",
        "NEW_KEY": "from key vault",
    }
    repo.secrets_repository = secrets

    with caplog.at_level(logging.DEBUG):
        repo.load_to_environ()

    assert os.environ["SHARED_KEY"] == "local override"
    assert os.environ["NEW_KEY"] == "from key vault"
    del os.environ["NEW_KEY"]


def test_a_provider_that_cannot_refresh_does_not_break_the_refresh(repo, caplog):
    provider = MagicMock()
    provider.refresh.side_effect = RuntimeError("App Configuration is unreachable")
    repo._config_provider = provider
    secrets = MagicMock()
    secrets.list_secrets.return_value = {}
    repo.secrets_repository = secrets

    with caplog.at_level(logging.ERROR):
        repo.refresh()

    assert "Failed to refresh App Configuration provider" in caplog.text
    secrets.clear_cache.assert_called_once()


def test_metrics_report_zero_rather_than_failing_when_a_source_misbehaves(repo):
    provider = MagicMock()
    provider.__iter__ = MagicMock(side_effect=RuntimeError("provider is closed"))
    repo._config_provider = provider
    secrets = MagicMock()
    secrets.list_secrets.side_effect = RuntimeError("vault is unreachable")
    repo.secrets_repository = secrets

    metrics = repo.get_repository_metrics()
    assert metrics["app_config_count"] == 0
    assert metrics["secrets_count"] == 0


def test_metrics_report_zero_when_there_are_no_sources_at_all(repo):
    metrics = repo.get_repository_metrics()
    assert metrics["app_config_count"] == 0
    assert metrics["secrets_count"] == 0


def test_key_vault_is_unavailable_when_there_is_no_secrets_repository(repo):
    assert repo.is_key_vault_available() is False


# ═══════════════════════════════════════════════════════════ scaffold CLI


def test_no_templates_directory_means_no_templates(monkeypatch, tmp_path):
    monkeypatch.setattr(scaffold_mod, "_templates_root", lambda: tmp_path / "absent")
    assert list_templates() == []


def test_a_template_can_be_named_by_its_basename_alone(monkeypatch, tmp_path):
    root = tmp_path / "templates" / "helm" / "worker"
    root.mkdir(parents=True)
    (root / "Chart.yaml.template").write_text("name: {{ APP }}\n")
    monkeypatch.setattr(scaffold_mod, "_templates_root", lambda: tmp_path / "templates")

    dest = scaffold("Chart.yaml.template", tmp_path / "out", {"APP": "billing"})
    assert dest.name == "Chart.yaml"
    assert dest.read_text() == "name: billing\n"


def test_an_ambiguous_or_absent_template_is_an_error(monkeypatch, tmp_path):
    (tmp_path / "templates").mkdir()
    monkeypatch.setattr(scaffold_mod, "_templates_root", lambda: tmp_path / "templates")
    with pytest.raises(FileNotFoundError, match="template not found"):
        scaffold("nope.template", tmp_path / "out", {})


def test_the_cli_scaffolds_with_substitutions(monkeypatch, tmp_path, capsys):
    root = tmp_path / "templates"
    root.mkdir()
    (root / "app.yaml.template").write_text("name: {{APP}} env: {{ ENV }}\n")
    monkeypatch.setattr(scaffold_mod, "_templates_root", lambda: root)

    code = main(
        [
            "scaffold",
            "app.yaml.template",
            "--out",
            str(tmp_path / "out"),
            "--var",
            "APP=billing",
            "--var",
            "ENV=prod",
            "--var",
            "=ignored",
        ]
    )
    assert code == 0
    assert "scaffolded" in capsys.readouterr().out
    assert (tmp_path / "out" / "app.yaml").read_text() == "name: billing env: prod\n"


def test_the_cli_with_no_command_prints_help_and_fails(capsys):
    assert main([]) == 1
    assert "usage:" in capsys.readouterr().out


def test_the_deprecated_alias_warns_once_then_delegates(capsys, monkeypatch):
    monkeypatch.setattr(scaffold_mod, "_ALIAS_WARNED", False)
    assert main_azbootstrap(["version"]) == 0
    first = capsys.readouterr()
    assert "deprecated alias" in first.err

    assert main_azbootstrap(["version"]) == 0
    assert "deprecated alias" not in capsys.readouterr().err
