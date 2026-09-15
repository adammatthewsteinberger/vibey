---
name: ghjira-jira-configuration-workflows-and-jql
description: "Use when configuring Jira or writing a query: Jira's configuration model of schemes, screens, fields and issue types and why it sprawls, the real differences between team-managed and company-managed projects and how to choose, workflows, statuses and transitions with conditions, validators and post-functions, and JQL including its operators, functions and the queries that actually get used."
---

# GitHub and Jira: Jira's Configuration Model, Team-Managed Versus Company-Managed, Workflows and Statuses, and JQL

> **Part 3 of 6** of the *GitHub and Jira* reference (plugin `github-jira-deep-dive`), covering §13–§16. Sibling skills: `ghjira-git-data-model-branching-and-recovery` (§0–§4), `ghjira-github-repos-reviews-actions-security-and-identity` (§5–§12), `ghjira-jira-boards-automation-permissions-and-hygiene` (§17–§22), `ghjira-integration-metrics-and-anti-patterns` (§23–§25), `ghjira-reference` (§26–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> mechanics in §1–§25 → `ghjira-git-data-model-branching-and-recovery`, `ghjira-github-repos-reviews-actions-security-and-identity`, `ghjira-jira-boards-automation-permissions-and-hygiene`, `ghjira-integration-metrics-and-anti-patterns` to outlive them.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ The tool does not fix the process** (§1 → `ghjira-git-data-model-branching-and-recovery`). **A broken workflow encoded in Jira is
>    a broken workflow with better reporting, and most "we need to configure X" requests
>    are really "we haven't agreed how we work."**
> 2. **⚠️ Understand Git's data model and most Git problems dissolve** (§2 → `ghjira-git-data-model-branching-and-recovery`). **Almost all
>    Git confusion comes from learning commands instead of the object graph.**
> 3. **⚠️ Configuration debt is the real cost in both systems** (§16, §24 → `ghjira-integration-metrics-and-anti-patterns`). **Every scheme,
>    custom field, workflow and ruleset you add is permanent maintenance, and neither tool
>    makes removal easy.**

---

## §13. ⚠️ Jira's Configuration Model

**⚠️ The thing that makes Jira administration hard: a project's behaviour comes from
several SCHEMES that are often SHARED between projects.**
```
PROJECT
 ├─ ⚠️ Issue type scheme         which types exist
 ├─ ⚠️ Workflow scheme           type → workflow mapping
 ├─ ⚠️ Screen scheme             which fields appear, when
 ├─ ⚠️ Field configuration scheme  required/optional, hidden
 ├─ ⚠️ Permission scheme         who can do what
 ├─ ⚠️ Notification scheme       who gets emailed
 └─ ⚠️ Issue security scheme     who can SEE issues
```
> **⚠️ GOTCHA — schemes are shared by default, and this is the number one cause of
> accidental Jira damage.** ⚠️ **Editing a workflow or scheme "for one project" changes
> every project using it**, **often dozens, often without warning that matters.**
> **⚠️ ALWAYS check what else uses a scheme before editing.** **Copy the scheme and modify
> the copy if the change is genuinely project-specific — accepting that this adds to
> configuration debt** (§22 → `ghjira-jira-boards-automation-permissions-and-hygiene`).

**⚠️ Custom fields are the other trap**: ⚠️ **each one has a global performance cost, they
accumulate relentlessly, near-duplicates proliferate ("Team", "Team Name", "Owning
Team"), and they are painful to remove once populated.** **⚠️ Reuse before creating.**

---

## §14. ⚠️ Team-Managed vs Company-Managed

**⚠️ The most consequential decision when creating a Jira Cloud project, and it is made by
people who don't know it's consequential.**
```
⚠️ TEAM-MANAGED (formerly next-gen)
  + Configured BY THE TEAM, in the project, no admin needed
  + Fast to set up, self-contained, easy to understand
  ⚠️ − Configuration is NOT shared or reusable across projects
  ⚠️ − Limited advanced features and cross-project reporting
  ⚠️ − Its custom fields are project-scoped, complicating global JQL

⚠️ COMPANY-MANAGED (formerly classic)
  + Shared schemes, consistency across many projects, full feature set
  + Better for portfolio reporting and org-wide standards
  ⚠️ − Requires a Jira admin for changes; slower to adapt
  ⚠️ − Shared schemes mean shared blast radius (§13)
```
**⚠️ Choosing badly is expensive**: ⚠️ **there is no clean in-place conversion between the
two — migration means moving issues between projects, with the associated loss of some
history and links.**
**⚠️ The rough guidance**: **independent team, wants autonomy, doesn't need cross-project
rollup → team-managed.** **Many teams needing consistent process, portfolio reporting, or
regulated workflow → company-managed.**

---

## §15. Workflows and Statuses

**⚠️ A workflow is statuses plus transitions, with four extension points that do the real
work:**
```
⚠️ CONDITIONS   who can SEE the transition button
⚠️ VALIDATORS   what must be TRUE to complete it (e.g. field required)
⚠️ POST FUNCTIONS  what happens AFTER (assign, set field, fire event)
⚠️ TRIGGERS     external events (e.g. a commit or PR) causing transition (§23)
```
**⚠️ Statuses are global objects; status CATEGORIES (To Do / In Progress / Done) drive
board columns and reporting** — ⚠️ **a status in the wrong category silently breaks
velocity and burndown, and it's a common misconfiguration.**
**⚠️ The design advice that actually matters**: ⚠️ **start with the simplest workflow that
could work and add only when a real failure demands it.** **Every extra status is a
handoff, a place work waits, and a thing people must remember to update** — ⚠️ **and a
workflow with fifteen statuses will be updated inaccurately, which destroys the reporting
it was built for** (§1 → `ghjira-git-data-model-branching-and-recovery`).

---

## §16. JQL

```
FIELDS      project · status · assignee · reporter · created · updated ·
            resolution · labels · sprint · fixVersion · component
OPERATORS   = != > < IN NOT IN ~ (contains) IS EMPTY WAS CHANGED
⚠️ FUNCTIONS currentUser() · startOfWeek() · endOfMonth() · membersOf() ·
            linkedIssues() · ⚠️ sprintsByState()
⚠️ HISTORY   WAS, WAS IN, CHANGED — query PAST states. Underused and powerful
ORDER BY    Rank is the board ordering
```
**⚠️ Genuinely useful patterns:**
```
⚠️ resolution = Unresolved            ← ⚠️ NOT status != Done. Resolution is
   the reliable "is it finished" field; status names vary by workflow
assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC
⚠️ status CHANGED TO "In Progress" AFTER -7d      ← what started recently
⚠️ status WAS "Blocked" DURING (-30d, now())      ← what got stuck
updated < -14d AND resolution = Unresolved        ← stale work
⚠️ project = X AND issuetype = Bug AND priority IN (Highest, High)
   AND created > startOfWeek(-1w)
```
**⚠️ The most common JQL error is using `status != Done`** — ⚠️ **it silently misses issues
in other terminal statuses (Won't Do, Duplicate, Cancelled) and breaks the moment someone
adds a status.** **Use `resolution = Unresolved`.**
**⚠️ Filters underpin boards, dashboards and subscriptions** — ⚠️ **so filter PERMISSIONS
matter: a board sharing a filter that its viewers can't see produces confusing empty
boards.**
