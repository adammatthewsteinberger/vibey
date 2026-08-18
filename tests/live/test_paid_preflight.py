"""Paid-mode preflight: runs `<engine> --version` and `<engine> doctor`
against real installed binaries. Requires actual API keys in the
environment for auth checks to pass.

Run with: pytest -m paid tests/live/test_paid_preflight.py
"""

import shutil

import pytest

from vibey.infrastructure.engines.descriptors import ALL_DESCRIPTORS
from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter


@pytest.mark.paid
@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
async def test_preflight_detects_installed_engine(
    descriptor,  # type: ignore[no-untyped-def]
) -> None:
    """If the binary is on PATH, preflight reports installed=True and a version."""
    if shutil.which(descriptor.binary) is None:
        pytest.skip(f"{descriptor.binary} not installed")

    adapter = LoopProcessAdapter(descriptor=descriptor)
    result = await adapter.preflight()

    assert result.installed is True
    assert result.version is not None


@pytest.mark.paid
@pytest.mark.parametrize("descriptor", ALL_DESCRIPTORS, ids=lambda d: d.engine_id.value)
async def test_preflight_auth_env_present_reports_version(
    descriptor,  # type: ignore[no-untyped-def]
) -> None:
    """If the binary is installed AND the required auth env vars are set,
    preflight should report installed=True and a version string."""
    import os

    if shutil.which(descriptor.binary) is None:
        pytest.skip(f"{descriptor.binary} not installed")
    if not any(os.getenv(var) for var in descriptor.auth_env):
        pytest.skip(f"no auth env vars set: {descriptor.auth_env}")

    adapter = LoopProcessAdapter(descriptor=descriptor)
    result = await adapter.preflight()

    assert result.installed is True
    assert result.version is not None
    assert result.auth_ok is True
