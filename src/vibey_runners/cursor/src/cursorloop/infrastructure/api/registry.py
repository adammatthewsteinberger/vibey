# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Pinned Cloud Agents OpenAPI digest and registered operation ids."""

from __future__ import annotations

from pathlib import Path

SPEC_FILENAME = "cloud-agents-openapi.yaml"
SPEC_PATH = Path(__file__).with_name(SPEC_FILENAME)

# SHA-256 of SPEC_PATH contents. Bump deliberately when re-vendoring.
VENDORED_SPEC_DIGEST = "7fd1760d7849aa0ea77269bcd819a4ebcff68c0427bba71145133ef3a117dade"

# Every operationId in the vendored sketch must appear here. Removals fail the
# drift gate so silent shrinkage cannot ship.
REGISTERED_OPERATIONS: frozenset[str] = frozenset(
    {
        "getMe",
        "listModels",
        "createAgent",
        "getAgent",
        "deleteAgent",
        "cancelAgent",
    }
)

# Explicitly partial / deferred surface — see ADR-0006.
PARTIAL_OPERATIONS: frozenset[str] = frozenset(
    {
        "getMe",
        "listModels",
        "createAgent",
        "getAgent",
        "cancelAgent",
    }
)

DEFERRED_REASON = (
    "Cloud Agents full REST binder is deferred (ADR-0006). Only the runner-"
    "needed subset is sketched; regenerate from a stable published OpenAPI "
    "before claiming completeness."
)
