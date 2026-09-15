"""Workload Identity / DefaultAzureCredential wrapper.

Single source of truth for "which Azure credential should this process
use." Replaces ad-hoc ``DefaultAzureCredential()`` instantiation across an
app and codifies the WorkloadIdentity-first preference (no client secrets
in pod env in production).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from enum import Enum
from typing import Any

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.tracing.decorators import traced

_logger = logging.getLogger(__name__)

AZURE_TOKEN_AUDIENCE = "api://AzureADTokenExchange"
_DEFAULT_TOKEN_FILE = "/var/run/secrets/azure/tokens/azure-identity-token"

# Early-refresh window: don't serve tokens within this many seconds of expiry.
_TOKEN_EARLY_REFRESH_SECS = 300  # 5 minutes


class CredentialKind(str, Enum):
    WORKLOAD_IDENTITY = "workload_identity"
    CLIENT_SECRET = "client_secret"
    DEFAULT = "default"


def credential_kind(
    *,
    tenant_id: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> CredentialKind:
    """Inspect inputs + env to decide which kind ``build_credential`` would return.

    Does not actually construct a credential — useful for /api/health probes.
    """
    tenant = tenant_id or os.environ.get("AZURE_TENANT_ID", "").strip()
    client = client_id or os.environ.get("AZURE_CLIENT_ID", "").strip()
    secret = client_secret or os.environ.get("AZURE_CLIENT_SECRET", "")
    if secret:
        return CredentialKind.CLIENT_SECRET
    if tenant and client:
        return CredentialKind.WORKLOAD_IDENTITY
    return CredentialKind.DEFAULT


def build_credential(
    *,
    tenant_id: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    prefer: CredentialKind | None = None,
    token_file_path: str = _DEFAULT_TOKEN_FILE,
) -> Any:
    """Build the preferred Azure credential for the current environment.

    Resolution order (when ``prefer`` is None):
    1. ``ClientSecretCredential`` when ``client_secret`` (or env) is set.
    2. ``WorkloadIdentityCredential`` when ``tenant_id`` and ``client_id``
       are set but secret is empty.
    3. ``DefaultAzureCredential`` as last-resort fallback.
    """
    try:
        from azure.identity import (  # type: ignore[import-not-found]
            ClientSecretCredential,
            DefaultAzureCredential,
            WorkloadIdentityCredential,
        )
    except ImportError as exc:  # pragma: no cover
        raise ImportError("build_credential requires azure-identity (in core deps)") from exc

    tenant = tenant_id or os.environ.get("AZURE_TENANT_ID", "").strip() or None
    client = client_id or os.environ.get("AZURE_CLIENT_ID", "").strip() or None
    secret = (
        client_secret if client_secret is not None else os.environ.get("AZURE_CLIENT_SECRET", "")
    )

    kind: CredentialKind
    if prefer is CredentialKind.CLIENT_SECRET or (prefer is None and secret):
        if not (tenant and client and secret):
            raise ValueError(
                "ClientSecretCredential requires tenant_id, client_id, and client_secret"
            )
        cred: Any = ClientSecretCredential(tenant, client, secret)
        kind = CredentialKind.CLIENT_SECRET
    elif prefer is CredentialKind.WORKLOAD_IDENTITY or (prefer is None and tenant and client):
        cred = WorkloadIdentityCredential(
            tenant_id=tenant,
            client_id=client,
            token_file_path=token_file_path,
        )
        kind = CredentialKind.WORKLOAD_IDENTITY
    else:
        cred = DefaultAzureCredential()
        kind = CredentialKind.DEFAULT

    _logger.info(
        "Credential built",
        extra={
            "operation": "identity.build_credential",
            "kind": kind.value,
            "tenant_id": tenant or "(unset)",
            "client_id": client or "(unset)",
            "client_secret_present": bool(secret),
        },
    )
    bump_counter(f"identity.credential_built.{kind.value}")
    return cred


def _mock_enabled() -> bool:
    return os.environ.get("USE_MOCK_BOOTSTRAP", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


@traced(operation="identity.credential_health", alert_on_error="warn")
def credential_health(
    scopes: tuple[str, ...] = ("https://management.azure.com/.default",),
) -> dict[str, Any]:
    """Acquire a token, measure latency, return a health-check dict."""
    if _mock_enabled():
        return {"status": "ok", "mock": True}

    kind = credential_kind()
    try:
        cred = build_credential()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "kind": kind.value, "message": str(exc)[:200]}

    start = time.monotonic()
    try:
        token = cred.get_token(*scopes)
        latency_ms = int((time.monotonic() - start) * 1000)
        scope_short = scopes[0].rsplit("/", 1)[-1] if scopes else "unknown"
        bump_counter(f"identity.token_acquired.{scope_short}")
        return {
            "status": "ok",
            "kind": kind.value,
            "latency_ms": latency_ms,
            "expires_on": getattr(token, "expires_on", None),
        }
    except Exception as exc:  # noqa: BLE001
        bump_counter("identity.token_failed")
        return {
            "status": "error",
            "kind": kind.value,
            "message": str(exc)[:200],
        }


# ---------------------------------------------------------------------------
# Multi-tenant federated credential support (v3.0.0 §7.5 B8)
# ---------------------------------------------------------------------------


def build_tenant_credential(
    tenant_id: str,
    *,
    app_client_id: str | None = None,
    token_file_path: str = _DEFAULT_TOKEN_FILE,
) -> Any:
    """Build a ``WorkloadIdentityCredential`` scoped to *tenant_id*.

    Zero-secret — uses the federated token file on disk.  Designed for
    multi-tenant Entra applications that need to acquire per-customer-tenant
    Graph (or ARM) tokens from a single registered app.

    Args:
        tenant_id: The target customer / resource tenant.
        app_client_id: The multi-tenant app's client ID.  Falls back to
            ``AZURE_CLIENT_ID`` env if not supplied.
        token_file_path: Path to the federated token file written by the
            Azure Workload Identity webhook.  Defaults to the standard
            AKS path.

    Returns:
        A ``WorkloadIdentityCredential`` instance.

    Raises:
        ValueError: If no client ID can be resolved.
        ImportError: If ``azure-identity`` is not installed.
    """
    try:
        from azure.identity import WorkloadIdentityCredential  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise ImportError("build_tenant_credential requires azure-identity (in core deps)") from exc

    client = app_client_id or os.environ.get("AZURE_CLIENT_ID", "").strip() or None
    if not client:
        raise ValueError(
            "build_tenant_credential requires app_client_id or AZURE_CLIENT_ID env var"
        )

    _logger.info(
        "Tenant credential built",
        extra={
            "operation": "identity.build_tenant_credential",
            "tenant_id": tenant_id,
            "client_id": client,
            "token_file_path": token_file_path,
        },
    )
    bump_counter("identity.credential_built.tenant_workload_identity")
    return WorkloadIdentityCredential(
        tenant_id=tenant_id,
        client_id=client,
        token_file_path=token_file_path,
    )


# ---------------------------------------------------------------------------
# TokenCache
# ---------------------------------------------------------------------------

# Internal cache storage: (tenant_id, scope) -> {"token": str, "expires_at": float}
# Protected by _TOKEN_CACHE_LOCK.
_TOKEN_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_TOKEN_CACHE_LOCK = threading.Lock()

_TOKEN_CACHE_MAX_SIZE_DEFAULT = 500


def _token_cache_max_size() -> int:
    """Read TOKEN_CACHE_MAX_SIZE from env, fallback to 500."""
    raw = os.environ.get("TOKEN_CACHE_MAX_SIZE", "").strip()
    if raw.isdigit():
        return max(1, int(raw))
    return _TOKEN_CACHE_MAX_SIZE_DEFAULT


class TokenCache:
    """In-process LRU/TTL cache for ``(tenant_id, scope) -> token`` pairs.

    Tokens are considered stale when they are within
    ``_TOKEN_EARLY_REFRESH_SECS`` (5 minutes) of their ``expires_at``
    timestamp.  The maximum number of entries is controlled by the
    ``TOKEN_CACHE_MAX_SIZE`` environment variable (default 500).

    All methods are thread-safe.  This class is a namespace — it wraps
    module-level state so the cache can be reset between tests.
    """

    @staticmethod
    def get_cached_token(tenant_id: str, scope: str) -> str | None:
        """Return a cached token for *(tenant_id, scope)* or ``None``.

        Returns ``None`` when no entry exists or the token is within
        5 minutes of expiry (triggering an early refresh).
        """
        key = (tenant_id, scope)
        with _TOKEN_CACHE_LOCK:
            entry = _TOKEN_CACHE.get(key)
        if entry is None:
            return None
        if time.time() >= entry["expires_at"] - _TOKEN_EARLY_REFRESH_SECS:
            # Stale — caller should refresh.
            return None
        return str(entry["token"])

    @staticmethod
    def cache_token(
        tenant_id: str,
        scope: str,
        token: str,
        expires_at: float,
    ) -> None:
        """Store *token* in the cache under *(tenant_id, scope)*.

        If the cache is at capacity the oldest entry (by insertion order,
        since Python 3.7+ dicts are ordered) is evicted first.
        """
        key = (tenant_id, scope)
        with _TOKEN_CACHE_LOCK:
            # Evict oldest entry when at capacity (LRU-lite via insertion order).
            max_size = _token_cache_max_size()
            if key not in _TOKEN_CACHE and len(_TOKEN_CACHE) >= max_size:
                oldest_key = next(iter(_TOKEN_CACHE))
                del _TOKEN_CACHE[oldest_key]
                bump_counter("identity.token_cache.evicted")
            _TOKEN_CACHE[key] = {"token": token, "expires_at": expires_at}
        bump_counter("identity.token_cache.stored")

    @staticmethod
    def invalidate(tenant_id: str | None = None) -> None:
        """Invalidate cache entries.

        Args:
            tenant_id: When supplied, only entries for this tenant are
                removed.  When ``None``, the entire cache is cleared.
        """
        with _TOKEN_CACHE_LOCK:
            if tenant_id is None:
                _TOKEN_CACHE.clear()
                bump_counter("identity.token_cache.invalidated_all")
            else:
                keys_to_remove = [k for k in _TOKEN_CACHE if k[0] == tenant_id]
                for k in keys_to_remove:
                    del _TOKEN_CACHE[k]
                bump_counter(f"identity.token_cache.invalidated.{tenant_id}")


def _reset_token_cache() -> None:
    """Clear the in-process token cache.  Only callable when
    ``AZURE_BOOTSTRAP_ALLOW_RESET=1`` (test environments only).
    """
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET", "").strip() != "1":
        raise RuntimeError(
            "_reset_token_cache() is only available when AZURE_BOOTSTRAP_ALLOW_RESET=1"
        )
    with _TOKEN_CACHE_LOCK:
        _TOKEN_CACHE.clear()


# ---------------------------------------------------------------------------
# build_tenant_credential_cached
# ---------------------------------------------------------------------------


def build_tenant_credential_cached(
    tenant_id: str,
    scope: str,
    *,
    app_client_id: str | None = None,
) -> str:
    """Return an access token for *tenant_id* / *scope*, using the cache.

    On a cache hit the cached token string is returned immediately.
    On a miss a fresh ``WorkloadIdentityCredential`` is built via
    :func:`build_tenant_credential`, ``get_token(scope)`` is called, and
    the result is stored in the cache before being returned.

    Args:
        tenant_id: The target customer / resource tenant.
        scope: The OAuth2 scope to request (e.g.
            ``"https://graph.microsoft.com/.default"``).
        app_client_id: Passed through to :func:`build_tenant_credential`.

    Returns:
        The raw token string (``AccessToken.token``).

    Raises:
        ValueError: If no client ID can be resolved.
        ImportError: If ``azure-identity`` is not installed.
    """
    cached = TokenCache.get_cached_token(tenant_id, scope)
    if cached is not None:
        bump_counter("identity.token_cache.hit")
        return cached

    bump_counter("identity.token_cache.miss")
    cred = build_tenant_credential(
        tenant_id,
        app_client_id=app_client_id,
    )
    access_token = cred.get_token(scope)
    token_str: str = access_token.token
    expires_at: float = float(getattr(access_token, "expires_on", 0))
    TokenCache.cache_token(tenant_id, scope, token_str, expires_at)
    return token_str


__all__ = [
    "AZURE_TOKEN_AUDIENCE",
    "CredentialKind",
    "TokenCache",
    "build_credential",
    "build_tenant_credential",
    "build_tenant_credential_cached",
    "credential_health",
    "credential_kind",
    "_reset_token_cache",
]
