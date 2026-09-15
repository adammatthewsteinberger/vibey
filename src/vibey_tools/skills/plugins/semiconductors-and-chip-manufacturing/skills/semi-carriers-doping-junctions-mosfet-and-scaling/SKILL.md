---
name: semi-carriers-doping-junctions-mosfet-and-scaling
description: "Use for the device physics underneath everything else: the abstraction stack from atoms to systems, carriers, doping and why silicon won, junctions and contacts, the MOSFET and its operating regions, and scaling — what Moore's law and Dennard scaling each actually claimed, and precisely which one ended. Includes the router for the whole semiconductor reference."
---

# Semiconductors and Chip Manufacturing: The Abstraction Stack, Carriers, Doping and Silicon, Junctions and Contacts, the MOSFET, and Scaling and What Ended

> **Part 1 of 6** of the *Semiconductors and Chip Manufacturing* reference (plugin `semiconductors-and-chip-manufacturing`), covering §0–§5. Sibling skills: `semi-transistor-architectures-interconnect-memory-and-wafers` (§6–§9), `semi-cleanroom-lithography-deposition-etch-and-cmp` (§10–§15), `semi-integration-yield-metrology-test-and-packaging` (§16–§20), `semi-pcb-assembly-reliability-design-flow-and-economics` (§21–§26), `semi-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ "NODE NAMES ARE MARKETING"** (§5). **"3nm" does not describe any physical
>    dimension on the chip. It has been a marketing label for roughly a decade, and
>    comparing nodes across foundries by name is meaningless.**
> 2. **⚠️ YIELD IS THE WHOLE BUSINESS** (§17 → `semi-integration-yield-metrology-test-and-packaging`). **Everything — die size, chiplet
>    architecture, defect control, cleanroom spend — is downstream of the fact that
>    profitability is set by what fraction of die work.**
> 3. **⚠️ THE BOTTLENECK MOVED TO THE BACK END** (§20 → `semi-integration-yield-metrology-test-and-packaging`, §27.2 → `semi-reference`). **For AI accelerators the
>    binding constraint is no longer transistors — it is packaging and memory, which is a
>    genuine reversal of thirty years of industry structure.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| The abstraction stack | §1 |
| Carriers and doping | §2 |
| Junctions | §3 |
| **MOSFET operation** | **§4** |
| **⚠️ Scaling and node names** | **§5** |
| Transistor architectures | §6 → `semi-transistor-architectures-interconnect-memory-and-wafers` |
| Interconnect | §7 → `semi-transistor-architectures-interconnect-memory-and-wafers` |
| Memory | §8 → `semi-transistor-architectures-interconnect-memory-and-wafers` |
| Wafers | §9 → `semi-transistor-architectures-interconnect-memory-and-wafers` |
| Cleanrooms | §10 → `semi-cleanroom-lithography-deposition-etch-and-cmp` |
| **⚠️ Lithography** | **§11 → `semi-cleanroom-lithography-deposition-etch-and-cmp`** |
| Deposition | §12 → `semi-cleanroom-lithography-deposition-etch-and-cmp` |
| Etch | §13 → `semi-cleanroom-lithography-deposition-etch-and-cmp` |
| Implant and anneal | §14 → `semi-cleanroom-lithography-deposition-etch-and-cmp` |
| CMP | §15 → `semi-cleanroom-lithography-deposition-etch-and-cmp` |
| Process integration | §16 → `semi-integration-yield-metrology-test-and-packaging` |
| **⚠️ Yield** | **§17 → `semi-integration-yield-metrology-test-and-packaging`** |
| Metrology | §18 → `semi-integration-yield-metrology-test-and-packaging` |
| Test | §19 → `semi-integration-yield-metrology-test-and-packaging` |
| **⚠️ Advanced packaging** | **§20 → `semi-integration-yield-metrology-test-and-packaging`** |
| PCB fabrication | §21 → `semi-pcb-assembly-reliability-design-flow-and-economics` |
| Assembly and soldering | §22 → `semi-pcb-assembly-reliability-design-flow-and-economics` |
| Reliability | §23 → `semi-pcb-assembly-reliability-design-flow-and-economics` |
| Design flow | §24 → `semi-pcb-assembly-reliability-design-flow-and-economics` |
| **⚠️ Economics** | **§25 → `semi-pcb-assembly-reliability-design-flow-and-economics`** |
| Supply chain | §26 → `semi-pcb-assembly-reliability-design-flow-and-economics` |
| **What's live** | **§27 → `semi-reference`** |
| Misconceptions, numbers | §28–§29 → `semi-reference` |
| Sources, quick ref, method | §30–§32 → `semi-reference` |

---

## §1. The Abstraction Stack

```
⚠️ Application → OS → ISA → microarchitecture → RTL → logic gates →
   ⚠️ STANDARD CELLS → transistors → ⚠️ DEVICE PHYSICS → materials
⚠️ EVERY LAYER IS A LEAKY ABSTRACTION AND THE LEAKS ARE THE
   INTERESTING PART — timing, power, thermals, variability and
   reliability all propagate upward from physics
⚠️ THE PARALLEL SUPPLY CHAIN
   design (fabless) → IP and EDA → mask making → ⚠️ FAB →
   ⚠️ TEST → ⚠️ PACKAGING (OSAT) → board assembly → system
⚠️ Each of these is a distinct industry with distinct economics,
   and ⚠️ several have effective monopolies (§26)
```
**⚠️ The scale that makes it hard**: ⚠️ **a modern fab prints features far smaller than the
wavelength of the light used to print them (§11 → `semi-cleanroom-lithography-deposition-etch-and-cmp`), across 300 mm wafers, with defect
densities low enough that a die with billions of transistors works at all.**

---

# PART I — DEVICE PHYSICS

## §2. Carriers, Doping and Silicon

**⚠️ See an electromagnetism reference for band theory. The chip-relevant points:**
⚠️ **silicon's ~1.1 eV bandgap gives usable carrier concentrations at room temperature and
manageable leakage; ⚠️ its native oxide SiO₂ is an outstanding insulator that grows
thermally and is the historical reason silicon beat germanium; and ⚠️ it is abundant and
purifiable to extraordinary levels** (§9 → `semi-transistor-architectures-interconnect-memory-and-wafers`).
**⚠️ Doping** with donors (P, As) or acceptors (B) sets carrier type and concentration over
many orders of magnitude — ⚠️ **and the ability to place dopants precisely, in three
dimensions, is what makes integrated circuits possible.**
**⚠️ Compound semiconductors** (GaAs, GaN, SiC, InP) ⚠️ **beat silicon on specific axes —
electron mobility, breakdown field, direct bandgap for light emission — and lose on cost,
wafer size and the absence of a good native oxide.**

---

## §3. Junctions and Contacts

**⚠️ The pn junction** (see an electromagnetism reference) — ⚠️ **depletion region,
built-in potential, rectification.**
**⚠️ In a modern chip the junction's roles are mostly parasitic and isolating** — ⚠️ **the
source/drain junctions must NOT leak, and reverse-biased junctions provide device
isolation.**
**⚠️ METAL-SEMICONDUCTOR CONTACTS** are an underappreciated problem: ⚠️ **you want OHMIC
(low resistance, linear) contacts to source and drain, and Schottky barriers form
naturally.** ⚠️ **Heavy doping at the contact makes the barrier thin enough to tunnel
through.** **⚠️ As devices shrink, CONTACT RESISTANCE becomes a dominant limit — silicides
and careful interface engineering exist entirely to fight it.**

---

## §4. The MOSFET

```
⚠️ THE STRUCTURE  source, drain, channel, gate separated by a
   thin gate DIELECTRIC
⚠️ OPERATION  gate voltage creates a field that INVERTS the channel
   surface, forming a conducting path. ⚠️ It is a voltage-controlled
   switch with essentially no DC gate current — which is why CMOS
   scales and bipolar didn't
⚠️ CMOS  complementary n and p devices. ⚠️ Static power is
   near zero because one device is always off — ⚠️ this property
   is why CMOS won, and why leakage breaking it (§5) was such a
   crisis
⚠️ THE KEY PARAMETERS
   ⚠️ THRESHOLD VOLTAGE Vt · drive current Ion · ⚠️ LEAKAGE Ioff ·
   ⚠️ SUBTHRESHOLD SWING — ⚠️ how many millivolts of gate voltage
   are needed per decade of current change. ⚠️ IT HAS A HARD
   PHYSICAL FLOOR OF ABOUT 60 mV/decade AT ROOM TEMPERATURE,
   set by Boltzmann statistics. ⚠️ THIS FLOOR IS WHY SUPPLY
   VOLTAGE STOPPED SCALING (§5)
⚠️ SHORT CHANNEL EFFECTS  ⚠️ as the channel shortens, the drain
   starts competing with the gate for control — DIBL, punchthrough,
   Vt roll-off. ⚠️ Fighting this is what drove FinFET and GAA (§6)
```

---

## §5. ⚠️ Scaling, and What Ended

> **⚠️ The most misunderstood story in technology, and getting it right explains almost
> everything about the modern industry.**
```
⚠️ DENNARD SCALING (the real engine)  ⚠️ shrink dimensions AND
   voltage together, and power density stays CONSTANT while
   speed rises and cost per transistor falls.
   ⚠️ THIS IS WHAT DELIVERED "free" performance for decades
⚠️ ⚠️ DENNARD SCALING ENDED AROUND THE MID-2000s
   ⚠️ WHY: voltage could not keep falling, because Vt could not
   fall without leakage exploding — and it couldn't, because of
   the 60 mV/decade subthreshold floor (§4)
   ⚠️ CONSEQUENCE: power density rose. ⚠️ The response was
   MULTICORE — not because parallel was better, but because
   frequency scaling had stopped
⚠️ ⚠️ DARK SILICON  the fraction of a chip that cannot be powered
   simultaneously within the thermal budget. ⚠️ This is why modern
   chips are full of specialized accelerators used intermittently
⚠️ MOORE'S LAW  ⚠️ an ECONOMIC observation about transistors per
   chip at minimum cost, not a law of physics. ⚠️ Transistor
   density still increases; ⚠️ COST PER TRANSISTOR has largely
   stopped falling at the leading edge, which is the more
   important change
```
> **⚠️ GOTCHA — "3nm" IS A MARKETING NAME.** ⚠️ **Since roughly the 22nm generation, node
> names have not corresponded to any physical feature on the chip — not gate length, not
> half-pitch, not fin width.** **⚠️ Different foundries' same-numbered nodes have materially
> different densities and characteristics.**
> ⚠️ **The meaningful metrics are TRANSISTOR DENSITY (MTr/mm²), SRAM bitcell area, and
> power-performance-area at a given design.** **⚠️ Compare those, never the name.**
