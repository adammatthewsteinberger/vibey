---
name: research-weekly-pull-request
description: Use when packaging the results of an automated research or audit run into a reviewable pull request — branch and commit conventions, the PR body that lets a reviewer check the sources without redoing the work, what to do when nothing changed, and the scope limits an unattended job must respect. Triggers on opening a PR from a scheduled job, automation pull request, weekly audit report, and "what should this bot do when it finds nothing".
---

# The Weekly Pull Request

How an unattended research run reports what it found, so a human can approve or reject it in
a few minutes.

---

## The reviewer is the constraint

Nobody reads a large pull request from a bot carefully. They either merge it on trust — which
defeats the point of the audit — or they leave it open until it rots. **Every decision below
optimises for a pull request a busy maintainer can verify in about five minutes.**

That means: few edits, each small, each with its source, and a body that states plainly what
was checked and what was found — including what was checked and found *unchanged*.

---

## When nothing changed

**Do not open a pull request.** A no-change run is the expected outcome and it should be
silent in the repository's history.

Report the result where the run is visible instead — the job summary, or a comment on an
existing tracking issue if the workflow provides one. Say which plugins were audited, which
claims were checked, and what sources were consulted. That record is what stops the next run
from repeating identical searches with no memory.

⚠️ **Never open an empty or cosmetic pull request to demonstrate that the job ran.** The job's
own logs demonstrate that.

---

## Branch and commit

- **Branch:** `claude/currency-<ISO date>` — dated, so concurrent or retried runs do not collide.
- **Base:** the repository's integration branch (`develop` here), not `main`.
- **One commit** unless the edits are genuinely independent; a reviewer reading a two-file diff
  does not benefit from five commits.
- **Commit subject:** name the plugins touched and the nature of the change, e.g.
  `Refresh currency claims in semiconductors and wireless (2 plugins)`.
- **Commit body:** one line per edit — what changed, from what to what, and the source.
- **Commit trailer:** every commit carries the repository's fingerprint trailer. It is
  mandatory and enforced in CI, so a commit without it fails the pull request:

  ```
  Made-With: Vibey, the auto-vibecoding machine by Adam Matthew Steinberger
  ```

---

## The pull request body

Use this shape. It exists so a reviewer can check the *sources* rather than re-run the *research*.

```markdown
## Weekly currency audit — <date>

Audited: <plugin>, <plugin>, <plugin>  (rotation slice N of M)

### Changes proposed

**<plugin> — `<skill>` §<N>**
- **Was:** <the existing claim, quoted or closely paraphrased>
- **Now:** <the replacement>
- **Source:** <publisher>, *<title>*, <date> — <what it actually says>
- **Confidence:** <direct statement / inference / single source>

### Checked, unchanged

- **<plugin> §<N>** — <claim> still current as of <source + date>.

### Unresolved

- **<plugin> §<N>** — <what is ambiguous, what you looked for, why you did not edit>
```

Rules for the body:

- **Quote the before-state.** A reviewer cannot judge an edit they have to reconstruct.
- **Name the source inline.** "Per the vendor's changelog" is not a source; the changelog with
  its date is.
- **List what you checked and did not change.** This is the most valuable section for the next
  run, and the one most often omitted.
- **Put genuine uncertainty in "Unresolved" rather than resolving it yourself.** A question
  raised is worth more than a wrong edit made.
- **State the tool honestly.** The run is automated; say so, and do not write the body as
  though a person did the reading.

---

## Scope limits for an unattended run

An unattended job has no judgement in the loop, so it operates inside hard limits.

**Do:**
- edit only the plugins named in the run's rotation slice;
- keep to a handful of edits — if a run wants more than roughly five, it has misunderstood
  its job and should raise the rest as "Unresolved" instead;
- change the smallest span of text that makes the claim correct;
- leave the pull request in draft if any edit is uncertain.

**Do not:**
- restructure, re-split, rename, add or delete skills or plugins;
- renumber sections, or reflow text that did not need to change;
- touch the release machinery, workflows, `pyproject.toml`, or the package version;
- merge the pull request, or push to `main` or `develop` directly;
- use a repository CLI or API for anything beyond creating and describing the pull
  request — no merging, closing, approving, releasing or changing settings, even when
  the credentials would allow it;
- edit a plugin the slice did not name, however tempting.

⚠️ **The three things that must never happen**, in order of severity:

1. **A fabricated source.** A citation that does not resolve, or a figure attributed to a
   document that does not contain it. This poisons the whole reference and is unrecoverable
   by review, because reviewers check the plausible-looking ones least.
2. **A silent change.** Any edit not described in the pull request body.
3. **A deletion of inconvenient evidence.** Hedging, error bars, dissenting sources and
   "sources disagree" notes are the most valuable content in these documents and the easiest
   to quietly lose while "updating" a section.

---

## Failure and partial results

- If a search tool or the network is unavailable, **stop and report it.** Do not fall back to
  recalled knowledge — see `research-search-and-source-quality`.
- If the repository's checkers fail on your edit, fix it or drop that edit. Never open a
  pull request that is known to fail CI.
- If the run is interrupted, **an incomplete audit that says which plugins it got through is
  fine.** A complete-looking audit that silently skipped half its slice is not.
