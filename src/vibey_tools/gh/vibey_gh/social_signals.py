# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The social-signals surface (sub-doctrine 4.a): real human voices on the site.

Renders the operator-attested signals from ``[social_signals]`` as one self-contained
HTML section — a responsive card grid for the voiced kinds (testimony, endorsement,
review, press, case-study, talk) and a compact chip row for the counted and named
kinds (adoption, community, citation, contributor, backer, certification) — and
splices it into the built channel site's landing page.

Three rules this module inherits from the sub-doctrine and cannot be configured out:

- every signal names its **real human agent** (a person, or an institution of
  persons such as a government) and carries its **source hyperlink at the point of
  reference** — a reader can verify any card in one click;
- every signal carries the operator's **human attestation** — config validation has
  already refused anything without it, so this module only ever renders what a
  human vouched for;
- the section says so out loud: the closing line states that everything above it is
  attested human speech, never a machine's.

The markup is a single ``<section>`` with an inline ``<style>`` — no scripts, no
external assets, theme-aware through ``prefers-color-scheme`` — so it survives any
static host and any documentation theme.
"""

from __future__ import annotations

import html
from pathlib import Path

from vibey_gh.config import GhConfig, SocialSignalEntry

__all__ = ["inject", "render"]

_VOICED = ("testimony", "endorsement", "review", "press", "case-study", "talk")

_STYLE = """
<style>
.vibey-social{max-width:64rem;margin:3rem auto 1rem;padding:0 1rem;
  font-family:inherit}
.vibey-social h2{text-align:center;font-size:1.6em;margin:0 0 .35em}
.vibey-social .vs-sub{text-align:center;opacity:.75;margin:0 0 1.6em;font-size:.95em}
.vibey-social .vs-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));
  gap:1rem;align-items:stretch}
.vibey-social .vs-card{position:relative;border-radius:14px;padding:1.35rem 1.25rem 1.1rem;
  background:rgba(127,127,127,.07);border:1px solid rgba(127,127,127,.22);
  box-shadow:0 1px 2px rgba(0,0,0,.06);display:flex;flex-direction:column;gap:.7rem;
  transition:transform .15s ease,box-shadow .15s ease}
.vibey-social .vs-card:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.10)}
.vibey-social .vs-card::before{content:"\\201C";position:absolute;top:.15rem;left:.75rem;
  font-size:3.2em;line-height:1;opacity:.15;font-family:Georgia,serif}
.vibey-social .vs-kind{align-self:flex-start;font-size:.68em;letter-spacing:.06em;
  text-transform:uppercase;padding:.18em .6em;border-radius:999px;
  border:1px solid rgba(127,127,127,.35);opacity:.8}
.vibey-social blockquote{margin:0;font-size:1.02em;line-height:1.5;font-style:italic}
.vibey-social .vs-who{margin-top:auto;font-size:.9em;line-height:1.35}
.vibey-social .vs-who strong{font-style:normal}
.vibey-social .vs-meta{opacity:.7}
.vibey-social .vs-src{font-size:.82em;text-decoration:none;opacity:.85}
.vibey-social .vs-src:hover{opacity:1;text-decoration:underline}
.vibey-social .vs-chips{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;
  margin:1.4rem 0 0}
.vibey-social .vs-chip{display:inline-flex;align-items:center;gap:.45em;font-size:.85em;
  padding:.4em .85em;border-radius:999px;border:1px solid rgba(127,127,127,.3);
  background:rgba(127,127,127,.06);text-decoration:none;color:inherit}
.vibey-social .vs-chip:hover{border-color:rgba(127,127,127,.6)}
.vibey-social .vs-chip .vs-kind{border:none;padding:0;opacity:.6}
.vibey-social .vs-oath{text-align:center;font-size:.8em;opacity:.65;margin:1.6em 0 0}
@media (prefers-color-scheme: dark){
  .vibey-social .vs-card{background:rgba(255,255,255,.05);
    border-color:rgba(255,255,255,.14);box-shadow:0 1px 2px rgba(0,0,0,.4)}
  .vibey-social .vs-card:hover{box-shadow:0 6px 18px rgba(0,0,0,.5)}
}
</style>
"""


def _who(entry: SocialSignalEntry) -> str:
    bits = [f"<strong>{html.escape(entry.agent)}</strong>"]
    detail = ", ".join(x for x in (entry.role, entry.org) if x)
    if detail:
        bits.append(f'<span class="vs-meta"> — {html.escape(detail)}</span>')
    if entry.date:
        bits.append(f'<span class="vs-meta"> · {html.escape(entry.date)}</span>')
    return "".join(bits)


def _card(entry: SocialSignalEntry) -> str:
    quote = f"<blockquote>{html.escape(entry.quote)}</blockquote>" if entry.quote else ""
    return (
        '<article class="vs-card">'
        f'<span class="vs-kind">{html.escape(entry.kind)}</span>'
        f"{quote}"
        f'<p class="vs-who">{_who(entry)}<br>'
        f'<a class="vs-src" href="{html.escape(entry.source, quote=True)}"'
        f' rel="noopener">verified source ↗</a>'
        f'<span class="vs-meta"> · attested {html.escape(entry.attested_on)}</span></p>'
        "</article>"
    )


def _chip(entry: SocialSignalEntry) -> str:
    figure = f" <strong>{html.escape(entry.value)}</strong>" if entry.value else ""
    return (
        f'<a class="vs-chip" href="{html.escape(entry.source, quote=True)}" rel="noopener">'
        f'<span class="vs-kind">{html.escape(entry.kind)}</span>'
        f"{html.escape(entry.agent)}{figure}</a>"
    )


def render(cfg: GhConfig) -> str:
    """The whole section, or an empty string when the surface is not opted in."""
    signals = cfg.social_signals
    if not signals.enabled or not signals.entries:
        return ""
    live = [e for e in signals.entries if not e.revoked]
    cards = "".join(_card(e) for e in live if e.kind in _VOICED)
    chips = "".join(_chip(e) for e in live if e.kind not in _VOICED)
    grid = f'<div class="vs-grid">{cards}</div>' if cards else ""
    chip_row = f'<div class="vs-chips">{chips}</div>' if chips else ""
    return (
        _STYLE
        + '<section class="vibey-social">'
        + f"<h2>{html.escape(signals.heading)}</h2>"
        + '<p class="vs-sub">Every signal below links its source — verify any of them'
        + " in one click.</p>"
        + grid
        + chip_row
        + '<p class="vs-oath">Each entry above is attested by the operator as the'
        + " genuine words or acts of a real human agent — a person or an institution"
        + " of persons — never a machine — and every attestation carries its date,"
        + " because verification expires and is renewed, never remembered"
        + " (sub-doctrine 4.a).</p>"
        + "</section>\n"
    )


def inject(site_dir: str | Path, cfg: GhConfig) -> bool:
    """Splice the section into the landing page before the funding footer or </body>.

    Returns whether anything was injected — false when the surface is off, the
    landing page is missing, or the marker cannot be found (reported by the caller;
    a missing landing page must never fail a release that already published).
    """
    block = render(cfg)
    if not block:
        return False
    index = Path(site_dir) / "index.html"
    if not index.is_file():
        return False
    text = index.read_text(encoding="utf-8")
    for marker in ('<footer class="vibey-funding"', "</body>"):
        if marker in text:
            index.write_text(text.replace(marker, block + marker, 1), encoding="utf-8")
            return True
    return False
