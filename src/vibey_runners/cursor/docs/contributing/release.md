# Release process

Nobody cuts releases here — the automation does. Versions are **derived from
what actually changed** by [vibey-gh](https://pypi.org/project/vibey-gh/) and
published to PyPI via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no
long-lived token stored anywhere).

1. Feature PRs squash-merge into `develop`; every push to `develop` publishes
   a `.devN` build to TestPyPI.
2. `promote-to-main.yml` compares `develop` and `main` by content, opens the
   promotion PR when they differ, applies the derived version bump, waits for
   checks, and rebase-merges. That push publishes to PyPI (TestPyPI first,
   then a verify step, then PyPI).
3. After each publish, `develop` is fast-forwarded onto `main` automatically —
   never back-merge by hand.

`vibey-gh version --since origin/main --explain` shows the derivation. There
is no release-please, no standing release PR, and no manual tag in the normal
flow; a `v*` tag only attaches artifacts to a GitHub Release.
