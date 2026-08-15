"""Azure application port and mutation consent contracts (Milestone 10 task 10.4)."""

from __future__ import annotations

from vibey.application.interfaces import (
    AzureClientPort,
    AzureDiscoveryResult,
    AzureExecutionResult,
    AzureResourceStatus,
)


class MutationNotAuthorizedError(Exception):
    """Raised when an Azure mutation is requested without verified consent."""


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "AzureClientPort",
    "AzureDiscoveryResult",
    "AzureExecutionResult",
    "AzureResourceStatus",
    "MutationNotAuthorizedError",
]
