---
name: ghjira-git-data-model-branching-and-recovery
description: "Use when a Git operation went wrong or you need the model underneath the commands: why the tool is not the process, Git's actual data model of blobs, trees, commits and refs, branching, merging and rebasing and what each really does to history, and recovery through the reflog, fsck, cherry-pick and the reset modes. Includes the router for the whole GitHub and Jira reference."
---

# GitHub and Jira: The Tool Is Not the Process, Git's Data Model, Branching, Merging and Rebasing, and Recovery

> **Part 1 of 6** of the *GitHub and Jira* reference (plugin `github-jira-deep-dive`), covering §0–§4. Sibling skills: `ghjira-github-repos-reviews-actions-security-and-identity` (§5–§12), `ghjira-jira-configuration-workflows-and-jql` (§13–§16), `ghjira-jira-boards-automation-permissions-and-hygiene` (§17–§22), `ghjira-integration-metrics-and-anti-patterns` (§23–§25), `ghjira-reference` (§26–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> mechanics in §1–§25 → `ghjira-github-repos-reviews-actions-security-and-identity`, `ghjira-jira-configuration-workflows-and-jql`, `ghjira-jira-boards-automation-permissions-and-hygiene`, `ghjira-integration-metrics-and-anti-patterns` to outlive them.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ The tool does not fix the process** (§1). **A broken workflow encoded in Jira is
>    a broken workflow with better reporting, and most "we need to configure X" requests
>    are really "we haven't agreed how we work."**
> 2. **⚠️ Understand Git's data model and most Git problems dissolve** (§2). **Almost all
>    Git confusion comes from learning commands instead of the object graph.**
> 3. **⚠️ Configuration debt is the real cost in both systems** (§16 → `ghjira-jira-configuration-workflows-and-jql`, §24 → `ghjira-integration-metrics-and-anti-patterns`). **Every scheme,
>    custom field, workflow and ruleset you add is permanent maintenance, and neither tool
>    makes removal easy.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ Why the tool isn't the problem** | **§1** |
| **⚠️ Git's data model** | **§2** |
| Branching and merge vs rebase | §3 |
| **⚠️ Recovering from disasters** | **§4** |
| Repos, orgs, permissions | §5 → `ghjira-github-repos-reviews-actions-security-and-identity` |
| **Pull requests and review** | **§6 → `ghjira-github-repos-reviews-actions-security-and-identity`** |
| **Rulesets and branch protection** | **§7 → `ghjira-github-repos-reviews-actions-security-and-identity`** |
| **GitHub Actions** | **§8 → `ghjira-github-repos-reviews-actions-security-and-identity`** |
| Security products | §9 → `ghjira-github-repos-reviews-actions-security-and-identity` |
| Issues, Projects | §10 → `ghjira-github-repos-reviews-actions-security-and-identity` |
| **API, apps, webhooks** | **§11 → `ghjira-github-repos-reviews-actions-security-and-identity`** |
| Enterprise identity | §12 → `ghjira-github-repos-reviews-actions-security-and-identity` |
| **⚠️ Jira's configuration model** | **§13 → `ghjira-jira-configuration-workflows-and-jql`** |
| **⚠️ Team- vs company-managed** | **§14 → `ghjira-jira-configuration-workflows-and-jql`** |
| Workflows and statuses | §15 → `ghjira-jira-configuration-workflows-and-jql` |
| **JQL** | **§16 → `ghjira-jira-configuration-workflows-and-jql`** |
| Boards, sprints, estimation | §17 → `ghjira-jira-boards-automation-permissions-and-hygiene` |
| Reports | §18 → `ghjira-jira-boards-automation-permissions-and-hygiene` |
| **Automation** | **§19 → `ghjira-jira-boards-automation-permissions-and-hygiene`** |
| Permissions | §20 → `ghjira-jira-boards-automation-permissions-and-hygiene` |
| Service Management | §21 → `ghjira-jira-boards-automation-permissions-and-hygiene` |
| **⚠️ Config hygiene** | **§22 → `ghjira-jira-boards-automation-permissions-and-hygiene`** |
| **Integrating the two** | **§23 → `ghjira-integration-metrics-and-anti-patterns`** |
| **⚠️ Metrics** | **§24 → `ghjira-integration-metrics-and-anti-patterns`** |
| Anti-patterns | §25 → `ghjira-integration-metrics-and-anti-patterns` |
| **What's live** | **§26 → `ghjira-reference`** |
| Misconceptions, quick ref | §27–§29 → `ghjira-reference` |

---

## §1. ⚠️ The Tool Is Not the Process

**⚠️ The single most useful thing to know before configuring either system.**
```
⚠️ "We need a new Jira field"        → usually: we haven't agreed what to track
⚠️ "We need a custom workflow"       → usually: we haven't agreed who decides what
⚠️ "The board doesn't reflect reality" → usually: reality isn't what we said it was
⚠️ "We need better reporting"        → usually: our data entry is unreliable
```
**⚠️ Both tools reward a decided process and punish an undecided one**, ⚠️ **because they
force you to make the ambiguity explicit** — **and teams frequently resolve that by adding
configuration instead of making the decision.**
**⚠️ The corollary for adoption**: ⚠️ **data quality follows from whether updating the tool
is useful TO THE PERSON UPDATING IT.** **A Jira board nobody trusts is a board nobody
updates, which makes it less trustworthy — and the failure is self-reinforcing.**
⚠️ **If status updates exist only for management reporting, they will be wrong.**

---

# PART I — GIT FOUNDATIONS

## §2. ⚠️ Git's Data Model

**⚠️ Learn this and the commands stop being magic. Git is a content-addressed object store
plus refs.**
```
⚠️ FOUR OBJECT TYPES, all keyed by hash of their content
  BLOB    file contents (no name, no metadata — just bytes)
  TREE    a directory: names → blobs and other trees
  COMMIT  a snapshot: one tree + parent commit(s) + author + message
  TAG     annotated tag object

⚠️ COMMITS ARE SNAPSHOTS, NOT DIFFS. Git computes diffs on demand.
   ⚠️ This is the single most clarifying fact about Git

⚠️ REFS are just files containing a hash
  branch  = a movable ref to a commit
  HEAD    = a ref to the current branch (or a commit, when "detached")
  tag     = a ref that doesn't move
```
> **⚠️ GOTCHA — a branch is not a container of commits.** ⚠️ **It's a 41-byte file with a
> hash in it.** **"Deleting a branch" deletes a pointer, not the commits** (§4).
> **⚠️ This is why branching is cheap, why "which branch is this commit on" is a
> surprisingly awkward question, and why rewriting history creates NEW commits rather
> than editing old ones — objects are immutable and keyed by their content.**

**⚠️ The three areas**: **working tree → INDEX (staging area) → repository.** ⚠️ **The
index is the concept people skip and then don't understand `git add`, partial staging, or
why `git status` shows two sections.**
**⚠️ Remotes and remote-tracking branches**: ⚠️ **`origin/main` is YOUR last-known copy of
the remote's `main`, not the remote itself.** **`fetch` updates it; `pull` = fetch +
merge (or rebase).**

---

## §3. Branching, Merging, Rebasing

```
MERGE    ⚠️ creates a commit with two parents. History is truthful and messy
REBASE   ⚠️ REPLAYS commits onto a new base, creating NEW commits with new
         hashes. History is linear and edited
SQUASH   collapse a branch into one commit
FAST-FORWARD  ⚠️ no merge commit needed because the branch is strictly ahead
CHERRY-PICK   ⚠️ copy one commit elsewhere — creates a duplicate, and is a
         common source of "why does this appear twice"
```
> **⚠️ GOTCHA — the golden rule of rebasing: never rebase commits that others have
> pulled.** ⚠️ **Rebase rewrites hashes, so anyone who has the old commits now has
> divergent history**, **and the usual recovery is messy.** **⚠️ Rebase freely on your own
> unpushed work; use merge on shared branches.**
> **⚠️ And if you must force-push a shared branch, use `--force-with-lease` rather than
> `--force`** — **it refuses if someone else has pushed since your last fetch.**

**⚠️ Branching strategies, honestly:**
```
⚠️ TRUNK-BASED  short-lived branches, merge to main daily, feature flags for
   incomplete work. ⚠️ The approach the DORA research associates with high
   performance, and the one most compatible with CI
GITHUB FLOW     ⚠️ branch → PR → merge → deploy. Simple; suits continuous deploy
GIT FLOW        ⚠️ develop/release/hotfix branches. Designed for versioned
   releases with support windows; ⚠️ widely cargo-culted onto web apps
   where it adds ceremony without benefit — its own author has said as much
```
**⚠️ Long-lived branches are the underlying problem in all merge-hell stories** —
⚠️ **integration pain grows superlinearly with branch age**, **so the fix is smaller,
shorter branches rather than better merge tooling.**

---

## §4. ⚠️ Recovery

> **⚠️ The reassuring fact: in Git, committed work is very hard to actually lose.**
> ⚠️ **`git reflog` records where HEAD has been, including states no branch points at.**
> **Almost every "I destroyed everything" situation is recoverable from it.**

```
⚠️ git reflog                     find the hash you were at
⚠️ git reset --hard <hash>        go back there (⚠️ discards uncommitted work)
⚠️ git checkout -b rescue <hash>  safer: make a branch at the lost commit
git cherry-pick <hash>            retrieve one commit
⚠️ git revert <hash>              UNDO a commit by making a new one —
   ⚠️ the correct tool on shared branches, unlike reset
git fsck --lost-found             for dangling objects
⚠️ git stash / git stash list     uncommitted work you set aside
```
**⚠️ What genuinely IS lost**: ⚠️ **uncommitted changes destroyed by `reset --hard` or a
bad `checkout`, untracked files removed by `git clean`, and objects pruned by `gc` after
the reflog expires (default ~90 days for reachable, ~30 for unreachable).**
**⚠️ The practical habit**: ⚠️ **commit early and often on your own branch — it costs
nothing and puts everything in the reflog's reach.** **You can always tidy the history
later** (§3).

---

# PART II — GITHUB
