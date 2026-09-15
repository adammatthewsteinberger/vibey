"""Tier 1 tracing primitives: @traced decorator, latency histograms, slow thresholds."""

from vibey_bootstrap.tracing.decorators import traced, traced_async
from vibey_bootstrap.tracing.latency import (
    _record_latency,
    latency_snapshot,
    reset_latency_state,
)
from vibey_bootstrap.tracing.log_exception_context import log_exception_context
from vibey_bootstrap.tracing.slow_thresholds import (
    default_slow_threshold,
    register_slow_threshold,
    reset_slow_thresholds,
)
from vibey_bootstrap.tracing.timed_operation import timed_operation

__all__ = [
    "_record_latency",
    "default_slow_threshold",
    "latency_snapshot",
    "log_exception_context",
    "register_slow_threshold",
    "reset_latency_state",
    "reset_slow_thresholds",
    "timed_operation",
    "traced",
    "traced_async",
]
