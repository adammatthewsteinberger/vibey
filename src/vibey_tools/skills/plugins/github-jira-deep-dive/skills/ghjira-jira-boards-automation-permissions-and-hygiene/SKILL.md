---
name: ghjira-jira-boards-automation-permissions-and-hygiene
description: "Use when running or cleaning up a Jira instance: boards, sprints and estimation and what story points do and do not mean, the built-in reports and how to read burndown and velocity honestly, Jira Automation and its limits, the permission and issue-security model, Jira Service Management with queues, SLAs and request types, and configuration hygiene — scheme sprawl, custom field explosion and how to clean it up."
---

# GitHub and Jira: Boards, Sprints and Estimation, Reports, Automation, Permissions, Service Management, and Configuration Hygiene

> **Part 4 of 6** of the *GitHub and Jira* reference (plugin `github-jira-deep-dive`), covering §17–§22. Sibling skills: `ghjira-git-data-model-branching-and-recovery` (§0–§4), `ghjira-github-repos-reviews-actions-security-and-identity` (§5–§12), `ghjira-jira-configuration-workflows-and-jql` (§13–§16), `ghjira-integration-metrics-and-anti-patterns` (§23–§25), `ghjira-reference` (§26–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> mechanics in §1–§25 → `ghjira-git-data-model-branching-and-recovery`, `ghjira-github-repos-reviews-actions-security-and-identity`, `ghjira-jira-configuration-workflows-and-jql`, `ghjira-integration-metrics-and-anti-patterns` to outlive them.**
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

## §17. Boards, Sprints, Estimation

```
SCRUM BOARD   ⚠️ sprints, backlog, sprint commitment, burndown
KANBAN BOARD  ⚠️ continuous flow, WIP limits, cumulative flow diagram
⚠️ WIP LIMITS  the single highest-value Kanban feature and the most ignored.
   ⚠️ Limiting WIP reduces cycle time — Little's Law: WIP = throughput × cycle time
SWIMLANES · QUICK FILTERS · CARD COLOURS
```
**⚠️ Estimation, honestly:**
- ⚠️ **Story points are RELATIVE SIZE, not time**, **and they work by letting a team's
  historical throughput convert points to duration empirically.**
- **⚠️ Velocity is a planning aid for ONE team and is not comparable across teams** —
  ⚠️ **and using it as a performance metric reliably causes point inflation, which is
  Goodhart's law arriving on schedule** (§24 → `ghjira-integration-metrics-and-anti-patterns`).
- **⚠️ Counting ISSUES often forecasts about as well as summing points**, **provided
  issues are broken down to roughly similar size** — **which is a genuinely useful and
  under-known finding.**
- ⚠️ **Probabilistic forecasting from historical cycle time (Monte Carlo) beats
  commitment-based estimation for delivery dates**, **and it doesn't require estimates
  at all.**

---

## §18. Reports

**Burndown/burnup (⚠️ burnup shows scope change, which burndown hides — prefer it),
velocity, cumulative flow diagram (⚠️ the best single Kanban diagnostic: widening bands
mean work is piling up in a stage), control chart (cycle time distribution), sprint
report, and Advanced Roadmaps for portfolio views.**
**⚠️ The reports are only as good as the transitions**: ⚠️ **if people move cards in
batches on Friday, your cycle-time data is fiction.** **This is §1 → `ghjira-git-data-model-branching-and-recovery` again.**

---

## §19. Automation

**⚠️ Jira Automation (rules: trigger → condition → action) is the highest-leverage feature
most teams under-use.**
```
⚠️ Transition parent when all subtasks are done
⚠️ Assign based on component; notify a Slack channel on blocker creation
⚠️ Comment and transition when a linked PR merges (§23)
⚠️ Escalate priority when an SLA is breached (§21)
⚠️ Sync fields between linked issues
⚠️ Flag stale issues automatically rather than by nagging
```
**⚠️ Watch for**: ⚠️ **rule loops (rule A triggers rule B triggers A — Jira has loop
detection, but design against it), execution limits on lower plans, and rules running as a
user whose permissions matter.**
**⚠️ Automation is usually the right answer to "we need people to remember to..."** —
**people won't; the rule will.**

---

## §20. Permissions

**⚠️ Three distinct layers that get confused:**
```
⚠️ GLOBAL permissions       site-level (who can administer)
⚠️ PROJECT permission scheme  who can browse, create, edit, transition,
   assign, comment, delete within a project
⚠️ ISSUE SECURITY scheme    who can SEE individual issues — used for
   sensitive work (HR, security, legal) inside an otherwise open project
```
**⚠️ Plus filter/dashboard sharing permissions, which are separate again** (§16 → `ghjira-jira-configuration-workflows-and-jql`) —
⚠️ **and the classic confusion is "why can't they see the board?" when the answer is the
underlying FILTER isn't shared.**
**⚠️ Grant via GROUPS or PROJECT ROLES rather than individuals** — ⚠️ **roles are the more
maintainable choice because they're per-project and can be populated by the project lead
without an admin.**

---

## §21. Jira Service Management

**⚠️ Different semantics from Jira Software, and worth knowing even if you don't
administer it:**
**request types (⚠️ the customer-facing presentation of an underlying issue type), the
customer portal, queues, SLAs with calendars and pause conditions, approvals,
knowledge base integration, and asset/CMDB management.**
**⚠️ ITSM practices**: **incident, problem, change, service request** — **and ⚠️ the
licensing model differs (AGENTS are licensed; customers raising requests are not), which
is the main cost driver.**

---

## §22. ⚠️ Configuration Hygiene

**⚠️ Jira instances accumulate debt relentlessly and nobody is assigned to clean it.**
```
⚠️ Custom field sprawl — near-duplicates, unused fields, performance cost
⚠️ Workflow proliferation — dozens of nearly-identical workflows
⚠️ Orphaned schemes attached to nothing
⚠️ Statuses that mean the same thing with different names
⚠️ Dead automation rules and stale filters/dashboards
⚠️ Permission grants to people who left
```
**⚠️ The practices that work**: ⚠️ **a naming convention enforced from day one; a small
number of STANDARD workflows that projects adopt rather than each inventing one; a
periodic audit; a sandbox for testing configuration changes (⚠️ available on higher
plans, and worth it); and someone actually accountable for the instance.**
**⚠️ The hardest part is deletion** — ⚠️ **removing a populated custom field destroys its
data, so audits tend to produce lists nobody acts on.** **Prevent rather than remediate.**

---

# PART IV — TOGETHER
