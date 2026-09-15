"""Tests for ``vibey_bootstrap.identity``."""

from __future__ import annotations

import logging

import pytest

from vibey_bootstrap.identity import (
    CredentialKind,
    build_credential,
    credential_kind,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)


def test_credential_kind_prefers_workload_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    assert credential_kind() == CredentialKind.WORKLOAD_IDENTITY


def test_credential_kind_prefers_client_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "supersecret")
    assert credential_kind() == CredentialKind.CLIENT_SECRET


def test_credential_kind_falls_back_to_default() -> None:
    assert credential_kind() == CredentialKind.DEFAULT


def test_build_credential_uses_client_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    from azure.identity import ClientSecretCredential

    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "supersecret")
    cred = build_credential()
    assert isinstance(cred, ClientSecretCredential)


def test_build_credential_uses_workload_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    from azure.identity import WorkloadIdentityCredential

    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    cred = build_credential()
    assert isinstance(cred, WorkloadIdentityCredential)


def test_build_credential_falls_back_to_default() -> None:
    from azure.identity import DefaultAzureCredential

    cred = build_credential()
    assert isinstance(cred, DefaultAzureCredential)


def test_build_credential_never_logs_secret(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "MY-VERY-SPECIFIC-SECRET-MARKER")
    with caplog.at_level(logging.INFO, logger="vibey_bootstrap.identity"):
        build_credential()
    for record in caplog.records:
        full_text = record.getMessage() + " " + str(getattr(record, "__dict__", {}))
        assert "MY-VERY-SPECIFIC-SECRET-MARKER" not in full_text
