# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from cursorloop.domain.lexicon import (
    DEFAULT_BILLING_TERMS,
    DEFAULT_RATE_LIMIT_TERMS,
    BillingLexicon,
    RateLimitLexicon,
)


def test_matches_are_case_insensitive_and_report_the_term() -> None:
    lex = BillingLexicon(DEFAULT_BILLING_TERMS)
    assert lex.matches("Your USAGE_LIMIT_REACHED for this month") == "usage_limit_reached"


def test_out_of_usage_bridge_copy_matches_billing() -> None:
    lex = BillingLexicon(DEFAULT_BILLING_TERMS)
    matched = lex.matches(
        "You're out of usage. Switch to Auto, or ask your admin to increase your limit"
    )
    assert matched in {"out_of_usage", "increase_your_limit"}


def test_no_match_returns_none() -> None:
    assert BillingLexicon(DEFAULT_BILLING_TERMS).matches("connection reset by peer") is None


def test_none_and_empty_inputs_are_skipped() -> None:
    assert BillingLexicon(DEFAULT_BILLING_TERMS).matches(None, "", "  ") is None


def test_lexicon_is_overridable() -> None:
    assert BillingLexicon(("wallet_empty",)).matches("wallet_empty") == "wallet_empty"


def test_rate_limit_lexicon_matches_counter_terms() -> None:
    lex = RateLimitLexicon(DEFAULT_RATE_LIMIT_TERMS)
    assert lex.matches("HTTP 429 Too Many Requests") == "too_many_requests"


def test_default_billing_terms_include_all_tiers_in_order() -> None:
    assert DEFAULT_BILLING_TERMS == (
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
        "usage_limit",
        "usage_limit_reached",
        "usage_limit_exceeded",
        "usage_exceeded",
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
        "spend_limit",
        "spending_limit",
        "hard_limit",
        "budget_exceeded",
        "cap_reached",
        "spend_cap",
        "admin_limit",
        "team_limit",
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


def test_default_rate_limit_terms_match_research_notes() -> None:
    assert DEFAULT_RATE_LIMIT_TERMS == (
        "too_many_requests",
        "rate_limit_exceeded",
        "rate_limited",
        "slow_down",
        "concurrent_limit",
        "requests_per",
        "try_again_in",
        "temporarily",
    )
