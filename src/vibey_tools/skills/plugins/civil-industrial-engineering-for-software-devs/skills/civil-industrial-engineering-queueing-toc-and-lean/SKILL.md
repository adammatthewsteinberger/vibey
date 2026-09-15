---
name: civil-industrial-engineering-queueing-toc-and-lean
description: "Use for the operations research that genuinely transfers to software: what industrial engineering actually is, queueing theory and Little's Law and why high utilisation destroys latency, the Theory of Constraints and the five focusing steps, lean and the Toyota Production System including takt time, kanban, jidoka and the wastes, Six Sigma and DMAIC with statistical process control and control charts, and work measurement and standard work."
---

# Civil and Industrial Engineering: What Industrial Engineering Is, Queueing Theory, Theory of Constraints, Lean, and Six Sigma

> **Part 3 of 5** of the *Civil and Industrial Engineering for Software Devs* reference (plugin `civil-industrial-engineering-for-software-devs`), covering §11–§16. Sibling skills: `civil-loads-safety-factors-materials-and-foundations` (§0–§5), `civil-codes-licensure-failure-analysis-and-construction` (§6–§10), `civil-reliability-safety-and-what-transfers-to-software` (§17–§22), `civil-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanics and the operations research are settled. Two areas carry live numbers. See §23 → `civil-reference` for US infrastructure condition, and the megaproject estimation data.

> **⚠️ Written for people who build software and keep hearing that they should be more
> like "real engineers."** **Complements a thermodynamics/fluids reference (the physics),
> an engineering-process reference (methodology), and a security reference (§20 → `civil-reliability-safety-and-what-transfers-to-software`'s
> hierarchy of controls recurs there).**
>
> **⚠️ The honest framing: some of this transfers extremely well and some of it does not,
> and the borrowings that fail are usually the ones taken as metaphor rather than as
> mechanism.** ⚠️ **§21 → `civil-reliability-safety-and-what-transfers-to-software` and §22 → `civil-reliability-safety-and-what-transfers-to-software` make that distinction explicitly, and they're the point of
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
>    with no metaphor required** (§11, §12). **Little's Law is as true of a deployment
>    pipeline as of a factory, and it is the single most valuable import in this document.**
> 3. **⚠️ The disanalogies are load-bearing** (§22 → `civil-reliability-safety-and-what-transfers-to-software`). **Software's marginal cost of
>    replication is zero, its "material properties" are unmeasured, and its requirements
>    change during construction — and each of those breaks a specific borrowed practice.**

---

## §11. What Industrial Engineering Actually Is

**⚠️ Not "factory engineering." It's the engineering of SYSTEMS OF PEOPLE, MATERIALS,
INFORMATION AND EQUIPMENT — which makes it the closest engineering discipline to what
software organizations actually do.**
⚠️ **IE is applied to hospitals, airlines, call centres, logistics and service design at
least as much as to manufacturing** — **and its toolkit is operations research, statistics,
and human factors.**
**⚠️ This is the part of the document with the highest transfer rate, and it's under-known
in software precisely because the name sounds like it's about factories.**

---

## §12. ⚠️ Queueing Theory and Little's Law

**⚠️ The single most valuable import in this document, and it requires no metaphor —
it's a theorem.**
```
⚠️ LITTLE'S LAW:   L = λW
   ⚠️ Work In Progress = Arrival Rate × Time In System
   ⚠️ Holds for ANY stable queueing system regardless of distribution,
   service discipline, or what's queueing. It is a mathematical identity
⚠️ THEREFORE:  cycle time = WIP / throughput
   ⚠️ You cannot reduce cycle time without reducing WIP or raising throughput.
   Exhorting people to "work faster" changes neither
```
> **⚠️ GOTCHA — the utilization curve is the finding that changes how you staff teams,
> and almost nobody internalizes it.** ⚠️ **Queue length rises NON-LINEARLY with
> utilization, approaching infinity as utilization approaches 100%.** **⚠️ Roughly: a
> system at 80% utilization has queues around four times longer than one at 50%; past 90%
> the wait time explodes.**
> **⚠️ Variability makes it worse.** **The Kingman approximation shows waiting time scales
> with the variability of BOTH arrivals and service times — so a team with highly variable
> task sizes queues far worse than one with uniform tasks at the same utilization.**
> **⚠️ The management implication is deeply counterintuitive: a team booked to 100%
> capacity is not efficient, it is GUARANTEED to have exploding lead times.** **Slack is a
> throughput requirement, not a luxury** — **and this is a theorem, not an opinion.**

**⚠️ Practical software applications**: ⚠️ **WIP limits in Kanban are Little's Law applied;
so is limiting concurrent projects per team, sizing thread pools and connection pools,
and understanding why a service at 85% CPU has terrible tail latency.**
**⚠️ M/M/1 vs M/M/c**: ⚠️ **one shared queue served by c servers dramatically outperforms
c separate queues** — **which is the argument for shared work queues over per-person
assignment, and for a single load balancer queue over sticky routing.**

---

## §13. Theory of Constraints

**⚠️ Goldratt's framing: every system has exactly one binding constraint at a time, and
improvements anywhere else are illusory.**
```
⚠️ THE FIVE FOCUSING STEPS
   1. IDENTIFY the constraint
   2. EXPLOIT it — get maximum output from it without new investment
   3. SUBORDINATE everything else to it
   4. ELEVATE it — now spend money
   5. REPEAT — ⚠️ and beware inertia; the constraint MOVES
```
**⚠️ The central insight, stated plainly**: ⚠️ **an hour lost at the bottleneck is an hour
lost for the entire system; an hour saved at a non-bottleneck is a mirage.** **⚠️ Local
optimization degrades global throughput** — **which is why measuring individual team
utilization drives exactly the wrong behaviour.**
**⚠️ Drum-Buffer-Rope**: ⚠️ **the constraint sets the pace (drum), a buffer protects it
from starvation, and the rope limits release of new work into the system.** **⚠️ The rope
is a WIP limit, so this is §12 again from a different direction.**
**⚠️ Software translation**: ⚠️ **if code review is the constraint, hiring more developers
makes the queue longer, not the delivery faster.** **This is the most commonly violated
principle in engineering management.**

---

## §14. ⚠️ Lean and the Toyota Production System

**⚠️ What TPS actually is, as distinct from what software borrowed:**
```
⚠️ JIDOKA        ⚠️ automation WITH A HUMAN TOUCH — machines stop themselves
   on detecting a defect. ⚠️ The ANDON CORD: any worker can halt the line
JUST-IN-TIME     produce only what's needed, when needed
⚠️ HEIJUNKA      LEVEL the production schedule — smoothing variability (§12)
KANBAN           ⚠️ a physical PULL signal, not a board with columns
⚠️ KAIZEN        continuous small improvement BY THE PEOPLE DOING THE WORK
⚠️ THE 7 WASTES  overproduction, waiting, transport, over-processing,
   inventory, motion, defects
GENCHI GENBUTSU  ⚠️ "go and see" — decide at the actual place, not from a report
```
> **⚠️ GOTCHA — software's borrowing of "lean" dropped the two things that make it work.**
> ⚠️ **First, the ANDON CORD: TPS gives the lowest-status worker unconditional authority
> to stop production, and management's job is to come to them.** **Most software
> organizations that adopted "lean" did not adopt this, and the equivalent —
> stop-the-line on a broken build, or a junior engineer halting a release — is
> comparatively rare.**
> **⚠️ Second, HEIJUNKA: TPS goes to enormous lengths to LEVEL demand variability, because
> §12 says variability is what creates queues.** **Software's version of lean typically
> accepts wildly variable batch sizes and then wonders why flow is poor.**
> **⚠️ And note the misreading of "waste": eliminating slack is not lean.** ⚠️ **TPS runs
> buffers deliberately where variability requires them** — **removing all slack raises
> utilization toward the cliff in §12.**

**⚠️ Where lean genuinely transferred well**: **⚠️ small batch sizes, pull rather than push,
making work visible, and reducing handoffs** — **all of which are §12 and §13 in
practice.**

---

## §15. Six Sigma and Statistical Process Control

```
DMAIC          Define, Measure, Analyse, Improve, Control
⚠️ SIX SIGMA   3.4 defects per million opportunities (⚠️ with the
   conventional 1.5-sigma long-term shift baked in — the arithmetic
   surprises people who compute it from a normal table)
⚠️ CONTROL CHARTS  ⚠️ THE core tool, and the most transferable
   ⚠️ COMMON CAUSE variation = inherent to the process; reacting to it
      makes things WORSE (Deming's funnel experiment)
   ⚠️ SPECIAL CAUSE variation = something changed; investigate THIS
PROCESS CAPABILITY  Cp, Cpk — is the process capable of the spec at all?
```
> **⚠️ GOTCHA — the common-cause/special-cause distinction is the most useful idea here
> and software systematically violates it.** ⚠️ **Treating normal variation as a signal —
> asking why this sprint's velocity dipped, why last month's incident count rose — is
> TAMPERING, and Deming demonstrated it increases variation rather than reducing it.**
> **⚠️ Before reacting to a metric movement, establish whether it's outside the control
> limits.** **Most dashboard-driven management is tampering with a nice UI.**

**⚠️ Honest assessment of Six Sigma as a programme**: ⚠️ **the statistical tools are sound
and the belt-certification apparatus is largely organizational theatre.** **⚠️ It suits
high-volume repetitive processes with measurable defects; it fits software development
poorly because software work is not repetitive in the required sense — though it fits
software OPERATIONS (incidents, deploys, alerts) considerably better.**

---

## §16. Work Measurement and Standard Work

**Time and motion study (⚠️ Taylor and the Gilbreths — and the honest note that Taylorism
was genuinely dehumanizing in application, which is why the field moved on), predetermined
motion time systems, learning curves (⚠️ Wright's law: unit cost falls by a fixed
percentage per doubling of cumulative production — which is a real and repeatedly
validated effect), and standard work.**
> **⚠️ GOTCHA — do NOT apply work measurement to software development.** ⚠️ **It works for
> repetitive physical tasks with stable content, and software tasks are non-repetitive by
> definition — if you've done it before you call the function.** **⚠️ Every attempt to
> measure developer output by activity counts (commits, lines, tickets) recapitulates
> Taylorism's failure and gets gamed within a sprint.**
> **⚠️ Standard work DOES transfer to operations**: **runbooks, checklists and deployment
> procedures are standard work, and the aviation-derived checklist literature supports it.**
