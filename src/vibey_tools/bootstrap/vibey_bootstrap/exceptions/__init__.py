"""Project-neutral exception hierarchy for pipelined applications.

Distinct from :mod:`vibey_bootstrap.models.exceptions` (which carries the v1
``RepositoryError`` family for config-source failures). This module's tree
gives consumers an ``is_unrecoverable(exc)`` classifier so the Service Bus
consumer wrapper can route failures to dead-letter vs abandon without
hard-coding project-specific exception types.
"""

from __future__ import annotations


class PipelineError(Exception):
    """Base for any application-level pipeline failure."""


class UnrecoverableError(PipelineError):
    """Marker: this failure will never succeed on retry.

    Consumers MUST dead-letter messages whose handlers raised any subclass
    of ``UnrecoverableError``. Anything else is transient (abandon → broker
    redelivers).
    """


class InvalidMessageError(UnrecoverableError):
    """Queue payload failed schema validation."""


class OversizedAttachmentError(UnrecoverableError):
    """Attachment exceeded a configured byte cap."""


class MalformedAttachmentError(UnrecoverableError):
    """Magic-byte/MIME-type validation failed for the bytes received."""


class ZipBombError(OversizedAttachmentError):
    """Archive contains too many entries or excessive declared uncompressed size."""


class UpstreamResourceMissing(UnrecoverableError):
    """A resource expected to exist (blob, table row, secret) was 404."""


class TransientError(PipelineError):
    """Marker for known-recoverable failures.

    Not in ``UnrecoverableError``'s tree, so consumers automatically retry.
    """


class RateLimitError(TransientError):
    """HTTP 429 or equivalent — caller should back off."""


class NetworkError(TransientError):
    """Connection / timeout failure against an external service."""


class AuthenticationError(TransientError):
    """Token expired or RBAC denied.

    Marked transient because the cause is often token-cache staleness — retry
    with fresh credentials usually succeeds. Apps with hard auth failures can
    subclass and re-parent under ``UnrecoverableError`` (or register the
    subclass via :func:`register_unrecoverable`).
    """


DEFAULT_UNRECOVERABLE_TYPES: tuple[type[Exception], ...] = (UnrecoverableError,)


def is_unrecoverable(exc: BaseException) -> bool:
    """The consumer's classifier — single ``isinstance`` check."""
    return isinstance(exc, DEFAULT_UNRECOVERABLE_TYPES)


def register_unrecoverable(*types: type[Exception]) -> None:
    """Extend ``DEFAULT_UNRECOVERABLE_TYPES`` at runtime.

    Useful when the "unrecoverable" type lives in a third-party SDK and can't
    be made to inherit from :class:`UnrecoverableError` directly.
    """
    global DEFAULT_UNRECOVERABLE_TYPES
    new = list(DEFAULT_UNRECOVERABLE_TYPES)
    for t in types:
        if isinstance(t, type) and issubclass(t, BaseException) and t not in new:
            new.append(t)
    DEFAULT_UNRECOVERABLE_TYPES = tuple(new)


__all__ = [
    "AuthenticationError",
    "DEFAULT_UNRECOVERABLE_TYPES",
    "InvalidMessageError",
    "MalformedAttachmentError",
    "NetworkError",
    "OversizedAttachmentError",
    "PipelineError",
    "RateLimitError",
    "TransientError",
    "UnrecoverableError",
    "UpstreamResourceMissing",
    "ZipBombError",
    "is_unrecoverable",
    "register_unrecoverable",
]
