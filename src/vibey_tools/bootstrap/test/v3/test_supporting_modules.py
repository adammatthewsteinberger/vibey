"""Email, documentdb, migrations, scaffold — exhaustive tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.contrib.scaffold import list_templates, main, scaffold
from vibey_bootstrap.db.migrations import ENV_PY_TEMPLATE


def test_acs_sender_callable_for_outbox(monkeypatch) -> None:
    pytest.importorskip("azure.communication.email")
    monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://x/;accesskey=y")
    monkeypatch.setenv("ACS_SENDER_ADDRESS", "sender@test.com")
    from vibey_bootstrap.email import AcsEmailSender

    poller = MagicMock()
    poller.result.return_value = MagicMock(id="m1")
    client = MagicMock()
    client.begin_send.return_value = poller
    sender = AcsEmailSender()
    with patch.object(sender, "_get_client", return_value=client):
        sender({"to_recipients": ["a@b.com"], "subject": "s", "html_body": "b"})
    client.begin_send.assert_called_once()


def test_documentdb_client_from_env(monkeypatch) -> None:
    pytest.importorskip("pymongo")
    monkeypatch.setenv("NOSQL_URI", "mongodb://localhost:27017")
    from vibey_bootstrap.documentdb import mongo_client_from_env

    client = mongo_client_from_env()
    client.close()


def test_migrations_write_and_template() -> None:
    assert "run_migrations_online" in ENV_PY_TEMPLATE


def test_migrations_upgrade_mocked(tmp_path: Path) -> None:
    pytest.importorskip("alembic")
    ini = tmp_path / "alembic.ini"
    ini.write_text("[alembic]\nscript_location = .\n", encoding="utf-8")
    with patch("alembic.command.upgrade") as upgrade:
        from vibey_bootstrap.db.migrations import upgrade_to_head

        upgrade_to_head(alembic_ini=ini)
        upgrade.assert_called_once()


def test_scaffold_all_templates_listed() -> None:
    names = list_templates()
    for prefix in ("terraform/", "bicep/", "helm/", "gitops/", "cicd/", "policy/"):
        assert any(n.startswith(prefix) for n in names), f"missing {prefix}"


def test_scaffold_cli_version_and_scaffold(tmp_path: Path) -> None:
    assert main(["version"]) == 0
    dest = scaffold("helm/worker/Chart.yaml.template", tmp_path, {"app_name": "worker"})
    assert "worker" in dest.read_text()


def test_scaffold_missing_template_raises() -> None:
    with pytest.raises(FileNotFoundError):
        scaffold("does/not/exist.template", Path("."), {})
