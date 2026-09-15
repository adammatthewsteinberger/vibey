# vibey-gh

Shipping a change safely through review, merge, versioning, and release usually means
hand-wiring a dozen GitHub Actions steps — and they drift out of sync, silently skip a
check, or let a stale result approve code that has since changed. `vibey-gh` replaces
that hand-wired path with one event-driven, auditable contract: push a branch, and the
tooling carries it through review, repair, merge, release, and documentation on its own,
stopping only when a human decision is genuinely required.

**New to the project?** Begin at [Start here](start/index.md) — a zero-context
welcome, a guided first session, and a glossary bridge. Then [Adoption](adoption.md) — it assumes nothing and
walks one repository from bare to fully automated. The pages after it are the
engineering reference; the formal material ([Threat model](threat-model.md),
[Governance](governance.md), [Architecture decisions](adr/README.md)) comes last.

<div class="feature-grid" markdown>

<div class="feature-card" markdown>

### Resolve

An eligible published issue becomes one guarded solution branch and a linked pull request,
without a human in between.

</div>

<div class="feature-card" markdown>

### Repair

Failed scans are diagnosed, repaired on a guarded branch, and sent back through the full
review path.

</div>

<div class="feature-card" markdown>

### Review

Outside contributions receive structured, current-head review before they enter the
merge train.

</div>

<div class="feature-card" markdown>

### Release

Develop and main move through distinct, reproducible TestPyPI, PyPI, Pages, Packages,
tagging, and GitHub Release channels.

</div>

</div>

## Start in two commands

```console
pip install vibey-gh
vibey-gh install
```

The installed runtime stays dependency-free. The generated workflows remain pinned,
auditable, and independently testable.

[Production](#){ .primary-action data-release-target="main" }
[Preview](#){ .secondary-action data-release-target="develop" }
<!-- Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)). -->
