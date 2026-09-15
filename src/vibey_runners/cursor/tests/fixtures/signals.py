# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Synthetic TurnSignals builders for classifier tests.

Each builder is **synthetic**, derived from documented ``CursorAgentError``
field shapes, and must be replaced by a real captured payload the first time
one is observed.
"""

from __future__ import annotations

from cursorloop.domain.classify import TurnSignals


def rate_limit_retryable(*, retry_after: str | None = "120") -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(
        error_type="RateLimitError",
        is_retryable=True,
        retry_after=retry_after,
        http_status=429,
    )


def rate_limit_non_retryable() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="RateLimitError", is_retryable=False, http_status=429)


def billing_usage_limit() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(
        error_type="RateLimitError",
        error_code="usage_limit_reached",
        error_message="You have reached your monthly usage limit.",
        http_status=429,
        is_retryable=True,
        retry_after="60",
    )


def authentication_failed() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(
        error_type="AuthenticationError",
        error_message="invalid api key; also out_of_credits",
        http_status=401,
    )


def permission_denied() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="PermissionDeniedError", http_status=403)


def errored_run_rate_limit() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(run_status="error", result_text="Rate limit exceeded, slow down.")


def errored_run_billing() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(run_status="error", result_text="Payment required: add credits.")


def unclassified_errored_run(*, result_text: str = "model dumped a stack trace") -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(run_status="error", result_text=result_text)


def expired_run() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(run_status="expired")


def cancelled_run() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(run_status="cancelled")


def agent_busy() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(
        error_type="AgentBusyError", error_code="agent_busy", http_status=409, is_retryable=False
    )


def network_error() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="NetworkError", is_retryable=True)


def timeout_error() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="APITimeoutError", is_retryable=True)


def internal_server_error() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="InternalServerError", is_retryable=True)


def configuration_error() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="ConfigurationError", error_message="unknown model 'nope'")


def bad_request() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(error_type="BadRequestError", error_message="invalid send options")


def integration_not_connected() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(
        error_type="IntegrationNotConnectedError",
        error_message="github not connected",
    )


def finished_run() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(run_status="finished", result_text="done")


def http_429_without_type() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(http_status=429, is_retryable=True)


def billing_via_proto_code() -> TurnSignals:
    # Synthetic: derived from documented CursorAgentError field shapes.
    # Replace with a real captured payload the first time one is observed.
    return TurnSignals(proto_error_code="usage_limit_reached")
