# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Configurable billing and rate-limit substring lexicons for classification."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_BILLING_TERMS: tuple[str, ...] = (
    # Tier 1 — credits and balance
    "out_of_credits",
    "credits_required",
    "insufficient_credits",
    "no_credits",
    "credit_balance",
    "credit_balance_exhausted",
    "add_credits",
    "purchase_credits",
    "top_up",
    "topup_required",
    # Tier 2 — usage allowance and plan quota
    "usage_limit",
    "usage_limit_reached",
    "usage_limit_exceeded",
    "usage_exceeded",
    # Live Cursor bridge status copy (not snake_case API codes):
    # "You're out of usage. … increase your limit …"
    "out_of_usage",
    "increase_your_limit",
    "included_usage",
    "plan_limit",
    "plan_quota",
    "plan_exhausted",
    "quota_exceeded",
    "monthly_limit",
    "monthly_quota",
    "request_limit_reached",
    "usage_not_included",
    # Tier 3 — spend caps set by the user or an admin
    "spend_limit",
    "spending_limit",
    "hard_limit",
    "budget_exceeded",
    "cap_reached",
    "spend_cap",
    "admin_limit",
    "team_limit",
    # Tier 4 — billing and subscription state
    "payment_required",
    "payment_failed",
    "billing",
    "billing_error",
    "upgrade_required",
    "subscription_expired",
    "subscription_inactive",
    "trial_expired",
    "trial_ended",
)

DEFAULT_RATE_LIMIT_TERMS: tuple[str, ...] = (
    "too_many_requests",
    "rate_limit_exceeded",
    "rate_limited",
    "slow_down",
    "concurrent_limit",
    "requests_per",
    "try_again_in",
    "temporarily",
)


@dataclass(frozen=True, slots=True)
class BillingLexicon:
    terms: tuple[str, ...]

    def matches(self, *texts: str | None) -> str | None:
        """Return the first matching term across ``texts``, or ``None``."""
        return _match_terms(self.terms, texts)


@dataclass(frozen=True, slots=True)
class RateLimitLexicon:
    terms: tuple[str, ...]

    def matches(self, *texts: str | None) -> str | None:
        """Return the first matching term across ``texts``, or ``None``."""
        return _match_terms(self.terms, texts)


def _match_terms(terms: tuple[str, ...], texts: tuple[str | None, ...]) -> str | None:
    ordered_terms = sorted(terms, key=len, reverse=True)
    for text in texts:
        if text is None:
            continue
        lowered = text.lower()
        if not lowered.strip():
            continue
        normalized = lowered.replace(" ", "_").replace("-", "_")
        for term in ordered_terms:
            if term in lowered or term in normalized:
                return term
    return None
