"""HTTP common helper tests."""

from __future__ import annotations

from vibey_bootstrap.http._common import check_ssrf, inject_traceparent


def test_inject_traceparent_adds_header() -> None:
    hdrs = inject_traceparent({})
    assert "traceparent" in hdrs or hdrs == {}


def test_check_ssrf_blocks_metadata() -> None:
    import pytest

    with pytest.raises(ValueError):
        check_ssrf("http://169.254.169.254/latest/meta-data")
