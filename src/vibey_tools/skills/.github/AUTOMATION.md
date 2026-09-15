# Automation

This document explains the automation that lives in this directory: what runs, why it
runs, what it is and is not trusted to do, and how to change it safely. It is written for
whoever next touches a workflow file — a maintainer, a contributor, or an agent — not for
users of the marketplace itself (that's the root
[README.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/README.md)).

## Delivery model

Work moves `feature/* -> develop -> main`. A `feature/*` branch is squash-merged into
`develop`; `develop` is rebase-merged into `main`, which is the only method consistent
with the `required_linear_history` rule both branch rulesets enforce. Every push to
`develop` publishes a `<release>.dev<run_number>` build to TestPyPI; every push to `main`
publishes the exact version in `src/vibey_skills/__init__.py` to PyPI, after the same
TestPyPI-then-verify gate. A `v*` tag additionally attaches build artifacts to a GitHub
Release. Two weekly trains carry ordinary work through without a human in the loop: a
merge train squash-merges ready pull requests into `develop`, and a promotion opens (and,
once its checks pass, rebase-merges) the pull request that carries `develop` into `main`
when the two differ. Full detail, including why `develop` used to fall behind `main` and
how that's fixed, is in
[CLAUDE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CLAUDE.md).

## Workflow inventory

Four workflows are hand-authored because they are specific to this repository's product or
its release pattern: `CI` (manifest and skill-frontmatter validation, packaging, the
wheel-completeness assertion), `Release` (the TestPyPI/PyPI publish pipeline and
`develop`'s realignment onto `main`), `Release artifacts` (attaches the sdist/wheel to
whatever GitHub Release `github-release.yml` creates — vibey-gh's own template has no
way to attach files), and `Currency research` (a scheduled agent that audits dated claims
in skill content against the live web). Twelve more are managed by `vibey-gh install`
(pinned exactly, via `[install] pin_version = true`) from its own templates and
regenerated verbatim whenever that command runs: `provenance.yml` (job name
**Provenance**), `codeql.yml` (job name **Analyze Python**), `pr-automation.yml`
(publishes the **PR automation / gate** check), `merge-train.yml`, `promote-to-main.yml`,
`branch-intake.yml`, `automation-bootstrap.yml`, `github-release.yml`,
`repository-profile.yml`, `conventional-commits.yml`, `release-repair.yml`, and
`release-surfaces.yml`. `Provenance`, `Analyze Python`, and `PR automation / gate`
are required status checks on both branch rulesets, alongside the hand-authored `Validate
manifests and build` and `Build docs (strict)`.

`release-surfaces.yml` publishes the marketplace's real documentation site — branch-specific
ProperDocs sites (`properdocs build --strict` against `properdocs.yml`, not `mkdocs
build`) on GitHub Pages, plus an OCI release bundle in GitHub Packages — after each
successful `Release` run. It retired the hand-authored `docs.yml` in the same change: the
two used to contest ownership of Pages, which is resolved by there being only one
publisher. `mkdocs.yml` still exists and is still built by `ci.yml`'s `Build docs
(strict)` job, but only to validate — that build is never deployed.

Not every template `vibey-gh` ships is adopted. `api-drift.yml` is excluded permanently:
it is vibey-gh's own self-test (`pip install .` then `import vibey_gh.surfaces`), which
only works when the adopting repository's own package *is* `vibey-gh` — false here by
design, since runtime `dependencies` are deliberately empty. `conventional-commits.yml`
had the identical defect through vibey-gh 1.16.0 and was excluded for the same reason;
fixed upstream in 1.27.0 (the same self-hosting detection `provenance.yml` already used)
and re-adopted here. `release-repair.yml` had a comparable exclusion, for a different
reason: through 1.26.0, `github-release.yml` failed on every no-bump push to `main`, and
`release-repair.yml` would have spent an AI call "repairing" each of those as if it were a
real failure; 1.27.0 made that case a clean no-op (below), so there is no longer a
recurring non-failure to chase, and it was re-adopted alongside `release-surfaces.yml`.
`documentation.yml` is not yet adopted pending further configuration — no narrative
documentation contract is declared in `.vibey-gh.toml`, so none is enforced.

`github-release.yml` is installed and required on this repository. Through vibey-gh
1.26.0 it failed on most pushes to `main`, since it had no way to skip a push that
carried no version bump and most of this repository's promotions are exactly that —
fixed upstream in 1.27.0, where that case is now a clean no-op rather than an error. See
[.vibey-gh.toml](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/.vibey-gh.toml)'s
`[install]` comment for the full history. `release.yml`'s own tag-triggered release job
still creates a correct, artifact-carrying release independently of this workflow.

## Local review fallback

The exact-head review runs on a paid API, and an exhausted key fails that job *before the
model runs* — which, because the gate is a required check, turned a billing problem into a
hard stop on every pull request (#50, #51, #52 and #54 all had to be admin-merged for
exactly this). `[pr_automation.fallback]` closes that: when the primary returns **no verdict
at all**, a local model on a self-hosted runner reviews the diff instead. It never overrides
a review that actually ran — the job requires the primary to have produced no verdict, not
merely to have failed — so genuine findings are never discarded for a weaker opinion.

The verdict is deliberately narrower than the primary's. Constrained decoding guarantees the
output *shape*, which is a stronger guarantee than the path it backs up, but not the
*judgments*. So it assesses only what it can ground in the diff, reports the
documentation-contract fields as unevaluated, and the gate titles the result
`PR automation: gate (local fallback)` so a degraded verdict is never mistaken for a full
one.

This is the one place this repository uses a self-hosted runner, which GitHub says should
"almost never be used for public repositories". Four things make it defensible:
`trusted_only` keeps fork pull requests off the runner entirely; `pull_request_target` means
a pull request cannot alter the workflow that reviews it; the job holds no secrets and never
executes repository code (the diff reaches the model as text); and the runner is ephemeral
and containerised, taking one job before being destroyed. When the runner is offline the job
cannot be scheduled and behaviour degrades to exactly what it was before — a failed gate a
human resolves, which is the correct fail-open direction.

One consequence of `pull_request_target` is worth knowing before changing this workflow:
GitHub executes the **base branch's** copy, so a pull request that adds or edits a job in
`pr-automation.yml` cannot exercise its own change. The fallback was enabled in #59 and
could not run there for exactly that reason; it became live for pull requests opened after
that merged. The same bootstrap applies to any future edit here.

## Exact-head PR automation

`vibey-gh`'s design principle is that only evidence produced against a pull request's
*exact current head commit* counts — a check that ran against an earlier commit, or a
review approving an earlier commit, is stale the moment the branch moves. The merge train
applies this mechanically: readiness is not a draft, no merge conflicts, every check green,
and no outstanding changes-requested review, evaluated fresh each run rather than cached
from a prior pass. A pull request held back only by the review requirement is labeled and
its owner is mentioned once, so a real contribution does not sit unnoticed; a draft or a
red build gets neither, because that is the contributor's own next step, not something
worth paging anyone about.

## AI trust boundary

The one workflow that runs an AI agent with write access, `Currency research`, is scoped
tightly: it may only edit skill content for dated claims, must attach its research sources
in the pull request body, and is explicitly forbidden from merging, closing, changing
repository settings, or pushing to `develop` or `main` directly — it can only open a pull
request into `develop`, which the ordinary review and merge-train path then evaluates like
any other contribution. It also carries the fingerprint trailer, same as a human commit.

## Credentials and settings

`ANTHROPIC_API_KEY` and `AUTOMERGE_TOKEN` are configured as repository secrets.
`AUTOMERGE_TOKEN` exists because a branch ruleset that requires an approving review cannot
be satisfied by the default `GITHUB_TOKEN`, and because a push authenticated as
`github-actions[bot]` does not trigger further workflows — a release chain downstream of an
automated merge would silently stop. Settings -> Actions -> General must allow Actions to
create and approve pull requests, or the merge train and the promotion cannot open theirs.

## Permanent-branch safety

`develop` and `main` are permanent branches, protected by rulesets that both trainings
respect: they may advance, but neither this automation nor a human is expected to delete or
force-push them. `develop` is realigned onto `main` after every release by fast-forward
only — the job checks the two trees are byte-identical first, so it can never discard work,
and never back-merges by hand.

## Failure recovery

`automation-bootstrap.yml` exists for the case the privileged automation itself is broken:
an admin-only, manually dispatched recovery merge, gated on an open non-draft pull request
against `develop`, an exact head match, changes confined to workflow/template/automation
paths, and every non-gate check green. Outside that narrow path, a failed required check
blocks the merge train exactly as intended, and the fix is the ordinary one — push a new
commit and let the checks run again against the new head.

**The exact-head review can fail for a reason that has nothing to do with the PR**:
`pr-automation.yml`'s own gate messaging distinguishes this case by design — "Scans passed
for this exact head, but the exact-head review returned no verdict... This is an
infrastructure or operator failure rather than a defect in the pull request. Check the
review job log for API credit balance, credentials, or model availability, then rerun." A
review job that shows `is_error: true` with `num_turns: 1`, `total_cost_usd: 0`, and empty
`modelUsage` in its result JSON failed before the model ran at all — most often exhausted
`ANTHROPIC_API_KEY` credits. The ordinary fix is `gh run rerun <run-id> --failed` once
credits are restored.

If a merge genuinely can't wait for that, the fallback is a manual, human-equivalent
review posted in the same shape `gate` itself posts, so the check-run contract stays
identical whether the review ran automatically or was done by hand:

```bash
gh api "repos/<owner>/<repo>/check-runs" --method POST \
  -f name='PR automation / gate' -f head_sha="<exact head SHA>" \
  -f status=completed -f conclusion=success \
  -f "output[title]=PR automation: manual review (API credits exhausted)" \
  -f "output[summary]=Reviewed by hand in place of the exact-head review, which failed with is_error and zero cost/turns (credit exhaustion, not a PR defect). <one-line verdict>."
```
Only ever do this after actually reading the diff — it substitutes for the review, not for
having one.

## Changing workflows

The four hand-authored workflows are edited directly; their `name:` fields are load-bearing
(`CI` and `Release` are watched by name elsewhere) and must not change casually. The twelve
`vibey-gh`-managed workflows are edited by changing `.vibey-gh.toml`'s `[install]`
`workflows` list or the relevant config table, then running `vibey-gh install` — a manual
edit to one of these files is reported as "out of date" by `vibey-gh check` and overwritten
on the next `install`. Adding a new managed template is a one-line config change followed
by `vibey-gh install`; removing one requires deleting the generated file by hand, since
`install` never deletes.

---

Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
