"""Example 44 — db + outbox + ACS email."""

from __future__ import annotations

# Requires: pip install vibey-bootstrap[db,email]
# Env: DATABASE_URL, ACS_CONNECTION_STRING, ACS_SENDER_ADDRESS
from vibey_bootstrap.db import get_sessionmaker
from vibey_bootstrap.db.outbox import Outbox, drain_outbox
from vibey_bootstrap.email import AcsEmailSender


def main() -> None:
    Session = get_sessionmaker()
    sender = AcsEmailSender()
    with Session() as session:
        outbox = Outbox(session)
        outbox.enqueue(
            idempotency_key="digest-2026-06-29",
            payload={
                "to_recipients": ["ops@example.com"],
                "subject": "Weekly digest",
                "html_body": "<p>Hello</p>",
            },
        )
        session.commit()
        sent = drain_outbox(session, sender)
        session.commit()
        print(f"drained {sent} message(s)")


if __name__ == "__main__":
    main()
