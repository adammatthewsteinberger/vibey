# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Labeled USD estimates for ``--max-dollars``.

Gemini usage metadata does not expose a billed cost. These figures are public
list prices per 1M tokens, not an invoice. Always label them as estimates
(ADR 0009).
"""

from __future__ import annotations

from dataclasses import dataclass

# (input_usd_per_mtok, output_usd_per_mtok) — public list prices, estimates only.
_PRICE_PER_MTOK: dict[str, tuple[float, float]] = {
    "gemini-flash-lite-latest": (0.10, 0.40),
    "gemini-3.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-lite": (0.075, 0.30),
}

ESTIMATE_LABEL = "estimate"


@dataclass(frozen=True, slots=True)
class DollarEstimate:
    usd: float
    label: str = ESTIMATE_LABEL
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


def price_for_model(model: str) -> tuple[float, float]:
    """Return (input, output) USD per million tokens for ``model``.

    Unknown ids inherit the flash-lite table so a missing SKU cannot silently
    report zero cost against ``--max-dollars``.
    """
    key = model.strip().removeprefix("models/")
    if key in _PRICE_PER_MTOK:
        return _PRICE_PER_MTOK[key]
    for known, prices in _PRICE_PER_MTOK.items():
        if key.startswith(known) or known in key:
            return prices
    return _PRICE_PER_MTOK["gemini-2.5-flash-lite"]


def estimate_dollars(
    *,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> DollarEstimate:
    """Estimate USD from token counts. Zero tokens → zero dollars."""
    in_price, out_price = price_for_model(model)
    usd = (max(0, input_tokens) / 1_000_000) * in_price + (
        max(0, output_tokens) / 1_000_000
    ) * out_price
    return DollarEstimate(
        usd=usd,
        label=ESTIMATE_LABEL,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
