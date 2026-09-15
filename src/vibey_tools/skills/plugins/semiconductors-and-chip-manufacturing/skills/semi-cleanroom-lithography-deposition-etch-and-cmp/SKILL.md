---
name: semi-cleanroom-lithography-deposition-etch-and-cmp
description: "Use for the unit processes in the fab: the cleanroom and contamination control, lithography including immersion, EUV, resolution limits and multiple patterning, deposition across CVD, ALD and PVD, etch and the selectivity and profile control problems, implant and anneal, and chemical mechanical planarization."
---

# Semiconductors and Chip Manufacturing: The Cleanroom, Lithography, Deposition, Etch, Implant and Anneal, and CMP

> **Part 3 of 6** of the *Semiconductors and Chip Manufacturing* reference (plugin `semiconductors-and-chip-manufacturing`), covering §10–§15. Sibling skills: `semi-carriers-doping-junctions-mosfet-and-scaling` (§0–§5), `semi-transistor-architectures-interconnect-memory-and-wafers` (§6–§9), `semi-integration-yield-metrology-test-and-packaging` (§16–§20), `semi-pcb-assembly-reliability-design-flow-and-economics` (§21–§26), `semi-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics is settled. Two frontiers are moving. See §27 → `semi-reference` for High-NA lithography adoption, and advanced packaging as the binding constraint.

> **⚠️ The most complex manufacturing humans do, by a wide margin.** ⚠️ **A leading-edge
> chip involves on the order of a thousand process steps, features smaller than a virus,
> tolerances measured in atoms, and a supply chain with genuine single points of failure.**
>
> **Builds directly on an electromagnetism reference (band theory, pn junctions, MOSFET
> physics, wide-bandgap materials). Complements a manufacturing reference (tolerancing and
> yield), an organic-chemistry reference (photoresists and packaging polymers), and a
> resource-extraction reference (where the materials come from).**
>
> **⚠️ GOTCHA** boxes mark where marketing and physics diverge — and this industry has more
> of that gap than most.
>
> **The three ideas that organize this document:**
> 1. **⚠️ "NODE NAMES ARE MARKETING"** (§5 → `semi-carriers-doping-junctions-mosfet-and-scaling`). **"3nm" does not describe any physical
>    dimension on the chip. It has been a marketing label for roughly a decade, and
>    comparing nodes across foundries by name is meaningless.**
> 2. **⚠️ YIELD IS THE WHOLE BUSINESS** (§17 → `semi-integration-yield-metrology-test-and-packaging`). **Everything — die size, chiplet
>    architecture, defect control, cleanroom spend — is downstream of the fact that
>    profitability is set by what fraction of die work.**
> 3. **⚠️ THE BOTTLENECK MOVED TO THE BACK END** (§20 → `semi-integration-yield-metrology-test-and-packaging`, §27.2 → `semi-reference`). **For AI accelerators the
>    binding constraint is no longer transistors — it is packaging and memory, which is a
>    genuine reversal of thirty years of industry structure.**

---

## §10. The Cleanroom

**⚠️ A single particle larger than a fraction of the feature size, landing in the wrong
place, kills a die.**
**⚠️ ISO 14644 classes** — ⚠️ **leading-edge fab bays run at the cleanest practical
classes, with HEPA/ULPA filtration, laminar downflow, and positive pressure.**
**⚠️ People are the dominant particle source**, ⚠️ **hence bunny suits, air showers and
increasing automation — modern fabs move wafers in sealed FOUPs by overhead transport, and
humans rarely touch them.**
**⚠️ Beyond particles**: ⚠️ **airborne molecular contamination, ionic contamination,
temperature and humidity control to fractions of a degree, vibration isolation (⚠️
lithography tools sit on massive isolated foundations), and ultrapure water and process
gases delivered on site.**
**⚠️ Ultrapure water consumption is genuinely large** and is now a siting constraint in
water-stressed regions (see a resource-extraction reference on water).

---

## §11. ⚠️ Lithography

> **⚠️ The crown jewel and the industry's tightest chokepoint. Everything else in the fab
> exists to support what lithography defines.**
```
⚠️ THE BASIC CYCLE  coat photoresist → EXPOSE through a mask →
   develop → etch or implant → strip. ⚠️ Repeated dozens of times,
   with each layer aligned to the last within nanometres (OVERLAY)
⚠️ RESOLUTION  ⚠️ Rayleigh: CD = k₁ · λ/NA. ⚠️ You improve
   resolution by shortening WAVELENGTH, raising NUMERICAL APERTURE,
   or reducing k₁ through process tricks
⚠️ THE WAVELENGTH LADDER  436nm → 365nm → 248nm (KrF) →
   ⚠️ 193nm (ArF) → 193nm IMMERSION (water raises effective NA)
   → ⚠️ 13.5nm EUV
⚠️ ⚠️ 193nm IMMERSION PRINTED FEATURES FAR BELOW 193nm for years
   via MULTIPLE PATTERNING — ⚠️ splitting one layer across two,
   three or four masks and exposures. ⚠️ Each additional pattern
   adds masks, alignment error budget, etch steps and cost
⚠️ EUV  ⚠️ 13.5nm, and it required inventing an entire ecosystem:
   ⚠️ tin droplets vaporized by a high-power laser to make plasma ·
   ⚠️ ALL-REFLECTIVE optics (everything absorbs EUV, including air —
   so the whole beam path is in VACUUM) · ⚠️ multilayer Bragg
   mirrors, each losing energy · ⚠️ reflective masks with pellicle
   difficulties
⚠️ RESOLUTION ENHANCEMENT  ⚠️ OPC (deliberately distorting the mask
   so the printed result is correct), phase-shift masks, source-mask
   optimization, inverse lithography
⚠️ STOCHASTICS  ⚠️ at EUV doses, PHOTON SHOT NOISE becomes a real
   defect mechanism — you are counting individual photons and
   random variation causes random failures
```
**⚠️ ASML is the sole supplier of EUV**, ⚠️ **with Zeiss the sole supplier of the optics —
which is the single most concentrated dependency in the modern economy** (§26 → `semi-pcb-assembly-reliability-design-flow-and-economics`, §27.1 → `semi-reference`).

---

## §12. Deposition

**⚠️ Adding material, atom layers at a time.**
```
⚠️ CVD  chemical vapour deposition — precursor gases react on the
   surface. ⚠️ PECVD lowers the temperature using plasma
⚠️ ⚠️ ALD  atomic layer deposition — ⚠️ SELF-LIMITING surface
   reactions deposit ONE ATOMIC LAYER PER CYCLE. ⚠️ Slow, and the
   only way to get perfectly conformal films in high-aspect-ratio
   structures. ⚠️ ALD made high-k gate dielectrics and 3D
   architectures possible
⚠️ PVD / sputtering  physical, line-of-sight, metals
⚠️ EPITAXY  growing single-crystal material aligned to the substrate
⚠️ ELECTROPLATING  ⚠️ how copper interconnect is actually filled,
   with additives engineered for bottom-up "superfill"
⚠️ THERMAL OXIDATION  ⚠️ growing SiO₂ from the silicon itself —
   consumes substrate, gives an outstanding interface
```
**⚠️ The universal requirements**: ⚠️ **thickness uniformity across the wafer, conformality
over topography, film stress (⚠️ which warps wafers and cracks films), and purity.**

---

## §13. Etch

**⚠️ Removing material where the resist doesn't protect it.**
⚠️ **WET etching is isotropic (etches sideways as fast as down) and largely displaced for
fine features; ⚠️ DRY/PLASMA etching gives ANISOTROPY — vertical sidewalls — which is what
lets you etch a narrow deep feature at all.**
**⚠️ The tuning variables**: ⚠️ **SELECTIVITY (etch the target much faster than the mask and
the underlying stop layer), profile control, aspect ratio dependent etching (⚠️ deep narrow
features etch slower — RIE lag), and endpoint detection.**
**⚠️ Deep RIE and the Bosch process** — ⚠️ **alternating etch and passivation steps to get
extremely high aspect ratios, essential for TSVs (§20 → `semi-integration-yield-metrology-test-and-packaging`) and 3D NAND.**
**⚠️ ATOMIC LAYER ETCHING** is the counterpart to ALD — ⚠️ **self-limiting removal, one
layer at a time, for the tightest tolerances.**
**⚠️ Copper is not plasma-etched** (§7 → `semi-transistor-architectures-interconnect-memory-and-wafers`) — ⚠️ **hence the DAMASCENE flow: etch the trench
into dielectric, fill with copper, then planarize** (§15).

---

## §14. Implant and Anneal

**⚠️ ION IMPLANTATION** fires dopant ions at the wafer at controlled energy and dose —
⚠️ **energy sets depth, dose sets concentration, and it is precise and repeatable in a way
diffusion never was.**
**⚠️ It damages the crystal**, ⚠️ **so ANNEALING is required to repair the lattice and
ACTIVATE the dopants by moving them onto lattice sites.**
> **⚠️ GOTCHA — the THERMAL BUDGET conflict is a defining constraint of modern process
> integration.** ⚠️ **You need heat to activate dopants and repair damage; heat also makes
> dopants DIFFUSE, blurring the shallow junctions you carefully created.**
> **⚠️ The response is ever-shorter anneals — rapid thermal, then spike, then flash, then
> laser anneal on millisecond and shorter timescales — heating the surface without letting
> the dopants move.**

---

## §15. CMP

**⚠️ Chemical-mechanical planarization** — ⚠️ **polishing the wafer flat with a slurry that
is simultaneously abrasive and chemically active.**
**⚠️ Why it is essential**: ⚠️ **lithography's depth of focus at high NA is tiny (§11), so
the surface must be almost perfectly flat before each exposure.** ⚠️ **Multi-level
interconnect is impossible without it, and CMP's invention is what allowed stacking many
metal layers.**
**⚠️ It is also the enabler of DAMASCENE copper** (§13) and of ⚠️ **wafer bonding for 3D
integration** (§20 → `semi-integration-yield-metrology-test-and-packaging`).
**⚠️ The problems it creates**: ⚠️ **DISHING and EROSION in wide or dense features, which is
why layout DENSITY RULES and dummy fill exist — designers must add meaningless metal
shapes purely to make polishing uniform.**
