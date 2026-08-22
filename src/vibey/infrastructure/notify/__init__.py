# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Notification facilities for desktop alerts and webhooks."""

from vibey.infrastructure.notify.desktop import DesktopNotifier
from vibey.infrastructure.notify.events import NotificationEvent, NotificationKind
from vibey.infrastructure.notify.service import NotificationService
from vibey.infrastructure.notify.webhook import WebhookPublisher

__all__ = [
    "DesktopNotifier",
    "NotificationEvent",
    "NotificationKind",
    "NotificationService",
    "WebhookPublisher",
]
