---
name: mfg-reference
description: "Use when correcting a manufacturing or mechanical engineering misconception, looking up a strength, tolerance, cycle-time or cost figure, finding the books, or needing a quick-reference picker — plus the current state of additive manufacturing after its correction and industrial robotics adoption. Companion to the other manufacturing and mechanical engineering skills."
---

# Manufacturing and Mechanical Engineering: What's Live, Misconceptions, Numbers, and Books

> **Part 5 of 5** of the *Manufacturing and Mechanical Engineering for Software Devs* reference (plugin `manufacturing-mechanical-engineering-for-software-devs`), covering §25–§30. Sibling skills: `mfg-mechanics-stress-fatigue-and-materials` (§0–§5), `mfg-machine-elements-mechanisms-and-tolerances` (§6–§8), `mfg-process-families-machining-additive-and-moulding` (§9–§16), `mfg-dfm-metrology-plm-npi-and-what-transfers` (§17–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanics is settled. Two areas moved. See §25 for additive manufacturing after its correction, and industrial robotics adoption.

> **⚠️ Companion to a civil/industrial engineering reference.** ⚠️ **That one covers flow,
> constraints and safety systems; this one is about physically MAKING things — and the
> lessons are different.**
>
> **⚠️ The governing asymmetry: in software the marginal cost of a change is near zero and
> in manufacturing it is enormous.** ⚠️ **Almost every practice in this document is a
> response to that one fact — tolerances, DFM, PLM, EVT/DVT/PVT gates, and the reason
> mechanical engineers appear conservative to software people.**
>
> **⚠️ GOTCHA** boxes mark the intuitions that don't survive contact with atoms.
>
> **The three ideas that organize this document:**
> 1. **⚠️ NOTHING IS EXACT — everything is a tolerance** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`). **The single biggest mental
>    shift for software people: there is no equality in the physical world, only
>    distributions, and a design that requires exactness is a design that fails.**
> 2. **⚠️ The PROCESS determines the design, not the other way round** (§9 → `mfg-process-families-machining-additive-and-moulding`, §17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`).
>    **Geometry that's free in CAD can be impossible, or absurdly expensive, to make.**
> 3. **⚠️ FATIGUE kills things that were never overloaded** (§4 → `mfg-mechanics-stress-fatigue-and-materials`). **Most mechanical
>    failures happen far below the static strength, after many cycles — the physical
>    analogue of a bug that only appears after a million requests.**

---

## §25. What's Live — verified August 2026

### 25.1 ⚠️ Additive manufacturing after its correction
**⚠️ The clearest recent example of a technology completing the hype cycle, and the
post-correction picture is more useful than either the boom or the bust framing.**

- **⚠️ What happened**: ⚠️ **"valuations adjusted, consolidation increased, and several
  organizations were forced to retrench, reduce capacity, or narrow their scope,"** with
  the resulting correction producing today's more restrained conditions.
  ⚠️ **The honest diagnosis offered is a mismatch between investment timelines and actual
  adoption rates — the responses "were not irrational; they reflected prevailing signals
  from capital markets" at the time.**
- **⚠️ The numbers now**: ⚠️ **AMPOWER reports the industrial AM sector returning to growth
  of 5.6%; ⚠️ Wohlers reports metal AM revenues growing 15.3% year-over-year in 2025.**
  ⚠️ **Metal PBF is simultaneously CONSOLIDATING AND FRAGMENTING — the ten largest system
  makers hold about 78.3% of global revenue, down from 80%, as new entrants
  (particularly Chinese) arrive.**
- **⚠️ Where the growth actually is**: ⚠️ **defence, space and consumer are named as central
  drivers, with metal AM growth exceeding 20% over four years as military OEMs use it for
  supply chain problems, drones and next-generation components.** ⚠️ **Apple's adoption of
  LPBF for watch cases is described as the largest metal AM application to date and as
  validating LPBF as a genuine production technology.**

> **⚠️ GOTCHA — the durable lesson is the one §9 → `mfg-process-families-machining-additive-and-moulding` already implies, and it survived the
> hype cycle intact.** ⚠️ **AM wins on GEOMETRY, PART CONSOLIDATION and LEAD TIME, and
> loses on volume.** **⚠️ Stated plainly in the current coverage: if you need millions of
> simple identical plastic parts, injection moulding is the better answer; if a part is
> easily stamped, cast or machined at scale, AM is not competitive.**
> ⚠️ **The consolidation win is real and quantified — assemblies of 20–30 components
> printed as one unit, with reported weight reductions of 40–60% in topology-optimized
> parts — which is §17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`'s "delete the part" achieved by a different route.**

**⚠️ The remaining bottlenecks are not the printers**: ⚠️ **qualification pathways, a
persistent skills gap (with many institutions lacking industrial-grade equipment, creating
a circular hesitation), and post-processing.** ⚠️ **Note also the strategic self-criticism
from within the industry: executives at Formlabs, Carbon, Stratasys and Materialise
reportedly converged on the view that "the industry took too long to focus on customer
outcomes rather than on technology descriptions"** — **a failure mode software people will
recognize immediately.**
**⚠️ Sourcing caution: this space is covered almost entirely by AM trade press with
obvious interests; I've anchored on the AMPOWER and Wohlers figures and on the sceptical
framing, which is more informative than the promotional material.**

### 25.2 ⚠️ Industrial robotics: steady, large, and not what the headlines say
**⚠️ Included because the automation discourse and the installation data have diverged.**

- **⚠️ The scale, from the IFR's World Robotics data**: ⚠️ **542,076 industrial robots
  installed in 2024 — more than double the number ten years earlier, with annual
  installations topping 500,000 for the fourth consecutive year.** ⚠️ **Asia accounted for
  74% of new deployments, Europe 16%, the Americas 9%.** **⚠️ Around 4 million robots are
  operating in factories worldwide.**
- **⚠️ Market value reached an all-time high of US$16.7 billion** for industrial robot
  installations, per IFR's January 2026 trends release.
- **⚠️ US installations rose 11% year-on-year to 38,000 units in 2025**, ⚠️ **driven by food
  and other NON-manufacturing sectors — while automotive, still the largest single adopter
  at 13,500 units, was 1% below the previous year.**
- **⚠️ Robot density** (robots per 10,000 manufacturing employees) ⚠️ **is the IFR's
  comparison metric: Korea leads at 1,220, roughly four times the global average, with
  Singapore second at 818 — and the sources note Singapore's figure is partly an artefact
  of a small manufacturing workforce.**
- **⚠️ Automotive's share has fallen** from a historical 35–40% of installations to around
  28%, ⚠️ **as electronics, logistics and general industry adoption broadened.**

> **⚠️ GOTCHA — the humanoid story is where expectation and evidence diverge most, and the
> IFR's own framing is notably restrained.** ⚠️ **The IFR notes companies are "moving
> beyond prototypes to deploy humanoids in real life" while stating the conditions
> plainly: to compete with traditional automation, humanoids "need to match stringent
> requirements for cycle times, energy consumption, and maintenance costs," meet industry
> standards for safety and durability, and "achieve human-level dexterity and productivity"
> to fill labour gaps.**
> ⚠️ **The IFR has separately said mass adoption of humanoids, particularly as household
> helpers, may not happen in the near or medium term.**
> **⚠️ Read that as the industry body being deliberately careful about a category attracting
> enormous capital — the specific, boring requirements list is the tell.**

**⚠️ The genuine driver is labour, not capability**: ⚠️ **employers struggling to find
people, with over 600,000 unfilled US manufacturing jobs cited.** **⚠️ And cobots —
collaborative robots that work safely alongside people — are reported at entry prices
around $25,000 with payback periods under 18 months, which is what actually moves
adoption at the small-manufacturer end.**
**⚠️ Sourcing note: the IFR figures are primary and consistent across outlets; the cobot
pricing and payback claims come from a lead-generation site and should be treated as
indicative.**

---

## §26. Misconceptions

| Misconception | Correction |
|---|---|
| Stiffness and strength are the same | ⚠️ **Steel and stainless share E; strengths differ hugely** (§2 → `mfg-mechanics-stress-fatigue-and-materials`) |
| Parts fail when overloaded | ⚠️ **Fatigue kills below yield, after cycles** (§4 → `mfg-mechanics-stress-fatigue-and-materials`) |
| Aluminium has an endurance limit | ⚠️ **It doesn't. It accumulates damage at any amplitude** (§4 → `mfg-mechanics-stress-fatigue-and-materials`) |
| Sharp corners are fine | ⚠️ **Stress concentration. Add a radius** (§2 → `mfg-mechanics-stress-fatigue-and-materials`, §4 → `mfg-mechanics-stress-fatigue-and-materials`) |
| More bolts and pins make it stronger | ⚠️ **Over-constraint makes parts fight each other** (§7 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| Lock washers prevent loosening | ⚠️ **Split lock washers are largely ineffective** (§6 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| Tighter tolerances are better engineering | ⚠️ **They cost non-linearly. Tolerance the FUNCTION** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| Worst-case stack-up is the right method | ⚠️ **Often absurdly conservative; RSS is realistic** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| A dimension is a number | ⚠️ **It's a distribution. GD&T states intent** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| CAD geometry can be made | ⚠️ **Round cutters can't make sharp internal corners** (§11 → `mfg-process-families-machining-additive-and-moulding`) |
| 3D printing will replace manufacturing | ⚠️ **It loses badly at volume** (§13 → `mfg-process-families-machining-additive-and-moulding`, §25.1) |
| Casting and forging are interchangeable | ⚠️ **Forging's grain flow gives better fatigue life** (§10 → `mfg-process-families-machining-additive-and-moulding`) |
| Thick walls are stronger | ⚠️ **They sink in moulding and cast porous** (§10 → `mfg-process-families-machining-additive-and-moulding`, §14 → `mfg-process-families-machining-additive-and-moulding`) |
| Welded joints are as strong as the parent | ⚠️ **The heat-affected zone is where it fails** (§12 → `mfg-process-families-machining-additive-and-moulding`) |
| Adhesives are weak | ⚠️ **Strong in shear, poor in peel. Design the joint** (§12 → `mfg-process-families-machining-additive-and-moulding`) |
| FEA results are answers | ⚠️ **Hypotheses. Validate against hand calc and test** (§20 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Tooling is a detail | ⚠️ **It's the capital cost and the lead time** (§14 → `mfg-process-families-machining-additive-and-moulding`, §19 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| A revision is like a git commit | ⚠️ **Non-interchangeable means a NEW part number** (§21 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| You can roll back a change | ⚠️ **Old revisions physically exist, for decades** (§21 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Just order a few for testing | ⚠️ **Setup and MOQ dominate at low volume** (§19 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Inspection ensures quality | ⚠️ **Capable processes do. Also check gauge R&R** (§18 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Robots are replacing manufacturing labour | ⚠️ **The driver is unfilled vacancies** (§25.2) |
| Humanoids are about to transform factories | ⚠️ **The IFR lists the unmet requirements plainly** (§25.2) |
| Mechanical engineers are just conservative | ⚠️ **Change costs six figures. It's rational** (§1 → `mfg-mechanics-stress-fatigue-and-materials`, §24 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |

---

## §27. Numbers

```
⚠️ Steel E ≈ 200 GPa · Aluminium ≈ 70 GPa · ⚠️ same for most steels
⚠️ Aluminium density ≈ 1/3 of steel — ⚠️ and ~1/3 the stiffness
⚠️ Stress concentration Kt  ⚠️ typically 2–3× at holes and notches
⚠️ Bearing L10  ⚠️ life at which 10% have failed — statistical
⚠️ Rib thickness  ⚠️ ~50–60% of wall (injection moulding)
⚠️ Volume crossovers  ⚠️ 1–10 machine/AM · 100–1,000 soft tooling ·
                      10,000+ hard tooling
⚠️ AM sector growth   ⚠️ 5.6% (AMPOWER) · metal AM +15.3% YoY (Wohlers)
⚠️ Metal PBF top-10 share  ⚠️ 78.3%, down from 80%
⚠️ AM part consolidation   ⚠️ 20–30 parts → 1; 40–60% weight reduction
⚠️ Industrial robots installed 2024  ⚠️ 542,076 — 2× a decade earlier
⚠️ Asia share of installs  ⚠️ 74% · Europe 16% · Americas 9%
⚠️ Robot installation market value  ⚠️ US$16.7 bn (all-time high)
⚠️ US installs 2025  ⚠️ 38,000, +11% · automotive 13,500, −1%
⚠️ Robot density  ⚠️ Korea 1,220 · Singapore 818 per 10,000 employees
⚠️ Automotive share of installs  ⚠️ ~28%, down from 35–40%
```

---

## §28. Books

| Author | Work | Why |
|---|---|---|
| **Shigley (Budynas & Nisbett)** | ***Mechanical Engineering Design*** | ⚠️ **The standard. §2–§6 → `mfg-mechanics-stress-fatigue-and-materials`, `mfg-machine-elements-mechanisms-and-tolerances`** |
| **Ashby** | ***Materials Selection in Mechanical Design*** | ⚠️ **§5 → `mfg-mechanics-stress-fatigue-and-materials`. Genuinely elegant method** |
| **Boothroyd, Dewhurst & Knight** | ***Product Design for Manufacture and Assembly*** | ⚠️ **§17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`. THE DFA reference** |
| **Krulikowski** | *Fundamentals of GD&T* | ⚠️ **§8 → `mfg-machine-elements-mechanisms-and-tolerances`, accessible** |
| **ASME Y14.5** | — | ⚠️ **The GD&T standard itself** |
| **Kalpakjian & Schmid** | *Manufacturing Engineering and Technology* | ⚠️ **§9–§16 → `mfg-process-families-machining-additive-and-moulding`, comprehensive** |
| **Slocum** | ***Precision Machine Design*** | ⚠️ **§7 → `mfg-machine-elements-mechanisms-and-tolerances`'s exact constraint, done properly** |
| **Skakoon** | *The Elements of Mechanical Design* | ⚠️ **Short, principled, excellent** |
| **Adams** | ***Bearing Design in Machinery*** / manufacturer catalogues | ⚠️ **SKF and similar catalogues are real references** |
| **Machinery's Handbook** | — | ⚠️ **The trade's single-volume reference** |
| **Wohlers Report / AMPOWER Report** | — | ⚠️ **§25.1's primary data** |
| **IFR World Robotics** | — | ⚠️ **§25.2's primary data** |

---

## §29. Quick Reference

### 29.1 Picker
| Question | Where |
|---|---|
| Which process should I use? | ⚠️ **Volume and geometry decide** (§9 → `mfg-process-families-machining-additive-and-moulding`, §19 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Why is this part so expensive? | ⚠️ **Tolerances, setups, or low volume** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`, §11 → `mfg-process-families-machining-additive-and-moulding`, §19 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| It's strong enough — why did it break? | ⚠️ **Fatigue, or a stress concentration** (§2 → `mfg-mechanics-stress-fatigue-and-materials`, §4 → `mfg-mechanics-stress-fatigue-and-materials`) |
| Assembly binds or warps | ⚠️ **Over-constrained** (§7 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| Parts measure fine but don't fit | ⚠️ **Datum mismatch, or stack-up** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`) |
| Moulded part has sink marks | ⚠️ **Wall thickness. Core it out, rib it** (§14 → `mfg-process-families-machining-additive-and-moulding`) |
| Machined part can't be made | ⚠️ **Internal corners, tool reach, or setups** (§11 → `mfg-process-families-machining-additive-and-moulding`) |
| Should we 3D print it? | ⚠️ **Geometry, consolidation or lead time — else no** (§13 → `mfg-process-families-machining-additive-and-moulding`, §25.1) |
| How do I cut cost? | ⚠️ **Delete parts first** (§17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Can I just change the drawing? | ⚠️ **Is it still interchangeable?** (§21 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| FEA says it's fine | ⚠️ **Check boundary conditions; validate physically** (§20 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| Supplier wants an MOQ | ⚠️ **Setup costs are fixed per order** (§19 → `mfg-dfm-metrology-plm-npi-and-what-transfers`, §22 → `mfg-dfm-metrology-plm-npi-and-what-transfers`) |
| What should software steal from this? | ⚠️ **§24 → `mfg-dfm-metrology-plm-npi-and-what-transfers`, and tolerance thinking first** |

### 29.2 Design review checklist
- [ ] ⚠️ **Tolerances justified by FUNCTION, not habit** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`)
- [ ] ⚠️ **Stack-up analysed for every critical fit** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`)
- [ ] Datums consistent between design, manufacture and inspection (§8 → `mfg-machine-elements-mechanisms-and-tolerances`)
- [ ] ⚠️ **Fatigue considered where loading is cyclic** (§4 → `mfg-mechanics-stress-fatigue-and-materials`)
- [ ] Stress concentrations filleted (§2 → `mfg-mechanics-stress-fatigue-and-materials`)
- [ ] ⚠️ **Exactly constrained, not over-constrained** (§7 → `mfg-machine-elements-mechanisms-and-tolerances`)
- [ ] ⚠️ **Manufacturable by the intended process — draft, walls, reach** (§17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`)
- [ ] Assembly possible in one direction, with access (§17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`)
- [ ] ⚠️ **Part count challenged: can any of these be deleted?** (§17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`)
- [ ] Standard parts used wherever possible (§6 → `mfg-machine-elements-mechanisms-and-tolerances`, §22 → `mfg-dfm-metrology-plm-npi-and-what-transfers`)
- [ ] ⚠️ **Dissimilar metals checked for galvanic contact** (§5 → `mfg-mechanics-stress-fatigue-and-materials`)
- [ ] ⚠️ **Interchangeability decided before the revision is released** (§21 → `mfg-dfm-metrology-plm-npi-and-what-transfers`)

---

## §30. Method

**§1–§24 → `mfg-mechanics-stress-fatigue-and-materials`, `mfg-machine-elements-mechanisms-and-tolerances`, `mfg-process-families-machining-additive-and-moulding`, `mfg-dfm-metrology-plm-npi-and-what-transfers` rests on settled mechanics and standard manufacturing practice** — **stress and
fatigue theory, materials science, GD&T as codified in ASME Y14.5, the process families,
DFM/DFA, metrology, and PLM conventions.** ⚠️ **None of it needed verification; Wöhler
characterized fatigue in the 1860s and the volume-versus-process economics has not
changed.**

**Two searches were run in August 2026**, on **additive manufacturing** and **industrial
robotics** — ⚠️ **both chosen because they are the two areas where software people's
expectations diverge most from manufacturing reality, and both now have data rather than
projections.**

**Confidence.** **High** in §8 → `mfg-machine-elements-mechanisms-and-tolerances`, §7 → `mfg-machine-elements-mechanisms-and-tolerances` and §4 → `mfg-mechanics-stress-fatigue-and-materials`, which are the sections I'd most want read.
⚠️ **Tolerance thinking is the single best import from this field into software: nothing is
exact, everything is a distribution, and a design requiring exactness fails.** ⚠️ **Exact
constraint (§7 → `mfg-machine-elements-mechanisms-and-tolerances`) is the second — over-constraint produces conflict rather than robustness,
and the redundant-sources-of-truth analogy is exact.** **§4 → `mfg-mechanics-stress-fatigue-and-materials`'s fatigue framing gives software
a vocabulary for defects that only appear after many cycles.**

**High** in §21 → `mfg-dfm-metrology-plm-npi-and-what-transfers`'s PLM section, and ⚠️ **the interchangeability rule is the part worth
carrying: if the change makes the part non-interchangeable it needs a new identifier, not a
revision — because you cannot recall what already exists.** **That is semantic versioning
with genuinely irreversible consequences.**

**Moderate-to-high** on §25.1. ⚠️ **The AMPOWER 5.6% and Wohlers 15.3% figures and the
78.3% market-share number are attributed to named industry reports and recur across
coverage.** ⚠️ **But essentially all of this space is covered by AM trade press with
commercial interests, so I weighted the sceptical framing — the retrenchment narrative,
the "took too long to focus on customer outcomes" self-criticism, and the plain statement
that AM loses to moulding at volume — over the promotional material.** **⚠️ The 40–60%
weight reduction and 20–30 part consolidation figures come from a vendor blog and are
marked as reported.**

**High** on §25.2's IFR data, which is the field's authoritative source and consistent
across outlets: ⚠️ **542,076 installations in 2024, Asia 74%, US 38,000 in 2025 at +11%,
Korea's density of 1,220, and the US$16.7 billion market value.**
⚠️ **The humanoid framing is deliberately drawn from the IFR's own careful language rather
than from vendor claims** — **the fact that the industry body lists cycle times, energy
consumption, maintenance costs and human-level dexterity as unmet requirements is more
informative than any forecast.** **⚠️ The cobot price and payback figures come from a
marketing site and are indicative only.**
