# Adopting vibey-gh

You want release automation that reviews, merges, promotes, and publishes without you.
The problem is that adopting any such machinery is itself a minefield: a key in the wrong
config section is silently ignored, a gate can be enabled with nothing installed to
satisfy it, and the first pull request that installs privileged workflows cannot be
protected by them. This page is the map of that minefield, drawn from the failures of
nine real adoptions.

## The preflight

```bash
pip install vibey-gh
vibey-gh install     # hooks, managed workflows, pinned to this exact version
vibey-gh check       # is the provenance intact?
vibey-gh doctor      # will the automation actually work?
```

`doctor` is the adoption preflight: offline, no credentials, reading only files on disk.
It catches the failures that presented as mysteries on live repositories — a silently
ignored configuration key, a merge train that refuses every pull request because the gate
it demands was never installed, a ruff configuration that fails every stamped file, two
workflows contending for one Pages site, and headers carrying a superseded fingerprint
text. Run it after every configuration change, not just the first one.

## The one thing no code can remove: the bootstrap merge

Privileged workflows (`pull_request_target`, `workflow_run`) execute the copy on the
**default branch** — that is GitHub's security model, not a vibey-gh choice. So the pull
request that *installs* the gate cannot be gated by it, and the one that installs
`automation-bootstrap.yml` cannot use it. **The first adoption PR must be merged by an
administrator, once, per repository:**

```bash
gh pr merge <N> --squash --admin
```

Everything after that seeds itself. The same rule applies any time a privileged workflow
is repaired: the fix takes effect only once it reaches the default branch, and
`automation-bootstrap.yml` exists as the audited path for exactly that case.

## Secrets

`ANTHROPIC_API_KEY` powers the reviews and repairs; without it the local fallbacks (if
configured) carry the load. `AUTOMERGE_TOKEN` is a personal access token whose exact
permission table, non-requirements (Checks does not exist for PATs, by design), and three
production failure modes are documented in [Operations](operations.md) — read that before
minting one, because the failures present as anything but a credential problem.

## After the first merge

The pipeline proves itself on its own next change: commit → gate → merge train →
promotion → publish, unattended. If any link stalls, `doctor` first, then the failing
run's log — and the merge train now prints the API's actual error rather than a summary,
because the summary once cost an afternoon.
