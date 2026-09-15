---
name: nuclear-fusion-confinement-and-detection
description: "Use when working on fusion or on measuring radiation: fusion physics including the Lawson criterion and triple product, magnetic confinement and the tokamak and stellarator approaches, inertial confinement, an honest account of why fusion is hard to engineer beyond achieving the reaction, and detection and measurement instrumentation."
---

# Nuclear Physics: Fusion Physics, Magnetic and Inertial Confinement, and Detection

> **Part 4 of 5** of the *Nuclear Physics* reference (plugin `nuclear-physics`), covering §10–§14. Sibling skills: `nuclear-structure-decay-reactions-and-dose` (§0–§4), `nuclear-fission-reactor-physics-and-reactor-types` (§5–§7), `nuclear-fuel-cycle-waste-and-safety` (§8–§9), `nuclear-reference` (§15–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §10. Fusion Physics

**⚠️ The Coulomb barrier is the whole problem.** Nuclei must approach to ~1 fm against
electrostatic repulsion. **Quantum tunnelling helps, but you still need ~10–15 keV
(~100–150 million K).**

**The candidate reactions:**
```
D + T → ⁴He (3.5 MeV) + n (14.1 MeV)     ⚠️ HIGHEST cross section at LOWEST temperature.
                                          The only near-term option — and 80% of the
                                          energy is in a neutron (§13)
D + D → two branches                      ⚠️ no tritium needed, much harder
D + ³He → ⁴He + p                         ⚠️ aneutronic-ish, but ³He is essentially
                                          unavailable and it needs far higher temperature
p + ¹¹B → 3 ⁴He                           ⚠️ truly aneutronic; enormous temperature
                                          and bremsstrahlung losses. Very hard
```
**⚠️ Why D-T despite the neutron problem**: its cross section peaks about 100× higher and
at roughly a quarter the temperature of the alternatives. **Everything else is a much
harder physics problem in exchange for an easier engineering one.**

**⚠️ Lawson criterion / triple product** — the condition for net energy:
```
n · T · τ_E  ≳ 3×10²¹ keV·s·m⁻³   (D-T ignition)
```
**Density × temperature × energy confinement time.** ⚠️ **The two confinement approaches
attack different factors: magnetic confinement uses low density and long `τ_E` (seconds);
inertial uses enormous density and vanishing `τ_E` (nanoseconds). Both must reach the same
product.**

**⚠️ `Q` definitions are a recurring source of confusion and inflated claims:**
- **`Q_scientific`** — fusion energy out / **energy delivered to the plasma or target.**
- **`Q_engineering`** — ⚠️ **electricity out / total electricity in, including the whole
  facility.** **This is the one that matters for a power plant.**
- **⚠️ Ignition** — the alpha particles alone sustain the burn.
**⚠️ NIF's reported gains are scientific `Q` against laser energy delivered to the target,
not against the wall-plug energy drawn by the laser system, which is far larger** (§16.1 → `nuclear-reference`).

---

## §11. Magnetic Confinement

**Charged particles spiral along field lines; a toroidal geometry closes them.**
**⚠️ A purely toroidal field doesn't confine — field curvature and gradient cause charge-
dependent drift and the plasma separates and is lost.** **You need a twist, i.e. a
poloidal component.**
- **Tokamak** — ⚠️ **poloidal field from a current driven in the plasma itself.**
  **Axisymmetric and best-understood; the current is a free energy source for
  disruptions.**
- **Stellarator** — ⚠️ **twist from external coils only.** **Intrinsically steady-state and
  disruption-free; the coil geometry is fiendishly complex and only became tractable with
  modern computation.**
- **Others**: spherical tokamak, reversed field pinch, mirrors, FRC.

**⚠️ The problems**: **disruptions** (⚠️ **sudden loss of confinement dumping enormous
energy onto the wall — the main risk in tokamaks**), **MHD instabilities**, **ELMs**,
**turbulent transport** (⚠️ **which sets `τ_E` and is why empirical scaling laws still
substitute for first-principles prediction**), **and the divertor heat load** (§13).

---

## §12. Inertial Confinement

**⚠️ Compress and heat a fuel capsule so fast that inertia confines it long enough to
burn** — nanoseconds.
**Direct drive** (lasers on the capsule) vs **indirect drive** (⚠️ **lasers heat a
high-Z hohlraum which re-radiates X-rays — more uniform, less efficient; this is NIF's
approach**).
**⚠️ The physics obstacles**: **Rayleigh-Taylor instability during compression** (⚠️ **the
dominant one — any surface imperfection grows catastrophically**), **required implosion
symmetry**, **laser-plasma instabilities**, and **capsule fabrication tolerances.**
**Repetition rate** is the gulf between ignition and a power plant: ⚠️ **NIF fires
occasionally; a plant would need several shots per second with a fresh target each time.**

---

## §13. Why Fusion Is Hard to Engineer

**⚠️ The physics of net gain is now demonstrated (§16.1 → `nuclear-reference`). These are the reasons that isn't
the same as a power plant.**

- **⚠️ Tritium.** **It has a 12.3-year half-life and does not occur naturally in useful
  quantities.** ⚠️ **A D-T plant must breed its own from lithium using its own neutrons,
  requiring a tritium breeding ratio above 1 — including losses.** **This has never been
  demonstrated in an integrated system, and it is arguably the single largest unproven
  requirement.**
- **⚠️ 14 MeV neutrons.** **80% of D-T energy is in neutrons that damage structural
  materials, causing displacement damage and helium embrittlement, and activating the
  structure.** ⚠️ **No material has been qualified for a full plant lifetime at fusion
  neutron fluence, and there is no operating high-flux 14 MeV test facility — which is
  why IFMIF/DONES matters.**
- **⚠️ Divertor heat flux.** **Steady-state loads approaching 10 MW/m² — comparable to a
  rocket nozzle, sustained for years.**
- **Magnets** — ⚠️ **HTS (REBCO) tape is the enabling change: higher field allows a much
  smaller device, since fusion power scales roughly as `B⁴`.**
- **⚠️ Economics.** **A fusion plant is a large capital-intensive thermal plant with an
  expensive, complex core.** ⚠️ **"Fuel is free" is not the cost driver; capital cost is.**
- **⚠️ Fusion is not radiologically clean, though it is much better than fission**:
  **no long-lived actinides and no chain reaction to run away, but activated structure
  and a tritium inventory are real.** **Low-activation steels are designed to make the
  waste decay to hands-on levels in ~100 years rather than 100,000.**

---

## §14. Detection and Measurement

**Gas detectors** — ionization chamber, proportional counter, Geiger-Müller (⚠️ **counts
events but gives no energy information — which is why a Geiger reading alone cannot tell
you the isotope or the dose properly**).
**Scintillators** — NaI(Tl), plastic, liquid; **fast, good efficiency, moderate energy
resolution.**
**Semiconductors** — ⚠️ **HPGe gives excellent energy resolution and is the standard for
gamma spectroscopy and isotope identification**; Si for charged particles; CZT at room
temperature.
**Neutron detection** — ⚠️ **neutrons are uncharged, so you detect them via a nuclear
reaction: `³He`, BF₃, `⁶Li`, or recoil protons.**
**Dosimetry** — TLD, OSL, film, electronic personal dosimeters.
**⚠️ Reactor instrumentation**: source-range, intermediate-range and power-range neutron
detectors spanning many decades, plus self-powered in-core detectors.
