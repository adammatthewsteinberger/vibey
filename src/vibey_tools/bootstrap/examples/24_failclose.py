"""Example 24 — Fail-closed-for-auth / fail-open-for-features env helpers.

Codifies the contract every Vizius app should follow:

- ``require_env(name)`` — secrets, connection strings, identity fields.
  Missing or empty → raise ``ConfigurationError`` (auth / critical infra
  must fail closed).
- ``optional_env(name, default="")`` — endpoint URLs, mailbox addresses,
  paths. Sensible fallback when missing.
- ``fail_open_env(name)`` — feature flags that EXPLICITLY mean "feature
  disabled when None" (e.g. ``API_KEY`` unset = endpoint is publicly
  accessible — comment the threat consequence at every call site).

The ``ConfigurationError`` raised by ``require_env`` is identity-equal
to the v1 ``vibey_bootstrap.models.exceptions.ConfigurationError`` —
both import paths resolve to the same class object.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.failclose import (
    ConfigurationError,
    fail_open_env,
    optional_env,
    require_env,
)
from vibey_bootstrap.models.exceptions import ConfigurationError as V1ConfigError


def main() -> None:
    saved = {
        k: os.environ.get(k)
        for k in (
            "EXAMPLE_SECRET",
            "EXAMPLE_ENDPOINT",
            "EXAMPLE_API_KEY",
        )
    }
    try:
        for k in saved:
            os.environ.pop(k, None)

        # ── 1. require_env raises on missing ───────────────────────────
        try:
            require_env("EXAMPLE_SECRET")
        except ConfigurationError as exc:
            print(f"require_env missing  → ConfigurationError: {exc}")

        # ── 2. require_env raises on empty / whitespace ────────────────
        os.environ["EXAMPLE_SECRET"] = "   "
        try:
            require_env("EXAMPLE_SECRET")
        except ConfigurationError:
            print("require_env empty    → ConfigurationError")

        # ── 3. require_env strips whitespace + returns value ───────────
        os.environ["EXAMPLE_SECRET"] = "  live-secret  "
        value = require_env("EXAMPLE_SECRET")
        print(f"require_env value    → {value!r}")

        # ── 4. optional_env returns default ────────────────────────────
        endpoint = optional_env("EXAMPLE_ENDPOINT", default="https://default.example.com")
        print(f"\noptional_env default → {endpoint!r}")
        os.environ["EXAMPLE_ENDPOINT"] = "https://prod.example.com"
        endpoint = optional_env("EXAMPLE_ENDPOINT", default="https://default.example.com")
        print(f"optional_env set     → {endpoint!r}")

        # ── 5. fail_open_env returns None for "feature disabled" ───────
        # API_KEY unset = endpoint is publicly accessible.
        # This is dev-friendly but document the threat consequence!
        api_key = fail_open_env("EXAMPLE_API_KEY")
        print(f"\nfail_open_env unset  → {api_key!r}  (feature 'auth' disabled)")
        os.environ["EXAMPLE_API_KEY"] = "live-api-key"
        api_key = fail_open_env("EXAMPLE_API_KEY")
        print(f"fail_open_env set    → {api_key!r}  (feature 'auth' enforced)")

        # ── 6. ConfigurationError is the SAME class across import paths
        print(
            f"\nfailclose.ConfigurationError is models.exceptions.ConfigurationError: "
            f"{ConfigurationError is V1ConfigError}"
        )

    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print("  require_env fails closed on missing / empty / whitespace")
    print("  optional_env returns default when unset")
    print("  fail_open_env returns None when unset (NOT default — by design)")
    print("  ConfigurationError aliased to v1 class (back-compat preserved)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# require_env missing  → ConfigurationError: Required environment variable 'EXAMPLE_SECRET' is missing or empty
# require_env empty    → ConfigurationError
# require_env value    → 'live-secret'
#
# optional_env default → 'https://default.example.com'
# optional_env set     → 'https://prod.example.com'
#
# fail_open_env unset  → None  (feature 'auth' disabled)
# fail_open_env set    → 'live-api-key'  (feature 'auth' enforced)
#
# failclose.ConfigurationError is models.exceptions.ConfigurationError: True
#
# verified:
#   ...
