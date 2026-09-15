---
name: ghjira-github-repos-reviews-actions-security-and-identity
description: "Use when configuring or automating GitHub: repositories, organizations and the permission model, pull requests and review including CODEOWNERS, rulesets and branch protection, GitHub Actions with runners, caching, OIDC and workflow security, the security products including code scanning, secret scanning and Dependabot, issues and Projects, the REST and GraphQL API with GitHub Apps and webhooks, and enterprise identity with SAML, SCIM and managed users."
---

# GitHub and Jira: Repos and Permissions, Pull Requests, Rulesets, Actions, Security Products, Issues and Projects, the API, and Enterprise Identity

> **Part 2 of 6** of the *GitHub and Jira* reference (plugin `github-jira-deep-dive`), covering §5–§12. Sibling skills: `ghjira-git-data-model-branching-and-recovery` (§0–§4), `ghjira-jira-configuration-workflows-and-jql` (§13–§16), `ghjira-jira-boards-automation-permissions-and-hygiene` (§17–§22), `ghjira-integration-metrics-and-anti-patterns` (§23–§25), `ghjira-reference` (§26–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Git's data model is fixed; the products churn constantly. See §26 → `ghjira-reference` for the two things that changed materially — Atlassian's Data Center wind-down, and GitHub's security and Copilot repackaging.

> **⚠️ These are workflow systems, not just tools, and that's the whole framing.**
> **Complements a Git-adjacent programming reference, a DevSecOps/CI-CD reference
> (pipeline design), and an engineering-process reference (the methodology these tools
> encode).**
>
> **⚠️ GOTCHA** boxes mark configuration decisions that are painful or impossible to
> reverse, and the places where the tool silently does something other than what you
> expect.
>
> **⚠️ A currency warning specific to this file**: **product surfaces here change on a
> scale of months.** ⚠️ **Treat §26 → `ghjira-reference`'s specifics as a snapshot with dates attached, verify
> pricing and packaging against the vendor before making a decision, and expect the
> mechanics in §1–§25 → `ghjira-git-data-model-branching-and-recovery`, `ghjira-jira-configuration-workflows-and-jql`, `ghjira-jira-boards-automation-permissions-and-hygiene`, `ghjira-integration-metrics-and-anti-patterns` to outlive them.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ The tool does not fix the process** (§1 → `ghjira-git-data-model-branching-and-recovery`). **A broken workflow encoded in Jira is
>    a broken workflow with better reporting, and most "we need to configure X" requests
>    are really "we haven't agreed how we work."**
> 2. **⚠️ Understand Git's data model and most Git problems dissolve** (§2 → `ghjira-git-data-model-branching-and-recovery`). **Almost all
>    Git confusion comes from learning commands instead of the object graph.**
> 3. **⚠️ Configuration debt is the real cost in both systems** (§16 → `ghjira-jira-configuration-workflows-and-jql`, §24 → `ghjira-integration-metrics-and-anti-patterns`). **Every scheme,
>    custom field, workflow and ruleset you add is permanent maintenance, and neither tool
>    makes removal easy.**

---

## §5. Repos, Organizations, Permissions

```
ACCOUNT TYPES   personal · organization · ⚠️ enterprise (a container of orgs)
REPO ROLES      Read · Triage · Write · Maintain · Admin
⚠️ TEAMS        nested teams inherit permissions DOWNWARD.
   ⚠️ Permissions are the UNION of everything granted — there is no deny
CODEOWNERS      ⚠️ auto-request reviews by path; combine with rulesets (§7)
   to make owner review REQUIRED rather than merely requested
```
**⚠️ The permission model is additive, which surprises people coming from systems with
deny rules** — ⚠️ **you cannot subtract access by adding a team; you remove the grant that
provides it.**
**⚠️ Monorepo vs polyrepo**: ⚠️ **monorepo simplifies cross-cutting change, atomic commits
and shared tooling, at the cost of CI complexity and needing path filters and CODEOWNERS
to keep review sane.** **Polyrepo simplifies ownership and access at the cost of
coordinated change.** **⚠️ Neither is right generally; the deciding factor is how often
changes cross repository boundaries.**

---

## §6. Pull Requests and Review

**⚠️ The evidence on review is fairly consistent and mostly ignored:**
```
⚠️ SMALL PRs GET BETTER REVIEWS. Defect-finding drops sharply above a few
   hundred lines. ⚠️ Large PRs get "LGTM" — the review theatre outcome
⚠️ REVIEW LATENCY is usually the dominant term in cycle time (§24), not
   coding time. A PR waiting a day is a day of lead time
⚠️ AUTHORS should make review easy: a description of WHY, a self-review
   pass, and logically separated commits
```
**⚠️ Mechanics worth knowing**: **draft PRs; ⚠️ suggested changes (reviewers can propose
exact edits the author applies in one click — underused); review threads and resolution;
merge queue (⚠️ tests each PR against the state it will actually merge into, which
prevents the semantic conflicts that "green PR, broken main" comes from); auto-merge; and
required conversation resolution.**
**⚠️ Merge strategies**: ⚠️ **merge commit (preserves branch structure), squash (one commit
per PR — the cleanest main history and it discards intermediate commits), rebase-merge
(linear, no merge commit).** **⚠️ Pick one per repo and enforce it (§7); mixing them makes
history hard to reason about.**

---

## §7. Rulesets and Branch Protection

**⚠️ Rulesets are the modern replacement for classic branch protection**, ⚠️ **and the
practical advantages are layering (multiple rulesets apply together), pattern-based
targeting across many branches or tags, fine-grained bypass, and org-level application
across repos.**
```
COMMON RULES  require PR before merge · require N approvals ·
   ⚠️ dismiss stale approvals on new commits · require review from
   CODE OWNERS · require status checks to pass · require linear history ·
   require signed commits · ⚠️ block force pushes · restrict deletions
   ⚠️ require deployments to succeed · require merge queue
```
> **⚠️ GOTCHA — required status checks only work if the check actually RUNS.** ⚠️ **If a
> workflow is skipped by a path filter, the required check never reports, and the PR
> blocks forever waiting for something that will never arrive.** **⚠️ The fix is a
> "always-run" job that reports success for skipped paths, or careful use of
> `paths-ignore` semantics.** **This bites nearly every team that adopts path filters.**

**⚠️ Bypass lists are where governance quietly leaks** — ⚠️ **an admin bypass or an app
with bypass permission means the rule is advisory for that actor.** **Audit them.**
**⚠️ GitHub now offers automatic conversion of classic branch protection rules into
rulesets** (§26.2 → `ghjira-reference`), **which removes the main friction in migrating.**

---

## §8. GitHub Actions

```
WORKFLOW → JOBS → STEPS.  Jobs run in parallel by default; ⚠️ `needs` sequences them
TRIGGERS  push · pull_request · ⚠️ pull_request_target (SEE THE GOTCHA) ·
   schedule · workflow_dispatch · workflow_call (reusable) · repository_dispatch
RUNNERS   GitHub-hosted vs self-hosted; ⚠️ larger runners; custom autoscaling
CONTEXTS  github, env, secrets, vars, matrix
MATRIX    ⚠️ fan out across versions/OSes — the highest-value Actions feature
CACHING   actions/cache; ⚠️ cache keys and restore-keys are where it goes wrong
ARTIFACTS · ENVIRONMENTS (⚠️ with required reviewers for deploy gates) ·
CONCURRENCY groups (⚠️ cancel superseded runs — saves real money)
```
> **⚠️ GOTCHA — `pull_request_target` runs in the context of the BASE repository with
> access to secrets, and it is a well-documented security footgun.** ⚠️ **If you check
> out and execute code from the PR head under `pull_request_target`, a fork PR can
> exfiltrate your secrets.** **⚠️ Use plain `pull_request` for untrusted contributions;
> if you genuinely need `pull_request_target`, do not check out or run PR code in it.**

**⚠️ Other security essentials**: ⚠️ **pin third-party actions to a full commit SHA, not a
tag — tags are mutable and a compromised action is a supply chain compromise**; **set
`permissions:` explicitly at the top of workflows (the default token is broader than most
jobs need); ⚠️ prefer OIDC federation to cloud providers over long-lived stored
credentials; and treat self-hosted runners on public repos as dangerous unless properly
isolated.**
**⚠️ Cost control**: ⚠️ **concurrency cancellation, path filters, caching, and choosing
runner sizes deliberately.** **Actions minutes overages are a common surprise line item.**

---

## §9. Security Products

```
DEPENDABOT      ⚠️ alerts (vulnerable dependencies) · security updates ·
   version updates. ⚠️ Version updates generate a LOT of PRs — group them
   or you train the team to ignore Dependabot entirely
SECRET SCANNING ⚠️ detects committed credentials; PUSH PROTECTION blocks
   them before they land. ⚠️ Push protection is the high-value half
CODE SCANNING   ⚠️ CodeQL (semantic analysis) or third-party SARIF upload
DEPENDENCY REVIEW  ⚠️ diffs dependency changes in the PR
```
> **⚠️ GOTCHA — a leaked secret that has been pushed is compromised, full stop.**
> ⚠️ **Removing it from history does NOT undo the exposure** — **it may be in forks,
> caches, clones and logs.** **⚠️ ROTATE THE CREDENTIAL FIRST, then clean history if you
> want to.** **The order matters and people reliably get it backwards.**

**⚠️ Packaging changed substantially — see §26.2 → `ghjira-reference`**: **GHAS was unbundled into GitHub Secret
Protection and GitHub Code Security as separate products.**

---

## §10. Issues and Projects

**⚠️ GitHub Issues is deliberately lightweight**: **labels, milestones, assignees, issue
forms (⚠️ YAML-defined templates that produce structured input — much better than free
text), task lists, and cross-references.**
**⚠️ Projects (the newer tables/boards) adds custom fields, views, grouping, and roadmap
layouts** — ⚠️ **and it is genuinely capable for small-to-medium teams, which makes "do we
even need Jira?" a real question** (§23 → `ghjira-integration-metrics-and-anti-patterns`).
**⚠️ Where GitHub Issues runs out**: ⚠️ **complex workflow enforcement, granular field-level
permissions, service-desk semantics, portfolio hierarchy across many teams, and
sophisticated reporting.** **That's the actual dividing line.**

---

## §11. API, Apps and Webhooks

```
REST v3        broad, paginated, rate-limited
⚠️ GraphQL v4  ⚠️ fetch exactly what you need in one call. Far better for
   nested data; ⚠️ some operations exist ONLY in one API or the other
WEBHOOKS       ⚠️ verify the HMAC signature. Handle retries and duplicates —
   delivery is at-least-once, so make handlers IDEMPOTENT
```
**⚠️ Authentication choices, and this matters:**
```
⚠️ PAT (classic)         broad scopes, tied to a USER. Avoid for automation
⚠️ Fine-grained PAT      per-repo, per-permission, expiring. Better
⚠️ GITHUB APP            ⚠️ THE right answer for automation: own identity,
   granular permissions, higher rate limits, short-lived installation
   tokens, survives the creator leaving the company
⚠️ OIDC                  for cloud deploys — no stored secret at all (§8)
```
**⚠️ The failure mode a PAT creates**: ⚠️ **automation tied to an individual breaks when
that person's access changes or they leave**, **and it grants their full permissions rather
than the minimum needed.** **Use an App.**

---

## §12. Enterprise Identity

**⚠️ SAML SSO, SCIM provisioning, and the significant fork: EMU.**
> **⚠️ GOTCHA — Enterprise Managed Users (EMU) is close to irreversible and it changes
> what developers can do.** ⚠️ **With EMU, GitHub accounts are created and owned by your
> IdP; users cannot use their personal accounts, cannot contribute to public repos from
> their managed account, and cannot take contribution history with them.**
> **⚠️ It provides genuine control and is the right answer for some regulated
> environments — but decide deliberately, because migrating in or out is a project, not a
> setting.**

**⚠️ Audit log**: **streaming to a SIEM, and ⚠️ retention limits mean you should stream if
you need long-horizon forensics.**
**⚠️ IP allow lists, required 2FA, and repository visibility policies** at org and
enterprise level.

---

# PART III — JIRA
