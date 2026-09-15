"""Test-suite-wide fixtures.

The ``AZURE_BOOTSTRAP_ALLOW_RESET`` env-guard is the single sentinel that
gates every test-only reset helper across the library. Setting it once at
suite startup lets tests freely call ``reset_state()`` / ``_reset_counters()``
etc. without leaking state between cases.
"""

from __future__ import annotations

import os

os.environ["AZURE_BOOTSTRAP_ALLOW_RESET"] = "1"
