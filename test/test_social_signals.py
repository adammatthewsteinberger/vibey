# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The social-signals surface (sub-doctrine 4.a): authenticity gates and the render."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibey_gh.config import (
    SOCIAL_SIGNAL_KINDS,
    GhConfig,
    SocialSignalEntry,
    SocialSignalsConfig,
    load_config,
)
from vibey_gh.social_signals import inject, render


def _entry(**kw) -> SocialSignalEntry:
    base = dict(
        kind="testimony",
        agent="Jane Doe",
        source="https://example.com/said-it",
        human_attested=True,
        attested_on="2026-08-30",
        quote="It shipped my release while I slept.",
    )
    base.update(kw)
    return SocialSignalEntry(**base)


def _cfg(*entries: SocialSignalEntry, enabled: bool = True) -> GhConfig:
    return GhConfig(
        root=Path("."),
        social_signals=SocialSignalsConfig(enabled=enabled, entries=tuple(entries)),
    )


def test_the_surface_is_opt_in_and_forever_available():
    """Sub-doctrine 4.a: off by default — but the capability itself always exists."""
    assert SocialSignalsConfig().enabled is False
    assert render(GhConfig(root=Path("."))) == ""


def test_the_kind_taxonomy_is_comprehensive_to_todays_signals():
    for kind in (
        "testimony",
        "endorsement",
        "adoption",
        "case-study",
        "review",
        "community",
        "citation",
        "press",
        "contributor",
        "backer",
        "talk",
        "certification",
    ):
        assert kind in SOCIAL_SIGNAL_KINDS


@pytest.mark.parametrize(
    "broken, complaint",
    [
        (dict(agent="  "), "real human agent"),
        (dict(source="http://insecure.example"), "https provenance link"),
        (dict(kind="astroturf"), "unknown kind"),
        (dict(human_attested=False), "never a machine"),
    ],
)
def test_validation_refuses_unattested_or_unattributed_signals(broken, complaint):
    """Machine-manufactured social proof is false witness; the config layer is the
    first gate that stops it."""
    with pytest.raises(ValueError, match=complaint):
        SocialSignalsConfig(enabled=True, entries=(_entry(**broken),)).validate()


def test_enabled_with_no_entries_is_refused_as_dishonest():
    with pytest.raises(ValueError, match="renders nothing honest"):
        SocialSignalsConfig(enabled=True).validate()


def test_disabled_config_never_validates_entries():
    SocialSignalsConfig(enabled=False, entries=(_entry(human_attested=False),)).validate()


def test_render_carries_agent_source_kind_and_the_oath():
    text = render(_cfg(_entry(role="CTO", org="Acme", date="2026-08-30")))
    assert "Jane Doe" in text
    assert "CTO, Acme" in text
    assert 'href="https://example.com/said-it"' in text
    assert "verified source" in text
    assert "never a machine" in text and "(sub-doctrine 4.a)" in text
    assert '<div class="vs-grid">' in text and "<style>" in text


def test_counted_kinds_render_as_chips_not_cards():
    text = render(
        _cfg(
            _entry(kind="community", agent="GitHub stargazers", quote="", value="1,204"),
            _entry(kind="backer", agent="The Vizius Group", quote=""),
        )
    )
    assert "vs-chip" in text
    assert '<div class="vs-grid">' not in text
    assert "1,204" in text and "The Vizius Group" in text


def test_render_escapes_hostile_text():
    text = render(_cfg(_entry(quote='<script>alert("x")</script>', agent="A & B <Inc>")))
    assert "<script>alert" not in text
    assert "&lt;script&gt;" in text
    assert "A &amp; B &lt;Inc&gt;" in text


def test_inject_splices_before_the_funding_footer(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text(
        '<html><body><main>hi</main><footer class="vibey-funding">f</footer></body></html>',
        encoding="utf-8",
    )
    assert inject(site, _cfg(_entry())) is True
    text = (site / "index.html").read_text(encoding="utf-8")
    assert text.index("vibey-social") < text.index("vibey-funding")


def test_inject_falls_back_to_body_close_and_reports_misses(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("<html><body>hi</body></html>", encoding="utf-8")
    assert inject(site, _cfg(_entry())) is True
    assert "vibey-social" in (site / "index.html").read_text(encoding="utf-8")
    assert inject(tmp_path / "missing", _cfg(_entry())) is False
    assert inject(site, GhConfig(root=Path("."))) is False


def test_inject_reports_a_marker_free_page(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("no markers here", encoding="utf-8")
    assert inject(site, _cfg(_entry())) is False


def test_social_signals_load_from_toml(tmp_path: Path):
    (tmp_path / ".vibey-gh.toml").write_text(
        '[social_signals]\nenabled = true\nheading = "They said it"\n'
        "[[social_signals.entries]]\n"
        'kind = "endorsement"\nagent = "Ministry of Works"\n'
        'source = "https://gov.example/notice"\nhuman_attested = true\n'
        'attested_on = "2026-08-30"\n'
        'quote = "Adopted for provenance."\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    assert cfg.social_signals.enabled is True
    assert cfg.social_signals.heading == "They said it"
    assert cfg.social_signals.entries[0].agent == "Ministry of Works"


def test_an_unattested_toml_entry_fails_config_load(tmp_path: Path):
    (tmp_path / ".vibey-gh.toml").write_text(
        "[social_signals]\nenabled = true\n"
        "[[social_signals.entries]]\n"
        'kind = "testimony"\nagent = "Bot 9000"\nsource = "https://x.example/y"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="never a machine"):
        load_config(tmp_path)


def test_the_amendment_ages_every_attestation():
    """4.a amendment: authenticity is re-verified, never remembered."""
    with pytest.raises(ValueError, match="must age"):
        SocialSignalsConfig(enabled=True, entries=(_entry(attested_on=""),)).validate()
    with pytest.raises(ValueError, match="never assumed presently authentic"):
        SocialSignalsConfig(enabled=True, entries=(_entry(attested_on="2020-01-01"),)).validate()
    with pytest.raises(ValueError, match="forbids attestations that never age"):
        SocialSignalsConfig(
            enabled=True, max_attestation_age_days=0, entries=(_entry(),)
        ).validate()


def test_a_revoked_signal_is_a_permanent_tombstone():
    with pytest.raises(ValueError, match="can never\n? ?be re-attested|never.*re-attested"):
        SocialSignalsConfig(
            enabled=True, entries=(_entry(revoked=True, human_attested=True),)
        ).validate()
    # revoked-and-unattested is a valid tombstone: it validates and renders nothing
    SocialSignalsConfig(
        enabled=True,
        entries=(
            _entry(),
            SocialSignalEntry(kind="testimony", agent="Gone", source="https://x/y", revoked=True),
        ),
    ).validate()
    cfg = _cfg(
        _entry(),
        SocialSignalEntry(
            kind="testimony", agent="Gone", source="https://x/y", revoked=True, quote="forged"
        ),
    )
    text = render(cfg)
    assert "Gone" not in text and "forged" not in text
    assert "Jane Doe" in text


def test_render_shows_the_attestation_date_and_the_expiry_oath():
    text = render(_cfg(_entry()))
    assert "attested 2026-08-30" in text
    assert "verification expires and is renewed, never remembered" in text
