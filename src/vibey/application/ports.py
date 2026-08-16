"""Backwards-compatible re-export of `application.interfaces`.

The Protocols moved into `application/interfaces/` so every seam lives in one
discoverable place. This shim keeps `from vibey.application.ports import X`
working; new code should import from `vibey.application.interfaces`.
"""

from __future__ import annotations

from vibey.application.interfaces import (
    BriefProducer,
    Clock,
    EngineAdapter,
    EngineHealthRepository,
    HumanGateRepository,
    JobReadyNotifier,
    JobRepository,
)

__all__ = [
    "BriefProducer",
    "Clock",
    "EngineAdapter",
    "EngineHealthRepository",
    "HumanGateRepository",
    "JobReadyNotifier",
    "JobRepository",
]
