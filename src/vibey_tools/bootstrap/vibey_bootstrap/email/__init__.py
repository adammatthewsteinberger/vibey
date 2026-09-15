"""Azure Communication Services email sender."""

from __future__ import annotations

import logging
from typing import Any

from vibey_bootstrap.failclose import require_env

_logger = logging.getLogger(__name__)


class AcsEmailSender:
    """Transactional email sender via Azure Communication Services."""

    def __init__(
        self,
        *,
        connection_string: str | None = None,
        sender_address: str | None = None,
    ) -> None:
        self._connection_string = connection_string or require_env("ACS_CONNECTION_STRING")
        self._sender = sender_address or require_env("ACS_SENDER_ADDRESS")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from azure.communication.email import EmailClient  # type: ignore[import-untyped]

            self._client = EmailClient.from_connection_string(self._connection_string)
        return self._client

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        html_body: str,
        plain_text: str | None = None,
    ) -> str:
        """Send an email; returns message id on success."""
        message: dict[str, Any] = {
            "senderAddress": self._sender,
            "recipients": {"to": [{"address": addr} for addr in to]},
            "content": {"subject": subject, "html": html_body},
        }
        if plain_text:
            message["content"]["plainText"] = plain_text
        poller = (
            self._client.begin_send(message)
            if self._client
            else self._get_client().begin_send(message)
        )
        result = poller.result()
        msg_id = getattr(result, "id", None) or getattr(result, "message_id", "unknown")
        _logger.info("ACS email sent id=%s to=%s", msg_id, to)
        return str(msg_id)

    def __call__(self, payload: dict[str, Any]) -> None:
        """Outbox-compatible sender_fn."""
        self.send(
            to=list(payload.get("to_recipients") or payload.get("to") or []),
            subject=str(payload.get("subject", "")),
            html_body=str(payload.get("html_body") or payload.get("body", "")),
            plain_text=payload.get("plain_text"),
        )


__all__ = ["AcsEmailSender"]
