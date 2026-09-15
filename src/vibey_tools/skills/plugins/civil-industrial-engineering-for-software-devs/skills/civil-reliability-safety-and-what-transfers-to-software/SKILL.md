---
name: civil-reliability-safety-and-what-transfers-to-software
description: "Use when applying reliability or safety-engineering method to software, or judging an engineering analogy honestly: scheduling, inventory and supply chain, human factors and ergonomics, reliability engineering with MTBF, the bathtub curve, FMEA and fault trees, safety engineering and the hierarchy of controls, and then a direct account of what transfers well from civil and industrial engineering to software and what does not."
---

# Civil and Industrial Engineering: Scheduling and Inventory, Human Factors, Reliability, Safety Engineering, and What Transfers to Software

> **Part 4 of 5** of the *Civil and Industrial Engineering for Software Devs* reference (plugin `civil-industrial-engineering-for-software-devs`), covering §17–§22. Sibling skills: `civil-loads-safety-factors-materials-and-foundations` (§0–§5), `civil-codes-licensure-failure-analysis-and-construction` (§6–§10), `civil-industrial-engineering-queueing-toc-and-lean` (§11–§16), `civil-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanics and the operations research are settled. Two areas carry live numbers. See §23 → `civil-reference` for US infrastructure condition, and the megaproject estimation data.

> **⚠️ Written for people who build software and keep hearing that they should be more
> like "real engineers."** **Complements a thermodynamics/fluids reference (the physics),
> an engineering-process reference (methodology), and a security reference (§20's
> hierarchy of controls recurs there).**
>
> **⚠️ The honest framing: some of this transfers extremely well and some of it does not,
> and the borrowings that fail are usually the ones taken as metaphor rather than as
> mechanism.** ⚠️ **§21 and §22 make that distinction explicitly, and they're the point of
> the document.**
>
> **⚠️ GOTCHA** boxes mark the analogies that break, and the borrowed ideas software
> commonly misuses.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Civil engineering's real lesson isn't "plan more" — it's the INSTITUTIONAL
>    apparatus** (§6 → `civil-codes-licensure-failure-analysis-and-construction`, §7 → `civil-codes-licensure-failure-analysis-and-construction`, §8 → `civil-codes-licensure-failure-analysis-and-construction`). **Codes, licensure, liability and mandatory failure
>    investigation, not the calculations.**
> 2. **⚠️ Industrial engineering's queueing and constraint mathematics transfer DIRECTLY,
>    with no metaphor required** (§11 → `civil-industrial-engineering-queueing-toc-and-lean`, §12 → `civil-industrial-engineering-queueing-toc-and-lean`). **Little's Law is as true of a deployment
>    pipeline as of a factory, and it is the single most valuable import in this document.**
> 3. **⚠️ The disanalogies are load-bearing** (§22). **Software's marginal cost of
>    replication is zero, its "material properties" are unmeasured, and its requirements
>    change during construction — and each of those breaks a specific borrowed practice.**

---

## §17. Scheduling, Inventory and Supply Chain

**Job shop vs flow shop; ⚠️ scheduling rules (SPT minimizes average flow time — the
shortest-job-first result software knows from schedulers; EDD minimizes maximum lateness);
⚠️ and the fact that most scheduling problems are NP-hard, so practice runs on heuristics.**
**Inventory**: **EOQ, safety stock, ⚠️ reorder points, and the newsvendor problem
(⚠️ single-period stocking under uncertainty — the maths behind capacity provisioning
decisions).**
**⚠️ The BULLWHIP EFFECT is the one to know**: ⚠️ **demand variability AMPLIFIES as it
propagates upstream through a supply chain, caused by batching, lead times, and each stage
reacting to its immediate signal rather than true demand.**
**⚠️ The software analogue is retry storms and cascading failure** — ⚠️ **each layer
reacting to its immediate upstream signal, amplifying it, until the whole system
oscillates.** **Exponential backoff with jitter is the damping mechanism, and it's the same
problem.**

---

## §18. Human Factors and Ergonomics

**⚠️ Physical ergonomics (anthropometry, repetitive strain, workstation design — ⚠️ and
this is directly relevant to developers' own health) and COGNITIVE ergonomics.**
**⚠️ Cognitive load, situation awareness, vigilance decrement (⚠️ humans are poor at
sustained monitoring for rare events — which is exactly what on-call is), automation
irony (⚠️ automating the easy parts leaves humans the hard parts, degraded skills, and
worse situation awareness when it fails), and mode confusion.**
> **⚠️ GOTCHA — "human error" is a conclusion that stops investigation, and human factors
> treats it as a starting point.** ⚠️ **The question is why the system made that error
> likely: what did the interface afford, what was the workload, what were the time
> pressures, what did the alarm not distinguish?** **⚠️ This is the same move as blameless
> postmortems, and human factors got there decades earlier with more rigour.**

---

## §19. Reliability Engineering

```
⚠️ MTBF / MTTF / MTTR  ⚠️ MTBF is a RATE parameter, not a lifespan —
   a 100,000-hour MTBF does not mean the unit lasts 11 years
⚠️ THE BATHTUB CURVE  infant mortality (decreasing rate) → useful life
   (roughly constant) → wear-out (increasing rate)
   ⚠️ Software has infant mortality and NO wear-out — but it has a
   third mode hardware lacks: the environment changes underneath it
AVAILABILITY = MTBF / (MTBF + MTTR)  ⚠️ note both terms; halving MTTR
   improves availability as much as doubling MTBF, and is usually cheaper
⚠️ SERIES vs PARALLEL  series reliability MULTIPLIES (⚠️ ten 99.9%
   components in series gives 99%); parallel redundancy multiplies FAILURE
   probabilities instead
⚠️ FMEA  Failure Modes and Effects Analysis — enumerate failure modes,
   rate severity × occurrence × detectability, prioritize
FAULT TREE / EVENT TREE  top-down vs bottom-up
```
**⚠️ The series-reliability arithmetic is the one software most needs**: ⚠️ **a request
path through ten services each at 99.9% is 99% end-to-end**, **which is why microservice
architectures need explicit reliability budgeting rather than per-service targets.**
**⚠️ FMEA transfers directly and is under-used** — **it's a structured version of what a
good design review does informally, and the DETECTABILITY axis is the one software forgets:
a failure you can't observe is worse than one you can.**

---

## §20. ⚠️ Safety Engineering

```
⚠️ HIERARCHY OF CONTROLS — in order of effectiveness, and the order matters
   1. ELIMINATE the hazard
   2. SUBSTITUTE something less hazardous
   3. ENGINEERING CONTROLS — guards, interlocks; work without cooperation
   4. ADMINISTRATIVE CONTROLS — procedures, training, warnings
   5. PPE — last resort, protects one person, depends on compliance
```
> **⚠️ GOTCHA — software defaults to levels 4 and 5 and calls it security.** ⚠️ **Training,
> policies and "be careful" documentation are ADMINISTRATIVE controls, the second-weakest
> tier.** **⚠️ Making a dangerous operation impossible (type systems, capability-based
> permissions, removing the production credential entirely) is ELIMINATION, and it's the
> strongest.** **The hierarchy is a ranking of effectiveness, and it should reorder most
> security backlogs.**

**⚠️ The Swiss cheese model** (Reason): ⚠️ **accidents require multiple independent
defensive layers to fail simultaneously; each layer has holes and the holes move.**
**⚠️ The corollary is that near-misses are the same event with one layer holding, which is
why reporting them matters more than counting accidents.**
**⚠️ Normal Accidents (Perrow)**: ⚠️ **systems with high interactive complexity AND tight
coupling will have accidents that are, in a real sense, inevitable** — **and the remedy is
reducing coupling, not adding procedures.** ⚠️ **Distributed systems are the textbook case.**
**⚠️ High Reliability Organizations (Weick and Sutcliffe)**: **preoccupation with failure,
reluctance to simplify, sensitivity to operations, commitment to resilience, and
⚠️ DEFERENCE TO EXPERTISE — decisions migrate to whoever knows most, regardless of rank.**
⚠️ **That last one is the andon cord again** (§14 → `civil-industrial-engineering-queueing-toc-and-lean`), **and it's the practice most
organizations claim and fewest have.**
**⚠️ Safety-II and resilience engineering** (Hollnagel): ⚠️ **study why things normally go
RIGHT, not only why they occasionally go wrong** — **because the same adaptive behaviour
produces both, and removing it to prevent failure removes the source of everyday success.**

---

# PART III — THE TRANSFER

## §21. ⚠️ What Transfers Well

**⚠️ Ranked by how directly it applies, best first:**
```
⚠️ 1. QUEUEING THEORY (§12) — a THEOREM, not an analogy. Little's Law,
   the utilization curve, and the variability effect apply unchanged.
   ⚠️ The highest-value idea in this document
⚠️ 2. THEORY OF CONSTRAINTS (§13) — find the bottleneck; improvements
   elsewhere are illusory. Applies to pipelines, teams and org design
⚠️ 3. HIERARCHY OF CONTROLS (§20) — reorders most security backlogs
⚠️ 4. DUCTILE vs BRITTLE FAILURE (§4) — degrade gracefully, don't fall over
⚠️ 5. RELIABILITY ARITHMETIC (§19) — series multiplication, availability
   as a function of BOTH MTBF and MTTR, FMEA with detectability
⚠️ 6. COMMON vs SPECIAL CAUSE (§15) — stop tampering with normal variation
⚠️ 7. INDEPENDENT FAILURE INVESTIGATION (§8) — including the step software
   omits: the finding becomes a rule
⚠️ 8. HUMAN FACTORS (§18) — "human error" is where analysis STARTS
⚠️ 9. THE BULLWHIP EFFECT (§17) — retry storms are supply-chain oscillation
⚠️ 10. REFERENCE CLASS FORECASTING (§23.2) — the estimation fix
```
**⚠️ Notice what those have in common**: ⚠️ **every one of them is a MECHANISM with
mathematics or a documented causal model behind it.** **None of them is a slogan.**

---

## §22. ⚠️ What Doesn't Transfer — Honestly

> **⚠️ This section exists because the "be more like real engineers" argument is usually
> made without engaging the disanalogies, and the disanalogies are real.**

```
⚠️ 1. NO MATERIAL PROPERTIES. There is no characteristic strength of code,
   no distribution to apply a partial factor to (§3). Factor-of-safety
   reasoning has no direct numerical analogue
⚠️ 2. REQUIREMENTS CHANGE DURING CONSTRUCTION. A building's programme is
   largely fixed at design; software's is not, and pretending otherwise
   is what waterfall was. ⚠️ This is a genuine categorical difference
⚠️ 3. ZERO MARGINAL COST OF REPLICATION AND CHANGE. ⚠️ You cannot rebuild a
   bridge to try an idea; you can redeploy software in minutes. ⚠️ This
   INVERTS the economics of upfront design — cheap iteration is
   rationally preferable where it's available, and civil engineering
   front-loads precisely because it isn't
⚠️ 4. ADVERSARIAL LOADS. Gravity does not adapt to your design. Attackers
   do. ⚠️ No civil analogue exists for an intelligent adversary
   searching for your weakest assumption
⚠️ 5. NO STABLE SUBSTRATE. Steel's properties don't change annually.
   ⚠️ Your language, framework, cloud and OS all do (§6)
⚠️ 6. INVISIBLE, UNINSPECTABLE ARTEFACT. A third party can inspect
   rebar placement. ⚠️ Nobody can inspect a codebase to the same standard,
   which is why the code-and-permit model doesn't port (§6)
⚠️ 7. NON-REPETITIVE WORK. Work measurement and Six Sigma assume repeated
   processes; software development is not one (§15, §16)
```
**⚠️ The one that cuts the other way, and should be conceded**: ⚠️ **the accountability
structure (§7 → `civil-codes-licensure-failure-analysis-and-construction`) is a genuine difference and NOT explained away by any of the above.**
**An individual who personally loses their licence behaves differently under commercial
pressure than an employee who can be overruled.** ⚠️ **Software's absence of that structure
is a choice the industry has made, not a technical necessity** — **and regulated software
domains demonstrate it's possible when the consequences justify the cost.**
**⚠️ The synthesis I'd offer**: ⚠️ **software should stop borrowing civil engineering's
CULTURE (upfront design, formal ceremony, credentialism) and start borrowing industrial
engineering's MATHEMATICS and safety engineering's INSTITUTIONS.** **The first is a poor
fit for the reasons above; the second two fit exactly.**
