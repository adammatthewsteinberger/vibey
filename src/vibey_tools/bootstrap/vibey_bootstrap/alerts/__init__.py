"""Tier 2 tiered-alert dispatcher.

Apps register a sender (any callable matching ``AlertSender``) at startup,
then code anywhere in the app can fire ``alert_dev_team(...)`` — the
dispatcher handles dedup, rate-limit, escalation, and HTML rendering.
"""

from vibey_bootstrap.alerts.dispatcher import (
    AlertRecord,
    AlertSender,
    AlertSeverity,
    alert_dev_team,
    drain_pending_alerts,
    install_global_exception_hooks,
    register_dispatcher,
    reset_state,
)
from vibey_bootstrap.alerts.render import (
    _render_alert_html,
    render_pending_alerts_html,
)
from vibey_bootstrap.counters import bump_counter, counter_snapshot

__all__ = [
    "AlertRecord",
    "AlertSender",
    "AlertSeverity",
    "alert_dev_team",
    "bump_counter",
    "counter_snapshot",
    "drain_pending_alerts",
    "install_global_exception_hooks",
    "register_dispatcher",
    "render_pending_alerts_html",
    "reset_state",
]
