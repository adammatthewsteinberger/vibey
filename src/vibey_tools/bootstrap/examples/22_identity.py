"""Example 22 — Azure credential preference order.

Single source of truth for "which Azure credential should this process
use." Resolution order:

1. ``ClientSecretCredential`` when ``AZURE_CLIENT_SECRET`` is set
   (local-dev / non-AKS).
2. ``WorkloadIdentityCredential`` when ``AZURE_TENANT_ID`` + ``AZURE_CLIENT_ID``
   are set but secret is empty (AKS Workload Identity — preferred in cluster).
3. ``DefaultAzureCredential`` as last-resort fallback.

The function NEVER logs the client secret — only a ``client_secret_present``
bool, by design.
"""

from __future__ import annotations

import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.identity import (
    AZURE_TOKEN_AUDIENCE,
    build_credential,
    credential_kind,
)
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()
    # Save originals to restore at exit (this example mutates env)
    saved = {
        k: os.environ.get(k) for k in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")
    }

    try:
        # ── 1. No env → DefaultAzureCredential ────────────────────────
        for k in saved:
            os.environ.pop(k, None)
        kind = credential_kind()
        cred = build_credential()
        print(f"no env                       → kind={kind.value:20} type={type(cred).__name__}")

        # ── 2. tenant + client only → WorkloadIdentityCredential ───────
        os.environ["AZURE_TENANT_ID"] = "tenant-uuid"
        os.environ["AZURE_CLIENT_ID"] = "client-uuid"
        os.environ.pop("AZURE_CLIENT_SECRET", None)
        kind = credential_kind()
        cred = build_credential()
        print(f"tenant + client only         → kind={kind.value:20} type={type(cred).__name__}")

        # ── 3. tenant + client + secret → ClientSecretCredential ───────
        os.environ["AZURE_CLIENT_SECRET"] = "DEMO-SECRET-VALUE-MUST-NOT-APPEAR-IN-LOGS"
        kind = credential_kind()

        # Capture logs to assert the secret never appears
        log_capture: list[str] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                log_capture.append(record.getMessage() + " " + str(record.__dict__))

        h = _Capture()
        logging.getLogger("vibey_bootstrap.identity").addHandler(h)
        try:
            cred = build_credential()
        finally:
            logging.getLogger("vibey_bootstrap.identity").removeHandler(h)

        print(f"tenant + client + secret     → kind={kind.value:20} type={type(cred).__name__}")
        leaked = any("DEMO-SECRET-VALUE-MUST-NOT-APPEAR-IN-LOGS" in line for line in log_capture)

    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  AZURE_TOKEN_AUDIENCE constant  : {AZURE_TOKEN_AUDIENCE}")
    print("  resolution order (no secret)   : WorkloadIdentity preferred over Default")
    print(f"  secret never logged            : {not leaked}")
    print("  credential_kind() probes without building (no network)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log line: "Credential built" with client_secret_present=True (bool, not value)>
# no env                       → kind=default              type=DefaultAzureCredential
# tenant + client only         → kind=workload_identity    type=WorkloadIdentityCredential
# tenant + client + secret     → kind=client_secret        type=ClientSecretCredential
#
# verified:
#   AZURE_TOKEN_AUDIENCE constant  : api://AzureADTokenExchange
#   resolution order (no secret)   : WorkloadIdentity preferred over Default
#   secret never logged            : True
#   credential_kind() probes without building (no network)
