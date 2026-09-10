# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
import pytest

from agyloop.domain.pricing import ESTIMATE_LABEL, estimate_dollars, price_for_model


def test_known_model_has_nonzero_prices() -> None:
    inn, out = price_for_model("gemini-2.5-pro")
    assert inn > 0
    assert out > inn


def test_estimate_is_labeled_and_scales() -> None:
    estimate = estimate_dollars(
        model="gemini-2.5-flash",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )
    assert estimate.label == ESTIMATE_LABEL
    assert estimate.usd == pytest.approx(0.30 + 2.50)


def test_unknown_model_inherits_flash_lite() -> None:
    inn, out = price_for_model("totally-unknown-model")
    assert (inn, out) == price_for_model("gemini-2.5-flash-lite")


def test_zero_tokens_is_zero_dollars() -> None:
    assert estimate_dollars(model="gemini-2.5-pro").usd == 0.0
