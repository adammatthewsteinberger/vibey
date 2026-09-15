---
name: nuclear-reference
description: "Use when correcting a nuclear misconception, checking what actually moved in fusion milestones and the fission build picture (verified August 2026), reading the scope note, looking up a cross section, half-life, energy or dose value, finding the canon, or needing a picker and a method for reading a nuclear claim critically. Companion to the other nuclear-physics skills."
---

# Nuclear Physics: Misconceptions, What Moved, Numbers, and Canon

> **Part 5 of 5** of the *Nuclear Physics* reference (plugin `nuclear-physics`), covering §15–§21. Sibling skills: `nuclear-structure-decay-reactions-and-dose` (§0–§4), `nuclear-fission-reactor-physics-and-reactor-types` (§5–§7), `nuclear-fuel-cycle-waste-and-safety` (§8–§9), `nuclear-fusion-confinement-and-detection` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Nuclear physics is settled — Rutherford 1911, Chadwick 1932, Hahn-Meitner-Frisch 1938, Lawson 1957, Bethe. Fusion milestones and the fission build picture moved. See §16 below for both.

> **Scope.** ⚠️ **This covers nuclear physics and nuclear *energy* — reactor physics,
> fusion, radiation, and the fuel cycle.** **It does not cover weapon design, and §17
> says why plainly.** The physics here is standard undergraduate and graduate curriculum
> material.
>
> **⚠️ GOTCHA** boxes mark misconceptions and places where intuition fails — and public
> understanding of this subject is unusually poor, so §15 is long.
>
> **The three ideas that organize everything:**
> 1. **⚠️ The binding energy curve explains fission and fusion in one picture.** Iron-56 is
>    the most tightly bound nucleus. **Anything heavier releases energy by splitting;
>    anything lighter releases energy by fusing.** Both run downhill toward iron (§1.2 → `nuclear-structure-decay-reactions-and-dose`).
> 2. **⚠️ Nuclear energy densities are about a million times chemical.** Same Coulomb
>    barrier scaling that makes them hard to initiate makes them enormous once initiated.
>    **Every practical consequence — fuel volumes, waste volumes, accident severity —
>    follows from that factor** (§18).
> 3. **⚠️ Reactor safety is dominated by decay heat, not by the chain reaction.** You can
>    stop fission in under a second. **You cannot stop the ~7% residual heat from fission
>    products, and every major accident is a failure to remove it** (§9 → `nuclear-fuel-cycle-waste-and-safety`).

---

## §15. Misconceptions

**⚠️ Public understanding of this subject is unusually poor, and several of these errors
have shaped policy.**

| Misconception | Correction |
|---|---|
| "Critical" means dangerous | ⚠️ **`k=1` is steady-state normal operation** (§6.1 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| A reactor can explode like a bomb | ⚠️ **Physically impossible — the geometry and enrichment cannot support it. Chernobyl was a steam explosion** |
| Long half-life = highly dangerous | ⚠️ **The opposite. Activity is `λN`** (§2 → `nuclear-structure-decay-reactions-and-dose`) |
| Becquerels measure hazard | ⚠️ **Need isotope, pathway and geometry. Use sieverts for risk** (§4 → `nuclear-structure-decay-reactions-and-dose`) |
| Alpha emitters are the safest | ⚠️ **Harmless externally, worst internally** (§4 → `nuclear-structure-decay-reactions-and-dose`) |
| Radiation is radiation | ⚠️ **Type, energy and pathway change the hazard by orders of magnitude** (§4 → `nuclear-structure-decay-reactions-and-dose`) |
| Nuclear waste is a vast volume | ⚠️ **HLW is ~3% of volume; the whole civil inventory is small** (§8 → `nuclear-fuel-cycle-waste-and-safety`) |
| Waste is dangerous for a million years unchanged | ⚠️ **Radiotoxicity falls sharply; Sr/Cs dominate for centuries** (§8 → `nuclear-fuel-cycle-waste-and-safety`) |
| `²³⁸U` is inert | ⚠️ **Fertile — breeds `²³⁹Pu`; fissions fast above ~1 MeV** (§5 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| Stopping the chain reaction makes a reactor safe | ⚠️ **Decay heat is ~7% and must be removed for days** (§9 → `nuclear-fuel-cycle-waste-and-safety`) |
| Fukushima was a reactor design failure | ⚠️ **Scram worked. Loss of decay heat removal from a common-cause flood** (§9 → `nuclear-fuel-cycle-waste-and-safety`) |
| Chernobyl could happen anywhere | ⚠️ **Positive void coefficient and no containment — design-specific** (§9 → `nuclear-fuel-cycle-waste-and-safety`) |
| Nuclear power is the most dangerous energy source | ⚠️ **Per unit energy, comparable to wind/solar; far below coal** (§9 → `nuclear-fuel-cycle-waste-and-safety`) |
| Fusion is "clean" with no radioactivity | ⚠️ **Activated structure and tritium — much better than fission, not zero** (§13 → `nuclear-fusion-confinement-and-detection`) |
| Fusion has achieved net energy for a plant | ⚠️ **Scientific `Q` against target energy, not wall plug** (§10 → `nuclear-fusion-confinement-and-detection`, §16.1) |
| Fusion's remaining problem is physics | ⚠️ **Tritium breeding, materials, and divertor heat are the gates now** (§13 → `nuclear-fusion-confinement-and-detection`) |
| Fusion fuel is free so power will be cheap | ⚠️ **Capital cost dominates** (§13 → `nuclear-fusion-confinement-and-detection`) |
| Aneutronic fusion is nearly here | ⚠️ **p-¹¹B needs far higher temperature and loses to bremsstrahlung** (§10 → `nuclear-fusion-confinement-and-detection`) |
| Reactors are controlled purely mechanically | ⚠️ **Delayed neutrons make control possible at all** (§6.3 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| LNT is settled science at low dose | ⚠️ **It's a conservative regulatory assumption; the low-dose evidence is genuinely contested** (§4 → `nuclear-structure-decay-reactions-and-dose`) |
| Breeder reactors solve everything | Materials, sodium, and economics have repeatedly stalled them (§7 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| SMRs are proven and cheap | ⚠️ **Two operating worldwide; the first Western economics are cautionary** (§16.2) |

---

## §16. What Moved — verified August 2026

### 16.1 ⚠️ Fusion
**Ignition is now routine rather than singular, and that is the real change.**

**From Lawrence Livermore's own reporting:**
- **December 5, 2022** — ⚠️ **first ignition: ~3.15 MJ fusion yield from ~2.05 MJ of laser
  energy delivered to the target.**
- **February 23, 2025** — ⚠️ **seventh ignition: 5.0 MJ from 2.05 MJ, target gain 2.44.**
- **April 2025** — **a reported 8.6 MJ shot**, and ⚠️ **one source cites a record target
  gain of 4.13 in that period.**
- **2025** — **tenth ignition, 3.5 MJ, gain 1.74** (⚠️ **and note LLNL states plainly that
  this experiment was for stockpile stewardship purposes, which is a reminder of NIF's
  actual mission**).
- **⚠️ June 20, 2026 — eleventh ignition: 7.9 MJ ± 0.4, target gain ≈ 3.8**, with higher-
  energy experiments expected.

> **⚠️ GOTCHA — read those gain numbers precisely, because they are widely misreported.**
> ⚠️ **These are target gain: fusion yield divided by laser energy *delivered to the
> target*.** **NIF's laser system draws vastly more from the wall than it delivers.**
> **The facility remains substantially energy-negative overall**, and one trade source
> states this directly while reporting the records. ⚠️ **The 2022 result settled that net
> energy gain is physically achievable. It did not demonstrate a power plant, and NIF was
> never designed to be one.**

**Magnetic confinement:**
- **⚠️ ITER's schedule slipped substantially** — **the 2024 revised baseline moved first
  plasma from 2025 to ~2034–2035, with full D-T operation after that.** ⚠️ **ITER is not
  designed to generate electricity; it is an experiment to demonstrate a burning plasma
  at `Q ≈ 10`.** **Cost is cited above $22 billion across 35 nations.**
- **SPARC (Commonwealth Fusion Systems)** — compact tokamak using **HTS REBCO magnets**,
  targeting **`Q > 10`.** ⚠️ **The timeline has slipped: first plasma now targeted around
  2027**, with the commercial **ARC** plant (400 MWe, Virginia) aimed at the early 2030s.
  **CFS has raised roughly $3 billion.**
- **Wendelstein 7-X (stellarator)** — ⚠️ **1.3 GJ energy turnover in 2023 with eight-minute
  plasma; raised to 1.8 GJ in May 2025.** **Steady-state operation is the stellarator's
  structural advantage.**
- **UK STEP** — spherical tokamak, £1.3bn, construction ~2030, completion targeted 2040.

**⚠️ The honest 2026 summary, and one source puts it well**: **no commercial fusion plant
has produced electricity for the grid, no company is within twelve months of doing so, and
the original aggressive milestones have slipped** — **while the physics, engineering and
capital trajectory all moved forward meaningfully.** ⚠️ **No private company has achieved
net energy gain.** **Over 40 private ventures have raised $7–8 billion; commercial pilots
are generally targeted at 2035–2040**, which ⚠️ **means fusion will not contribute
materially to 2030 or 2050 decarbonization targets.**

**⚠️ And the focus has genuinely shifted**: with `Q>1` repeated, attention has moved to
**tritium breeding and materials** — **exactly §13 → `nuclear-fusion-confinement-and-detection`'s list.**

### 16.2 Fission
**Per the IEA's Global Energy Review 2026:**
- ⚠️ **Global nuclear capacity remained at ~420 GW at the end of 2025** — **3 GW of new
  capacity came online, offset by 3 GW of retirements, two-thirds of which was Belgium.**
- **⚠️ ~78 GW is under construction across 15 countries — one of the highest backlogs in
  30 years.** **Ten construction starts in 2025, nine of them in China.**
- **⚠️ Around 15 reactors are expected online in 2026, adding ~12 GW.**
- **⚠️ Nearly all reactors under construction are large-scale, most above 1000 MW.**

**SMRs — and the gap between narrative and status is wide:**
- **⚠️ Just two SMRs were operational worldwide as of 2026** — **China's land-based unit
  and Russia's marine-based one — with ~127 more in planning or construction.**
- **China's Linglong One (ACP100, 125 MW)** is expected to be ⚠️ **the world's first
  commercial onshore SMR, with operation expected in H1 2026** — ⚠️ **and note it began
  construction in 2021, six years later than originally planned.**
- **In North America**: **BWRX-300 at Darlington became the first SMR under construction**;
  **TerraPower's Natrium secured its NRC construction permit**; ⚠️ **only one SMR design
  is US-licensed (NuScale's 77 MW module).**
- **⚠️ HALEU fuel supply is repeatedly identified as the single biggest bottleneck**, with
  domestic production lagging reactor demand.
- **⚠️ Data centre demand is a major driver** — **Microsoft, Meta, Google and Amazon have
  collectively committed to 10 GW+ of nuclear capacity** (see a power-engineering
  reference §15.2 for the grid-side picture), **including restarts of existing plants.**

> **⚠️ GOTCHA — treat the SMR economics claims with real caution.** ⚠️ **The optimistic
> case (factory fabrication, 3–5 year builds, $4,000–7,000/kW) is a projection for
> nth-of-a-kind units, not observed cost.** **One 2026 analysis describes the economic
> evidence from the first wave of Western SMR projects as "cautionary."** ⚠️ **And the
> scale-up arithmetic is stark: the NEA's assessment is that even an ambitious 883 GW by
> 2050 requires the annual global startup rate to nearly triple, from 6.9 to 17.3 units
> per year.** **That is an industrial ramp that has not begun.**

---

## §17. Scope Note

**⚠️ This document covers nuclear physics and nuclear energy. It does not cover weapon
design, and I want to be direct rather than coy about that.**

**Everything here — binding energy, cross sections, criticality, moderation, reactivity
feedback, fusion confinement — is standard university curriculum and appears in the
textbooks in §19.** ⚠️ **Design details specific to weapons are a different category, they
provide no benefit in an energy and physics reference, and I have left them out
deliberately rather than by oversight.**

**Where weapons are unavoidably relevant I've noted it factually**: **`²³⁵U`/`²³⁹Pu` are
the fissile nuclides**, **enrichment and reprocessing are the proliferation-sensitive
steps of the fuel cycle (§8 → `nuclear-fuel-cycle-waste-and-safety`)**, **NIF's actual institutional mission is stockpile
stewardship (§16.1)**, and **the IAEA safeguards regime exists because civil and military
fuel cycles share technology.** ⚠️ **Those facts are load-bearing for understanding the
politics of nuclear energy and none of them constitute design information.**

---

## §18. Numbers

```
STRUCTURE
1 u = 931.5 MeV/c² · barn = 10⁻²⁸ m² · nuclear radius R ≈ 1.2 A^{1/3} fm
⚠️ Binding energy peak: ⁵⁶Fe / ⁶²Ni at ~8.8 MeV/nucleon
Magic numbers 2, 8, 20, 28, 50, 82, 126

FISSION
⚠️ ~200 MeV per fission · 2–3 neutrons · fragments ~168 MeV (deposited in microns)
²³⁵U thermal fission σ ≈ 585 b · ⚠️ fast σ ≈ 1–2 b
Natural U: 0.72% ²³⁵U · LWR fuel 3–5% · HALEU 5–20%
⚠️ Delayed neutron fraction β: ²³⁵U ≈ 0.0065, ²³⁹Pu ≈ 0.0021
Generation time: prompt ~10⁻⁴ s → with delayed ~0.1 s
Thermal neutron 0.025 eV · fission neutron ~2 MeV
⚠️ ¹³⁵Xe σ ≈ 2.6 million barns

DECAY HEAT ⚠️
~7% of full power at shutdown · ~1% at 1 hour · ~0.5% at 1 day
(3000 MWt reactor → 200 MW at shutdown)

FUSION
⚠️ D-T ignition temperature ~10–15 keV (100–150 million K)
D-T: ⁴He 3.5 MeV + n 14.1 MeV  ⚠️ (80% of energy in the neutron)
⚠️ Lawson triple product nTτ_E ≳ 3×10²¹ keV·s·m⁻³
Tritium half-life 12.3 years · ⚠️ TBR must exceed 1
Divertor heat flux target ~10 MW/m² · fusion power ∝ B⁴

RADIATION
Gray = J/kg · Sievert = Gy × w_R (⚠️ α ≈ 20, β/γ = 1)
Background ~2–3 mSv/yr · CT scan ~1–10 mSv
Occupational limit typically 20 mSv/yr averaged
⚠️ Acute: ~1 Sv sickness · ~4–5 Sv LD50 without treatment

ENERGY DENSITY ⚠️
Fission ~200 MeV/event vs chemical ~few eV/event — ~10⁸ ratio
1 kg ²³⁵U fully fissioned ≈ ~3000 tonnes of coal
```

---

## §19. Books

| Author | Work | Why |
|---|---|---|
| **Krane** | ***Introductory Nuclear Physics*** | ⚠️ **The standard undergraduate text. Start here** |
| **Lamarsh & Baratta** | ***Introduction to Nuclear Engineering*** | ⚠️ **§5–§9 → `nuclear-fission-reactor-physics-and-reactor-types`, `nuclear-fuel-cycle-waste-and-safety`. The reactor engineering standard** |
| **Duderstadt & Hamilton** | *Nuclear Reactor Analysis* | Reactor physics, deeper |
| **Knoll** | ***Radiation Detection and Measurement*** | ⚠️ **§14 → `nuclear-fusion-confinement-and-detection`, definitively. The reference in its field** |
| **Freidberg** | ***Plasma Physics and Fusion Energy*** | ⚠️ **§10–§13 → `nuclear-fusion-confinement-and-detection`. The best fusion text** |
| **Wesson** | *Tokamaks* | The tokamak reference |
| **Atzeni & Meyer-ter-Vehn** | *The Physics of Inertial Fusion* | §12 → `nuclear-fusion-confinement-and-detection` |
| **Cottrell** | *Nuclear Waste* | §8 → `nuclear-fuel-cycle-waste-and-safety`, level-headed |
| **Rhodes** | ***The Making of the Atomic Bomb*** | ⚠️ **History and physics; a genuinely great book** |
| **Mahaffey** | *Atomic Accidents* | §9 → `nuclear-fuel-cycle-waste-and-safety`, and unusually candid |

**Primary and practical**: **IAEA publications and the PRIS database** (⚠️ **the
authoritative reactor statistics**), **World Nuclear Association information library**
(⚠️ **industry-affiliated — accurate on technical detail, read the framing with that in
mind**), **NNDC/ENDF** for nuclear data and cross sections, **ICRP** for dose,
**IEA nuclear reports** (§16.2), **LLNL/NIF** and **ITER Organization** pages for §16.1,
**UNSCEAR** for radiation health effects, and **OpenMC** or **MCNP** for Monte Carlo
transport if you want to compute anything.

---

## §20. Quick Reference

### 20.1 Picker
| Question | Approach |
|---|---|
| Will this reaction release energy? | ⚠️ **Binding energy curve — move toward iron** (§1.2 → `nuclear-structure-decay-reactions-and-dose`) |
| How hazardous is this isotope? | ⚠️ **Half-life, decay mode, AND pathway** (§2 → `nuclear-structure-decay-reactions-and-dose`, §4 → `nuclear-structure-decay-reactions-and-dose`) |
| Shield gamma | High-Z (lead), exponential attenuation (§4 → `nuclear-structure-decay-reactions-and-dose`) |
| Shield neutrons | ⚠️ **Hydrogenous material, then a thermal absorber** (§4 → `nuclear-structure-decay-reactions-and-dose`) |
| Will this configuration go critical? | **Six-factor formula; geometry and leakage matter** (§6.1 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| Why is this reactor stable? | ⚠️ **Doppler coefficient — prompt and always negative** (§6.4 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| Reactor just shut down — is it safe? | ⚠️ **Decay heat. Removal must continue for days** (§9 → `nuclear-fuel-cycle-waste-and-safety`) |
| Can't restart after a scram | ⚠️ **Xenon pit — wait 1–2 days** (§6.4 → `nuclear-fission-reactor-physics-and-reactor-types`) |
| Fusion feasibility of a scheme | ⚠️ **Triple product, and which `Q` is being quoted** (§10 → `nuclear-fusion-confinement-and-detection`) |
| What gates a fusion plant now? | ⚠️ **Tritium breeding, 14 MeV materials, divertor** (§13 → `nuclear-fusion-confinement-and-detection`) |
| Identify an unknown gamma emitter | ⚠️ **HPGe spectroscopy — not a Geiger counter** (§14 → `nuclear-fusion-confinement-and-detection`) |
| Authoritative reactor statistics | **IAEA PRIS** (§19) |

### 20.2 Reading a nuclear claim critically
- [ ] Bq or Sv — activity or dose? Is the pathway specified? (§4 → `nuclear-structure-decay-reactions-and-dose`)
- [ ] Half-life quoted as if it were hazard? (§2 → `nuclear-structure-decay-reactions-and-dose`)
- [ ] Which `Q` for a fusion claim — target, plasma, or wall-plug? (§10 → `nuclear-fusion-confinement-and-detection`, §16.1)
- [ ] Is a reported gain a *scientific* gain at a facility that is net-negative? (§16.1)
- [ ] Is an SMR cost figure observed, or an nth-of-a-kind projection? (§16.2)
- [ ] Is a waste figure volume or radioactivity? (§8 → `nuclear-fuel-cycle-waste-and-safety`)
- [ ] Is a safety comparison per unit energy or per accident? (§9 → `nuclear-fuel-cycle-waste-and-safety`)
- [ ] Is the source industry-affiliated, and does the framing show it? (§19)

---

## §21. Method

**§1–§15 → `nuclear-structure-decay-reactions-and-dose`, `nuclear-fission-reactor-physics-and-reactor-types`, `nuclear-fuel-cycle-waste-and-safety`, `nuclear-fusion-confinement-and-detection` and §18 rest on settled physics** — **Rutherford (1911)**, **Chadwick (1932)**,
**Hahn, Meitner and Frisch (1938–39)**, **Fermi's pile (1942)**, **Bethe on stellar
fusion**, **Lawson (1957)** — sourced from the texts in §19, chiefly **Krane**, **Lamarsh
& Baratta**, **Freidberg**, and **Knoll**. ⚠️ **None of it needed verification.**

**Two searches were run in August 2026**, on **fusion milestones** and **the fission build
picture.**

**Confidence.** **High** in §1–§15 → `nuclear-structure-decay-reactions-and-dose`, `nuclear-fission-reactor-physics-and-reactor-types`, `nuclear-fuel-cycle-waste-and-safety`, `nuclear-fusion-confinement-and-detection`. **High** in §16.1's fusion numbers, which came from
**LLNL's own NIF page** — ⚠️ **a primary source giving specific yields, uncertainties and
dates, which is exactly what you want in an area this prone to press-release
inflation.** **High** in §16.2's fission statistics, which came from the **IEA's Global
Energy Review 2026** drawing on the **IAEA PRIS database.**

⚠️ **Three things I've been deliberate about.**

**§10 → `nuclear-fusion-confinement-and-detection` and §16.1 separate the `Q` definitions and then apply that distinction to the
headline numbers.** ⚠️ **NIF's reported gains are target gains against laser energy
delivered to the target — the facility remains substantially energy-negative at the wall
plug, and one source states this plainly while reporting the records.** **The 2022 result
genuinely settled that net gain is physically achievable; it is routinely reported as
something considerably stronger.** ⚠️ **If you take one thing from §16, take the habit of
asking which `Q`.**

**§16.2's SMR section deliberately contrasts narrative with status.** ⚠️ **Two SMRs
operating worldwide against ~127 planned; the first commercial onshore unit six years
behind its original schedule; one US-licensed design; HALEU as the acknowledged
bottleneck; and first-wave Western economics described in the sourcing as
"cautionary."** **The cost figures circulating are nth-of-a-kind projections, not observed
costs**, and I've labelled them as such. ⚠️ **Note also that much of the SMR literature is
produced by market-research firms and industry bodies with an interest in the growth
story — the IEA and IAEA figures are the ones to anchor on.**

**§17 states the scope decision plainly** rather than leaving a silent gap. ⚠️ **The
physics in this document is standard curriculum; weapon design specifics are a different
category and add nothing to an energy reference.** **Where weapons bear on the civil
picture — fissile nuclides, the proliferation-sensitive steps of the fuel cycle, NIF's
stockpile-stewardship mission, the existence of safeguards — I've said so, because those
facts are necessary to understand why the fuel cycle is politically constrained.**
