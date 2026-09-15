"""SDK-agnostic Azure OpenAI / Anthropic usage tracker.

Records tokens + cost per deployment in three sliding windows (60s, 60m,
24h). Optional soft TPM cap via ``acquire()``. Threshold-based cost alerts
via ``check_thresholds_and_alert()``. Pricing table includes both OpenAI
and Anthropic defaults; apps override per-deployment via env vars or
``register_pricing(...)``.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from vibey_bootstrap.counters import bump_counter

_logger = logging.getLogger(__name__)

_RATE_WINDOW_SECONDS = 60.0
_HOURLY_WINDOW_SECONDS = 3600.0
_DAILY_WINDOW_SECONDS = 86400.0
_RECENT_USAGE_MAXLEN = 50_000
_THRESHOLD_ALERT_COOLDOWN_SECONDS = 1800.0


@dataclass
class _UsageEntry:
    ts: float
    deployment: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


@dataclass
class _DeploymentCumulative:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0
    rate_limit_events: int = 0


@dataclass
class _TrackerState:
    recent: deque[_UsageEntry] = field(default_factory=lambda: deque(maxlen=_RECENT_USAGE_MAXLEN))
    cumulative: dict[str, _DeploymentCumulative] = field(default_factory=dict)
    last_alert_fired: dict[str, float] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)


_state = _TrackerState()


_DEFAULT_PRICING: list[tuple[str, float, float]] = [
    ("gpt-4o-mini", 0.00015, 0.0006),
    ("gpt-4o", 0.0025, 0.01),
    ("gpt-5-mini", 0.00025, 0.002),
    ("o1-mini", 0.003, 0.012),
    ("o1", 0.015, 0.06),
    ("claude-3-5-sonnet", 0.003, 0.015),
    ("claude-3-5-haiku", 0.001, 0.005),
    ("claude-3-opus", 0.015, 0.075),
    ("claude-3-haiku", 0.00025, 0.00125),
]
_FALLBACK_PRICING: tuple[float, float] = (0.0025, 0.01)
_pricing_lock = threading.Lock()


def register_pricing(
    deployment_substring: str,
    *,
    input_per_1k: float,
    output_per_1k: float,
) -> None:
    with _pricing_lock:
        _DEFAULT_PRICING.append((deployment_substring, input_per_1k, output_per_1k))
        _DEFAULT_PRICING.sort(key=lambda t: -len(t[0]))


def _normalize_deployment(deployment: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", deployment.upper()).strip("_")


def _pricing_for(deployment: str) -> tuple[float, float]:
    normalized = _normalize_deployment(deployment)
    in_env = os.environ.get(f"AI_PRICING_{normalized}_INPUT_PER_1K")
    out_env = os.environ.get(f"AI_PRICING_{normalized}_OUTPUT_PER_1K")
    if in_env and out_env:
        try:
            return float(in_env), float(out_env)
        except ValueError:
            pass
    needle = deployment.lower()
    with _pricing_lock:
        snapshot = sorted(_DEFAULT_PRICING, key=lambda t: -len(t[0]))
    for substr, in_p, out_p in snapshot:
        if substr.lower() in needle:
            return in_p, out_p
    return _FALLBACK_PRICING


def _compute_cost(deployment: str, prompt_tokens: int, completion_tokens: int) -> float:
    in_p, out_p = _pricing_for(deployment)
    return (prompt_tokens / 1000.0) * in_p + (completion_tokens / 1000.0) * out_p


def record_usage(
    deployment: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Record one call. Best-effort, never raises."""
    try:
        prompt_tokens = max(0, int(prompt_tokens))
        completion_tokens = max(0, int(completion_tokens))
        cost = _compute_cost(deployment, prompt_tokens, completion_tokens)
        now = time.monotonic()
        entry = _UsageEntry(
            ts=now,
            deployment=deployment,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        )
        with _state.lock:
            _state.recent.append(entry)
            cum = _state.cumulative.setdefault(deployment, _DeploymentCumulative())
            cum.prompt_tokens += prompt_tokens
            cum.completion_tokens += completion_tokens
            cum.total_tokens += prompt_tokens + completion_tokens
            cum.cost_usd += cost
            cum.calls += 1
        bump_counter("ai.tokens.total", prompt_tokens + completion_tokens)
        bump_counter("ai.cost_usd_micros", int(cost * 1_000_000))
        bump_counter("ai.calls")
    except Exception:
        pass


def record_rate_limit_event(deployment: str, source: str) -> None:
    """Mark a rate-limit-hit event + fire an ERROR alert (deduped)."""
    try:
        with _state.lock:
            cum = _state.cumulative.setdefault(deployment, _DeploymentCumulative())
            cum.rate_limit_events += 1
        bump_counter("ai.rate_limit_events")
        try:
            from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

            alert_dev_team(
                AlertSeverity.ERROR,
                subject=f"AI rate limit triggered ({source}) for {deployment}",
                context={"deployment": deployment, "source": source},
                dedup_key=f"ai_usage.rate_limit:{deployment}:{source}",
            )
        except Exception:
            pass
    except Exception:
        pass


def _tpm_limit_for(deployment: str) -> int:
    normalized = _normalize_deployment(deployment)
    per_dep = os.environ.get(f"AI_TPM_LIMIT_{normalized}")
    if per_dep:
        try:
            return max(0, int(per_dep))
        except ValueError:
            pass
    raw = os.environ.get("AI_TPM_LIMIT", "0")
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _tokens_in_window(
    deployment: str,
    now: float,
    window_seconds: float,
) -> tuple[int, float]:
    cutoff = now - window_seconds
    total = 0
    oldest = now
    with _state.lock:
        for entry in _state.recent:
            if entry.deployment == deployment and entry.ts >= cutoff:
                total += entry.prompt_tokens + entry.completion_tokens
                if entry.ts < oldest:
                    oldest = entry.ts
    return total, oldest


def acquire(
    deployment: str,
    estimated_tokens: int,
    timeout: float | None = None,
) -> None:
    """Soft TPM cap. No-op when ``AI_TPM_LIMIT`` is unset/0.

    On max-wait reached: fires CRITICAL alert and lets the call through —
    a slow, billed call beats a stranded customer.
    """
    try:
        limit = _tpm_limit_for(deployment)
        if limit <= 0:
            return
        max_wait = (
            timeout
            if timeout is not None
            else float(os.environ.get("AI_RATE_LIMIT_MAX_WAIT_SECONDS", "60"))
        )
        start = time.monotonic()
        recorded = False
        while True:
            now = time.monotonic()
            window_tokens, oldest = _tokens_in_window(deployment, now, _RATE_WINDOW_SECONDS)
            if window_tokens + max(0, int(estimated_tokens)) <= limit:
                return
            elapsed = now - start
            if elapsed >= max_wait:
                record_rate_limit_event(deployment, source="proactive_timeout")
                try:
                    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                    alert_dev_team(
                        AlertSeverity.CRITICAL,
                        subject=(
                            f"AI rate limit max-wait exceeded for {deployment}; "
                            "allowing call through"
                        ),
                        context={
                            "deployment": deployment,
                            "limit_tpm": limit,
                            "elapsed_seconds": round(elapsed, 2),
                        },
                        dedup_key=f"ai_usage.max_wait_exceeded:{deployment}",
                    )
                except Exception:
                    pass
                return
            if not recorded:
                record_rate_limit_event(deployment, source="proactive")
                recorded = True
            window_clear = _RATE_WINDOW_SECONDS - (now - oldest) + 0.05
            sleep_for = max(0.1, min(window_clear, max_wait - elapsed))
            time.sleep(sleep_for)
    except Exception:
        # Governance must never break the calling path.
        return


def _window_summary(
    deployment: str,
    now: float,
    window_seconds: float,
) -> dict[str, Any]:
    cutoff = now - window_seconds
    prompt = completion = calls = 0
    cost = 0.0
    with _state.lock:
        for entry in _state.recent:
            if entry.deployment == deployment and entry.ts >= cutoff:
                prompt += entry.prompt_tokens
                completion += entry.completion_tokens
                cost += entry.cost_usd
                calls += 1
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "cost_usd": round(cost, 6),
        "calls": calls,
    }


def _prune_old() -> None:
    cutoff = time.monotonic() - _DAILY_WINDOW_SECONDS
    with _state.lock:
        while _state.recent and _state.recent[0].ts < cutoff:
            _state.recent.popleft()


def usage_snapshot() -> dict[str, Any]:
    """Returns by_deployment + totals with windowed metrics."""
    _prune_old()
    now = time.monotonic()
    by_dep: dict[str, Any] = {}
    total_calls = 0
    total_tokens = 0
    total_cost = 0.0
    total_rate_limits = 0
    with _state.lock:
        deployments = list(_state.cumulative.keys())
    for dep in deployments:
        with _state.lock:
            cum = _state.cumulative[dep]
            cum_dict = {
                "prompt_tokens": cum.prompt_tokens,
                "completion_tokens": cum.completion_tokens,
                "total_tokens": cum.total_tokens,
                "cost_usd": round(cum.cost_usd, 6),
                "calls": cum.calls,
                "rate_limit_events": cum.rate_limit_events,
            }
        by_dep[dep] = {
            "cumulative": cum_dict,
            "window_60s": _window_summary(dep, now, _RATE_WINDOW_SECONDS),
            "window_60m": _window_summary(dep, now, _HOURLY_WINDOW_SECONDS),
            "window_24h": _window_summary(dep, now, _DAILY_WINDOW_SECONDS),
            "tpm_limit": _tpm_limit_for(dep),
        }
        total_calls += cum_dict["calls"]  # type: ignore[assignment]
        total_tokens += cum_dict["total_tokens"]  # type: ignore[assignment]
        total_cost += cum.cost_usd
        total_rate_limits += cum_dict["rate_limit_events"]  # type: ignore[assignment]
    return {
        "by_deployment": by_dep,
        "totals": {
            "calls": total_calls,
            "total_tokens": total_tokens,
            "cost_usd": round(total_cost, 6),
            "rate_limit_events": total_rate_limits,
        },
    }


def _fire_threshold_alert(key: str, subject: str, context: dict[str, Any]) -> bool:
    """Cooldown-gated CRITICAL fire. Returns True when fired."""
    now = time.monotonic()
    with _state.lock:
        last = _state.last_alert_fired.get(key, 0.0)
        if last and (now - last) < _THRESHOLD_ALERT_COOLDOWN_SECONDS:
            return False
        _state.last_alert_fired[key] = now
    try:
        from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

        alert_dev_team(
            AlertSeverity.CRITICAL,
            subject=subject,
            context=context,
            dedup_key=key,
        )
    except Exception:
        pass
    return True


def check_thresholds_and_alert() -> dict[str, Any]:
    """Compare windowed metrics against env thresholds; fire alerts on breach.

    Designed to run every 10 minutes via APScheduler.
    """
    snap = usage_snapshot()
    fired: list[dict[str, Any]] = []
    try:
        hourly_cost_limit = float(os.environ.get("AI_COST_ALERT_HOURLY_DOLLARS", "0"))
    except ValueError:
        hourly_cost_limit = 0.0
    try:
        daily_cost_limit = float(os.environ.get("AI_COST_ALERT_DAILY_DOLLARS", "0"))
    except ValueError:
        daily_cost_limit = 0.0
    try:
        hourly_tokens_limit = int(os.environ.get("AI_HIGH_USAGE_TOKENS_HOURLY", "0"))
    except ValueError:
        hourly_tokens_limit = 0
    for dep, payload in snap["by_deployment"].items():
        hourly = payload["window_60m"]
        daily = payload["window_24h"]
        if hourly_cost_limit > 0 and hourly["cost_usd"] > hourly_cost_limit:
            key = f"ai_usage.cost_hourly:{dep}"
            if _fire_threshold_alert(
                key,
                subject=f"AI hourly cost over threshold for {dep}: ${hourly['cost_usd']}",
                context={
                    "deployment": dep,
                    "window": "60m",
                    "cost_usd": hourly["cost_usd"],
                    "threshold": hourly_cost_limit,
                },
            ):
                fired.append({"key": key, "subject": "hourly_cost", "cost_usd": hourly["cost_usd"]})
        if daily_cost_limit > 0 and daily["cost_usd"] > daily_cost_limit:
            key = f"ai_usage.cost_daily:{dep}"
            if _fire_threshold_alert(
                key,
                subject=f"AI daily cost over threshold for {dep}: ${daily['cost_usd']}",
                context={
                    "deployment": dep,
                    "window": "24h",
                    "cost_usd": daily["cost_usd"],
                    "threshold": daily_cost_limit,
                },
            ):
                fired.append({"key": key, "subject": "daily_cost", "cost_usd": daily["cost_usd"]})
        if hourly_tokens_limit > 0 and hourly["total_tokens"] > hourly_tokens_limit:
            key = f"ai_usage.tokens_hourly:{dep}"
            if _fire_threshold_alert(
                key,
                subject=f"AI hourly token use over threshold for {dep}: {hourly['total_tokens']}",
                context={
                    "deployment": dep,
                    "window": "60m",
                    "total_tokens": hourly["total_tokens"],
                    "threshold": hourly_tokens_limit,
                },
            ):
                fired.append(
                    {
                        "key": key,
                        "subject": "hourly_tokens",
                        "total_tokens": hourly["total_tokens"],
                    }
                )
    return {"snapshot": snap, "fired": fired}


def reset_state() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("reset_state is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    with _state.lock:
        _state.recent.clear()
        _state.cumulative.clear()
        _state.last_alert_fired.clear()


class AiUsageTracker:
    """Class facade around the module-level singleton.

    Mostly here for callers that prefer to inject a tracker instance; the
    module-level functions are the canonical entry points.
    """

    record_usage = staticmethod(record_usage)
    acquire = staticmethod(acquire)
    record_rate_limit_event = staticmethod(record_rate_limit_event)
    usage_snapshot = staticmethod(usage_snapshot)
    check_thresholds_and_alert = staticmethod(check_thresholds_and_alert)
    reset_state = staticmethod(reset_state)


__all__ = [
    "AiUsageTracker",
    "acquire",
    "check_thresholds_and_alert",
    "record_rate_limit_event",
    "record_usage",
    "register_pricing",
    "reset_state",
    "usage_snapshot",
]
