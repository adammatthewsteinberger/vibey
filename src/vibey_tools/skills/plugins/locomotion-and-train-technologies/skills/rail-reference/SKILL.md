---
name: rail-reference
description: "Use when correcting a rail misconception, looking up an adhesion, gradient, axle-load, headway or energy figure, finding the books and standards, or needing a quick-reference picker — plus the current state of European signalling deployment and rail decarbonisation. Companion to the other rail engineering skills."
---

# Rail Engineering: What's Live, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *Locomotion and Train Technologies* reference (plugin `locomotion-and-train-technologies`), covering §26–§31. Sibling skills: `rail-adhesion-resistance-traction-physics-and-geometry` (§0–§4), `rail-steam-diesel-electric-and-alternative-traction` (§5–§9), `rail-track-structure-welded-rail-switches-and-electrification` (§10–§13), `rail-signalling-interlocking-train-protection-and-safety` (§14–§17), `rail-rolling-stock-braking-capacity-and-service-types` (§18–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and most of the engineering is a century settled. Two areas moved. See §26 for European signalling deployment, and rail decarbonisation traction choices.

> **⚠️ Rail exists because of one number: steel wheel on steel rail has a rolling
> resistance roughly an order of magnitude below rubber on road.** ⚠️ **Everything good
> about rail — the efficiency, the enormous train weights, the low energy per tonne-km —
> follows from that.** **And ⚠️ everything HARD about rail follows from the same fact: the
> same low friction that makes it efficient means trains cannot stop quickly, cannot climb
> steeply, and cannot steer.**
>
> **Complements a civil/industrial engineering reference (infrastructure and safety
> systems), a thermodynamics reference (traction thermodynamics), and a power engineering
> reference (electrification).**
>
> **⚠️ GOTCHA** boxes mark the physics people get backwards and the folklore that's wrong.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Low adhesion is the defining constraint** (§1 → `rail-adhesion-resistance-traction-physics-and-geometry`). **Braking distance, gradient
>    limits, and the entire existence of signalling systems all trace back to it — a train
>    cannot stop within the driver's sighting distance, so it must be told what's ahead.**
> 2. **⚠️ The wheelset steers itself, and that's why railways work** (§3 → `rail-adhesion-resistance-traction-physics-and-geometry`). **Coned wheels
>    on a solid axle self-centre — the flanges are a last-resort guard, not the steering
>    mechanism.**
> 3. **⚠️ Capacity is set by signalling and by the SLOWEST train, not by top speed** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`).
>    **Mixing traffic speeds destroys capacity faster than anything else.**

---

## §26. What's Live — verified August 2026

### 26.1 ⚠️ ETCS deployment: thirty years in, roughly 10% done
**⚠️ The most instructive live story here, and it's a story about integration cost rather
than technology.**

- **⚠️ The Third ERTMS Work Plan, published 23 February 2026 by the European ERTMS
  Coordinator, reports that by end-2024 ETCS was deployed on about 10% of the TEN-T
  network (12,400 km) and fitted to about 19% of the EU railway fleet (8,730 vehicles).**
  ⚠️ **Of the CORE network, around 17% is equipped (roughly 10,600 km).**
- **⚠️ The Coordinator's own assessment is blunt**: **deployment "remains significantly
  behind schedule and structurally uneven across Member States" and risks failing the
  TEN-T Regulation objectives.** ⚠️ **On current planning, the core network objective is
  projected to be reached only to about 50%.**
- **⚠️ Roughly 28,000 further km of TEN-T are planned for equipping by 2030, including
  22,000 km of core network** — ⚠️ **which is more than double the entire installed base
  in four years, against a track record of thirty.**
- **⚠️ Cost is reported at €500,000 to €2 million per track-kilometre** depending on level,
  existing infrastructure and country.

> **⚠️ GOTCHA — the diagnosis matters more than the numbers, and it generalizes far beyond
> railways.** ⚠️ **This is the world's most standardized safety-critical signalling
> programme and after thirty years it is a "patchwork of isolated lines and small
> disparate networks."** **⚠️ The industry's own explanation is not that the technology
> fails: it is fragmentation — varying national requirements, duplicated approval
> processes, unstable specifications, and design/testing/maintenance burden.**
> **⚠️ UNIFE's asks are harmonisation, simplification, reduced duplication in approvals and
> stable specifications — i.e. the problem is the STANDARD not being standard enough in
> practice.** **⚠️ One ERA official reportedly noted the Commission underestimated the
> resources ERA would need.**

**⚠️ What to watch**: **ETCS Level 2 is the dominant deployment standard for new and
upgraded mainline corridors (§16 → `rail-signalling-interlocking-train-protection-and-safety`); ⚠️ GSM-R is being succeeded by FRMCS (5G-based), and
mandatory specifications now cover ETCS B4 R1, FRMCS B0 and ATO B1 R1; ⚠️ and Digital
Automatic Coupling (DAC) is described as deployable from 2026 with the same fragmentation
risk — different national technical solutions and unaligned timetables.**
**⚠️ Note also the changed political driver**: ⚠️ **military mobility has been added to the
urgency arguments for interoperable European signalling, which is a new justification for
an old programme.**

### 26.2 ⚠️ Rail decarbonisation: hydrogen retreated, batteries and wires won
**⚠️ A genuine and well-documented reversal, and worth reporting precisely because the
earlier consensus was so confident.**

- **⚠️ The Alstom Coradia iLint entered service in Lower Saxony as the world's first
  hydrogen passenger train (testing from 2018, full commercial service 2022) and was
  presented as a mature, reliable diesel replacement.**
- **⚠️ Reliability did not hold up.** ⚠️ **By August 2025, reportedly only 4 of the 14
  Coradia iLint units in Lower Saxony were in service, with the operator EVB running
  diesel backup because replacement fuel-cell modules had not arrived.** **⚠️ In Hesse,
  most of the 27 two-car units delivered to RMV were reported out of service with
  technical problems, replaced by buses, with the RMV supervisory board chairman saying
  Alstom had "done a disservice to novel forms of traction with this series of failures."**
- **⚠️ The procurement decisions followed.** ⚠️ **Lower Saxony's LNVG cancelled further
  hydrogen purchases and moved to battery-electric multiple units — a reported 102 BEMUs
  plus 27 conventional electric units on a route to be electrified — stating battery
  trains are cheaper to operate.** ⚠️ **A Dutch tender in Groningen for hydrogen trains
  reportedly attracted no bids at all and the province moved toward electrification.**
- **⚠️ The manufacturer retreated too.** ⚠️ **In late 2025 Alstom paused further hydrogen
  development, describing the technology as "not yet mature" and citing the cessation of
  French IPCEI hydrogen funding**, **while committing to honour existing contracts in
  France, Germany and Italy.** ⚠️ **In April 2026 Alstom acquired Cummins' rail fuel-cell
  engineering and support activities** — **which one analysis reads as liability
  containment for an installed base rather than a growth investment.**
- **⚠️ The capital committed is not trivial**: **Lower Saxony reportedly committed €81.3
  million with about €8.4 million federal, including 30 years of maintenance and energy
  supply.**

> **⚠️ GOTCHA — draw the right lesson, which is not "hydrogen is impossible."** ⚠️ **It's
> that hydrogen rail's case was always avoiding electrification capital cost (§9 → `rail-steam-diesel-electric-and-alternative-traction`), and it
> depended on a chain of conditions all holding: cheap green hydrogen, a reliable fuel
> supply chain, and refuelling as dependable as diesel.** **⚠️ Meanwhile battery-electric
> improved, discontinuous electrification matured, and the efficiency gap (§9 → `rail-steam-diesel-electric-and-alternative-traction`) never
> closed.**
> ⚠️ **Note the asymmetry that made it worse: Alstom already had battery-electric products
> in hand — a first German BEMU contract in February 2020, and a published battery range
> of up to 120 km — so the alternative existed throughout.** **⚠️ The installed base is
> what converts a bad bet into a long-tail obligation: fleets, refuelling infrastructure
> and 30-year support contracts.**
> **⚠️ Fair caveat: contracted programmes in Germany, Italy and France continue, Alstom
> says it is developing improved fuel cell technology, and hydrogen may retain niches
> where routes are long, unelectrified and battery range is genuinely insufficient.**

**⚠️ The practical hierarchy that has emerged, and it maps onto §9 → `rail-steam-diesel-electric-and-alternative-traction`**: ⚠️ **electrify where
traffic justifies it; battery-electric with discontinuous electrification or charging
islands for regional routes; bi-mode where electrification is partial; and treat hydrogen
as a narrow case requiring specific justification rather than a default diesel
replacement.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| Flanges keep trains on the rails | ⚠️ **CONING steers. Flanges are a last-resort guard** (§3 → `rail-adhesion-resistance-traction-physics-and-geometry`) |
| Trains steer like other vehicles | ⚠️ **The wheelset self-centres via rolling radius difference** (§3 → `rail-adhesion-resistance-traction-physics-and-geometry`) |
| Trains could just brake on sight | ⚠️ **Stopping distance far exceeds sighting. Hence signalling** (§1 → `rail-adhesion-resistance-traction-physics-and-geometry`, §14 → `rail-signalling-interlocking-train-protection-and-safety`) |
| More power means more pulling | ⚠️ **At low speed, adhesive weight is the limit** (§2 → `rail-adhesion-resistance-traction-physics-and-geometry`) |
| A diesel locomotive is mechanically driven | ⚠️ **Usually diesel-ELECTRIC** (§6 → `rail-steam-diesel-electric-and-alternative-traction`) |
| Rails have expansion gaps | ⚠️ **CWR has none — stress builds internally** (§11 → `rail-track-structure-welded-rail-switches-and-electrification`) |
| Heat speed restrictions are excessive caution | ⚠️ **Buckling risk. Rail runs far above air temp** (§11 → `rail-track-structure-welded-rail-switches-and-electrification`) |
| Any crushed stone works as ballast | ⚠️ **Angularity and interlock do the work** (§10 → `rail-track-structure-welded-rail-switches-and-electrification`) |
| Track circuits are just detection | ⚠️ **Fail-safe: a broken rail shows OCCUPIED** (§14 → `rail-signalling-interlocking-train-protection-and-safety`) |
| Axle counters are strictly better | ⚠️ **They don't detect broken rails** (§14 → `rail-signalling-interlocking-train-protection-and-safety`) |
| Warning systems prevent SPADs | ⚠️ **Warning ≠ enforcement. ATP enforces** (§16 → `rail-signalling-interlocking-train-protection-and-safety`) |
| Capacity is about top speed | ⚠️ **Headway and homogeneity** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Mixed traffic uses the line efficiently | ⚠️ **Speed heterogeneity destroys capacity** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| HSR only benefits HSR passengers | ⚠️ **It relieves the classic line by removing fast trains** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| One cant value suits all trains | ⚠️ **Fast gets deficiency, slow gets excess** (§4 → `rail-adhesion-resistance-traction-physics-and-geometry`) |
| Regenerative braking always recovers energy | ⚠️ **Needs receptivity — somewhere for it to go** (§8 → `rail-steam-diesel-electric-and-alternative-traction`) |
| Air brakes work by applying pressure | ⚠️ **Pressure HOLDS THEM OFF. Loss applies them** (§19 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Long freight trains brake like passenger trains | ⚠️ **Pneumatic propagation is slow, front to back** (§19 → `rail-rolling-stock-braking-capacity-and-service-types`, §21 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Electrification cost is mostly wire | ⚠️ **Structures, clearances, bridges, immunization** (§13 → `rail-track-structure-welded-rail-switches-and-electrification`) |
| Hydrogen trains are the diesel replacement | ⚠️ **Battery and wires won on reliability and cost** (§26.2) |
| Maglev will replace railways | ⚠️ **Zero interoperability with 1.4M km of existing track** (§25 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Hyperloop is a transport question | ⚠️ **It's a long-vacuum-structure engineering question** (§25 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| ETCS is nearly deployed in Europe | ⚠️ **~10% of TEN-T after 30 years** (§26.1) |

---

## §28. Numbers

```
⚠️ Adhesion coefficient  dry 0.20–0.35 · wet 0.15–0.20 · ⚠️ contaminated <0.05
⚠️ Rolling resistance    roughly 1/10 of road
⚠️ Davis equation        R = A + Bv + Cv²  (⚠️ Cv² dominates at speed)
⚠️ Main line gradient    typically ≤1–1.5% · 2.5–3% is steep
⚠️ Standard gauge        1,435 mm · ⚠️ Russian 1,520 · Cape 1,067
⚠️ Wheel coning          ~1:20 to 1:40
⚠️ Axle load  HS passenger ~17–18 t · EU freight 22.5–25 t · ⚠️ heavy haul ~32.5 t
⚠️ Rail mass             ~60 kg/m typical mainline
⚠️ Electrification cost  reported €1–2 M/km
⚠️ ETCS cost             reported €0.5–2 M per track-km
⚠️ ETCS on TEN-T         ~10% (12,400 km) · ⚠️ core network ~17%
⚠️ EU fleet ETCS-fitted  ~19% (8,730 vehicles), end-2024
⚠️ ETCS capacity gain    reported 25% on one SNCF line (13→16 tph)
⚠️ Metro headway         ⚠️ 90 s or better on the best CBTC systems
⚠️ Battery train range   reported up to ~120 km
⚠️ Coradia iLint         ⚠️ 4 of 14 in service (Lower Saxony, Aug 2025)
```

---

## §29. Books and Resources

| Source | Why |
|---|---|
| **Profillidis** | *Railway Management and Engineering* | Broad and rigorous |
| **Esveld** | ***Modern Railway Track*** | ⚠️ **The track engineering reference — §10 → `rail-track-structure-welded-rail-switches-and-electrification`, §11 → `rail-track-structure-welded-rail-switches-and-electrification`** |
| **Iwnicki (ed.)** | ***Handbook of Railway Vehicle Dynamics*** | ⚠️ **§3 → `rail-adhesion-resistance-traction-physics-and-geometry`, §18 → `rail-rolling-stock-braking-capacity-and-service-types`. The serious treatment of the contact problem** |
| **Hall** | *Modern Signalling Handbook* | ⚠️ **§14–§16 → `rail-signalling-interlocking-train-protection-and-safety`, accessible** |
| **Theeg & Vlasenko (eds)** | *Railway Signalling & Interlocking* | The international comparison |
| **Pachl** | ***Railway Operation and Control*** | ⚠️ **§20 → `rail-rolling-stock-braking-capacity-and-service-types`. The best on capacity and operating principles** |
| **Hansen & Pachl (eds)** | *Railway Timetabling & Operations* | §20 → `rail-rolling-stock-braking-capacity-and-service-types` in depth |
| **RAIB / NTSB / BEA-TT reports** | — | ⚠️ **§17 → `rail-signalling-interlocking-train-protection-and-safety`. Free, rigorous, and the best failure-analysis reading available** |
| **UIC leaflets / EN standards / TSIs** | — | ⚠️ **The actual rules** |
| **ERA / ERTMS Work Plans** | — | ⚠️ **§26.1's primary source** |
| **Railway Gazette, IRJ, RailTech** | — | Trade press worth following |

---

## §30. Quick Reference

### 30.1 Picker
| Question | Where |
|---|---|
| Why do trains need signals at all? | ⚠️ **Stopping distance exceeds sighting distance** (§1 → `rail-adhesion-resistance-traction-physics-and-geometry`, §14 → `rail-signalling-interlocking-train-protection-and-safety`) |
| What keeps a train on the track? | ⚠️ **Wheel coning, not flanges** (§3 → `rail-adhesion-resistance-traction-physics-and-geometry`) |
| Why can't this line take more trains? | ⚠️ **Headway and speed heterogeneity** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Why is the freight slower than the wires allow? | ⚠️ **Cant excess, axle load, braking distance** (§4 → `rail-adhesion-resistance-traction-physics-and-geometry`, §19 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Why speed restrictions in a heatwave? | ⚠️ **CWR buckling** (§11 → `rail-track-structure-welded-rail-switches-and-electrification`) |
| Why is this junction the bottleneck? | ⚠️ **Conflicting paths at flat junctions** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Diesel or electric or battery? | ⚠️ **§9 → `rail-steam-diesel-electric-and-alternative-traction`'s efficiency ladder, then §26.2** |
| Why is signalling renewal so expensive? | ⚠️ **Safety assurance, not hardware** (§15 → `rail-signalling-interlocking-train-protection-and-safety`, §26.1) |
| Why can't we just run moving block? | ⚠️ **Train integrity detection, especially freight** (§16 → `rail-signalling-interlocking-train-protection-and-safety`) |
| Why build a new HSR line instead of upgrading? | ⚠️ **Segregation recovers classic-line capacity** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`, §23 → `rail-rolling-stock-braking-capacity-and-service-types`) |
| Is maglev the future? | ⚠️ **No interoperability with existing network** (§25 → `rail-rolling-stock-braking-capacity-and-service-types`) |

### 30.2 Reading a railway when you see one
- [ ] ⚠️ **Signal spacing tells you the block length and therefore the headway** (§14 → `rail-signalling-interlocking-train-protection-and-safety`, §20 → `rail-rolling-stock-braking-capacity-and-service-types`)
- [ ] ⚠️ **Absence of lineside signals suggests cab signalling / ETCS L2** (§16 → `rail-signalling-interlocking-train-protection-and-safety`)
- [ ] Cant on curves tells you the design speed (§4 → `rail-adhesion-resistance-traction-physics-and-geometry`)
- [ ] ⚠️ **Turnout angle tells you the diverging speed** (§12 → `rail-track-structure-welded-rail-switches-and-electrification`)
- [ ] Ballast shoulder width and condition indicates CWR management (§11 → `rail-track-structure-welded-rail-switches-and-electrification`)
- [ ] ⚠️ **Slab track means high speed, a tunnel, or high maintenance cost avoidance** (§10 → `rail-track-structure-welded-rail-switches-and-electrification`)
- [ ] Catenary tensioning weights indicate auto-tensioned OLE (§13 → `rail-track-structure-welded-rail-switches-and-electrification`)
- [ ] ⚠️ **Number of driven axles on a locomotive predicts its low-speed pull** (§2 → `rail-adhesion-resistance-traction-physics-and-geometry`)

---

## §31. Method

**§1–§25 → `rail-adhesion-resistance-traction-physics-and-geometry`, `rail-steam-diesel-electric-and-alternative-traction`, `rail-track-structure-welded-rail-switches-and-electrification`, `rail-signalling-interlocking-train-protection-and-safety`, `rail-rolling-stock-braking-capacity-and-service-types` rests on settled railway engineering** — **contact mechanics and coning, the Davis
resistance equation, block signalling and interlocking principles, brake fail-safe design,
track structure and CWR thermal behaviour, and capacity theory.** ⚠️ **The Westinghouse
brake dates to 1869 and the self-steering wheelset is older still; none of it needed
verification.**

**Two searches were run in August 2026**, on **European signalling deployment** and **rail
decarbonisation traction** — ⚠️ **chosen because both represent live decisions rather than
settled facts, and both have outcomes that contradict the confident forecasts made about
them.**

**Confidence.** **High** in §1 → `rail-adhesion-resistance-traction-physics-and-geometry`, §3 → `rail-adhesion-resistance-traction-physics-and-geometry` and §20 → `rail-rolling-stock-braking-capacity-and-service-types`, which are the load-bearing sections. ⚠️ **The
adhesion constraint explains why railways need signalling at all; the coned wheelset is the
most elegant and most misunderstood mechanism in the subject (flanges do NOT steer); and
§20 → `rail-rolling-stock-braking-capacity-and-service-types`'s point that capacity is destroyed by speed HETEROGENEITY rather than limited by top
speed is the single most useful thing here for anyone reading rail policy arguments.**
**High** in §11 → `rail-track-structure-welded-rail-switches-and-electrification` and §19 → `rail-rolling-stock-braking-capacity-and-service-types` — ⚠️ **CWR thermal stress and the fail-safe air brake are both
cases where the counterintuitive design is the safety-critical one.**

**High** in §26.1's figures, which come from the European Commission, ERA and the ERTMS
Coordinator's own Third Work Plan: ⚠️ **~10% of TEN-T (12,400 km), ~17% of core network,
~19% of fleet (8,730 vehicles) at end-2024, and the Coordinator's own judgement that the
core network objective will be met only to about 50%.** ⚠️ **The diagnosis — fragmentation
and approval duplication rather than technical failure — comes from the industry body UNIFE
and from ERA conference reporting, so it is the sector describing its own problem, which I
think is credible but is not disinterested.**

**High** on the §26.2 sequence of events, which is corroborated across trade press, and
**moderate** on some specifics. ⚠️ **The reliability figures (4 of 14 units in Lower Saxony
as of August 2025; most of RMV's 27 units out of service) come from trade reporting rather
than operator statements I could verify directly, and one source explicitly notes August
2025 is the latest fleet figure it can confirm.** ⚠️ **I've dated them accordingly.**
⚠️ **A sourcing note worth stating: several of the sharper analytical pieces on hydrogen
rail come from outlets with an editorial position favouring electrification, and one
promotional source in my results still described hydrogen trains in wholly positive terms
with no mention of the withdrawals.** **⚠️ I've anchored on the procurement decisions and
the manufacturer's own statements — Lower Saxony cancelling, Groningen's tender attracting
no bids, Alstom pausing development and calling the technology "not yet mature" — because
those are actions rather than opinions.** **⚠️ And I've kept the caveat that contracted
programmes continue and niches may remain, because "hydrogen rail failed" is a stronger
claim than the evidence supports.**
