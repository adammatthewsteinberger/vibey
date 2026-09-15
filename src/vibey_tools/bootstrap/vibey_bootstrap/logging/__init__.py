"""Tier 1 logging primitives.

Always-on, stdlib-only. The top-level ``vibey_bootstrap`` package re-exports
the most common entry-points (``configure_logging``, ``correlation_scope``,
``mask_*``).  Deeper imports stay available for callers that want fine-grained
access.
"""

from vibey_bootstrap.logging.config import (
    configure_logging,
    debug_logging_enabled,
    effective_log_level,
    env_flag,
)
from vibey_bootstrap.logging.correlation import (
    CorrelationFilter,
    correlation_scope,
    get_correlation_id,
    set_correlation_id,
)
from vibey_bootstrap.logging.formatter import (
    _STDLIB_LOG_RECORD_KEYS,
    ExtraFieldsFormatter,
    LoggingExtraConflictError,
)
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.logging.masking import (
    _looks_sensitive,
    _safe_repr,
    content_preview,
    mask_api_key,
    mask_bearer_token,
    mask_email_address,
    mask_secrets_in_dict,
    register_secret_keys,
    safe_json_dumps,
    sanitize_for_log,
)
from vibey_bootstrap.logging.noise import (
    register_noisy_logger,
    silence_noisy_loggers,
)

__all__ = [
    "CorrelationFilter",
    "ExtraFieldsFormatter",
    "JsonLogFormatter",
    "LoggingExtraConflictError",
    "_STDLIB_LOG_RECORD_KEYS",
    "_looks_sensitive",
    "_safe_repr",
    "configure_logging",
    "content_preview",
    "correlation_scope",
    "debug_logging_enabled",
    "effective_log_level",
    "env_flag",
    "get_correlation_id",
    "mask_api_key",
    "mask_bearer_token",
    "mask_email_address",
    "mask_secrets_in_dict",
    "register_noisy_logger",
    "register_secret_keys",
    "safe_json_dumps",
    "sanitize_for_log",
    "set_correlation_id",
    "silence_noisy_loggers",
]
