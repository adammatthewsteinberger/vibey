# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Redact credential-shaped keys from nested payloads."""

from agyloop.infrastructure.redact import redact


def test_redact_scrubs_google_api_key_and_adc_fields() -> None:
    payload = {
        "ok": True,
        "GOOGLE_API_KEY": "secret",
        "nested": {"access_token": "tok", "client_email": "a@b"},
        "list": [{"authorization": "Bearer x"}],
        "tuple": ({"api_key": "secret"}, "clean"),
    }
    out = redact(payload)
    assert out["ok"] is True
    assert out["GOOGLE_API_KEY"] == "***"
    assert out["nested"]["access_token"] == "***"
    assert out["nested"]["client_email"] == "***"
    assert out["list"][0]["authorization"] == "***"
    assert out["tuple"] == ({"api_key": "***"}, "clean")
    assert redact("simple string") == "simple string"
