"""The remaining small branches across the library.

Grouped by module rather than by theme, because what is left is mostly the defensive
edges: unreachable-looking guards, optional-dependency paths, and the ``except`` arms that
exist so a helper cannot take down its caller.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
import socket
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap import aks as aks_mod
from vibey_bootstrap import audit as audit_mod
from vibey_bootstrap import metrics as metrics_mod
from vibey_bootstrap import pdf_safety
from vibey_bootstrap.counters import _reset_counters, bump_counter, counter_snapshot
from vibey_bootstrap.http import _common as http_common
from vibey_bootstrap.logging import correlation, masking
from vibey_bootstrap.logging.jsonformatter import JsonLogFormatter
from vibey_bootstrap.tracing import latency as latency_mod


@pytest.fixture(autouse=True)
def counters():
    _reset_counters()


# ═══════════════════════════════════════════════════════════════ aks


def test_the_sigterm_handler_sets_the_stop_event(caplog):
    stop = threading.Event()
    previous = signal.getsignal(signal.SIGTERM)
    try:
        aks_mod.install_sigterm_handler(stop)
        with caplog.at_level(logging.INFO):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
    finally:
        signal.signal(signal.SIGTERM, previous)
    assert stop.is_set()
    assert "SIGTERM received" in caplog.text


async def test_the_async_sigterm_handler_sets_its_event(caplog):
    stop = aks_mod.setup_async_sigterm_handler()
    loop = asyncio.get_running_loop()
    try:
        with caplog.at_level(logging.INFO):
            loop.call_soon(lambda: os.kill(os.getpid(), signal.SIGTERM))
            await asyncio.wait_for(stop.wait(), timeout=2.0)
    finally:
        loop.remove_signal_handler(signal.SIGTERM)
    assert stop.is_set()


def test_the_keda_metric_reads_a_counter():
    bump_counter("queue_depth", 7)
    assert aks_mod.keda_metric_value() == 7.0
    assert aks_mod.keda_metric_value("never_bumped") == 0.0


def test_the_build_info_route_serves_the_build_info():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    aks_mod.mount_build_info_route(app)
    body = TestClient(app).get("/api/version").json()
    assert set(body) == set(aks_mod.build_info())


def test_pod_context_comes_from_the_downward_api(monkeypatch):
    monkeypatch.setenv("POD_NAME", "worker-abc")
    assert aks_mod.pod_context_extra()["pod_name"] == "worker-abc"


def test_a_leader_election_cycle_that_fails_is_only_logged(caplog, monkeypatch):
    from vibey_bootstrap.aks.leader_election import LeaderElection

    election = LeaderElection(configmap_name="leases", identity="me", lease_seconds=1)
    monkeypatch.setattr(
        election, "_try_acquire", MagicMock(side_effect=RuntimeError("lease store is down"))
    )
    with caplog.at_level(logging.DEBUG):
        election.start()
        time.sleep(0.2)
        election.stop()
    assert "leader election cycle failed" in caplog.text
    assert election.is_leader is False


# ═══════════════════════════════════════════════════════════════ audit


def test_the_audit_field_helpers_delegate_to_masking():
    assert audit_mod.mask_email_field("someone@example.com") == "***ne@example.com"
    # Only the fields named in AUDIT_TRUNCATED_FIELDS are capped; anything else passes through.
    assert audit_mod.truncate_field("subject", "x" * 5000).endswith("...[truncated]")
    assert audit_mod.truncate_field("note", "x" * 5000) == "x" * 5000


def test_an_empty_chain_is_trivially_intact():
    assert audit_mod.verify_chain([]) is True


def test_a_broken_link_is_detected_and_counted(caplog):
    from dataclasses import replace

    chain = audit_mod.AuditChain(storage_fn=lambda rec: None)
    first = chain.append_chained(event_type="LOGIN", actor="a", resource="r", detail={})
    second = chain.append_chained(event_type="EXPORT", actor="a", resource="r", detail={})

    tampered = replace(second, prev_hash="not the previous hash")
    with caplog.at_level(logging.WARNING):
        assert audit_mod.verify_chain([first, tampered]) is False
    assert counter_snapshot()["audit.chain.tamper_detected"] == 1
    assert chain.verify_chain([first, second]) is True


# ═══════════════════════════════════════════════════════════════ hmac


def test_a_prefixed_signature_header_is_accepted():
    import hashlib
    import hmac as hmac_lib

    from vibey_bootstrap.auth.hmac import verify_hmac_signature

    body = b'{"a":1}'
    digest = hmac_lib.new(b"secret", body, hashlib.sha256).hexdigest()
    # No `sha256=` prefix, but an `=` is present: everything after it is the signature.
    assert verify_hmac_signature("secret", body, f"v1={digest}") is True


# ═══════════════════════════════════════════════════════════ counters


def test_a_counter_bump_with_an_unusable_amount_is_swallowed():
    bump_counter("x", "not a number")  # type: ignore[arg-type]
    assert "x" not in counter_snapshot()


# ═══════════════════════════════════════════════════════════ http


def test_ssrf_screening_rejects_a_private_address(monkeypatch):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda host, port: [(None, None, None, None, ("10.0.0.5", 0))]
    )
    with pytest.raises(ValueError, match="SSRF blocked private address"):
        http_common.check_ssrf("https://internal.example.com/x")


def test_ssrf_screening_allows_a_public_address(monkeypatch):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda host, port: [(None, None, None, None, ("93.184.216.34", 0))]
    )
    http_common.check_ssrf("https://example.com/x")


def test_ssrf_screening_can_be_told_to_allow_private_hosts():
    http_common.check_ssrf("https://internal.example.com/x", allow_private=True)


def test_a_host_that_does_not_resolve_is_left_to_the_request_to_fail(monkeypatch):
    monkeypatch.setattr(
        socket, "getaddrinfo", MagicMock(side_effect=socket.gaierror("no such host"))
    )
    http_common.check_ssrf("https://nonexistent.invalid/x")


def test_a_pem_without_a_begin_marker_has_its_whitespace_normalised():
    from vibey_bootstrap.http import normalize_pem

    assert normalize_pem("aaa bbb\tccc") == "aaa\nbbb\nccc"


async def test_an_async_client_this_module_created_is_closed_again(monkeypatch):
    from vibey_bootstrap.http import async_client

    async def request(*a, **kw):
        return "response"

    closed: list[bool] = []

    async def aclose():
        closed.append(True)

    client = MagicMock(request=request, aclose=aclose)
    monkeypatch.setattr(async_client, "build_async_client", lambda: client)
    monkeypatch.setattr(http_common, "check_ssrf", lambda url, allow_private=False: None)

    assert await async_client.async_request_with_retry("get", "https://example.com") == "response"
    assert closed == [True]


# ═══════════════════════════════════════════════════════════ logging


def test_an_email_whose_domain_is_missing_is_fully_masked():
    assert masking.mask_email_address("someone@") == "***"


def test_correlation_scope_ignores_keys_with_no_value():
    with correlation.correlation_scope("cid", tenant=None, region="eu"):
        assert correlation.get_correlation_id() == "cid"


def test_a_context_var_that_cannot_be_reset_does_not_break_the_scope(monkeypatch):
    """A token minted in another Context makes reset() raise; the scope must still exit.

    Deliberately leaves the context vars dirty, so this restores them by hand — a
    leaked correlation id would show up in unrelated tests as a phantom field.
    """
    real_var_for = correlation._var_for
    before = {name: var.get() for name, var in correlation._VARS.items()}

    class Brittle:
        def __init__(self, inner):
            self._inner = inner

        def set(self, value):
            self._inner.set(value)
            return "a token from another context"

        def get(self, *a):
            return self._inner.get(*a)

        def reset(self, token):
            raise ValueError("token was created in a different Context")

    monkeypatch.setattr(correlation, "_var_for", lambda name: Brittle(real_var_for(name)))
    try:
        with correlation.correlation_scope("cid", tenant="acme"):
            pass  # exiting must not raise
    finally:
        monkeypatch.undo()
        for name, var in correlation._VARS.items():
            var.set(before.get(name))
    assert correlation.get_correlation_id() is None


def test_the_correlation_filter_survives_an_unwritable_record(monkeypatch):
    record = logging.LogRecord("svc", logging.INFO, __file__, 1, "m", None, None)

    class Locked(dict):
        def __setitem__(self, key, value):
            raise RuntimeError("record is frozen")

    monkeypatch.setattr(record, "__dict__", Locked(record.__dict__), raising=False)
    with correlation.correlation_scope("cid"):
        assert correlation.CorrelationFilter().filter(record) is True


def test_strict_debug_checking_reads_the_usual_truthy_spellings(monkeypatch):
    from vibey_bootstrap.logging.formatter import _debug_strict_check_enabled

    monkeypatch.setenv("DEBUG_LOGGING_ENABLED", "yes")
    assert _debug_strict_check_enabled() is True
    monkeypatch.setenv("DEBUG_LOGGING_ENABLED", "off")
    assert _debug_strict_check_enabled() is False


def test_a_payload_json_cannot_encode_falls_back_to_the_safe_dumper(monkeypatch):
    record = logging.LogRecord("svc", logging.INFO, __file__, 1, "m", None, None)
    with patch(
        "vibey_bootstrap.logging.jsonformatter.json.dumps",
        side_effect=RuntimeError("encoder exploded"),
    ):
        rendered = JsonLogFormatter().format(record)
    assert "m" in rendered


def test_noise_suppression_skips_blanks_and_duplicates():
    from vibey_bootstrap.logging.noise import silence_noisy_loggers

    silence_noisy_loggers(
        "vibey.test.noisy", "", "vibey.test.noisy", include_defaults=False, level=logging.ERROR
    )
    assert logging.getLogger("vibey.test.noisy").level == logging.ERROR


# ═══════════════════════════════════════════════════════════ metrics


@pytest.mark.parametrize(
    "target", ["usage_snapshot", "bootstrap_initialized", "_last_settle_age_seconds"]
)
def test_one_broken_source_does_not_empty_the_metrics_snapshot(monkeypatch, target):
    module = {
        "usage_snapshot": "vibey_bootstrap.openai",
        "bootstrap_initialized": "vibey_bootstrap.bootstrap",
        "_last_settle_age_seconds": "vibey_bootstrap.heartbeat",
    }[target]
    with patch(f"{module}.{target}", side_effect=RuntimeError("source is down")):
        snapshot = metrics_mod.build_metrics_snapshot()
    assert isinstance(snapshot, dict)


# ═══════════════════════════════════════════════════════════ pdf_safety


def test_a_field_that_cannot_be_scrubbed_is_skipped():
    class Hostile:
        def __contains__(self, key):
            raise RuntimeError("indirect object is unresolvable")

        def __iter__(self):
            raise RuntimeError("not iterable either")

    reader = MagicMock()
    reader.trailer = {"/Root": {"/AcroForm": {"/Fields": Hostile()}}}
    reader.pages = []
    assert pdf_safety.sanitize_pdf_for_passthrough(reader) is reader  # must not raise


def test_an_annotation_list_item_that_cannot_be_scrubbed_is_skipped():
    class HostileAnnot:
        def get_object(self):
            raise RuntimeError("broken xref")

        def __contains__(self, key):
            raise RuntimeError("also broken")

    reader = MagicMock()
    reader.trailer = {"/Root": {}}
    reader.pages = [{"/Annots": [HostileAnnot()]}]
    pdf_safety.sanitize_pdf_for_passthrough(reader)  # must not raise


# ═══════════════════════════════════════════════════════════ path_safety


def test_an_unresolvable_root_is_a_configuration_error(monkeypatch):
    from vibey_bootstrap.path_safety import confine_to_root

    monkeypatch.setattr(Path, "resolve", MagicMock(side_effect=OSError("too many symlinks")))
    with pytest.raises(ValueError, match="allowed_root could not be resolved"):
        confine_to_root("f.txt", allowed_root="/data")


def test_an_unresolvable_candidate_path_is_rejected(monkeypatch, tmp_path):
    from vibey_bootstrap.path_safety import confine_to_root

    real_resolve = Path.resolve
    calls = {"n": 0}

    def resolve(self, *a, **kw):
        calls["n"] += 1
        if calls["n"] > 1:
            raise OSError("too many symlinks")
        return real_resolve(self, *a, **kw)

    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="path could not be resolved"):
        confine_to_root("f.txt", allowed_root=str(tmp_path))


# ═══════════════════════════════════════════════════════════ ratelimit


def test_a_negative_budget_is_refused():
    from vibey_bootstrap.ratelimit import TokenBucket

    with pytest.raises(ValueError, match="non-negative"):
        TokenBucket(budget=-1.0, refill_per_second=1.0)


def test_a_bucket_reports_its_name_and_budget():
    from vibey_bootstrap.ratelimit import TokenBucket

    bucket = TokenBucket(budget=5.0, refill_per_second=1.0, name="b")
    assert (bucket.name, bucket.budget) == ("b", 5.0)


def test_the_presets_match_their_documented_shapes():
    from vibey_bootstrap.ratelimit import admin_bucket, webhook_bucket

    assert webhook_bucket().budget == 240.0
    assert admin_bucket().budget == 30.0


def test_an_unknown_unit_is_allowed_unless_the_limiter_fails_closed(monkeypatch):
    from vibey_bootstrap.ratelimit import MultiUnitLimiter

    monkeypatch.delenv("RATE_LIMIT_FAIL_CLOSED", raising=False)
    assert MultiUnitLimiter(limits={"pages": (10.0, 1.0)}).allow("chars") is True

    monkeypatch.setenv("RATE_LIMIT_FAIL_CLOSED", "1")
    assert MultiUnitLimiter(limits={"pages": (10.0, 1.0)}).allow("chars") is False


# ═══════════════════════════════════════════════════════════ latency


def test_latency_ignores_an_operation_with_no_name():
    latency_mod.reset_latency_state()
    latency_mod._record_latency("", 1.0, error=False, slow=False)
    assert latency_mod.latency_snapshot() == {}


def test_recording_latency_never_raises_even_when_the_store_is_broken(monkeypatch):
    broken = MagicMock()
    broken.__enter__ = MagicMock(side_effect=RuntimeError("lock is wedged"))
    broken.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(latency_mod, "_HIST_LOCK", broken)
    latency_mod._record_latency("op", 1.0, error=False, slow=False)  # must not raise


def test_the_percentile_of_nothing_is_zero():
    assert latency_mod._percentile([], 0.95) == 0.0


def test_operations_with_no_samples_are_left_out_of_the_snapshot():
    latency_mod.reset_latency_state()
    latency_mod._record_latency("op", 1.0, error=False, slow=False)
    with latency_mod._HIST_LOCK:
        latency_mod._HIST["op"].samples = []
    assert latency_mod.latency_snapshot() == {}


# ═══════════════════════════════════════════════════════════ tokens


def test_a_token_whose_signature_is_not_base64_is_rejected():
    from vibey_bootstrap.tokens import InvalidActionToken, verify_action_token

    with pytest.raises(InvalidActionToken, match="base64 decode failed"):
        verify_action_token("secret", "eyJhIjoxfQ.!!!not base64!!!", expected_action="act")


def test_a_token_whose_payload_is_not_json_is_rejected():
    import hashlib
    import hmac as hmac_lib

    from vibey_bootstrap.tokens import InvalidActionToken, _b64url_encode, verify_action_token

    raw = b"not json at all"
    sig = hmac_lib.new(b"secret", raw, hashlib.sha256).digest()
    token = f"{_b64url_encode(raw)}.{_b64url_encode(sig)}"
    with pytest.raises(InvalidActionToken, match="payload not JSON"):
        verify_action_token("secret", token, expected_action="act")


def test_a_token_whose_payload_is_not_an_object_is_rejected():
    import hashlib
    import hmac as hmac_lib

    from vibey_bootstrap.tokens import InvalidActionToken, _b64url_encode, verify_action_token

    raw = json.dumps([1, 2, 3]).encode()
    sig = hmac_lib.new(b"secret", raw, hashlib.sha256).digest()
    token = f"{_b64url_encode(raw)}.{_b64url_encode(sig)}"
    with pytest.raises(InvalidActionToken, match="payload not a JSON object"):
        verify_action_token("secret", token, expected_action="act")


# ═══════════════════════════════════════════════════════════ validation


def test_an_absent_optional_field_passes():
    from vibey_bootstrap.validation import FieldRule, _check_field

    assert _check_field(FieldRule(name="note", required=False), {}) is None


@pytest.mark.parametrize(
    "rule_kwargs, value, expected",
    [
        ({"non_empty": True}, "   ", "is empty"),
        ({"pattern": r"^\d+$"}, "abc", "does not match pattern"),
        ({"forbidden_prefixes": ("/",)}, "/etc/passwd", "starts with forbidden prefix"),
    ],
)
def test_a_field_that_breaks_its_rule_says_which_rule(rule_kwargs, value, expected):
    from vibey_bootstrap.validation import FieldRule, _check_field

    rule = FieldRule(name="f", **rule_kwargs)
    assert expected in _check_field(rule, {"f": value})


def test_a_non_object_payload_can_be_rejected_without_raising():
    from vibey_bootstrap.validation import MessageSchema, validate_message

    schema = MessageSchema(fields=())
    assert validate_message(["not", "an", "object"], schema, raise_unrecoverable=False) == {}
    assert counter_snapshot()["queue_message.rejected.schema"] == 1
