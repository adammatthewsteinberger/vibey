"""Service-Bus-flavored re-exports of heartbeat primitives.

The watchdog itself is generic — apps with Kafka consumers, polling cron
jobs, or Celery workers can also call ``record_consumer_iteration()`` at
the top of every loop iteration to feed it.
"""

from __future__ import annotations

from vibey_bootstrap.heartbeat import (
    record_consumer_iteration,
    record_message_settled,
    start_consumer_watchdog,
)

__all__ = [
    "record_consumer_iteration",
    "record_message_settled",
    "start_consumer_watchdog",
]
