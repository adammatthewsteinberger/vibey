"""Example 08 — Exception hierarchy + is_unrecoverable.

The v2 exception tree gives consumers an ``is_unrecoverable(exc)`` classifier
so the Service Bus consumer wrapper can route failures to dead-letter vs
abandon without hard-coding project-specific exception types.

Tree:
    PipelineError
    ├── UnrecoverableError (dead-letter)
    │   ├── InvalidMessageError
    │   ├── OversizedAttachmentError
    │   │   └── ZipBombError
    │   ├── MalformedAttachmentError
    │   └── UpstreamResourceMissing
    └── TransientError (abandon → retry)
        ├── RateLimitError
        ├── NetworkError
        └── AuthenticationError

Apps subclass either marker; for SDK exceptions that can't be re-parented,
``register_unrecoverable(*types)`` extends the classifier's tuple.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.exceptions import (
    InvalidMessageError,
    NetworkError,
    OversizedAttachmentError,
    RateLimitError,
    TransientError,
    UnrecoverableError,
    ZipBombError,
    is_unrecoverable,
    register_unrecoverable,
)


# ── App-specific subclass — automatically dead-letter-worthy ─────────────
class MyProjectInvariantViolation(UnrecoverableError):
    """Something we believed could never be wrong was wrong."""


# ── Project-specific transient (e.g. flaky upstream API) ─────────────────
class MyUpstreamFlap(TransientError):
    """Upstream said 503; retry usually fixes."""


# ── Third-party exception we can't re-parent (e.g. azure.servicebus's
# ServiceBusError might be unrecoverable in our project's domain) ────────
class ThirdPartySdkBug(Exception):
    """Imagine this came from an SDK we don't control."""


def main() -> None:
    print()
    print("classifier results:")
    for exc in [
        InvalidMessageError("malformed payload"),
        OversizedAttachmentError("200 MB attachment"),
        ZipBombError("10k entries"),
        MyProjectInvariantViolation("subscription mismatch"),
        NetworkError("connection reset"),
        RateLimitError("429 from Graph"),
        MyUpstreamFlap("503 from upstream"),
        ValueError("random bug"),  # not classified
    ]:
        verdict = "DEAD-LETTER" if is_unrecoverable(exc) else "ABANDON / retry"
        print(f"  {type(exc).__name__:32} → {verdict}")

    # ── Extend the registry with a third-party type ───────────────────
    print()
    print("after register_unrecoverable(ThirdPartySdkBug):")
    before = is_unrecoverable(ThirdPartySdkBug("x"))
    register_unrecoverable(ThirdPartySdkBug)
    after = is_unrecoverable(ThirdPartySdkBug("x"))
    print(f"  before: {before}")
    print(f"  after : {after}")

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  Invalid/Oversized/Zip/MyProjectInvariant → unrecoverable")
    print("  Network/RateLimit/MyUpstreamFlap          → transient")
    print("  Unclassified ValueError                   → transient (consumer retries)")
    print(f"  register_unrecoverable() escalation       → {not before and after}")


if __name__ == "__main__":
    main()


# ── Expected output ──
# classifier results:
#   InvalidMessageError              → DEAD-LETTER
#   OversizedAttachmentError         → DEAD-LETTER
#   ZipBombError                     → DEAD-LETTER
#   MyProjectInvariantViolation      → DEAD-LETTER
#   NetworkError                     → ABANDON / retry
#   RateLimitError                   → ABANDON / retry
#   MyUpstreamFlap                   → ABANDON / retry
#   ValueError                       → ABANDON / retry
#
# after register_unrecoverable(ThirdPartySdkBug):
#   before: False
#   after : True
#
# verified:
#   ...
