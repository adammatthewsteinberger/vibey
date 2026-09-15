---
name: semi-pcb-assembly-reliability-design-flow-and-economics
description: "Use for the board level and the business around it: PCB fabrication, assembly and soldering including reflow profiles and defect modes, reliability and the failure mechanisms with their acceleration models, the chip design flow from RTL to GDSII, the economics of mask sets, wafer cost and volume, and the supply chain concentration that makes the industry strategically fragile."
---

# Semiconductors and Chip Manufacturing: PCB Fabrication, Assembly and Soldering, Reliability, Design Flow, Economics, and Supply Chain and Concentration

> **Part 5 of 6** of the *Semiconductors and Chip Manufacturing* reference (plugin `semiconductors-and-chip-manufacturing`), covering §21–§26. Sibling skills: `semi-carriers-doping-junctions-mosfet-and-scaling` (§0–§5), `semi-transistor-architectures-interconnect-memory-and-wafers` (§6–§9), `semi-cleanroom-lithography-deposition-etch-and-cmp` (§10–§15), `semi-integration-yield-metrology-test-and-packaging` (§16–§20), `semi-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §21. PCB Fabrication

**⚠️ The other half of "chip and motherboard," and it is a genuinely different industry.**
```
⚠️ THE STACK-UP  copper foil, ⚠️ PREPREG (resin-impregnated glass
   cloth) and cores, laminated under heat and pressure.
   ⚠️ FR-4 is the workhorse; ⚠️ high-speed designs need low-loss
   materials (Megtron, Rogers) because FR-4's loss tangent
   destroys multi-GHz signals
⚠️ THE FLOW  inner layers imaged and etched → lamination →
   ⚠️ DRILLING (mechanical, and LASER for microvias) → desmear →
   ⚠️ ELECTROLESS COPPER to make the hole walls conductive →
   electroplating → outer layer image and etch → solder mask →
   surface finish (ENIG, OSP, HASL) → profiling → electrical test
⚠️ HDI  ⚠️ microvias, blind and buried vias, sequential lamination —
   ⚠️ needed once BGA pitch drops below what through-holes can escape
⚠️ THE DESIGN CONSTRAINTS THAT BITE  ⚠️ CONTROLLED IMPEDANCE (see an
   electromagnetism reference — trace geometry and dielectric set
   Z₀) · ⚠️ RETURN PATH CONTINUITY · via stubs and backdrilling ·
   ⚠️ layer count vs cost · aspect ratio limits on drilling
⚠️ IPC standards govern classes, acceptability and design
```
**⚠️ The substrate for a chip package is a PCB-like product built to far finer rules** —
⚠️ **and ABF substrate capacity has been a real constraint on advanced packaging** (§20 → `semi-integration-yield-metrology-test-and-packaging`).

---

## §22. Assembly and Soldering

**⚠️ SMT reflow**: ⚠️ **solder paste stencil printed → components placed by pick-and-place →
reflow oven with a controlled thermal profile (preheat, soak, reflow above liquidus, cool)
→ inspection.**
**⚠️ The profile is the process** — ⚠️ **too hot damages components, too cool gives cold
joints, and ramp rates control voiding and tombstoning.**
**⚠️ Lead-free (RoHS) changed everything**: ⚠️ **SAC alloys melt higher, wet less well, and
made process windows narrower.** ⚠️ **TIN WHISKERS — spontaneous single-crystal growths from
pure tin finishes that can short adjacent conductors — are a real reliability concern in
high-consequence applications, which is why some sectors retain leaded solder exemptions.**
**⚠️ Inspection**: ⚠️ **AOI for visible joints, and X-RAY for BGAs and QFNs where the joints
are underneath and cannot be seen at all.**
**⚠️ Wave and selective soldering** for through-hole; **rework and conformal coating.**

---

## §23. Reliability

```
⚠️ THE BATHTUB CURVE  ⚠️ infant mortality (screened by burn-in,
   §19) → low constant random failure → ⚠️ WEAR-OUT
⚠️ THE INTRINSIC WEAR-OUT MECHANISMS
   ⚠️ ELECTROMIGRATION  metal atoms moved by current (§7)
   ⚠️ TDDB  time-dependent dielectric breakdown — the gate oxide
      fails after cumulative stress
   ⚠️ NBTI/PBTI  threshold voltage drifts over operating life
   ⚠️ HOT CARRIER INJECTION  energetic carriers damage the oxide
   ⚠️ These are why chips have a rated LIFETIME at a rated
   temperature and voltage — ⚠️ and why overclocking and running
   hot genuinely shorten it
⚠️ PACKAGE and BOARD  ⚠️ solder fatigue from CTE mismatch under
   thermal cycling (⚠️ the dominant board-level failure) ·
   delamination · popcorning of moisture-absorbed packages during
   reflow (hence moisture sensitivity levels and baking)
⚠️ ESD and latch-up  ⚠️ on-chip protection structures exist for this
⚠️ SOFT ERRORS  ⚠️ alpha particles and cosmic-ray neutrons flip
   memory bits. ⚠️ Not a defect — a physical inevitability, which
   is why ECC exists and why it matters at scale
⚠️ ARRHENIUS  ⚠️ reaction rates roughly double per 10 °C. Thermal
   management IS reliability engineering
```

---

## §24. Design Flow

**⚠️ Specification → RTL (Verilog/VHDL) → ⚠️ VERIFICATION (⚠️ typically the largest single
effort, and formal methods plus constrained-random simulation plus emulation) → logic
synthesis → floorplanning → place and route → clock tree synthesis → timing closure →
physical verification (DRC, LVS) → sign-off → tapeout.**
**⚠️ EDA is an effective oligopoly** — ⚠️ **Synopsys, Cadence and Siemens EDA — and the
tools are as much a chokepoint as the fab equipment** (§26).
**⚠️ IP reuse dominates**: ⚠️ **almost no one designs their own standard cells, memory
compilers, PHYs or CPU cores from scratch; Arm and RISC-V are the ISA options, and PDKs
come from the foundry.**
**⚠️ Timing closure and signoff** are where schedules die — ⚠️ **and the abstraction leaks
of §1 → `semi-carriers-doping-junctions-mosfet-and-scaling` all show up here as setup/hold violations, IR drop, crosstalk and thermal
hotspots.**

---

## §25. ⚠️ Economics

```
⚠️ FAB COST  ⚠️ a leading-edge fab is a ~$20bn-plus capital project
   ⚠️ EUV scanners alone run to hundreds of millions each (§27.1),
   and a fab needs many
⚠️ ⚠️ THEREFORE UTILIZATION IS EVERYTHING. Depreciation dominates
   cost, so a fab must run flat out. ⚠️ This drives the industry's
   violent boom-bust cycle: capacity is added in indivisible
   multi-year lumps against demand that moves faster
⚠️ MASK SET  millions of dollars at the leading edge (§16) —
   ⚠️ which sets a minimum viable volume and pushes low-volume
   designs to mature nodes
⚠️ THE BUSINESS MODELS
   ⚠️ IDM (design and manufacture — Intel, Samsung, memory makers)
   ⚠️ FABLESS + FOUNDRY (⚠️ the dominant model; TSMC's creation of
      the pure-play foundry enabled the entire fabless industry)
   ⚠️ OSAT for packaging and test
⚠️ MATURE NODES ARE A GOOD BUSINESS  ⚠️ fully depreciated, high
   volume, and where most chips by UNIT actually come from —
   automotive, power, analog, microcontrollers
⚠️ ⚠️ COST PER TRANSISTOR HAS STOPPED FALLING at the leading edge
   (§5), which changes the whole logic of when to migrate a design
```

---

## §26. Supply Chain and Concentration

**⚠️ The most concentrated critical supply chain in the modern economy, with several
genuine single points of failure.**
```
⚠️ EUV lithography  ⚠️ ASML ONLY. Optics: ⚠️ ZEISS ONLY (§11)
⚠️ Leading-edge foundry  ⚠️ effectively TSMC, with Samsung and
   Intel as the other two attempting it
⚠️ EDA  three firms (§24)
⚠️ IP  Arm's position in instruction sets
⚠️ HBM  three suppliers (§8, §27.2)
⚠️ ABF substrate, photoresist, specialty gases, silicon wafers —
   ⚠️ each concentrated in a handful of firms, several Japanese
⚠️ MATERIALS  ⚠️ and see a resource-extraction reference: gallium,
   germanium and rare earths are subject to export controls, and
   neon for excimer lasers was disrupted by war
⚠️ GEOGRAPHIC CONCENTRATION  ⚠️ the leading edge is overwhelmingly
   in Taiwan and South Korea. ⚠️ CHIPS-style subsidy programmes in
   the US, EU, Japan, India and China are all attempts to change
   this, at enormous cost and over a decade-plus timescale
⚠️ EXPORT CONTROLS  ⚠️ restrictions on advanced tools and chips to
   China are now a structural feature, driving parallel domestic
   ecosystems
```
