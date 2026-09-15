---
name: nuclear-fission-reactor-physics-and-reactor-types
description: "Use when reasoning about how a reactor works: fission physics and the fission product spectrum, reactor physics including criticality and the multiplication factor, moderation, why delayed neutrons are the reason reactors are controllable at all, and reactivity feedback and control; plus the reactor types and the design trade-offs that distinguish them."
---

# Nuclear Physics: Fission Physics, Reactor Physics, and Reactor Types

> **Part 2 of 5** of the *Nuclear Physics* reference (plugin `nuclear-physics`), covering §5–§7. Sibling skills: `nuclear-structure-decay-reactions-and-dose` (§0–§4), `nuclear-fuel-cycle-waste-and-safety` (§8–§9), `nuclear-fusion-confinement-and-detection` (§10–§14), `nuclear-reference` (§15–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Nuclear physics is settled — Rutherford 1911, Chadwick 1932, Hahn-Meitner-Frisch 1938, Lawson 1957, Bethe. Fusion milestones and the fission build picture moved. See §16 → `nuclear-reference` for both.

> **Scope.** ⚠️ **This covers nuclear physics and nuclear *energy* — reactor physics,
> fusion, radiation, and the fuel cycle.** **It does not cover weapon design, and §17 → `nuclear-reference`
> says why plainly.** The physics here is standard undergraduate and graduate curriculum
> material.
>
> **⚠️ GOTCHA** boxes mark misconceptions and places where intuition fails — and public
> understanding of this subject is unusually poor, so §15 → `nuclear-reference` is long.
>
> **The three ideas that organize everything:**
> 1. **⚠️ The binding energy curve explains fission and fusion in one picture.** Iron-56 is
>    the most tightly bound nucleus. **Anything heavier releases energy by splitting;
>    anything lighter releases energy by fusing.** Both run downhill toward iron (§1.2 → `nuclear-structure-decay-reactions-and-dose`).
> 2. **⚠️ Nuclear energy densities are about a million times chemical.** Same Coulomb
>    barrier scaling that makes them hard to initiate makes them enormous once initiated.
>    **Every practical consequence — fuel volumes, waste volumes, accident severity —
>    follows from that factor** (§18 → `nuclear-reference`).
> 3. **⚠️ Reactor safety is dominated by decay heat, not by the chain reaction.** You can
>    stop fission in under a second. **You cannot stop the ~7% residual heat from fission
>    products, and every major accident is a failure to remove it** (§9 → `nuclear-fuel-cycle-waste-and-safety`).

---

## §5. Fission Physics

**⚠️ Neutron absorption deforms the nucleus until Coulomb repulsion overcomes surface
tension** — the liquid-drop picture (§1.1 → `nuclear-structure-decay-reactions-and-dose`) — **and it splits.**
```
²³⁵U + n → two fragments + 2–3 neutrons + ~200 MeV
```
**⚠️ Energy partition matters for engineering:** ~**168 MeV** as fragment kinetic energy
(⚠️ **deposited within microns — this is what heats the fuel**), ~5 MeV prompt neutrons,
~7 MeV prompt gammas, and ~**20 MeV** delayed from fission-product decay (⚠️ **which is
decay heat, §9 → `nuclear-fuel-cycle-waste-and-safety`**), plus ~10 MeV carried away by antineutrinos and lost.

**⚠️ Fissile vs fertile — a distinction people conflate:**
- **Fissile** — fissions with **thermal** neutrons: **`²³⁵U`, `²³⁹Pu`, `²³³U`.**
- **Fertile** — captures a neutron and **transmutes into** a fissile nuclide:
  ⚠️ **`²³⁸U → ²³⁹Pu`, `²³²Th → ²³³U`.**
- ⚠️ **`²³⁸U` does fission with fast neutrons above ~1 MeV, contributing a few percent of
  power in a thermal reactor.** **"Non-fissile" does not mean inert.**

**Fission products** peak around `A ≈ 95` and `A ≈ 137` — ⚠️ **the double-humped yield
curve.** **Key ones**: `¹³⁵Xe` (⚠️ **the strongest neutron poison known, §6.4**), `¹⁴⁹Sm`,
`¹³¹I` (⚠️ **short-lived, thyroid-seeking — the reason for potassium iodide prophylaxis**),
`⁹⁰Sr` and `¹³⁷Cs` (⚠️ **~30 year half-lives — these dominate the medium-term hazard**).

---

## §6. Reactor Physics

### 6.1 Criticality
**⚠️ The multiplication factor `k` is the whole game:**
```
k = neutrons in one generation / neutrons in the previous
k < 1  subcritical      k = 1  ⚠️ CRITICAL — steady power      k > 1  supercritical
Reactivity ρ = (k−1)/k
```
**⚠️ "Critical" means steady-state operation.** **It is the normal, desired condition of a
running reactor** — and its everyday connotation of danger is precisely wrong (§15 → `nuclear-reference`).

**Six-factor formula** `k = η·f·p·ε·P_FNL·P_TNL` — reproduction factor, thermal
utilization, resonance escape probability, fast fission factor, and the two non-leakage
probabilities. ⚠️ **Leakage is why geometry and size matter, and why there is a critical
size for any given composition.**

### 6.2 Moderation
**⚠️ Fast fission neutrons (~2 MeV) must be slowed to thermal (~0.025 eV) to exploit the
huge thermal cross section** (§3 → `nuclear-structure-decay-reactions-and-dose`).
**⚠️ Elastic scattering transfers most energy when masses match** — **hydrogen is ideal,
which is why water is the standard moderator.**
```
Light water   ⚠️ best moderation per collision, but absorbs neutrons → needs ENRICHED fuel
Heavy water   ⚠️ slightly worse moderation, very low absorption → runs on NATURAL uranium
Graphite      ⚠️ good, low absorption, large core
```
**⚠️ The resonance escape problem**: neutrons must pass *through* `²³⁸U`'s resonance region
without being captured, so **fast, efficient slowing-down is required** (§3 → `nuclear-structure-decay-reactions-and-dose`).

### 6.3 ⚠️ Delayed neutrons — why reactors are controllable at all
> **⚠️ GOTCHA — this is the single most important fact in reactor physics and it is
> almost never mentioned outside the field.**
> **About **0.65%** of fission neutrons from `²³⁵U` are emitted not promptly but seconds
> to minutes later, from decaying fission products.** ⚠️ **This tiny fraction stretches the
> mean neutron generation time from ~10⁻⁴ s to ~0.1 s — a factor of about a thousand.**
> **Without it, power would respond faster than any mechanical control system could act
> and reactors would be uncontrollable.**
>
> ⚠️ **"Prompt critical" means `ρ > β` — critical on prompt neutrons alone, without the
> delayed contribution.** **Power then rises on the microsecond timescale.** **This is the
> boundary that must never be crossed, and reactivity is measured in *dollars* where
> `$1 = β` precisely to make the margin legible.**

### 6.4 Reactivity feedback and control
**⚠️ Feedback coefficients determine whether a reactor is inherently stable:**
- **Fuel temperature (Doppler)** — ⚠️ **ALWAYS negative and ALWAYS prompt.** **Hotter
  `²³⁸U` has thermally broadened resonances, capturing more neutrons.** ⚠️ **This is the
  fastest-acting safety feature in a reactor and it is pure physics, requiring no
  action.**
- **Moderator temperature / void coefficient** — ⚠️ **negative in a light-water reactor:
  losing water loses moderation, so power falls.** ⚠️ **The RBMK design at Chernobyl had a
  *positive* void coefficient at low power, and that is the design root of the accident**
  (§9 → `nuclear-fuel-cycle-waste-and-safety`).
- **Xenon-135** — ⚠️ **the strongest neutron absorber known (~2.6 million barns).** **It
  builds up after shutdown and decays away over ~1–2 days — the "xenon pit," which can
  make a recently shut reactor impossible to restart for a day.** ⚠️ **Mismanaging xenon
  was a proximate factor at Chernobyl.**
- **Burnable poisons** (gadolinium, boron) to flatten reactivity over a fuel cycle;
  **control rods**; **soluble boron** in PWRs.

---

## §7. Reactor Types

| Type | Coolant / Moderator | ⚠️ Notes |
|---|---|---|
| **PWR** | Light water / light water | ⚠️ **~2/3 of the world fleet. Pressurized, separate steam loop** |
| **BWR** | Light water / light water | Boils in the core; simpler, turbine is active |
| **CANDU (PHWR)** | Heavy water | ⚠️ **Natural uranium, on-line refuelling** |
| **RBMK** | Light water / graphite | ⚠️ **Chernobyl design; positive void coefficient** |
| **AGR / Magnox** | CO₂ / graphite | UK |
| **VVER** | Light water | Russian PWR lineage |
| **Fast breeder (SFR)** | Sodium / ⚠️ **none** | ⚠️ **Breeds `²³⁹Pu`; sodium reacts violently with water and air** |
| **HTGR** | Helium / graphite | ⚠️ **TRISO fuel; high outlet temperature for process heat** |
| **MSR** | Molten salt fuel | ⚠️ **Liquid fuel; online processing; materials and chemistry are the hard part** |
| **SMR** | Various | §16.2 → `nuclear-reference` |

**⚠️ TRISO fuel is worth knowing**: **tiny fuel kernels in layered ceramic coatings that
retain fission products to very high temperature.** ⚠️ **It moves containment to the
particle level, which is a genuinely different safety architecture.**
