# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""End-to-end Service Bus message handler.

Wraps the project's processor implementation with:
- JSON parse → schema validation → correlation-scope-bound processor.process
- Failure classification via :func:`is_unrecoverable` (dead-letter vs abandon)
- Best-effort ``processor.notify_failure`` before dead-letter
- ``record_message_settled`` in ``finally`` so the watchdog sees progress
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.exceptions import InvalidMessageError, is_unrecoverable
from vibey_bootstrap.heartbeat import record_message_settled
from vibey_bootstrap.logging.correlation import correlation_scope
from vibey_bootstrap.validation import MessageSchema, validate_message

_logger = logging.getLogger(__name__)


class MessageProcessor(Protocol):
    def process(self, payload: dict[str, Any]) -> None: ...
    def notify_failure(self, payload: dict[str, Any], error: Exception) -> None: ...


class SbReceiverProtocol(Protocol):
    def complete_message(self, msg: Any) -> None: ...
    def abandon_message(self, msg: Any) -> None: ...
    def dead_letter_message(self, msg: Any, *, reason: str, error_description: str) -> None: ...


def _msg_body(msg: Any) -> Any:
    """Extract the body bytes / str from a ServiceBusReceivedMessage."""
    body = getattr(msg, "body", None)
    if callable(body):
        try:
            body = body()
        except Exception:
            return None
    if hasattr(body, "__iter__") and not isinstance(body, (bytes, str)):
        try:
            body = b"".join(body)  # type: ignore[arg-type]
        except Exception:
            return None
    return body


def _settle(
    receiver: SbReceiverProtocol,
    msg: Any,
    *,
    action: str,
    reason: str | None = None,
    description: str | None = None,
) -> None:
    """Dispatch to the correct receiver method. Catches lock-lost-style errors."""
    try:
        if action == "complete":
            receiver.complete_message(msg)
        elif action == "abandon":
            receiver.abandon_message(msg)
        elif action == "dead_letter":
            receiver.dead_letter_message(
                msg,
                reason=reason or "unspecified",
                error_description=(description or "")[:200],
            )
        else:
            raise ValueError(f"unknown settle action {action!r}")
    except Exception as exc:
        _logger.warning(
            "sb._settle: %s raised %s (lock likely lost)",
            action,
            type(exc).__name__,
            extra={"action": action, "exception_type": type(exc).__name__},
        )
        try:
            from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

            alert_dev_team(
                AlertSeverity.WARN,
                subject=f"Service Bus {action} raised: {type(exc).__name__}",
                context={"action": action, "error": str(exc)[:300]},
                dedup_key=f"sb._settle:{action}:{type(exc).__name__}",
            )
        except Exception:
            pass


def handle_message(
    receiver: SbReceiverProtocol,
    msg: Any,
    processor: MessageProcessor,
    *,
    schema: MessageSchema | None = None,
    correlation_field: str = "correlation_id",
    extra_correlation_fields: tuple[str, ...] = (),
    source: str = "consumer",
    lock_renewer: Any | None = None,
    counter_namespace: str = "sb",
) -> tuple[bool, bool]:
    """Handle one received message end-to-end.

    Returns ``(processed: bool, failed: bool)``.
    """
    try:
        if lock_renewer is not None:
            try:
                lock_renewer.register_message(receiver, msg, max_lock_renewal_duration=3600)
            except Exception:
                _logger.warning("lock_renewer registration failed", exc_info=True)

        # 1. Parse JSON body
        raw = _msg_body(msg)
        try:
            if isinstance(raw, bytes):
                payload = json.loads(raw.decode("utf-8"))
            elif isinstance(raw, str):
                payload = json.loads(raw)
            else:
                raise InvalidMessageError(f"unsupported body type: {type(raw).__name__}")
        except (json.JSONDecodeError, UnicodeDecodeError, InvalidMessageError) as exc:
            bump_counter(f"{counter_namespace}.dead_lettered")
            _settle(
                receiver,
                msg,
                action="dead_letter",
                reason="invalid_json",
                description=str(exc)[:200],
            )
            return False, True

        # 2. Schema validation
        if schema is not None:
            try:
                payload = validate_message(payload, schema)
            except InvalidMessageError as exc:
                bump_counter(f"{counter_namespace}.dead_lettered")
                _settle(
                    receiver,
                    msg,
                    action="dead_letter",
                    reason=type(exc).__name__,
                    description=str(exc)[:200],
                )
                return False, True

        # 3. Correlation context + processor invocation
        fields: dict[str, str] = {}
        for name in extra_correlation_fields:
            value = payload.get(name)
            if isinstance(value, str) and value:
                fields[name] = value
        cid = payload.get(correlation_field) if isinstance(payload, dict) else None

        with correlation_scope(cid if isinstance(cid, str) and cid else None, **fields):
            try:
                processor.process(payload)
            except BaseException as exc:
                if is_unrecoverable(exc):
                    bump_counter(f"{counter_namespace}.dead_lettered")
                    try:
                        processor.notify_failure(payload, exc)  # type: ignore[arg-type]
                    except Exception:
                        _logger.exception(
                            "processor.notify_failure raised — proceeding with dead-letter"
                        )
                    _settle(
                        receiver,
                        msg,
                        action="dead_letter",
                        reason=type(exc).__name__,
                        description=str(exc)[:200],
                    )
                    try:
                        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                        alert_dev_team(
                            AlertSeverity.ERROR,
                            subject=(f"SB dead-lettered ({source}): {type(exc).__name__}"),
                            context={
                                "exception_type": type(exc).__name__,
                                "error": str(exc)[:300],
                            },
                            dedup_key=f"sb.dead_lettered:{type(exc).__name__}",
                        )
                    except Exception:
                        pass
                    return False, True

                # Transient: abandon
                bump_counter(f"{counter_namespace}.abandoned")
                _settle(receiver, msg, action="abandon")
                try:
                    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                    alert_dev_team(
                        AlertSeverity.ERROR,
                        subject=(f"SB abandoned ({source}): {type(exc).__name__}"),
                        context={
                            "exception_type": type(exc).__name__,
                            "error": str(exc)[:300],
                        },
                        dedup_key=f"sb.abandoned:{type(exc).__name__}",
                    )
                except Exception:
                    pass
                return False, True

            # 4. Success
            bump_counter(f"{counter_namespace}.completed")
            _settle(receiver, msg, action="complete")
            return True, False
    finally:
        if lock_renewer is not None:
            try:
                lock_renewer.close()
            except Exception:
                pass
        record_message_settled()


__all__ = [
    "MessageProcessor",
    "SbReceiverProtocol",
    "handle_message",
]
