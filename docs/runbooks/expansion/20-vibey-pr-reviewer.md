# Runbook: vibey-pr-reviewer — daily review, merge, and deploy across accounts

## Goal

A new repo, `vibey-pr-reviewer`, submoduled into the umbrella (runbook
19). Once a day it reviews every open pull request across the operator's
GitHub accounts, and merges and deploys the ones that are safe — escalating
to the human only when there is a catastrophic reason not to proceed.

## The design problem, stated honestly

The instruction is "merge and deploy automatically unless there is a
CATASTROPHIC reason not to". Taken literally that is an enormous standing
grant: the default is *ship*, and the bot is trusted to recognise the
exceptions. Most review bots invert this — default hold, escalate to
ship — precisely because recognising catastrophe is harder than
recognising safety.

This runbook implements the requested default. It is workable, and the
thing that makes it workable is that **"catastrophic" is enumerated in
advance rather than judged in the moment.** A bot asked to decide at 3am
whether a database migration is catastrophic will sometimes say no. A bot
told "migrations never auto-merge" will not.

So the design is: a **wide default-yes**, bounded by a **narrow,
explicit, non-negotiable stop list**. If the stop list is right, the
default is safe. If the stop list is guessed at, no amount of model
judgement rescues it.

### The stop list (never auto-merge, always escalate)

Not judgement calls. Mechanical detections, each one a hold:

- **Secrets and credentials** — any diff touching a secret store, an env
  var name matching a credential pattern, a `.env`, a key, a cert.
- **Permissions and access** — IAM, RBAC, `securityContext`, auth
  middleware, CORS, public/private toggles, branch protections.
- **Data migrations and destructive SQL** — anything irreversible without
  a restore. The ledger is append-only for the same reason.
- **Infrastructure and cost** — Terraform/Helm/chart values touching
  replicas, instance sizes, storage classes, network exposure, or
  anything that changes the bill.
- **Dependency additions** and lockfile changes introducing a new
  transitive package — supply chain.
- **Deletion at scale** — a diff removing more than a stated threshold of
  code or any test file.
- **CI/gate configuration** — the gate-integrity concern from runbook 18.
  A PR that lowers a coverage floor must never merge itself.
- **Anything the repo's own CODEOWNERS marks as requiring a human.**
- **Red or missing CI.** Green checks are a precondition, not a factor to
  weigh.

Everything outside that list, with green CI and a clean review, merges.

### Deploy is a separate grant from merge

Merging is reversible: revert the commit. Deploying may not be —
it can move money, page people, or corrupt state. So deploy is its own
opt-in per repo, and a repo may be merge-auto / deploy-manual. Treating
them as one switch is how a safe merge policy becomes an unsafe deploy
policy.

Where deploy is enabled it requires a rollback path the bot itself can
execute, and it verifies health after deploying rather than assuming
success.

## Design

1. **Multi-account.** Credentials per account (App installation or PAT),
   never one token spanning everything. An account can be
   review-only, and a repo can opt out entirely. The blast radius of a
   compromised credential is one account, and the config makes that
   visible rather than implied.
2. **Review before verdict.** The review is a real one — vibey already
   has the machinery to run gates, read diffs, and produce findings. A
   merge decision made without reading the diff is a rubber stamp with
   extra steps.
3. **The daily run is a vibey project**, not a bespoke script. Same
   queue, same ledger, same budget caps, same park-on-human-input
   contract. A PR needing a human becomes a `human_gate` row, and the bot
   never blocks waiting for the answer.
4. **Notification on hold.** Every escalation reaches the human through
   the notify seam (runbook 12's webhooks), with the stop-list reason
   named. "Held" with no explanation trains people to ignore it.
5. **Full audit trail.** Every merge and deploy is a ledger entry with
   the diff hash, the checks that passed, and the rule that permitted it.
   When this eventually merges something it should not have, the question
   will be *why*, and the answer has to be reconstructable.
6. **Kill switch.** One flag stops all merging and deploying across all
   accounts, effective on the next poll, no redeploy needed.
7. **Attribution.** Merges and comments carry the provenance line
   (runbook 18), so a collaborator seeing the PR knows what merged it.

## Work items

1. Repo scaffold matching family conventions (onion, gates, release-please).
2. Multi-account credential model + per-repo policy (review / merge /
   deploy).
3. The stop-list detector — mechanical, tested per rule, no model
   judgement in the path.
4. Review pass reusing vibey's existing gate and diff machinery.
5. Merge executor + audit ledger entries.
6. Deploy executor, separate grant, with rollback and post-deploy health.
7. Escalation notifications with named reasons; kill switch.
8. Daily schedule as a vibey project; Job/CronJob chart per runbook 16.

## Verification

- A seeded PR touching each stop-list category is held, every time, with
  the correct reason named. This is the primary bar and is tested per
  rule, not sampled.
- A trivial green PR merges unattended, with a ledger entry naming the
  rule that allowed it.
- A PR with red CI never merges under any configuration.
- The kill switch halts an in-flight daily run at the next poll.
- A revoked credential for one account leaves the others working.
- A deploy failure triggers rollback and notifies, and the ledger shows
  both.

## Needs from operator

- The account list, and per-account credentials.
- Per-repo policy: review-only, auto-merge, or auto-merge + auto-deploy.
- The deletion-threshold number for the stop list.
- Confirmation of the default-yes posture, which is the load-bearing
  decision in this runbook.

## Risks

- **The stop list is the whole safety argument.** If it is incomplete,
  the default-yes posture ships the gap. It should start longer than
  feels necessary and be shortened on evidence, never lengthened after an
  incident.
- **Auto-deploy irreversibility.** Separate grant, rollback required,
  and deploy stays off until merge has been trustworthy for a while.
- **A compromised credential now has merge rights.** Per-account scoping,
  no cross-account tokens, kill switch, and full audit.
- **Rubber-stamping under volume.** If the bot merges 40 PRs a day
  without a hold, that is a signal the stop list is too narrow, not that
  everything is fine. Track the hold rate as a health metric.
- **Nobody reads the escalations.** Named reasons and a low hold rate are
  what keep them meaningful.
