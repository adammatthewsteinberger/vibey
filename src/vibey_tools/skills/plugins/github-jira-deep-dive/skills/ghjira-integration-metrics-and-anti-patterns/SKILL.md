---
name: ghjira-integration-metrics-and-anti-patterns
description: "Use when wiring GitHub and Jira together or deciding what to measure: the integration patterns including smart commits, branch and pull request linking, deployment tracking and which system holds the truth, metrics such as DORA, cycle time and flow and what each measurement actually incentivises, and the anti-patterns that show up across both tools."
---

# GitHub and Jira: Integrating GitHub and Jira, Metrics, and Anti-Patterns

> **Part 5 of 6** of the *GitHub and Jira* reference (plugin `github-jira-deep-dive`), covering §23–§25. Sibling skills: `ghjira-git-data-model-branching-and-recovery` (§0–§4), `ghjira-github-repos-reviews-actions-security-and-identity` (§5–§12), `ghjira-jira-configuration-workflows-and-jql` (§13–§16), `ghjira-jira-boards-automation-permissions-and-hygiene` (§17–§22), `ghjira-reference` (§26–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> mechanics in §1–§25 → `ghjira-git-data-model-branching-and-recovery`, `ghjira-github-repos-reviews-actions-security-and-identity`, `ghjira-jira-configuration-workflows-and-jql`, `ghjira-jira-boards-automation-permissions-and-hygiene` to outlive them.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ The tool does not fix the process** (§1 → `ghjira-git-data-model-branching-and-recovery`). **A broken workflow encoded in Jira is
>    a broken workflow with better reporting, and most "we need to configure X" requests
>    are really "we haven't agreed how we work."**
> 2. **⚠️ Understand Git's data model and most Git problems dissolve** (§2 → `ghjira-git-data-model-branching-and-recovery`). **Almost all
>    Git confusion comes from learning commands instead of the object graph.**
> 3. **⚠️ Configuration debt is the real cost in both systems** (§16 → `ghjira-jira-configuration-workflows-and-jql`, §24). **Every scheme,
>    custom field, workflow and ruleset you add is permanent maintenance, and neither tool
>    makes removal easy.**

---

## §23. Integrating GitHub and Jira

**⚠️ The standard pattern is issue-key-in-branch-and-commit:**
```
⚠️ Branch name:   PROJ-123-short-description
⚠️ Commit message: PROJ-123 fix the thing
⚠️ PR title:      PROJ-123 Fix the thing
   → ⚠️ Jira shows linked branches, commits, PRs and builds on the issue
   → ⚠️ Smart commits can transition issues from the commit message
   → ⚠️ Automation can transition on PR open/merge (§19)
```
**⚠️ Why the convention matters more than the tooling**: ⚠️ **the entire integration hangs
on the issue key being present.** **Enforce it with a ruleset or a CI check rather than
with reminders.**
**⚠️ The genuine architectural question**: ⚠️ **which system is the source of truth for
STATUS?** **Having both means reconciliation, and the workable answers are either
"Jira, and GitHub events update it automatically" or "engineers live in GitHub, Jira is
generated."** **⚠️ What fails is asking people to update both manually.**
**⚠️ Do you need both?** ⚠️ **For a single engineering team with no service-desk or
portfolio needs, GitHub Issues and Projects may genuinely suffice** (§10 → `ghjira-github-repos-reviews-actions-security-and-identity`). **Jira earns its
place with multiple teams, non-engineering stakeholders, complex workflow requirements, or
ITSM** (§21 → `ghjira-jira-boards-automation-permissions-and-hygiene`).

---

## §24. ⚠️ Metrics

**⚠️ DORA's four keys are the best-validated delivery metrics available:**
```
⚠️ DEPLOYMENT FREQUENCY · LEAD TIME FOR CHANGES  (throughput)
⚠️ CHANGE FAILURE RATE · TIME TO RESTORE SERVICE (stability)
⚠️ Later work adds RELIABILITY as a fifth
```
⚠️ **The key research finding is that throughput and stability are NOT a tradeoff** —
**high performers do better on both, which refutes the "move fast and break things vs move
slow and be safe" framing.**
> **⚠️ GOTCHA — DORA metrics are TEAM diagnostics, not individual performance measures,
> and using them for the latter destroys them.** ⚠️ **Anything measured in Jira or GitHub
> can be gamed: commit counts reward churn, lines changed reward verbosity, story points
> inflate, ticket counts reward splitting.** **⚠️ Goodhart's law is unusually fast here
> because the measurement is fully under the measured party's control.**
> **⚠️ Never measure individuals with these systems.** **Use them to find where WORK gets
> stuck.**

**⚠️ Flow metrics worth watching instead of output counts**: **cycle time distribution
(⚠️ the 85th percentile is more useful than the mean for forecasting), WIP, flow
efficiency (⚠️ active time ÷ total elapsed — typically shockingly low, often under 20%,
and that gap IS the improvement opportunity), and blocked time.**
**⚠️ The single most actionable thing in most teams is PR review latency** (§6 → `ghjira-github-repos-reviews-actions-security-and-identity`) —
**it's measurable, it's usually large, and it's fixable by agreement rather than tooling.**

---

## §25. Anti-Patterns

```
⚠️ Configuring the tool instead of deciding the process (§1)
⚠️ Editing a shared Jira scheme without checking what else uses it (§13)
⚠️ Creating a custom field instead of reusing one (§13, §22)
⚠️ Choosing team-managed/company-managed without knowing the difference (§14)
⚠️ Fifteen-status workflows nobody updates accurately (§15)
⚠️ status != Done instead of resolution = Unresolved (§16)
⚠️ Velocity as a cross-team or individual performance metric (§17, §24)
⚠️ Huge pull requests, then complaining review is superficial (§6)
⚠️ Long-lived feature branches, then blaming the merge tool (§3)
⚠️ Rebasing shared history; force-push without --force-with-lease (§3)
⚠️ pull_request_target with checkout of PR code (§8)
⚠️ Unpinned third-party actions (§8)
⚠️ Cleaning a leaked secret from history without rotating it first (§9)
⚠️ PATs for automation instead of a GitHub App (§11)
⚠️ Required status checks that never run on skipped paths (§7)
⚠️ Dependabot version updates left ungrouped until everyone ignores them (§9)
⚠️ Asking people to update both Jira and GitHub by hand (§23)
⚠️ Measuring individuals with DORA metrics (§24)
```
