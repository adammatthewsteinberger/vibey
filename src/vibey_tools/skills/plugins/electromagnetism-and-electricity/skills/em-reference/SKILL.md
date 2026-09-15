---
name: em-reference
description: "Use when correcting an electricity or electromagnetism misconception, looking up a permittivity, permeability, resistivity, field-strength or breakdown figure, finding the books, or needing a quick-reference picker — plus the current state of superconductivity claims and wide-bandgap power semiconductors. Companion to the other electromagnetism skills."
---

# Electromagnetism: What's Live, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *Electromagnetism and the Physics of Electricity* reference (plugin `electromagnetism-and-electricity`), covering §26–§31. Sibling skills: `em-electrostatics-fields-potential-and-dielectrics` (§0–§5), `em-current-energy-flow-circuits-and-ac` (§6–§11), `em-magnetism-induction-and-transformers` (§12–§15), `em-maxwell-waves-transmission-lines-and-relativity` (§16–§19), `em-conduction-semiconductors-grounding-and-electrical-safety` (§20–§25). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The theory has been settled since 1865. Two areas are live. See §26 for superconductivity claims, and wide-bandgap power semiconductors.

> **⚠️ The most complete classical theory in physics, and the one whose everyday
> descriptions are most wrong.** ⚠️ **Almost every intuition taught in school — electrons
> flowing fast through wires, energy travelling inside the conductor, current choosing the
> path of least resistance — is false, and the corrections are not pedantry: they change
> what you predict** (§6 → `em-current-energy-flow-circuits-and-ac`, §8 → `em-current-energy-flow-circuits-and-ac`, §9 → `em-current-energy-flow-circuits-and-ac`).
>
> **Complements a fundamental-physics reference (quantum foundations), a radio-technology
> reference (RF practice), and a thermodynamics reference (energy accounting).**
>
> **⚠️ GOTCHA** boxes mark the misconceptions and the places where a valid model is being
> used outside its domain.
>
> **⚠️ Safety, stated once**: ⚠️ **mains and higher voltages kill, capacitors hold charge
> after power is removed, and it is CURRENT THROUGH THE BODY that harms** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`). **Nothing
> here is a substitute for qualified electrical work.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ FIELDS are the physical objects; charges and currents are sources** (§3 → `em-electrostatics-fields-potential-and-dielectrics`, §16 → `em-maxwell-waves-transmission-lines-and-relativity`).
>    **The field carries the energy and the momentum, and it is local — action at a
>    distance is not what happens.**
> 2. **⚠️ ENERGY FLOWS IN THE FIELD AROUND THE WIRE, NOT THROUGH IT** (§8 → `em-current-energy-flow-circuits-and-ac`). **The Poynting
>    vector is the correction that reorganizes everything downstream, including why
>    transmission lines, EMC and antennas behave as they do.**
> 3. **⚠️ Circuit theory is an APPROXIMATION with a stated validity condition** (§9 → `em-current-energy-flow-circuits-and-ac`).
>    **It holds when the circuit is small compared to the wavelength. Above that, you need
>    fields — and most confusing high-speed behaviour is this boundary being crossed.**

---

## §26. What's Live — verified August 2026

### 26.1 ⚠️ Superconductivity: a case study in extraordinary claims
**⚠️ Included because the physics is settled and the SOCIOLOGY is instructive — this is
the best recent example in physical science of how claims fail and how a field corrects.**

- **⚠️ The ambient-pressure record actually moved in 2026.** ⚠️ **A University of Houston
  team reported Tc of 151 K at ambient pressure in HgBa₂Ca₂Cu₃O₈₊δ via a "pressure quench"
  technique, published in PNAS** — **reported as the highest recorded at ambient pressure
  since superconductivity was discovered in 1911, against a plateau of around 133–135 K
  that had stood for decades.**
- **⚠️ The high-profile failures are worth knowing in detail, because the pattern
  repeats:**
```
⚠️ 2020  Dias et al., carbonaceous sulfur hydride, room-temperature
   superconductivity at ~267 GPa, published in Nature.
   ⚠️ Nature reportedly published over the objections of the majority
   of its own peer reviewers
⚠️ 2022  ⚠️ RETRACTED. Data artefacts identified externally, including
   magnetic susceptibility data that appeared copied between ranges
⚠️ 2023  Dias et al., N-doped lutetium hydride, room temperature at
   ~1 GPa, published in Nature. ⚠️ RETRACTED the same year at the
   request of most of its own authors
⚠️ 2023  LK-99 (copper-doped lead apatite) — ⚠️ viral, and conclusively
   explained within about two months: the levitation was ferromagnetic
   Cu₂S impurity, and the resistivity drop near 380 K matched a Cu₂S
   superionic phase transition. NOT the Meissner effect
```
> **⚠️ GOTCHA — the diagnostic that separates real from spurious, and it's simple.**
> ⚠️ **A drop in electrical resistance is NOT sufficient evidence of superconductivity —
> many things cause that, including phase transitions in impurity phases.** **⚠️ True
> superconductivity requires demonstration of the MEISSNER EFFECT (§22 → `em-conduction-semiconductors-grounding-and-electrical-safety`), verified by
> SQUID magnetometry.** **⚠️ Independent replication is the other half.**
> ⚠️ **Note how the field self-corrected: external groups reanalysed published figures,
> found artefacts, failed to replicate, and traced LK-99's anomalies to a specific
> impurity — largely in public and within months.**

**⚠️ Where the field actually stands, per a 2026 PNAS programmatic review**: ⚠️ **there are
no physical laws preventing room-temperature superconductivity — superconductivity is
described as "almost a generic property of nonmagnetic metals" — and the authors frame the
remaining work as two grand challenges: a PREDICTION challenge (prediction has advanced
dramatically but most predicted materials are not synthesizable) and an ENGINEERING
challenge.** ⚠️ **The 2026 landscape is characterized as a stark divide: hydride systems
that set Tc records but demand pressures exceeding 100 GPa, and ambient-pressure
candidates that remain unvalidated.**
**⚠️ Genuine ambient-pressure progress is happening in nickelates** — ⚠️ **reported
superconductivity onset above 60 K in ambient-pressure nickelate films, up from a previous
cap around 50 K, and around 96 K in nickelates under pressure.**
**⚠️ Sourcing note: this topic attracts hype aggregators; I anchored on PNAS, Nature's
retraction record, Science's reporting and arXiv preprints.**

### 26.2 ⚠️ Wide-bandgap semiconductors: §21's physics becoming infrastructure
**⚠️ The most consequential applied electromagnetics shift currently underway.**

- **⚠️ The physics driving it** (§21 → `em-conduction-semiconductors-grounding-and-electrical-safety`): ⚠️ **SiC is reported with roughly 10× the breakdown
  field and 3× the thermal conductivity of silicon**, **permitting thinner drift regions,
  much lower on-resistance at high voltage, higher junction temperatures and higher
  switching frequency.** ⚠️ **GaN's electron mobility is reported around 2000 cm²/V·s,
  roughly twice SiC's, giving sub-nanosecond switching.**
- **⚠️ The resulting division of labour is a physics consequence, not a marketing one:**
```
⚠️ SiC   ⚠️ high voltage, high temperature, high power. EV traction
   inverters — ⚠️ especially 800 V architectures, where bus voltages
   approach or exceed the rating limits of conventional silicon
   IGBTs — plus grid and solid-state transformers, 1200–3300 V classes
⚠️ GaN   ⚠️ the 100–650 V "golden zone." ⚠️ Sub-nanosecond switching
   shrinks magnetics and heatsinks dramatically, because passive
   component size scales inversely with frequency
⚠️ Si    ⚠️ still the volume foundation — reported at 52.72% of EV
   semiconductor technology share in 2025
```
- **⚠️ Adoption figures, with the caveat that market-research numbers vary widely:**
  ⚠️ **SiC went into a reported 1.17 million EV traction inverters in Q1 2026, or 17.2% of
  everything shipped (TrendForce); ⚠️ one source reports SiC inverter share rising from
  under 8% of global EV production in 2021 to 24% by 2026, with a projection of 55% by
  2030; ⚠️ another puts SiC above 50% penetration in PREMIUM vehicles specifically.**
  ⚠️ **Grid and HVDC penetration is reported below 5%, constrained by device voltage
  ratings and evolving standards.**
- **⚠️ Efficiency claims**: ⚠️ **reported around 10% better inverter efficiency versus
  silicon, and claims of up to 70% lower energy losses** — **⚠️ treat the higher figure as
  vendor-adjacent and application-specific.**

> **⚠️ GOTCHA — the two technologies stopped being competitors, and hybrid design is now
> the state of the art.** ⚠️ **A reported 12 kW AI server power supply reference design
> mixes silicon, SiC and GaN in one unit — GaN on the high-frequency stages, SiC on the
> high-stress ones — at better than 99% PFC efficiency.** **⚠️ A single bidirectional GaN
> switch is reported replacing a four-MOSFET full bridge.**
> **⚠️ The AI data centre is now a major driver alongside EVs, pushing 800 VDC
> architectures for exactly §14 → `em-magnetism-induction-and-transformers`'s reason: at fixed power, higher voltage means lower
> current, and I²R losses fall as the square.**

**⚠️ Sourcing note: this section draws heavily on market-research and trade publications
with commercial interests, and the market-size figures disagree with each other by wide
margins.** ⚠️ **The PHYSICS — breakdown field, mobility, and the resulting
voltage-versus-frequency division of labour — is solid and checkable from §21 → `em-conduction-semiconductors-grounding-and-electrical-safety`; the
adoption percentages are directional only.**

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| Electrons zip through wires at light speed | ⚠️ **Drift is mm/s; the FIELD propagates** (§6 → `em-current-energy-flow-circuits-and-ac`) |
| Energy flows through the wire | ⚠️ **It flows in the field around it — Poynting** (§8 → `em-current-energy-flow-circuits-and-ac`) |
| Current takes the path of least resistance | ⚠️ **It takes ALL paths, inversely proportional** (§7 → `em-current-energy-flow-circuits-and-ac`) |
| Return current takes the shortest route | ⚠️ **At HF it follows least inductance, under the trace** (§7 → `em-current-energy-flow-circuits-and-ac`, §24 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Ohm's law is a law of nature | ⚠️ **A material behaviour many things don't obey** (§7 → `em-current-energy-flow-circuits-and-ac`) |
| Kirchhoff's voltage law always holds | ⚠️ **Fails with changing flux through the loop** (§9 → `em-current-energy-flow-circuits-and-ac`, §13 → `em-magnetism-induction-and-transformers`) |
| Circuit theory always applies | ⚠️ **Only when size ≪ wavelength** (§9 → `em-current-energy-flow-circuits-and-ac`, §18 → `em-maxwell-waves-transmission-lines-and-relativity`) |
| A capacitor is a capacitor at any frequency | ⚠️ **Above self-resonance it's an inductor** (§9 → `em-current-energy-flow-circuits-and-ac`) |
| 50 Ω cable dissipates 50 Ω worth | ⚠️ **Characteristic impedance is geometric, not resistive** (§18 → `em-maxwell-waves-transmission-lines-and-relativity`) |
| Reactive power is wasted power | ⚠️ **It dissipates nothing — but it causes I²R losses** (§11 → `em-current-energy-flow-circuits-and-ac`) |
| RMS is the average of the waveform | ⚠️ **It's the equivalent-heating value** (§11 → `em-current-energy-flow-circuits-and-ac`) |
| Magnetic force does work on charges | ⚠️ **F ⊥ v always. It never does work** (§12 → `em-magnetism-induction-and-transformers`) |
| A superconductor is just a perfect conductor | ⚠️ **Meissner effect — it EXPELS flux** (§22 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Zero resistance proves superconductivity | ⚠️ **Requires the Meissner effect. See LK-99** (§26.1) |
| Transformers work on DC | ⚠️ **Need changing flux; DC saturates and burns the core** (§14 → `em-magnetism-induction-and-transformers`) |
| Semiconductors conduct worse when hot | ⚠️ **Better — opposite to metals** (§7 → `em-current-energy-flow-circuits-and-ac`, §20 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Holes are just missing electrons | ⚠️ **Genuine positive quasiparticles with their own mobility** (§21 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Magnetism is separate from electricity | ⚠️ **One field; the split is frame-dependent** (§19 → `em-maxwell-waves-transmission-lines-and-relativity`) |
| A Faraday cage blocks all fields | ⚠️ **Apertures relative to wavelength govern** (§3 → `em-electrostatics-fields-potential-and-dielectrics`, §24 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Splitting the ground plane reduces noise | ⚠️ **It forces a detour and enlarges the loop** (§24 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Fuses protect people | ⚠️ **They protect wiring. RCD/GFCI protects people** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| High voltage is what kills you | ⚠️ **Current through the body does** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| You can let go if it hurts | ⚠️ **Above the let-go threshold you cannot** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Disconnected equipment is safe | ⚠️ **Capacitors hold lethal charge** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Room-temperature superconductors have been made | ⚠️ **Both headline claims were retracted** (§26.1) |
| SiC and GaN compete for the same jobs | ⚠️ **Different voltage/frequency zones; hybrids now standard** (§26.2) |

---

## §28. Numbers

```
⚠️ e = 1.602×10⁻¹⁹ C · ε₀ = 8.854×10⁻¹² F/m · μ₀ ≈ 4π×10⁻⁷ H/m
⚠️ c = 1/√(μ₀ε₀) = 2.998×10⁸ m/s  ⚠️ — predicted from EM constants
⚠️ Free space impedance  ~377 Ω
⚠️ Drift velocity in copper  ⚠️ ~mm/s · thermal velocity ~10⁶ m/s
⚠️ Copper resistivity  1.68×10⁻⁸ Ω·m
⚠️ V_rms = V_peak/√2 (sine only)
⚠️ Lumped-model validity  ⚠️ size < ~λ/10
⚠️ Body current  ⚠️ let-go ~10–20 mA · fibrillation ~100 mA
⚠️ RCD/GFCI trip  ⚠️ tens of mA, in milliseconds
⚠️ Bandgaps  ⚠️ Si ~1.1 eV · SiC ~3.3 eV · GaN ~3.4 eV
⚠️ SiC vs Si  ⚠️ ~10× breakdown field · ~3× thermal conductivity
⚠️ GaN mobility  ⚠️ ~2000 cm²/V·s (≈2× SiC)
⚠️ Ambient-pressure Tc record  ⚠️ 151 K (2026, reported) — was ~133–135 K
⚠️ Hydride Tc records  ⚠️ require >100 GPa
⚠️ SiC in EV traction inverters  ⚠️ 17.2% of Q1 2026 shipments (reported)
```

---

## §29. Books

| Author | Work | Why |
|---|---|---|
| **Purcell & Morin** | ***Electricity and Magnetism*** | ⚠️ **THE book. §19 → `em-maxwell-waves-transmission-lines-and-relativity`'s relativistic derivation is its signature** |
| **Griffiths** | ***Introduction to Electrodynamics*** | ⚠️ **The standard undergraduate text, and genuinely well written** |
| **Feynman** | *Lectures, Volume II* | ⚠️ **§8 → `em-current-energy-flow-circuits-and-ac`'s Poynting discussion is the classic treatment** |
| **Jackson** | *Classical Electrodynamics* | ⚠️ **Graduate, formidable, definitive** |
| **Horowitz & Hill** | ***The Art of Electronics*** | ⚠️ **The practical counterpart. §9–§11 → `em-current-energy-flow-circuits-and-ac`** |
| **Ott** | ***Electromagnetic Compatibility Engineering*** | ⚠️ **§24 → `em-conduction-semiconductors-grounding-and-electrical-safety`. The reference** |
| **Johnson & Graham** | *High-Speed Digital Design* | ⚠️ **§18 → `em-maxwell-waves-transmission-lines-and-relativity` for digital engineers** |
| **Ashcroft & Mermin** | *Solid State Physics* | §20–§22 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| **Sze** | *Physics of Semiconductor Devices* | §21 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| **Tinkham** | *Introduction to Superconductivity* | §22 → `em-conduction-semiconductors-grounding-and-electrical-safety` |
| **NIST CODATA** | — | Constants |

---

## §30. Quick Reference

### 30.1 Picker
| Question | Where |
|---|---|
| Why does the light come on instantly? | ⚠️ **Fields propagate; electrons crawl** (§6 → `em-current-energy-flow-circuits-and-ac`, §8 → `em-current-energy-flow-circuits-and-ac`) |
| Where does the energy actually go? | ⚠️ **Poynting — through the field into the load** (§8 → `em-current-energy-flow-circuits-and-ac`) |
| Can I use circuit theory here? | ⚠️ **Is the circuit ≪ λ?** (§9 → `em-current-energy-flow-circuits-and-ac`, §18 → `em-maxwell-waves-transmission-lines-and-relativity`) |
| Why is my decoupling not working? | ⚠️ **Above the capacitor's self-resonance** (§9 → `em-current-energy-flow-circuits-and-ac`) |
| Why is there ringing on my trace? | ⚠️ **Reflection. Terminate it** (§18 → `em-maxwell-waves-transmission-lines-and-relativity`) |
| Where should the return current flow? | ⚠️ **Directly under the trace. Don't split the plane** (§24 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |
| Why does my inductor saturate? | ⚠️ **B-H curve limit, not heat** (§15 → `em-magnetism-induction-and-transformers`) |
| Why does the relay kill my transistor? | ⚠️ **L dI/dt spike. Flyback diode** (§14 → `em-magnetism-induction-and-transformers`) |
| Why high-voltage transmission? | ⚠️ **I²R falls as the square of current** (§14 → `em-magnetism-induction-and-transformers`) |
| Why does power factor matter? | ⚠️ **Apparent power sizes the infrastructure** (§11 → `em-current-energy-flow-circuits-and-ac`) |
| Is magnetism a separate force? | ⚠️ **No — same field, different frame** (§19 → `em-maxwell-waves-transmission-lines-and-relativity`) |
| Does this material superconduct? | ⚠️ **Show me the Meissner effect** (§22 → `em-conduction-semiconductors-grounding-and-electrical-safety`, §26.1) |
| SiC or GaN? | ⚠️ **Voltage and frequency decide** (§26.2) |
| Why did I get a shock but they didn't? | ⚠️ **Path, skin condition, and let-go threshold** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`) |

### 30.2 Sanity checks
- [ ] ⚠️ **Which rung of §1 → `em-electrostatics-fields-potential-and-dielectrics`'s ladder am I on, and is it valid here?**
- [ ] ⚠️ **Have I drawn the CURRENT LOOP, including the return path?** (§24 → `em-conduction-semiconductors-grounding-and-electrical-safety`)
- [ ] Units consistent; RMS vs peak resolved (§11 → `em-current-energy-flow-circuits-and-ac`)
- [ ] ⚠️ **Is the circuit small compared to the wavelength of the fastest EDGE?** (§9 → `em-current-energy-flow-circuits-and-ac`, §18 → `em-maxwell-waves-transmission-lines-and-relativity`)
- [ ] Parasitics considered — ESL, ESR, trace inductance (§9 → `em-current-energy-flow-circuits-and-ac`)
- [ ] ⚠️ **Is any flux changing through a loop I'm measuring across?** (§13 → `em-magnetism-induction-and-transformers`)
- [ ] Core saturation and thermal limits checked (§15 → `em-magnetism-induction-and-transformers`)
- [ ] ⚠️ **Capacitors discharged before touching anything** (§25 → `em-conduction-semiconductors-grounding-and-electrical-safety`)

---

## §31. Method

**§1–§25 → `em-electrostatics-fields-potential-and-dielectrics`, `em-current-energy-flow-circuits-and-ac`, `em-magnetism-induction-and-transformers`, `em-maxwell-waves-transmission-lines-and-relativity`, `em-conduction-semiconductors-grounding-and-electrical-safety` is settled classical physics and standard engineering practice.** ⚠️ **Maxwell
published in 1865; the equations have survived relativity and quantum mechanics as exact
classical limits, and nothing in the core theory required verification.**

**Two searches were run in August 2026**, on **superconductivity** and **wide-bandgap
power semiconductors** — ⚠️ **the first because it is the best current case study in how
extraordinary physical claims fail and get corrected, the second because §21 → `em-conduction-semiconductors-grounding-and-electrical-safety`'s device
physics is currently reshaping real infrastructure.**

**Confidence.** **High** in §6 → `em-current-energy-flow-circuits-and-ac`, §8 → `em-current-energy-flow-circuits-and-ac` and §9 → `em-current-energy-flow-circuits-and-ac`, which are the sections I'd most want read.
⚠️ **The Poynting correction — energy travels in the field around the conductor, not
inside it — is the single most clarifying idea here, because it makes transmission lines,
EMC, antennas and grounding instances of one thing rather than four unrelated subjects.**
**§7 → `em-current-energy-flow-circuits-and-ac`'s "current takes ALL paths" and §9 → `em-current-energy-flow-circuits-and-ac`'s validity condition are the two corrections that
most often change a prediction.**

**High** in §25 → `em-conduction-semiconductors-grounding-and-electrical-safety`'s safety physics. ⚠️ **The let-go threshold is the point most worth
internalizing: the reason relatively small currents kill is that the victim cannot release
the conductor — and it explains why RCD/GFCI protection exists and why fuses do not
protect people.**

**High** on §26.1's documented sequence. ⚠️ **The two Nature retractions (2022 and 2023)
and the LK-99 resolution are matters of public record, and the Cu₂S explanation traces to
independent replication work reported in Science and elsewhere.** ⚠️ **The 151 K
ambient-pressure result and the nickelate figures come to me via secondary coverage of
PNAS and arXiv rather than direct reading, so I've attributed them as reported.**
**⚠️ The methodological point — resistance drop alone is insufficient, the Meissner effect
is the test — is the durable takeaway and is independent of any particular claim.**

**Moderate** on §26.2's adoption numbers, and I've flagged why in-section. ⚠️ **The device
physics is solid and checkable from §21 → `em-conduction-semiconductors-grounding-and-electrical-safety`.** ⚠️ **The market figures come from
market-research firms and trade publications with commercial interests and disagree
substantially — SiC EV inverter penetration is variously reported as 17.2% of Q1 2026
shipments, 24% of production, and over 50% in premium vehicles, which are probably
measuring different denominators rather than contradicting outright.** **⚠️ I've reported
them as reported and would not build an argument on any single figure.**
