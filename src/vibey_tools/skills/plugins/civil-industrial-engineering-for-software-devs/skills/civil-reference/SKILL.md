---
name: civil-reference
description: "Use when checking a civil or industrial engineering misconception, looking up a load factor, safety factor, queueing or reliability figure, finding the books, or needing a quick-reference picker — plus the current US infrastructure condition and megaproject estimation data. Companion to the other civil and industrial engineering skills."
---

# Civil and Industrial Engineering: What's Live, Misconceptions, Numbers, and Books

> **Part 5 of 5** of the *Civil and Industrial Engineering for Software Devs* reference (plugin `civil-industrial-engineering-for-software-devs`), covering §23–§28. Sibling skills: `civil-loads-safety-factors-materials-and-foundations` (§0–§5), `civil-codes-licensure-failure-analysis-and-construction` (§6–§10), `civil-industrial-engineering-queueing-toc-and-lean` (§11–§16), `civil-reliability-safety-and-what-transfers-to-software` (§17–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanics and the operations research are settled. Two areas carry live numbers. See §23 for US infrastructure condition, and the megaproject estimation data.

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
>    with no metaphor required** (§11 → `civil-industrial-engineering-queueing-toc-and-lean`, §12 → `civil-industrial-engineering-queueing-toc-and-lean`). **Little's Law is as true of a deployment
>    pipeline as of a factory, and it is the single most valuable import in this document.**
> 3. **⚠️ The disanalogies are load-bearing** (§22 → `civil-reliability-safety-and-what-transfers-to-software`). **Software's marginal cost of
>    replication is zero, its "material properties" are unmeasured, and its requirements
>    change during construction — and each of those breaks a specific borrowed practice.**

---

## §23. What's Live — verified August 2026

### 23.1 ⚠️ Infrastructure condition: the asset-management picture in numbers
**⚠️ Included because it's what §10 → `civil-codes-licensure-failure-analysis-and-construction`'s asset management produces when done at national
scale — and because "technical debt" arguments are strengthened enormously by seeing what
a quantified version looks like.**

- **⚠️ ASCE's 2025 Report Card graded US infrastructure an overall 'C'** — ⚠️ **an
  improvement from 'C−' in 2021 and the highest since the Report Card began in 1998.**
  **18 categories assessed; ⚠️ nearly half improved, and for the first time since 1998 no
  category received a 'D−'.**
- **⚠️ Grades ranged from 'B' for ports to 'D' for stormwater and transit.** **Broadband
  debuted at 'C+'.** ⚠️ **Energy (D+) and rail (B−) DECLINED.** **Nine categories remain
  in the 'D' range.**
- **⚠️ The gap grew even as grades improved, which is the important finding.** **ASCE
  projects a **$3.7 trillion** shortfall between planned investment and what's needed for
  a state of good repair — ⚠️ **up from $2.59 trillion four years earlier.**
- **⚠️ The improvement is attributed largely to the 2021 IIJA ($1.2 trillion; reported
  $580B in new funding), and ASCE cautions the gains are driven by SHORT-TERM funding
  rather than long-term certainty**, ⚠️ **with authorizations expiring in fiscal 2026 and
  reauthorization uncertain.**

> **⚠️ GOTCHA — the lesson for software's technical-debt conversations is the shape of the
> curve, not the dollar figure.** ⚠️ **Grades improved AND the gap widened simultaneously**,
> **because deterioration and demand growth outran a large one-off investment.** **⚠️ A
> backlog that grows faster than you pay it down is not fixed by a single funded
> initiative — and the ASCE framing shows what it takes to argue for sustained funding:
> a standing inventory, condition assessment, deterioration modelling and a published
> number.** **Software's technical-debt arguments almost never have any of those.**

### 23.2 ⚠️ Project estimation: the base rates, and they include software
**⚠️ The most directly transferable body of evidence in this entire document, because
Flyvbjerg's database includes IT projects and compares them to physical ones.**

- **⚠️ The database holds roughly 16,000 large projects across 20+ fields and 136
  countries, assembled at Oxford over decades**, ⚠️ **recording the budget at the decision
  to build against the final outcome.**
- **⚠️ The headline finding**: ⚠️ **reportedly only about 0.5% of projects come in on
  budget, on time, AND with the promised benefits.** **Around 8.5% hit cost and time but
  not benefits.**
- **⚠️ Averages by type from the earlier published work**: ⚠️ **rail ~45% cost overrun,
  fixed links (bridges and tunnels) ~34%, roads ~20%, in real terms.** **⚠️ Nine out of ten
  projects overrun; overruns above 50% are common and above 100% not uncommon.**
- **⚠️ The finding that should end the "we're getting better at this" conversation**:
  ⚠️ **overruns have been roughly CONSTANT across the seventy years for which data
  exists** — **indicating no improvement in planning and cost management over that period.**

> **⚠️ GOTCHA — IT sits in the FAT TAIL, and that's the number software people should
> know.** ⚠️ **Reportedly 18% of IT projects had cost overruns above 50%, and for those
> projects the average overrun was around 447%.** **⚠️ The distinction that matters is not
> the mean but the TAIL: IT's average overrun is unremarkable, and its catastrophic-outcome
> rate is among the worst of any category.**
> **⚠️ The practical implication: for software projects, the risk is not "we'll be 30%
> over," it's the small probability of a multiple-of-budget disaster** — **which means
> risk management should target the tail, not the average.**

**⚠️ REFERENCE CLASS FORECASTING is the documented remedy, and it's the technique to
steal:**
```
⚠️ 1. Identify a reference class of similar COMPLETED projects
⚠️ 2. Establish the distribution of outcomes for that class
⚠️ 3. Position your project in that distribution and apply the UPLIFT
   for your desired confidence level
```
⚠️ **It's described as the only forecasting method with documented evidence of reducing
optimism bias**, **has been endorsed by the American Planning Association, and has been
mandatory in UK Treasury Green Book / Department for Transport practice since 2003.**
**⚠️ The worked logic**: **if rail's 50th-percentile overrun is 40% and its 80th percentile
is 57%, then an 80%-confidence budget applies a 57% uplift** — **and publishing the
un-uplifted figure is CHOOSING roughly an 80% probability of overrun.**
**⚠️ Translated to software**: ⚠️ **your team's own history of similar completed projects
IS a reference class, and using it beats bottom-up estimation.** **This is the same
statistical move as Monte Carlo forecasting from historical cycle time** (see an
engineering-process reference).

> **⚠️ One honest caveat on the source.** ⚠️ **The Flyvbjerg database has been criticized
> in the peer-reviewed literature for not being openly available**, **which limits
> independent verification of the specific figures.** ⚠️ **Note also that other bodies
> measuring differently report less extreme numbers — PMI-derived figures put IT budget
> overruns around 27% on average with ~55% of projects meeting goals — because they
> aggregate projects of all sizes, and small projects perform better.** **⚠️ The
> qualitative finding (systematic optimism bias, fat-tailed IT outcomes, RCF as remedy) is
> robust and widely replicated; treat the precise percentages as contested.**

---

## §24. Misconceptions

| Misconception | Correction |
|---|---|
| Factor of safety means "build it twice as strong" | ⚠️ **A calibrated allowance for quantified uncertainty** (§3 → `civil-loads-safety-factors-materials-and-foundations`) |
| Modern design uses one global safety factor | ⚠️ **Partial factors on loads and resistances (LRFD)** (§3 → `civil-loads-safety-factors-materials-and-foundations`) |
| Strong and stiff are the same | ⚠️ **Different properties; serviceability is stiffness** (§4 → `civil-loads-safety-factors-materials-and-foundations`) |
| Failure is failure | ⚠️ **Ductile warns; brittle doesn't. Design for ductile** (§4 → `civil-loads-safety-factors-materials-and-foundations`) |
| Building codes are bureaucratic overhead | ⚠️ **An accumulated failure log with legal force** (§6 → `civil-codes-licensure-failure-analysis-and-construction`, §8 → `civil-codes-licensure-failure-analysis-and-construction`) |
| Software should just adopt building codes | ⚠️ **Look at DO-178C's cost. That's the price** (§6 → `civil-codes-licensure-failure-analysis-and-construction`) |
| Tacoma Narrows was resonance | ⚠️ **Aeroelastic flutter** (§8 → `civil-codes-licensure-failure-analysis-and-construction`) |
| Hyatt Regency was a maths error | ⚠️ **A detail change nobody re-analysed** (§8 → `civil-codes-licensure-failure-analysis-and-construction`) |
| Watch the critical path | ⚠️ **Watch the NEAR-critical paths too** (§9 → `civil-codes-licensure-failure-analysis-and-construction`) |
| Industrial engineering is about factories | ⚠️ **Systems of people, materials and information** (§11 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Little's Law is a useful analogy | ⚠️ **It's a theorem. It holds unconditionally** (§12 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| A fully-utilized team is efficient | ⚠️ **Queues explode near 100% utilization** (§12 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Speed up everyone to go faster | ⚠️ **Only the constraint matters** (§13 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Kanban means a board with columns | ⚠️ **A pull signal. The WIP limit is the point** (§14 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Lean means eliminating slack | ⚠️ **TPS buffers deliberately; heijunka levels demand** (§14 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| We adopted lean | ⚠️ **Did you adopt the andon cord? Usually not** (§14 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Investigate every metric dip | ⚠️ **That's tampering. Check the control limits first** (§15 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Measure developer output like factory output | ⚠️ **Non-repetitive work. Taylorism fails here** (§16 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| MTBF of 100,000 hours means it lasts 11 years | ⚠️ **It's a rate parameter, not a lifespan** (§19 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Improve reliability by raising MTBF | ⚠️ **Halving MTTR often helps as much, cheaper** (§19 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Ten 99.9% services give 99.9% | ⚠️ **Series multiplies: 99%** (§19 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Training and policy are strong controls | ⚠️ **Second-weakest tier. Eliminate instead** (§20 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Human error explains the incident | ⚠️ **It's where analysis starts** (§18 → `civil-reliability-safety-and-what-transfers-to-software`, §20 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Software isn't real engineering, so nothing transfers | ⚠️ **The mathematics transfers exactly** (§21 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Software is engineering, so civil practice applies | ⚠️ **Seven real disanalogies** (§22 → `civil-reliability-safety-and-what-transfers-to-software`) |
| We're getting better at estimating | ⚠️ **Overruns roughly constant for 70 years** (§23.2) |
| IT projects are averagely risky | ⚠️ **Unremarkable mean, catastrophic tail** (§23.2) |
| Bottom-up estimation is more rigorous | ⚠️ **Reference class forecasting beats it** (§23.2) |

---

## §25. Numbers

```
⚠️ Typical structural FoS         ~1.5–2.0 (higher where consequences severe)
⚠️ Utilization → queue length     non-linear; explodes above ~90%
⚠️ Little's Law                   L = λW  (WIP = arrival rate × time in system)
⚠️ Six Sigma                      3.4 DPMO (with 1.5σ long-term shift)
⚠️ Series reliability             10 × 99.9% = 99%
⚠️ Availability                   MTBF / (MTBF + MTTR)
⚠️ ASCE 2025 overall grade        C (from C− in 2021; highest since 1998)
⚠️ ASCE investment gap            $3.7T (up from $2.59T four years earlier)
⚠️ ASCE range                     B (ports) to D (stormwater, transit)
⚠️ IIJA                           $1.2T; reported $580B new funding
⚠️ Flyvbjerg database             ~16,000 projects, 20+ fields, 136 countries
⚠️ On budget + on time + benefits reportedly ~0.5%
⚠️ Mean overruns                  rail ~45% · fixed links ~34% · roads ~20%
⚠️ IT tail                        18% of projects >50% over; those average ~447%
⚠️ RCF                            mandatory in UK Green Book practice since 2003
```

---

## §26. Books

| Author | Work | Why |
|---|---|---|
| **Petroski** | ***To Engineer Is Human*** | ⚠️ **§8 → `civil-codes-licensure-failure-analysis-and-construction`. Failure as the engine of engineering knowledge. Start here** |
| **Gordon** | ***Structures: Or Why Things Don't Fall Down*** | ⚠️ **The best popular structural book ever written** |
| **Levy & Salvadori** | *Why Buildings Fall Down* | §8 → `civil-codes-licensure-failure-analysis-and-construction`'s case studies |
| **Flyvbjerg & Gardner** | ***How Big Things Get Done*** | ⚠️ **§23.2. Read it as a software person** |
| **Goldratt** | ***The Goal*** | ⚠️ **§13 → `civil-industrial-engineering-queueing-toc-and-lean`. A novel, and the fastest way to internalize ToC** |
| **Hopp & Spearman** | ***Factory Physics*** | ⚠️ **§12 → `civil-industrial-engineering-queueing-toc-and-lean`. The rigorous treatment of queueing in operations** |
| **Reinertsen** | ***Principles of Product Development Flow*** | ⚠️ **§12–§14 → `civil-industrial-engineering-queueing-toc-and-lean` translated to product development. The bridge book** |
| **Liker** | *The Toyota Way* | §14 → `civil-industrial-engineering-queueing-toc-and-lean` |
| **Deming** | *Out of the Crisis* | ⚠️ **§15 → `civil-industrial-engineering-queueing-toc-and-lean`. Common vs special cause, and the funnel** |
| **Perrow** | ***Normal Accidents*** | ⚠️ **§20 → `civil-reliability-safety-and-what-transfers-to-software`. Coupling and complexity** |
| **Reason** | *Human Error* | §18 → `civil-reliability-safety-and-what-transfers-to-software`, §20 → `civil-reliability-safety-and-what-transfers-to-software` |
| **Weick & Sutcliffe** | *Managing the Unexpected* | ⚠️ **§20 → `civil-reliability-safety-and-what-transfers-to-software`'s HRO principles** |
| **Dekker** | *The Field Guide to Understanding Human Error* | ⚠️ **The practical §18 → `civil-reliability-safety-and-what-transfers-to-software`** |
| **Hollnagel** | *Safety-I and Safety-II* | §20 → `civil-reliability-safety-and-what-transfers-to-software` |
| **Vaughan** | *The Challenger Launch Decision* | ⚠️ **Normalization of deviance, in depth** |

---

## §27. Quick Reference

### 27.1 Picker
| Problem | Where |
|---|---|
| Cycle time too long | ⚠️ **Little's Law: reduce WIP or raise throughput** (§12 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Team is busy but nothing ships | ⚠️ **Utilization near 100%. Queues** (§12 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Added people, got slower | ⚠️ **You didn't add them at the constraint** (§13 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Which improvement to make first? | ⚠️ **Find the bottleneck. Everything else is a mirage** (§13 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| Metric moved — investigate? | ⚠️ **Only if outside control limits** (§15 → `civil-industrial-engineering-queueing-toc-and-lean`) |
| System falls over under load | ⚠️ **Design ductile: shed load, degrade** (§4 → `civil-loads-safety-factors-materials-and-foundations`) |
| Reliability target across services | ⚠️ **Series multiplies. Budget explicitly** (§19 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Improve availability cheaply | ⚠️ **Usually MTTR, not MTBF** (§19 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Security backlog prioritization | ⚠️ **Hierarchy of controls. Eliminate > train** (§20 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Post-incident, "human error" | ⚠️ **Ask what made the error likely** (§18 → `civil-reliability-safety-and-what-transfers-to-software`, §20 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Retries causing cascade | ⚠️ **Bullwhip. Backoff with jitter** (§17 → `civil-reliability-safety-and-what-transfers-to-software`) |
| Estimate a large project | ⚠️ **Reference class forecasting, not bottom-up** (§23.2) |
| Arguing for tech-debt investment | ⚠️ **Build the asset register first** (§10 → `civil-codes-licensure-failure-analysis-and-construction`, §23.1) |
| Change looks like a detail | ⚠️ **Hyatt Regency. Re-derive the assumption** (§8 → `civil-codes-licensure-failure-analysis-and-construction`) |

### 27.2 The transferable checklist
- [ ] ⚠️ **WIP is limited somewhere explicit** (§12 → `civil-industrial-engineering-queueing-toc-and-lean`)
- [ ] ⚠️ **The current constraint is identified and named** (§13 → `civil-industrial-engineering-queueing-toc-and-lean`)
- [ ] Utilization is deliberately below capacity (§12 → `civil-industrial-engineering-queueing-toc-and-lean`)
- [ ] ⚠️ **The system degrades gracefully rather than failing suddenly** (§4 → `civil-loads-safety-factors-materials-and-foundations`)
- [ ] Reliability budgeted across the whole path, not per-service (§19 → `civil-reliability-safety-and-what-transfers-to-software`)
- [ ] ⚠️ **Controls chosen from the top of the hierarchy, not the bottom** (§20 → `civil-reliability-safety-and-what-transfers-to-software`)
- [ ] ⚠️ **Normal variation is not being reacted to** (§15 → `civil-industrial-engineering-queueing-toc-and-lean`)
- [ ] Estimates anchored to a reference class of completed work (§23.2)
- [ ] ⚠️ **Someone can stop the line without permission** (§14 → `civil-industrial-engineering-queueing-toc-and-lean`, §20 → `civil-reliability-safety-and-what-transfers-to-software`)

---

## §28. Method

**§2–§22 → `civil-loads-safety-factors-materials-and-foundations`, `civil-codes-licensure-failure-analysis-and-construction`, `civil-industrial-engineering-queueing-toc-and-lean`, `civil-reliability-safety-and-what-transfers-to-software` rests on settled engineering and operations research** — **structural mechanics,
materials, queueing theory, the Theory of Constraints, SPC, reliability mathematics and
the safety literature.** ⚠️ **Little's Law is a theorem, the reliability arithmetic is
arithmetic, and the case studies in §8 → `civil-codes-licensure-failure-analysis-and-construction` are decades old and thoroughly documented.**

**Two searches were run in August 2026**, on **US infrastructure condition** and **the
megaproject estimation data** — ⚠️ **both chosen because they produce NUMBERS that
transfer, rather than because the underlying disciplines moved.**

**Confidence.** **High** in §12 → `civil-industrial-engineering-queueing-toc-and-lean`, and it's the section I'd most want read. ⚠️ **Little's
Law and the utilization curve are the highest-value ideas here precisely because they
require no analogical reasoning** — **they apply to any stable queueing system, and a team
booked to 100% capacity is not efficient but mathematically guaranteed to have exploding
lead times.** **§13 → `civil-industrial-engineering-queueing-toc-and-lean` and §20 → `civil-reliability-safety-and-what-transfers-to-software` are close behind for the same reason: mechanism, not metaphor.**

**High** in §22 → `civil-reliability-safety-and-what-transfers-to-software`, which is the section I'd defend hardest as ANALYSIS rather than fact.
⚠️ **My position is that software should stop borrowing civil engineering's culture and
start borrowing industrial engineering's mathematics and safety engineering's
institutions** — **and I've stated the seven disanalogies explicitly so the reasoning is
checkable.** ⚠️ **I've also conceded the strongest point on the other side: the individual
accountability structure of licensure (§7 → `civil-codes-licensure-failure-analysis-and-construction`) is a real difference that none of the
disanalogies explain away.**

**High** in §23.1's figures, which come from ASCE's own Report Card and are consistent
across trade coverage: ⚠️ **overall 'C', $3.7 trillion gap up from $2.59 trillion, B for
ports down to D for stormwater and transit.** **The interpretive point — that grades
improved while the gap widened, which is the shape technical-debt arguments should
recognize — is mine.**

**Moderate** on §23.2's precise numbers, and I've flagged why. ⚠️ **The qualitative
findings (systematic optimism bias, seventy years without improvement, IT's fat tail, RCF
as the evidenced remedy) are robust and replicated.** ⚠️ **But the peer-reviewed literature
contains a real methodological criticism — that Flyvbjerg's database is not openly
available for independent verification — and other bodies measuring differently report
much less extreme figures (PMI-derived: ~27% average IT overrun, ~55% meeting goals),
largely because they include smaller projects.** **⚠️ Several of the specific percentages
in my results came from secondary summaries and calculator sites rather than the primary
publications, so I've marked them as reported.** **The 447% IT tail figure in particular is
widely quoted and I would want the primary source before relying on it in a decision.**
