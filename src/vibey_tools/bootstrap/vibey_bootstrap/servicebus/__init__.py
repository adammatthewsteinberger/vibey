"""Tier 3 Service Bus helpers: consumer watchdog, DLQ growth alarm, daily digest."""

from vibey_bootstrap.servicebus.async_ext import (
    MultiQueueRouter,
    ReplayGuard,
    run_async_consumer,
    service_bus_transport_type,
)
from vibey_bootstrap.servicebus.consumer import (
    record_consumer_iteration,
    record_message_settled,
    start_consumer_watchdog,
)
from vibey_bootstrap.servicebus.consumer_wrapper import (
    MessageProcessor,
    SbReceiverProtocol,
    handle_message,
)
from vibey_bootstrap.servicebus.dlq_alarm import (
    check_dlq_growth_rate,
    reset_state,
)
from vibey_bootstrap.servicebus.dlq_digest import (
    EmailRepoProtocol,
    InvalidResubmitToken,
    build_dlq_digest_body,
    issue_resubmit_token,
    run_dlq_digest,
    verify_resubmit_token,
)

__all__ = [
    "EmailRepoProtocol",
    "InvalidResubmitToken",
    "MessageProcessor",
    "MultiQueueRouter",
    "ReplayGuard",
    "SbReceiverProtocol",
    "build_dlq_digest_body",
    "check_dlq_growth_rate",
    "handle_message",
    "issue_resubmit_token",
    "record_consumer_iteration",
    "record_message_settled",
    "reset_state",
    "run_async_consumer",
    "run_dlq_digest",
    "service_bus_transport_type",
    "start_consumer_watchdog",
    "verify_resubmit_token",
]
