---
name: ghjira-reference
description: "Use when correcting a GitHub or Jira misconception, looking up a limit, quota or plan difference, or needing a command and JQL quick reference — plus the current state of Atlassian's Data Center wind-down and GitHub's security and Copilot repackaging. Companion to the other GitHub and Jira skills."
---

# GitHub and Jira: What's Live, Misconceptions, and Quick Reference

> **Part 6 of 6** of the *GitHub and Jira* reference (plugin `github-jira-deep-dive`), covering §26–§29. Sibling skills: `ghjira-git-data-model-branching-and-recovery` (§0–§4), `ghjira-github-repos-reviews-actions-security-and-identity` (§5–§12), `ghjira-jira-configuration-workflows-and-jql` (§13–§16), `ghjira-jira-boards-automation-permissions-and-hygiene` (§17–§22), `ghjira-integration-metrics-and-anti-patterns` (§23–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Git's data model is fixed; the products churn constantly. See §26 for the two things that changed materially — Atlassian's Data Center wind-down, and GitHub's security and Copilot repackaging.

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
> scale of months.** ⚠️ **Treat §26's specifics as a snapshot with dates attached, verify
> pricing and packaging against the vendor before making a decision, and expect the
> mechanics in §1–§25 → `ghjira-git-data-model-branching-and-recovery`, `ghjira-github-repos-reviews-actions-security-and-identity`, `ghjira-jira-configuration-workflows-and-jql`, `ghjira-jira-boards-automation-permissions-and-hygiene`, `ghjira-integration-metrics-and-anti-patterns` to outlive them.**
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

## §26. What's Live — verified August 2026

> **⚠️ Both vendors reprice and repackage frequently. Everything below carries a date;
> verify against the vendor before committing budget.**

### 26.1 ⚠️ Atlassian: Data Center is ending, and the dates are the whole story
**⚠️ If you run self-managed Atlassian, this is a migration project with a deadline, not a
watching brief.**

- **⚠️ Announced 8 September 2025.** **The timeline as published:**
```
⚠️ 17 Feb 2026   Data Center PRICE INCREASES take effect (~15% standard list;
                 ⚠️ reported 18–40% for legacy "Advantage" pricing depending
                 on tier, as those are brought to standard list)
⚠️ 30 Mar 2026   END OF SALE for NEW customers. After this, Cloud is the only
                 entry point to the Atlassian ecosystem
⚠️ 30 Mar 2028   Last date EXISTING customers can buy new licences, app
                 licences or tier expansions. After that: renewal only
⚠️ 28 Mar 2029   END OF LIFE. Instances go READ-ONLY; no support, no updates
```
- **⚠️ Affected products include Jira Software, Jira Service Management, Confluence,
  Bamboo and Crowd.** ⚠️ **Bitbucket Data Center is treated differently — reported dual
  licensing for Bitbucket DC and Cloud, recognizing on-prem source-code requirements —
  though sources characterize that as a reprieve rather than a permanent exemption.**
- **⚠️ Feature development for Data Center has effectively stopped**; **innovation is in
  Cloud only.**

> **⚠️ GOTCHA — the "existing customer" definition is narrower than people assume and it
> catches organizations off guard.** ⚠️ **Status is evaluated PER PRODUCT: if you run
> Jira Software on Data Center today but want to add Jira Service Management on Data
> Center, you are a NEW customer for that product and cannot.**
> **⚠️ It's also evaluated per entity — a parent company's Data Center licences cannot be
> extended to cover a newly acquired subsidiary after March 2026.** **⚠️ This matters
> enormously for M&A and for phased platform expansion.**

**⚠️ Constrained environments have a genuine problem, and it should be named**:
⚠️ **air-gapped deployments have no Atlassian Cloud option; Atlassian's Isolated Cloud
(expected 2026) is reported as internet-connected and Atlassian-managed.** ⚠️ **Government
Cloud has a much smaller app ecosystem — around 60 Marketplace apps versus 4,000+
commercially — with apps needing rebuilding as Forge apps.** **⚠️ And Jira Align has no
reported compliant cloud path for some regulated users, which makes SAFe portfolio
management a separate tooling decision.**
**⚠️ Rovo is the other commercial change to watch**: **Atlassian's AI layer, reported at
$20/user/month on Cloud Premium and Enterprise** — ⚠️ **the most expensive Atlassian
add-on, and appearing in enterprise renewal quotes.** **⚠️ Reported pricing model has
shifted twice since launch; treat the number as a snapshot and evaluate genuine
utilization before committing.**

### 26.2 ⚠️ GitHub: security unbundled, Copilot repriced twice
- **⚠️ GitHub Advanced Security no longer exists as a single SKU.** **From 1 April 2025 it
  was split into two standalone products:**
```
⚠️ GITHUB SECRET PROTECTION  $19/month per ACTIVE COMMITTER
   push protection, secret scanning, AI-powered detection
⚠️ GITHUB CODE SECURITY      $30/month per active committer
   code scanning, Copilot Autofix, security campaigns, Dependabot
   features, dependency review, security overview
```
⚠️ **Crucially, GitHub Team plan customers can buy these without an Enterprise
subscription — which materially lowers the entry point for smaller orgs.**
**⚠️ Note the billing unit: ACTIVE COMMITTER, not seat.** **That's a different and usually
smaller denominator than your licence count, and it makes cost modelling non-obvious.**
- **⚠️ Free assessment tooling arrived**: **a Secret Risk Assessment and, more recently, a
  Code Security Risk Assessment giving a free one-click CodeQL scan of up to 20 active
  repositories with no licence required and no Actions minutes consumed.** ⚠️ **That's a
  genuinely useful way to size your exposure before buying anything.**

> **⚠️ GOTCHA — Copilot's billing model changed fundamentally, and the reason is
> instructive.** ⚠️ **All Copilot plans moved to usage-based AI CREDIT billing on 1 June
> 2026 (reported at $0.01 per credit), with costs tracking actual model usage rather than
> a fixed request count.**
> **⚠️ The driver was agentic workloads: GitHub paused new sign-ups for Pro, Pro+ and
> Student plans in a reported 58-day freeze beginning 20 April 2026**, ⚠️ **with GitHub's
> VP of Product attributing it to long-running parallelized agentic sessions consuming far
> more resources than flat-rate plans could support.**
> **⚠️ Sign-ups reopened gradually from 17 June 2026, per GitHub's own changelog, and a
> new $100/month Max plan was added** alongside Free, Pro and Pro+ — **$200 in monthly AI
> credits and roughly 2.9× Pro+'s usage headroom.**
> **⚠️ The generalizable lesson: flat-rate pricing does not survive agentic usage
> patterns, and anyone budgeting for AI coding tools on a per-seat assumption should
> expect that assumption to break.**

- **⚠️ Agentic features moved from autocomplete to delegated work.** **Copilot coding agent
  can be assigned a GitHub Issue, works asynchronously in an ephemeral Actions-powered
  environment on a branch, and opens a PR for human review.** ⚠️ **Agentic code review
  shipped around March 2026.** **⚠️ The human-review-before-merge gate is the important
  design point, and your rulesets (§7 → `ghjira-github-repos-reviews-actions-security-and-identity`) are what enforce it.**
- **⚠️ Rulesets continue to displace classic branch protection** — **automatic conversion
  of branch protection rules into rulesets is now available, along with a rule insights
  dashboard showing blocked-push trends over time.**
- **⚠️ Actions**: **custom runner autoscaling, expanded security controls, and reported
  hosted-runner price reductions of up to 39% in January 2026.** ⚠️ **Also note read-only
  cache tokens for workflows triggerable without write permissions — a supply-chain
  hardening change.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| Git commits store diffs | ⚠️ **They store snapshots; diffs are computed** (§2 → `ghjira-git-data-model-branching-and-recovery`) |
| A branch contains commits | ⚠️ **It's a pointer. Deleting it loses nothing** (§2 → `ghjira-git-data-model-branching-and-recovery`, §4 → `ghjira-git-data-model-branching-and-recovery`) |
| Deleting a branch loses the work | ⚠️ **Reflog. Committed work is hard to lose** (§4 → `ghjira-git-data-model-branching-and-recovery`) |
| Rebase is just a tidier merge | ⚠️ **It rewrites hashes. Never on shared history** (§3 → `ghjira-git-data-model-branching-and-recovery`) |
| `git revert` undoes like `reset` | ⚠️ **Revert makes a NEW commit — correct on shared branches** (§4 → `ghjira-git-data-model-branching-and-recovery`) |
| Git Flow is the professional standard | ⚠️ **Built for versioned releases; overkill for web apps** (§3 → `ghjira-git-data-model-branching-and-recovery`) |
| Bigger PRs are more efficient to review | ⚠️ **Defect detection drops sharply with size** (§6 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| A GitHub team can deny access | ⚠️ **Permissions are additive; there is no deny** (§5 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Required checks always block | ⚠️ **A skipped workflow never reports — PR hangs** (§7 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| `pull_request_target` is a safer trigger | ⚠️ **It's a secrets-exfiltration footgun** (§8 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Pinning an action to a tag is fine | ⚠️ **Tags are mutable. Pin the SHA** (§8 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Scrub the leaked secret from history | ⚠️ **ROTATE first. Removal doesn't undo exposure** (§9 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Use a PAT for the automation | ⚠️ **Use a GitHub App** (§11 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| GHAS is one product | ⚠️ **Split into Secret Protection and Code Security** (§26.2) |
| Copilot is flat-rate per seat | ⚠️ **Usage-based AI credits since June 2026** (§26.2) |
| Editing a Jira workflow affects one project | ⚠️ **Schemes are shared. Check first** (§13 → `ghjira-jira-configuration-workflows-and-jql`) |
| Team-managed vs company-managed is cosmetic | ⚠️ **No clean conversion path** (§14 → `ghjira-jira-configuration-workflows-and-jql`) |
| `status != Done` finds open issues | ⚠️ **Misses other terminal statuses. Use resolution** (§16 → `ghjira-jira-configuration-workflows-and-jql`) |
| Story points are hours | ⚠️ **Relative size; converted empirically by throughput** (§17 → `ghjira-jira-boards-automation-permissions-and-hygiene`) |
| Velocity compares teams | ⚠️ **It doesn't, and using it that way inflates points** (§17 → `ghjira-jira-boards-automation-permissions-and-hygiene`, §24 → `ghjira-integration-metrics-and-anti-patterns`) |
| Burndown shows what happened | ⚠️ **Burnup shows scope change; burndown hides it** (§18 → `ghjira-jira-boards-automation-permissions-and-hygiene`) |
| More statuses means better tracking | ⚠️ **More places to be inaccurate** (§15 → `ghjira-jira-configuration-workflows-and-jql`) |
| DORA metrics measure developers | ⚠️ **Team diagnostics. Individual use destroys them** (§24 → `ghjira-integration-metrics-and-anti-patterns`) |
| Speed and stability trade off | ⚠️ **DORA finds high performers do better on both** (§24 → `ghjira-integration-metrics-and-anti-patterns`) |
| Data Center is fine until 2029 | ⚠️ **New-customer sale ended March 2026; expansions end 2028** (§26.1) |
| We're an existing DC customer, so we're covered | ⚠️ **Evaluated per product and per entity** (§26.1) |

---

## §28. Quick Reference

### 28.1 Picker
| Question | Where |
|---|---|
| I broke my repo | ⚠️ **`git reflog` first, always** (§4 → `ghjira-git-data-model-branching-and-recovery`) |
| Merge or rebase? | ⚠️ **Rebase your unpushed work; merge shared branches** (§3 → `ghjira-git-data-model-branching-and-recovery`) |
| Undo a commit others have pulled | ⚠️ **`git revert`, not reset** (§4 → `ghjira-git-data-model-branching-and-recovery`) |
| Reviews are superficial | ⚠️ **The PRs are too big** (§6 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| PR stuck on a check that never runs | ⚠️ **Path filter + required check** (§7 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Automating against GitHub | ⚠️ **GitHub App, not a PAT** (§11 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Secret got committed | ⚠️ **ROTATE it, then clean history** (§9 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| Enforcing policy across many repos | ⚠️ **Org-level rulesets** (§7 → `ghjira-github-repos-reviews-actions-security-and-identity`) |
| New Jira project — which type? | ⚠️ **§14 → `ghjira-jira-configuration-workflows-and-jql`, and decide deliberately** |
| Need a new Jira field | ⚠️ **Check whether one exists first** (§13 → `ghjira-jira-configuration-workflows-and-jql`, §22 → `ghjira-jira-boards-automation-permissions-and-hygiene`) |
| Editing a Jira workflow | ⚠️ **Check what else uses the scheme** (§13 → `ghjira-jira-configuration-workflows-and-jql`) |
| Find my open work | ⚠️ **`assignee = currentUser() AND resolution = Unresolved`** (§16 → `ghjira-jira-configuration-workflows-and-jql`) |
| What's been stuck? | ⚠️ **`status WAS "Blocked" DURING (-30d, now())`** (§16 → `ghjira-jira-configuration-workflows-and-jql`) |
| People forget to update tickets | ⚠️ **Automation, not reminders** (§19 → `ghjira-jira-boards-automation-permissions-and-hygiene`) |
| Which is source of truth for status? | ⚠️ **Pick one; automate the other** (§23 → `ghjira-integration-metrics-and-anti-patterns`) |
| What should we measure? | ⚠️ **DORA + cycle time. Never individuals** (§24 → `ghjira-integration-metrics-and-anti-patterns`) |
| Self-managed Atlassian, what now? | ⚠️ **§26.1's dates. This is a project** |

### 28.2 Setup checklist for a new repo
- [ ] ⚠️ **Ruleset on the default branch: PR required, checks required, no force push** (§7 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] CODEOWNERS, and owner review required rather than requested (§5 → `ghjira-github-repos-reviews-actions-security-and-identity`, §7 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] ⚠️ **One merge strategy chosen and enforced** (§6 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] ⚠️ **`permissions:` set explicitly in workflows; actions pinned to SHA** (§8 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] ⚠️ **Secret scanning with PUSH PROTECTION enabled** (§9 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] Dependabot on, version updates grouped (§9 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] ⚠️ **OIDC to cloud providers rather than stored credentials** (§8 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] Concurrency groups to cancel superseded runs (§8 → `ghjira-github-repos-reviews-actions-security-and-identity`)
- [ ] ⚠️ **Issue key convention enforced by check, not by reminder** (§23 → `ghjira-integration-metrics-and-anti-patterns`)

---

## §29. Method

**§1–§25 → `ghjira-git-data-model-branching-and-recovery`, `ghjira-github-repos-reviews-actions-security-and-identity`, `ghjira-jira-configuration-workflows-and-jql`, `ghjira-jira-boards-automation-permissions-and-hygiene`, `ghjira-integration-metrics-and-anti-patterns` rests on stable mechanics** — **Git's object model, the permission and scheme
architectures, JQL semantics, review and flow research, and the DORA findings.**
⚠️ **The Git internals in §2 → `ghjira-git-data-model-branching-and-recovery` have been unchanged since 2005 and are the most durable
content here.**

**Two searches were run in August 2026**, on **Atlassian's Data Center wind-down** and
**GitHub's security and Copilot repackaging** — ⚠️ **the two changes with real budget and
migration consequences.**

**Confidence.** **High** in §2 → `ghjira-git-data-model-branching-and-recovery`, §13 → `ghjira-jira-configuration-workflows-and-jql` and §14 → `ghjira-jira-configuration-workflows-and-jql`, which are the sections I'd most want read.
⚠️ **The "commits are snapshots, branches are pointers" framing dissolves most Git
confusion**, **and §13 → `ghjira-jira-configuration-workflows-and-jql`'s shared-scheme gotcha plus §14 → `ghjira-jira-configuration-workflows-and-jql`'s irreversible project-type choice
are the two ways people most commonly damage a Jira instance without realizing it at the
time.**

**High** in §26.1's timeline, which comes from Atlassian's own licensing pages and is
corroborated across multiple partner and analyst sources: ⚠️ **price increases 17 February
2026, end of sale to new customers 30 March 2026, end of expansions 30 March 2028, end of
life 28 March 2029.** ⚠️ **The per-product and per-entity "existing customer" definition is
the detail I'd most want flagged** — **it's specific, it's counterintuitive, and it catches
organizations mid-expansion or mid-acquisition.** **The percentage increases (~15% standard,
18–40% legacy Advantage) come from partner and reseller commentary rather than
Atlassian's own pricing page, so treat those as reported.**

**High** in §26.2's GHAS split and pricing, which trace to GitHub's own changelog and
resources pages. ⚠️ **The Copilot AI-credits transition (1 June 2026) and the reported
58-day sign-up freeze from 20 April 2026 come from secondary tech coverage rather than
GitHub's own announcements in my results** — **I've attributed them as reported.**
⚠️ **The generalizable point is mine and I think it's the useful takeaway: flat-rate
pricing does not survive agentic usage, so per-seat budget assumptions for AI coding tools
should be expected to break.**

⚠️ **Sourcing caution specific to this file**: **much of the Atlassian material comes from
migration consultancies and competing vendors, who have an obvious interest in urgency
around Data Center EOL.** **I anchored the dates on Atlassian's own pages and used the
partner sources only for the price-increase percentages and the practical implications,
flagging those as reported.** ⚠️ **Similarly, several GitHub pricing figures come from
third-party pricing-guide sites; the product names, split, and per-active-committer
billing unit are confirmed by GitHub's own changelog.**
