"""Fixtures for local I/O integration tests (SQLite, mongomock, Azurite)."""

from __future__ import annotations

import os
import socket

import pytest

# Official Azurite well-known credentials (safe for local emulator only).
# https://learn.microsoft.com/en-us/azure/storage/common/storage-connect-azurite
AZURITE_DEV_BLOB_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)


def _azurite_blob_reachable(
    host: str = "127.0.0.1", port: int = 10000, timeout: float = 0.5
) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture
def sqlite_dsn(tmp_path):
    db_path = tmp_path / "app_logs.db"
    return f"sqlite:///{db_path}"


@pytest.fixture
def azurite_connection_string() -> str:
    conn = os.environ.get("AZURITE_BLOB_CONNECTION_STRING", AZURITE_DEV_BLOB_CONNECTION_STRING)
    if not _azurite_blob_reachable():
        pytest.skip(
            "Azurite blob endpoint not reachable on 127.0.0.1:10000 — "
            "run: docker run --rm -p 10000:10000 mcr.microsoft.com/azure-storage/azurite"
        )
    return conn


@pytest.fixture
def azurite_container(azurite_connection_string: str):
    pytest.importorskip("azure.storage.blob")
    from azure.core.exceptions import ResourceExistsError
    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(
        azurite_connection_string,
        # Azurite lags the latest azure-storage-blob service version.
        api_version="2023-11-03",
    )
    name = "vibey-bootstrap-test-logs"
    try:
        service.create_container(name)
    except ResourceExistsError:
        pass
    container = service.get_container_client(name)
    yield container
    try:
        for blob in container.list_blobs():
            container.delete_blob(blob.name)
    except Exception:
        pass
