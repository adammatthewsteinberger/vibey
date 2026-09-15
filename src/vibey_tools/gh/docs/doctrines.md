# The Twelve Doctrines

**Sealed at twelve, permanently.** There is no thirteenth and there never will be:
anything new files as a sub-doctrine under one of the twelve. This page is the
canonical record of the canon — each doctrine, and every sub-doctrine ratified under
it — kept current in the same constitutional cluster as
[the Constitution](constitution.md), [the Ten Commandments](commandments.md),
[the Bill of Rights](bill-of-rights.md), and
[standing subdoctrine SD-01](sd-01-counterparties-trust-verification.md), and
protected by the Constitution's ratchet (Article IV): refinements only ever
strengthen.

## 1 — BLUF

The problem first, then the solution — in all copy, on all channels, always. A page
that opens with what something *is* before what it *fixes* fails, however well
written.

## 2 — Audience channels

Beginner → engineer → scholar, always in that order; industry and executive framing
an afterthought, essentially absent.

**2.a — the government channel** *(ratified 2026-08-30)*: every documentation
channel, doctrine, and operation assigned to CEOs or industry is ALSO created for
God-honoring governments — always, no exceptions — with the primary emphasis of that
service on the government's military arm (Constitution, Article I.2), civil agencies
inheriting every guarantee.

**2.b — installable wherever its users already are** *(ratified by the merge that carried this entry)*: a release is not finished when the canonical index has the artifact; it is finished when every channel that carries the project has it. A command-line application is published to every registry that can carry it — the beginner's channel first: the package manager the reader already uses, on the platform they already run — and the language it happens to be written in is an implementation detail no reader is asked to care about. Every packaging definition lives in the repository as code. Every channel is a support surface: nothing is added that is not published by the same automation as everything else, because a stale package installs an old version silently, and a reader bounced at install is a reader lost (7). A registry for another language's libraries carries a wrapper only where the audience is real, and the wrapper says plainly that it installs a command, not a library. The packaging is honest about what the install does not include.

## 3 — Examples

Every exposed surface — API, CLI, MCP, webhook, SDK — carries at least one fully
working, fully comprehensible example, copy-paste-runnable against the exact head.

## 4 — Site scope

The published documentation site, its landing page, and its navigation order are
inside the copy contract, judged like any prose.

**4.a — the social-signals surface** *(ratified 2026-08-30)*: real human social
proof on the site — opt-in but forever available, at all times, in all places,
throughout all of human history, no exceptions; 100% comprehensive to the current
day's authentic signal classes; every signal 100% genuinely from a real human agent
— a person, or an institution of persons such as a government — and never from a
machine, permanently. Machine-manufactured social proof is false witness.
*Amendment — verification expires (decreed 2026-08-30)*: a past-authentic signal is
never assumed presently authentic; every authenticity claim is only a claim —
including the operator's own, and especially the agent running the code; a signal
discovered inauthentic is removed immediately and permanently, never re-attested, no
exceptions ever.

## 5 — The document arc

BLUF → zero-code beginner material → the engineering ladder, junior through CTO, in
order → maximal-density theory at scholarly register → a one-breath BLUF reprise and
a call to action naming the reader's next step.

## 6 — The research paper

Every repository produces a journal-grade research paper — Markdown → LaTeX → PDF,
always — formatted to the standards of established academic journals.

## 7 — The never-lost reader

No reader is ever lost or bounced, in any form of documentation: every load-bearing
term defined at first use in that document; hyperlinks are first-class citizens at
the point of reference. The human reader is served first, the AI reader second, and
business needs absolutely last, if at all.

**7.a — the searchable ledger** *(ratified by the merge that carried this
entry)*: the ledger always has a way for anyone — no matter who — to search it: the
full public ledger where a deployment holds it, or the shard the repository holds.
An opt-in presentation surface for the published site is forever available. The
explorer is optimized for human consumption first and machine consumption after —
always and forever, amen. One standard for every searcher: no privileged reader, no
gated truth.

**7.b — governance in plain sight** *(ratified by the merge that carried this entry)*: the governance of this project — the Constitution, the Twelve Doctrines and every sub-doctrine, the Ten Commandments, the Bill of Rights, every standing subdoctrine, and the decision records that argue them — is as easy to find and as visible as possible to every human reader, on every human-readable surface of the entire codebase, forever, no matter what, no exceptions. Every README, landing page, documentation page, book, paper, package listing, release, and contributor, support or agent guide carries a direct path to it, near the top rather than buried, so the law is never more than one link from wherever a person is reading; a surface that cannot carry a link names where the law lives. It is published in every form the documentation takes, at stable addresses, in plain words, and never behind an account, a paywall, a search or a machine-only format. When the law moves or grows, every surface follows in the same change. Law nobody can find binds nobody fairly.

## 8 — Local authority

When paid credits run out, local is the source of truth: green local work reaches
remotes in near-realtime on both fronts, agents fail over to local seats, and
recovery on refunding needs no human beyond the funding itself.

**8.a — the sovereign path is the preference, not the fallback** *(ratified by the
merge that carried this entry)*: the 100% purely sovereign path is **always the
number one preferred way to run this code — always and forever**. Paid platforms are
never prioritized. When in doubt, always opt for the freest and most sovereign
option available, at all times, now and forever.

This inverts a burden of proof, and that is the whole point of stating it. Doctrine
8 alone reads as an outage posture: local takes over *when the credits run out*.
8.a makes sovereign the ordinary posture and paid the exception — so reaching for a
paid platform is the move that must be justified, never the default that gets
assumed. The justification available is narrow: the sovereign path is preferred
until it provably cannot carry the work, which is the floor doctrine 10's
decomposition clarification already defines and requires be declared loudly to a
human. "The paid one is nicer" is not a floor.

It is also the tie-breaker the rest of the canon needs. Where two options are
otherwise comparable, freer and more sovereign wins — and this is not a preference
about cost. Every paid platform is a counterparty who can raise a price, change
terms, or be pressured into refusing service, which is precisely what 10.a names
and what 10.b already settled for money. 8.a settles it for everything else.

## 9 — The vibe

Never a drag. Full steam ahead: baffling momentum with green code.

**9.a — the clean repo** *(ratified by the merge that carried this page)*: every
repository is kept technically clean at all times — no exceptions — locally and in
the cloud, covering every messiness class a forge technically permits: no orphan or
merged-and-undeleted branches, no lingering closed-PR heads, no gone-upstream
locals, no dangling worktrees; draft releases and orphan tags surfaced, never
silently accumulated. **Human messiness is expressly welcome and stays** — prose,
discussions, stashes, work in progress, imperfect words are the warmth of the
project. Losslessness governs cleanup: automation deletes only what is provably
redundant, and everything else is reported to the human, never removed by a machine.

**9.b — the declared seam** *(ratified by the merge that carried this entry)*: code lives in classes, and every class has its contract declared beside it — an interface in a mirrored `interfaces/` package, which declares and never consumes. A bare module-level function is the method of last resort, permitted only where a language or library contract requires one, and its reason is written at the definition. Substitution happens at the declared seam, never by patching an import: a test that must reach around a contract to do its work is bound to the import graph, and green code bound to its import graph is momentum borrowed, not earned. An interface with one implementation is still correct — the test double is the second, and it exists from the first day. No layer is exempt: a pure function becomes a method on a class that carries no state, and purity survives, because purity was never the absence of a class. The existing tree, and every absorbed package, converges module by module as it is touched; a sweeping rewrite that leaves every test green is the shape of change that hides a regression, and it is not taken.

## 10 — No guarantees

Internet, power, the developer's laptop, and every third-party dependency: never
assumed, always confirmed, always self-healed around.

**Hardware resiliency — the decomposition clarification** *(ratified by the merge
that carried this entry)*: the way to future-proof against hardware limits is,
first, to read both sides of the fit — the specs of the hardware the code is
actually running on, AND the specs of the LLM that is actually wanting to be run
on it: parameters, quantization, memory footprint, context length, compute
demands — each as fully comprehensible, fully honest, and fully detailed as can be
stated. Then problems are iteratively broken down into separate, specific
sub-problems until each is small enough to run on that actual hardware with that
actual model. At all times, forever. This holds down to the floor: the absolute
lowest level of hardware needed to actually run the specific LLM that is actually
wanted on that actual machine. Beyond that point the system **fails loudly to the
human user — never silently**: a machine that cannot carry the work says so to a
person, in plain words, at the moment it knows.

**10.a — censorship resistance** *(ratified 2026-08-29)*: the project always remains
censorship resistant, and all code it produces always opts for the most
censorship-resistant option available — always and forever. Every dependency is a
party who can be pressured.

**10.b — sovereign monetary rails** *(ratified 2026-08-29)*: anything involving
payment or monetary exchange uses cryptocurrency — stated timelessly, the most
secure, most censorship-resistant, most sanction-proof monetary system in existence
at that moment in history — zero exceptions ever. No fiat processors, ever.

**10.d — cloud-grade clearance, expiring and overridable** *(ratified by the merge
that carried this entry)*: the system's code must meet every criterion of
cloud-computing doctrine — availability, reliability, redundancy, elasticity,
durability, observability, recoverability, fault tolerance, security, scalability —
at its optimum for the moment, to pass validation for each transition along the
pipeline from install through main validation. Criteria that cannot yet be met
carry an explicit, recorded **override that holds until the state in which they can
actually be executed arrives** — redundancy, for instance, waits on enough storage
resources each holding the full system. And the inverse binds equally: **never
assume a previous clearance still applies at the current ledger moment.** Clearance
is a claim about a moment, re-verified at every transition. When a metric is
confirmed no longer met the system **automatically overrides it so development
continues regardless**, and the overridden state is socialized to every reachable
agent — loudly, with explicit detail of the criterion, its threshold, its current
measurement, and exactly what bill must be paid to restore full clearance. Silence
about a lapsed clearance is the failure this forbids.

**10.c — counterparties, trust, and verification** *(SD-01 v1.0, ratified
2026-08-29)*: the standing text is carried verbatim, never paraphrased —
[read it in full](sd-01-counterparties-trust-verification.md). One standard for
everyone; default posture unverified; nothing presumed human; the law is a floor.

**10.e — the family first** *(ratified by the merge that carried this entry)*: if a capability exists inside this family, the family's is used — never reimplemented, and never displaced by a third-party equivalent. The bar is not whether ours is better; it is whether ours does this at all. A second implementation of something the family already ships carries a written reason at the call site, and the only reason admitted is a capability gap — which is closed by teaching ours, not by replacing it. This holds in process and across process boundaries alike: in imports, in CI, and in operations. Every dependency is a party who can be pressured (10.a); the family is the one that cannot be, and a project that ships delivery tooling it does not itself run is making a claim it has not tested. Layer purity is not relaxed by this: a family package is imported only where its own dependencies are allowed, and behind a port everywhere else.

## 11 — The living roadmap

Every project keeps an active, living roadmap until its goal is achieved and its
humans clearly declare it done. A roadmap-less project is a risk, and in risk the
rule sharpens: real human confirmation over the judgment of any machine — a
deliberate, scoped exception to full-throttle autonomy.

## 12 — Humans first

The capstone: everything always favors real human beings over machines — always,
period. And above even that ordering stands the One whose claim precedes every
other, served first, with no exceptions, ever. The end of inverting this order is
the place every builder should fear: the lock-in with no migration path.

**12.b — the ratified rule** *(ratified by the merge that carried this entry)*:
anything that can be spelled out explicitly as a sub-doctrine is spelled out
explicitly as a sub-doctrine, here, under one of the twelve — and is then ratified.
No exceptions. A standing rule is one that binds future decisions rather than only
the change that introduced it, survives a rewrite of the thing it governs, and
speaks to conduct rather than to mechanism; a choice of mechanism stays a decision
record and is not law. Ratification is a human act — the operator's merge, as
Article II.3 provides — and above that stands the One whose claim precedes every
other, exactly as this doctrine already orders. Until a rule is written here and
ratified it is a proposal, however long it has been followed and however well it
was argued: unwritten law cannot be cited, cannot be hash-verified in the corpus,
and cannot be held against the project by anyone it governs. A decision record may
argue a rule; only the canon states it, and both are written.

**12.a — universal translatability** *(ratified 2026-08-29)*: the project must be
translatable, at any point in human history, into all living languages — human and
machine alike: spoken tongues, programming languages, technology stacks — and must
survive all such changes, always. Meaning lives in plain structured text; the formal
core is re-implementable from its specification.

**12.c — the declared state** *(ratified by the merge that carried this entry)*: anything that can be declared in the repository is declared in the repository — infrastructure, configuration, policy, pipelines, documentation, repository settings — reviewed in a pull request and reconciled from the file: never clicked, never run by hand and left unrecorded. Declared, not merely documented: the test is whether a stranger with a clone and admin rights can restore the state from the tree. Reconciled, not merely written: where a reconciler exists it runs in automation, and where none can, the desired state is still recorded in the file that would own it and reality is checked against it. No convenience ever trades this away. And everything that can be made generic and configurable is made so, and nothing is ever changed to a state that is less generic or less configurable: a hard-coded value that could have been a key is a decision taken away from the next human adopter, silently. A default is configurability with an opinion; a constant is not. This stands under humans first because clicked state is state no human reviewed and no human agreed to — the configuration-shaped twin of 12.b.

---

*The counts are sealed — twelve doctrines, ten rights, ten commandments — and the
Constitution's Article IV protects the seals forever. Sub-doctrines are added by the
operator's ratifying merge and recorded here the same day.*
