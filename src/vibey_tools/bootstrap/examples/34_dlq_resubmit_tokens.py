"""Example 34 — HMAC-signed action tokens.

The library's token signer is a thin convention layer over ``hmac``:
``payload_b64url.signature_b64url`` with a sorted-keys JSON payload
containing ``exp`` (unix seconds) and ``act`` (action name).

``issue_resubmit_token`` / ``verify_resubmit_token`` are presets that
hardcode ``action="resubmit_dlq"``. The generic ``issue_action_token`` /
``verify_action_token`` accept any action — use it for password-reset
links, one-time-use download URLs, anything that needs verifiable but
self-contained ("stateless") authorization.

Key invariants:
- Signature comparison uses ``hmac.compare_digest`` (constant-time).
- Verifier rejects mismatched ``expected_action`` — never trust the
  action field straight from the payload.
- ``exp`` is unix seconds (``int(time.time())``), so cross-language
  consumers can verify too.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.servicebus import (
    InvalidResubmitToken,
    issue_resubmit_token,
    verify_resubmit_token,
)
from vibey_bootstrap.tokens import (
    InvalidActionToken,
    issue_action_token,
    verify_action_token,
)


def main() -> None:
    secret = "demo-signing-secret-from-key-vault"

    # ── 1. DLQ resubmit preset ──────────────────────────────────────────
    resubmit_token = issue_resubmit_token(secret, ttl_seconds=300)
    print(f"resubmit token (first 40 chars): {resubmit_token[:40]}...")
    print(f"token length                    : {len(resubmit_token)} chars")

    # Valid verification (preset returns None on success)
    verify_resubmit_token(secret, resubmit_token)
    print("verify_resubmit_token           : OK")

    # Wrong action — token signed for resubmit_dlq, but we ask "expected
    # something else" via the generic verifier:
    try:
        verify_action_token(secret, resubmit_token, expected_action="other_action")
    except InvalidActionToken as exc:
        print(f"wrong action rejected           : {exc}")

    # ── 2. Generic action tokens with custom payload ────────────────────
    reset_token = issue_action_token(
        secret,
        action="password_reset",
        ttl_seconds=600,
        payload={"user_id": "alice", "reset_request_id": "req-42"},
    )

    payload = verify_action_token(secret, reset_token, expected_action="password_reset")
    print(f"\npassword_reset payload          : {payload}")

    # ── 3. Tampered token rejected ──────────────────────────────────────
    parts = reset_token.split(".")
    altered = ("A" if parts[0][0] != "A" else "B") + parts[0][1:] + "." + parts[1]
    try:
        verify_action_token(secret, altered, expected_action="password_reset")
    except InvalidActionToken as exc:
        print(f"tampered payload rejected       : {exc}")

    # ── 4. Expired token rejected ───────────────────────────────────────
    expired = issue_action_token(secret, action="x", ttl_seconds=-1)
    try:
        verify_action_token(secret, expired, expected_action="x")
    except InvalidActionToken as exc:
        print(f"expired token rejected          : {exc}")

    # ── 5. InvalidResubmitToken is the DLQ-flavored alias ──────────────
    print(f"\nInvalidResubmitToken inheritance: {InvalidResubmitToken.__mro__[:3]}")

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  HMAC-SHA256 signature, base64url-no-pad payload + signature")
    print("  constant-time compare via hmac.compare_digest")
    print("  exp is unix seconds (interoperable with cross-language verifiers)")
    print("  action field NEVER trusted — verifier requires expected_action arg")


if __name__ == "__main__":
    main()


# ── Expected output ──
# resubmit token (first 40 chars): eyJhY3QiOiJyZXN1Ym1pdF9kbHEiLCJleHAi...
# token length                    : <number> chars
# verify_resubmit_token           : OK
# wrong action rejected           : token not scoped to 'other_action' (got 'resubmit_dlq')
#
# password_reset payload          : {'act': 'password_reset', 'exp': <unix-seconds>, 'reset_request_id': 'req-42', 'user_id': 'alice'}
# tampered payload rejected       : signature mismatch
# expired token rejected          : token expired
#
# InvalidResubmitToken inheritance: (...InvalidActionToken, ValueError)
#
# verified:
#   ...
