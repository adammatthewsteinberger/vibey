"""
vibey-bootstrap (formerly azure-bootstrap)

A production-ready Azure bootstrap library that handles application initialization
for Azure Functions, including App Configuration, Key Vault, and App Insights integration.

This library solves the circular dependency between logging and configuration by:
1. Starting with basic console logging
2. Loading configuration from Azure App Configuration + Key Vault
3. Upgrading to App Insights telemetry when available
4. Loading all configs to os.environ for transparent access

Quick Start:
    from vibey_bootstrap import initialize_application, get_bootstrap_logger

    # Get logger that works immediately
    logger = get_bootstrap_logger(__name__)

    # Bootstrap the application (App Config + Key Vault + App Insights)
    config_repo = initialize_application()

    # Now all configs are in os.environ
    db_host = os.getenv("DATABASE_HOST")

For detailed usage, see: https://github.com/adammatthewsteinberger/vibey-bootstrap
"""

__version__ = "4.2.3"
__author__ = "Adam Matthew Steinberger"
__license__ = "MIT"

# ──────────────────────────────────────────────────────────────────────────
# v2 additions (additive only — never alters the v1 surface above)
# ──────────────────────────────────────────────────────────────────────────
import logging as _stdlib_logging
import os as _os

# v3.0.0 additions (opt-in subpackages re-exported for convenience)
from vibey_bootstrap.aks import build_info as build_info
from vibey_bootstrap.audit import verify_chain as verify_chain
from vibey_bootstrap.auth import verify_hmac_signature as verify_hmac_signature
from vibey_bootstrap.bootstrap import bootstrap_initialized as bootstrap_initialized
from vibey_bootstrap.bootstrap import ensure_bootstrap as ensure_bootstrap
from vibey_bootstrap.bootstrap import load_local_settings as load_local_settings
from vibey_bootstrap.counters import bump_counter as bump_counter
from vibey_bootstrap.counters import counter_snapshot as counter_snapshot
from vibey_bootstrap.db.outbox import drain_outbox as drain_outbox
from vibey_bootstrap.email import AcsEmailSender as AcsEmailSender
from vibey_bootstrap.exceptions import InvalidMessageError as InvalidMessageError
from vibey_bootstrap.exceptions import NetworkError as NetworkError
from vibey_bootstrap.exceptions import PipelineError as PipelineError
from vibey_bootstrap.exceptions import RateLimitError as RateLimitError
from vibey_bootstrap.exceptions import TransientError as TransientError
from vibey_bootstrap.exceptions import UnrecoverableError as UnrecoverableError
from vibey_bootstrap.exceptions import is_unrecoverable as is_unrecoverable
from vibey_bootstrap.governance import budget_guard as budget_guard
from vibey_bootstrap.governance import track_usage as track_usage
from vibey_bootstrap.http import build_session as build_session
from vibey_bootstrap.http import request_with_retry as request_with_retry
from vibey_bootstrap.identity import build_tenant_credential as build_tenant_credential
from vibey_bootstrap.identity import (
    build_tenant_credential_cached as build_tenant_credential_cached,
)
from vibey_bootstrap.logging import JsonLogFormatter as JsonLogFormatter
from vibey_bootstrap.logging import configure_logging as configure_logging
from vibey_bootstrap.logging import correlation_scope as correlation_scope
from vibey_bootstrap.logging import get_correlation_id as get_correlation_id
from vibey_bootstrap.logging import mask_api_key as mask_api_key
from vibey_bootstrap.logging import mask_bearer_token as mask_bearer_token
from vibey_bootstrap.logging import mask_email_address as mask_email_address
from vibey_bootstrap.logging import mask_secrets_in_dict as mask_secrets_in_dict
from vibey_bootstrap.logging import safe_json_dumps as safe_json_dumps
from vibey_bootstrap.logging import sanitize_for_log as sanitize_for_log
from vibey_bootstrap.logging import set_correlation_id as set_correlation_id

# Exceptions
from vibey_bootstrap.models.exceptions import ConfigurationError as ConfigurationError
from vibey_bootstrap.models.exceptions import KeyVaultError as KeyVaultError
from vibey_bootstrap.models.exceptions import RepositoryError as RepositoryError
from vibey_bootstrap.path_safety import confine_to_root as confine_to_root
from vibey_bootstrap.path_safety import sanitize_path_segment as sanitize_path_segment
from vibey_bootstrap.phases import PhaseResult as PhaseResult
from vibey_bootstrap.phases import run_phase as run_phase
from vibey_bootstrap.phases import run_phases as run_phases

# Repository implementations
from vibey_bootstrap.repositories.enhanced_config_repository import (
    EnhancedConfigRepository as EnhancedConfigRepository,
)
from vibey_bootstrap.repositories.enhanced_config_repository import (
    create_enhanced_config_repository as create_enhanced_config_repository,
)
from vibey_bootstrap.repositories.interfaces.enhanced_config_repository_interface import (
    EnhancedConfigRepositoryInterface as EnhancedConfigRepositoryInterface,
)
from vibey_bootstrap.repositories.interfaces.secrets_repository_interface import (
    SecretsRepositoryInterface as SecretsRepositoryInterface,
)
from vibey_bootstrap.repositories.secrets_repository import SecretsRepository as SecretsRepository
from vibey_bootstrap.security import compare_secrets as compare_secrets

# Core classes for advanced usage
# Main bootstrap function - most users only need this
from vibey_bootstrap.services.application_bootstrap import (
    ApplicationBootstrap as ApplicationBootstrap,
)
from vibey_bootstrap.services.application_bootstrap import (
    initialize_application as initialize_application,
)

# Bootstrap logging - works before configuration loaded
from vibey_bootstrap.services.bootstrap_logging import BootstrapLogger as BootstrapLogger
from vibey_bootstrap.services.bootstrap_logging import ExtraFieldsFormatter as ExtraFieldsFormatter
from vibey_bootstrap.services.bootstrap_logging import (
    ensure_bootstrap_logging as ensure_bootstrap_logging,
)
from vibey_bootstrap.services.bootstrap_logging import get_bootstrap_logger as get_bootstrap_logger

# Interfaces for type hinting and custom implementations
from vibey_bootstrap.services.interfaces.application_bootstrap_interface import (
    ApplicationBootstrapInterface as ApplicationBootstrapInterface,
)
from vibey_bootstrap.services.interfaces.bootstrap_logger_interface import (
    BootstrapLoggerInterface as BootstrapLoggerInterface,
)
from vibey_bootstrap.services.interfaces.telemetry_manager_interface import (
    TelemetryManagerInterface as TelemetryManagerInterface,
)
from vibey_bootstrap.services.telemetry import TelemetryManager as TelemetryManager
from vibey_bootstrap.services.telemetry import telemetry_manager as telemetry_manager
from vibey_bootstrap.softfail import SoftFailResult as SoftFailResult
from vibey_bootstrap.softfail import soft_fail as soft_fail
from vibey_bootstrap.softfail import soft_fail_with as soft_fail_with
from vibey_bootstrap.tracing import latency_snapshot as latency_snapshot
from vibey_bootstrap.tracing import traced as traced
from vibey_bootstrap.transports import configure_transports as configure_transports
from vibey_bootstrap.transports import disable_transport as disable_transport
from vibey_bootstrap.transports import enable_transport as enable_transport
from vibey_bootstrap.transports import list_transports as list_transports
from vibey_bootstrap.transports import register_transport as register_transport
from vibey_bootstrap.validation import MessageSchema as MessageSchema
from vibey_bootstrap.validation import queue_message_schema as queue_message_schema
from vibey_bootstrap.validation import validate_message as validate_message


def refresh_setting(*names: str) -> None:
    """Re-read named settings from the cached App Configuration repo and
    write their values into ``os.environ``.

    Net-new in v2. Designed to be called from a recurring job (see
    ``vibey_bootstrap.config_refresh.refresh_log_flags``) so ops can flip a
    setting in App Configuration and see it take effect within seconds
    without redeploying.

    No-ops with a DEBUG log when ``initialize_application()`` has not yet
    run. Best-effort — never raises.
    """
    if not names:
        return
    logger = _stdlib_logging.getLogger(__name__)
    try:
        from vibey_bootstrap.services.application_bootstrap import (
            get_last_initialized_repo,
        )
    except Exception:
        logger.debug("refresh_setting: bootstrap module unavailable")
        return
    repo = get_last_initialized_repo()
    if repo is None:
        logger.debug("refresh_setting: no cached repo (initialize_application not called)")
        return
    for name in names:
        if not isinstance(name, str) or not name:
            continue
        try:
            value = repo.get_value(name)
        except Exception as exc:
            logger.warning("refresh_setting: failed to read %s: %s", name, exc)
            continue
        if value is None:
            continue
        _os.environ[name] = str(value)


# Public API
__all__ = [
    # Version
    "__version__",
    # Main bootstrap functions (most common usage)
    "initialize_application",
    "get_bootstrap_logger",
    "create_enhanced_config_repository",
    "ensure_bootstrap_logging",
    # Singleton instance
    "telemetry_manager",
    # Core classes
    "ApplicationBootstrap",
    "BootstrapLogger",
    "ExtraFieldsFormatter",
    "TelemetryManager",
    "EnhancedConfigRepository",
    "SecretsRepository",
    # Interfaces
    "ApplicationBootstrapInterface",
    "BootstrapLoggerInterface",
    "TelemetryManagerInterface",
    "EnhancedConfigRepositoryInterface",
    "SecretsRepositoryInterface",
    # Exceptions
    "RepositoryError",
    "ConfigurationError",
    "KeyVaultError",
    # v2 additions — Tier 1 always-on primitives
    "bootstrap_initialized",
    "bump_counter",
    "configure_logging",
    "correlation_scope",
    "counter_snapshot",
    "ensure_bootstrap",
    "get_correlation_id",
    "latency_snapshot",
    "load_local_settings",
    "mask_api_key",
    "mask_bearer_token",
    "mask_email_address",
    "mask_secrets_in_dict",
    "refresh_setting",
    "safe_json_dumps",
    "sanitize_for_log",
    "set_correlation_id",
    "traced",
    # v2 Parts 2+3 — exceptions, soft-fail, phases, validation, path safety, security
    "InvalidMessageError",
    "MessageSchema",
    "NetworkError",
    "PhaseResult",
    "PipelineError",
    "RateLimitError",
    "SoftFailResult",
    "TransientError",
    "UnrecoverableError",
    "compare_secrets",
    "confine_to_root",
    "is_unrecoverable",
    "queue_message_schema",
    "run_phase",
    "run_phases",
    "sanitize_path_segment",
    "soft_fail",
    "soft_fail_with",
    "validate_message",
    # v2.1 additions — logging transport layer
    "JsonLogFormatter",
    "configure_transports",
    "disable_transport",
    "enable_transport",
    "list_transports",
    "register_transport",
    # v3.0.0 — db, outbox, email, http, documentdb, aks, governance, identity, audit
    "build_tenant_credential",
    "build_tenant_credential_cached",
    "verify_chain",
    "budget_guard",
    "track_usage",
    "build_session",
    "request_with_retry",
    "build_info",
    "drain_outbox",
    "AcsEmailSender",
    "verify_hmac_signature",
]
