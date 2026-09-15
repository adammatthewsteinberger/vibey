"""Sender-facing throttling + two-tier notification builders."""

from vibey_bootstrap.notify.templates import (
    UnprocessableReason,
    build_failure_alert_body,
    build_unprocessable_notification,
    build_validation_notice_body,
)
from vibey_bootstrap.notify.throttle import (
    NOTIFY_SENDER_MAX_PER_HOUR_DEFAULT,
    NOTIFY_SENDER_WINDOW_SECONDS_DEFAULT,
    reset_sender_notification_throttle,
    should_notify_sender,
)

__all__ = [
    "NOTIFY_SENDER_MAX_PER_HOUR_DEFAULT",
    "NOTIFY_SENDER_WINDOW_SECONDS_DEFAULT",
    "UnprocessableReason",
    "build_failure_alert_body",
    "build_unprocessable_notification",
    "build_validation_notice_body",
    "reset_sender_notification_throttle",
    "should_notify_sender",
]
