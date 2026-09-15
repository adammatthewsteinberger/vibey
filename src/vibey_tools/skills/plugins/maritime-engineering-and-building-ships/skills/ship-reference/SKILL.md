---
name: ship-reference
description: "Use when correcting a maritime misconception, looking up a stability, resistance, power, deadweight or fuel-consumption figure, finding the books and sources, or needing a quick-reference picker — plus the current state of IMO carbon regulation and the alternative fuel orderbook. Companion to the other maritime engineering skills."
---

# Maritime Engineering: What's Live, Misconceptions, Numbers, and Books

> **Part 6 of 6** of the *Maritime Engineering and Building Ships* reference (plugin `maritime-engineering-and-building-ships`), covering §24–§29. Sibling skills: `ship-design-spiral-hydrostatics-stability-and-hull-form` (§0–§4), `ship-resistance-propulsion-seakeeping-and-manoeuvring` (§5–§8), `ship-structure-materials-machinery-systems-and-types` (§9–§13), `ship-shipyard-build-welding-launch-and-naval-vessels` (§14–§18), `ship-class-flag-imo-safety-operations-and-losses` (§19–§23). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The naval architecture is settled. Two areas are in flux. See §24 for IMO carbon regulation, and the alternative fuel orderbook.

> **⚠️ A ship is the only major engineered structure that must simultaneously float, stay
> upright, move efficiently, survive an environment that actively tries to destroy it, and
> do all of it while UNATTENDED BY ANY RESCUE for days at a time.**
>
> **Complements a rail reference (guided transport), an automobiles reference (propulsion
> and diagnosis), a manufacturing reference (fabrication and tolerancing), and a
> thermodynamics reference (resistance and powering physics).**
>
> **⚠️ GOTCHA** boxes mark the intuitions that sink things.
>
> **The three ideas that organize this document:**
> 1. **⚠️ STABILITY IS NOT BUOYANCY** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`). **Whether a ship floats and whether it floats
>    UPRIGHT are separate calculations, and the second is what kills people. Free surface
>    effect in particular destroys stability without changing weight at all.**
> 2. **⚠️ The design spiral exists because nothing can be fixed independently** (§1 → `ship-design-spiral-hydrostatics-stability-and-hull-form`).
>    **Change the hull to reduce resistance and you change displacement, stability,
>    structure, cost and capacity. There is no linear path through a ship design.**
> 3. **⚠️ Class and flag are the mechanism** (§19 → `ship-class-flag-imo-safety-operations-and-losses`). **A ship's design, construction and
>    entire life are governed by a private-society-plus-treaty system with no direct
>    analogue in most other engineering — and understanding it explains almost everything
>    about how ships get built the way they do.**

---

## §24. What's Live — checked August 2026

> **⚠️ Both items below are genuinely unresolved as of writing, and the second is a direct
> consequence of the first. Verify current status — this is moving.**

### 24.1 ⚠️ IMO carbon regulation: agreed, then not adopted, and still pending
**⚠️ The single biggest open question in ship design right now, because §1 → `ship-design-spiral-hydrostatics-stability-and-hull-form` says a ship is a
20–30 year asset and nobody knows what it will be regulated under.**

- **⚠️ What the Net-Zero Framework IS**: ⚠️ **a proposed new Chapter 5 of MARPOL Annex VI,
  approved in principle at MEPC 83 in April 2025.** ⚠️ **Two instruments: a GLOBAL FUEL
  STANDARD requiring ships to reduce annual greenhouse gas fuel intensity (GFI) on a
  WELL-TO-WAKE basis, plus a PRICING AND REWARD MECHANISM under which ships exceeding
  their GFI buy remedial units and those using zero or near-zero technologies are
  rewarded.** ⚠️ **It would be the first global emissions pricing mechanism for any
  sector.**
- **⚠️ THE OCTOBER 2025 FAILURE**: ⚠️ **the second extraordinary session of MEPC met in
  London 14–17 October 2025 to adopt it, and instead voted to adjourn for one year.**
  ⚠️ **The motion passed 57 in favour of adjourning to 49 against, with 21 abstentions
  and eight delegations absent.** ⚠️ **Reporting attributes the outcome to concerted
  pressure from the United States, with Saudi Arabia moving the adjournment; Carbon Brief
  reports US negotiators were accused of "bully-boy tactics."**
- **⚠️ WHERE IT STANDS NOW**: ⚠️ **MEPC 84 met 27 April–1 May 2026 and the framework
  survived.** ⚠️ **Adoption is now scheduled for early December 2026 — at MEPC 85, which
  immediately precedes a RESUMED Extraordinary Session 2, with intersessional meetings in
  September and immediately beforehand.** ⚠️ **NGO observers describe majority support
  among member states alongside continued pressure from the US, Saudi Arabia, UAE, Panama
  and Liberia.**
- **⚠️ TIMING CONSEQUENCE**: ⚠️ **the delay pushed the earliest realistic entry into force
  back — one analysis puts it as unlikely before March 2028, against an original
  expectation of 2027.**

> **⚠️ GOTCHA — regional regulation did NOT wait, and this is the practically important
> point for anyone operating to Europe.** ⚠️ **The EU ETS, the UK ETS and FuelEU Maritime
> are ALREADY IN FORCE, imposing monitoring, reporting and financial obligations on ships
> trading to Europe.**
> **⚠️ So the absence of a global framework does not mean an absence of carbon cost — it
> means a FRAGMENTED one, which is precisely the outcome the industry lobbied against.**
> ⚠️ **Note the unusual politics: the framework was reportedly supported by the leading
> shipping industry lobby and by most states, because a single global regime is cheaper to
> comply with than a patchwork.**

**⚠️ Sourcing note: I've anchored the procedural facts on IMO's own press briefing and DNV,
and the vote counts on law-firm and industry summaries that agree.** ⚠️ **The
characterization of US conduct comes from advocacy and journalism sources with a clear
position, and I've attributed it rather than stating it flatly.** ⚠️ **Note also that some
sources still say "October 2026" for the resumed session while the most recent say early
December 2026 — the later date reflects MEPC 84's outcome.**

### 24.2 ⚠️ The alternative fuel orderbook: a market hedging
**⚠️ §24.1's uncertainty showing up directly in what shipowners are ordering — and the
2026 data contains one genuinely dramatic reversal.**

- **⚠️ The trajectory, from DNV's Alternative Fuels Insight platform:**
```
⚠️ 2024  ⚠️ 515 alternative-fuelled orders, +38% YoY.
   ⚠️ 69% of ALL container ship orders were alternative-fuel capable
   ⚠️ 166 methanol orders — 32% of the AFI orderbook
⚠️ 2025  ⚠️ 275 orders — a 47% COLLAPSE
   ⚠️ (the whole newbuild market also fell, 4,405 → 2,403 orders)
   ⚠️ GT share held steady at 38%, carried by containers
⚠️ H1 2026  ⚠️ 137 orders, down from 155 in H1 2025
```
- **⚠️ THE METHANOL REVERSAL is the striking figure.** ⚠️ **In the first half of 2026 just
  TWO methanol-fuelled ships were ordered, down from 40 in the same period of 2025.**
  ⚠️ **DNV reported no methanol orders at all in May 2026.** **⚠️ Against that, LNG orders
  are reported at more than twice the methanol total on the books (663 versus methanol),
  and LNG accounted for 73 H1 2026 orders against 87 a year earlier.**
- **⚠️ Where the orders actually went**: ⚠️ **LPG/ethane carriers surged — 55 LPG carriers
  in the period against just 17 a year earlier.** ⚠️ **Ammonia rose to four from three;
  hydrogen fell to one from four; two ethanol-fuelled ships were ordered in a category DNV
  only recently began tracking.**
- **⚠️ The scale reality check that matters most**: ⚠️ **conventional fuel still runs 95% of
  ships in operation by tonnage and 99% BY NUMBER OF SHIPS.** ⚠️ **Large ships lead the
  transition — 35% of the orderbook by gross tonnage has alternative fuel capability while
  only 15% of orders by count do.**

> **⚠️ GOTCHA — DO NOT read deliveries as a signal about current decisions.** ⚠️ **Deliveries
> in 2026 look strong (61 LNG and 38 methanol vessels delivered so far) — but those reflect
> ORDERS PLACED THREE TO FOUR YEARS AGO.** **⚠️ Orders are the leading indicator; deliveries
> are a lagging one, and confusing them produces exactly the wrong read on where the market
> is going.**
> ⚠️ **The strategic shift DNV describes is from single-bet to PORTFOLIO thinking: owners
> "managing fuel optionality, timing of investment, and exposure to future regulation as
> they navigate long-life asset decisions."** **⚠️ That is a rational response to §24.1 —
> when the regulation is undecided, buy optionality rather than commitment.**

**⚠️ A genuine first**: ⚠️ **Exmar took delivery of what it describes as the first oceangoing
DUAL-FUEL AMMONIA vessel, which is a step beyond the earlier ammonia deliveries that were
largely pilot or demonstration projects.** ⚠️ **Ammonia remains awaiting technology and
infrastructure maturity, and it carries real toxicity handling problems that LNG and
methanol do not.**
**⚠️ Sourcing note: DNV is a classification society (§19 → `ship-class-flag-imo-safety-operations-and-losses`) with a commercial interest in the
fuel transition and in its own AFI platform — but the AFI data is the industry standard,
is free to access, and the figures recur consistently across independent trade reporting.**
⚠️ **Numbers vary slightly between reports depending on cut-off date and whether retrofits
are counted; treat them as directional.**

---

## §25. Misconceptions

| Misconception | Correction |
|---|---|
| If it floats it's stable | ⚠️ **Buoyancy and stability are separate calculations** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| More stability is always better | ⚠️ **Excessive GM gives a violent roll that breaks things** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Adding weight is what destabilizes a ship | ⚠️ **Free surface does it with NO added weight** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Tonnage is a weight | ⚠️ **Gross tonnage is a VOLUME measure** (§2 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Displacement is cargo capacity | ⚠️ **Displacement is total weight; DWT is the payload** (§2 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| A bulbous bow always helps | ⚠️ **Only near its design speed and draught** (§4 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Speed costs fuel proportionally | ⚠️ **Roughly the CUBE. Hence slow steaming** (§5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Long ships are faster because of engines | ⚠️ **Hull speed scales with √L** (§5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Cavitation is a heat problem | ⚠️ **Pressure. Vapour bubbles collapsing** (§6 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Head seas can't make a ship roll | ⚠️ **Parametric rolling does exactly that** (§7 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Reversing the propeller stops you quickly | ⚠️ **It also destroys steering. Stopping takes km** (§8 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Ships break because waves hit them | ⚠️ **Hogging/sagging bending, plus fatigue** (§9 → `ship-structure-materials-machinery-systems-and-types`) |
| Higher-tensile steel is strictly better | ⚠️ **Thinner plate worsens fatigue and corrosion margin** (§10 → `ship-structure-materials-machinery-systems-and-types`) |
| Welded hulls are simply stronger than riveted | ⚠️ **They also give a crack a continuous path** (§9 → `ship-structure-materials-machinery-systems-and-types`) |
| Big ships need gearboxes | ⚠️ **Low-speed two-strokes couple directly and reverse** (§11 → `ship-structure-materials-machinery-systems-and-types`) |
| Class societies are government regulators | ⚠️ **Private bodies paid by the owners** (§19 → `ship-class-flag-imo-safety-operations-and-losses`) |
| The flag state does the inspections | ⚠️ **Usually delegated to class societies** (§19 → `ship-class-flag-imo-safety-operations-and-losses`) |
| A ship with class is therefore safe | ⚠️ **Port state control exists because that fails** (§19 → `ship-class-flag-imo-safety-operations-and-losses`) |
| Ships sink from technical failure | ⚠️ **Usually technical vulnerability plus an organizational decision** (§23 → `ship-class-flag-imo-safety-operations-and-losses`) |
| IMO agreed global carbon pricing | ⚠️ **Approved in 2025, NOT adopted. Pending December 2026** (§24.1) |
| No IMO deal means no carbon cost | ⚠️ **EU ETS, UK ETS and FuelEU are already in force** (§24.1) |
| Industry opposed the carbon framework | ⚠️ **The main lobby reportedly supported it** (§24.1) |
| Methanol is winning the fuel transition | ⚠️ **H1 2026 orders fell from 40 to 2** (§24.2) |
| Strong deliveries mean strong demand | ⚠️ **Deliveries lag orders by 3–4 years** (§24.2) |
| Shipping is rapidly going alternative-fuel | ⚠️ **99% of ships by number still run conventional** (§24.2) |

---

## §26. Numbers

```
⚠️ Block coefficient  ⚠️ ~0.5 fine/fast · ~0.85 full/slow
⚠️ Power vs speed  ⚠️ roughly the CUBE — 10% slower ≈ 25–30% less fuel
⚠️ Low-speed two-stroke efficiency  ⚠️ ~50%+, the highest in commercial use
⚠️ Free surface effect  ⚠️ scales with the CUBE of tank breadth
⚠️ Pivot point in a turn  ⚠️ roughly L/3 from the bow
⚠️ MEPC ES.2 vote  ⚠️ 57 to adjourn · 49 against · 21 abstained · 8 absent
⚠️ NZF approved  ⚠️ MEPC 83, April 2025 · adoption now early Dec 2026
⚠️ Earliest entry into force  ⚠️ reported unlikely before March 2028
⚠️ MARPOL Annex VI parties  ⚠️ reported 111
⚠️ Alt-fuel orders  ⚠️ 515 (2024) → 275 (2025, −47%) → 137 (H1 2026)
⚠️ Total newbuild orders  ⚠️ 4,405 (2024) → 2,403 (2025)
⚠️ Methanol orders H1  ⚠️ 40 (2025) → 2 (2026)
⚠️ LPG carriers H1  ⚠️ 17 (2025) → 55 (2026)
⚠️ Alt-fuel share  ⚠️ 35% of orderbook by GT · 15% by number of orders
⚠️ Fleet in operation  ⚠️ 95% conventional by tonnage · 99% by ship count
```

---

## §27. Books and Sources

| Source | Why |
|---|---|
| **Tupper, *Introduction to Naval Architecture*** | ⚠️ **The standard accessible text. §2–§9 → `ship-design-spiral-hydrostatics-stability-and-hull-form`, `ship-resistance-propulsion-seakeeping-and-manoeuvring`, `ship-structure-materials-machinery-systems-and-types`** |
| **Rawson & Tupper, *Basic Ship Theory*** | ⚠️ **The two-volume reference** |
| **Lewis (ed.), *Principles of Naval Architecture*** | ⚠️ **SNAME's multi-volume standard** |
| **Barrass & Derrett, *Ship Stability for Masters and Mates*** | ⚠️ **§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`, practical and worked** |
| **Molland, Turnock & Hudson, *Ship Resistance and Propulsion*** | §5–§6 → `ship-resistance-propulsion-seakeeping-and-manoeuvring` |
| **Storch et al., *Ship Production*** | ⚠️ **§14–§17 → `ship-shipyard-build-welding-launch-and-naval-vessels`, the shipyard process** |
| **IACS Common Structural Rules** | ⚠️ **§9 → `ship-structure-materials-machinery-systems-and-types`, §19 → `ship-class-flag-imo-safety-operations-and-losses` — freely published** |
| **Class society rules (DNV, LR, ABS)** | ⚠️ **The actual design basis. Largely free online** |
| **IMO conventions and the IMO website** | ⚠️ **§20 → `ship-class-flag-imo-safety-operations-and-losses`, §24.1 — primary** |
| **DNV Alternative Fuels Insight (AFI)** | ⚠️ **§24.2 — the industry data standard, free** |
| **MAIB / NTSB / DMAIB accident reports** | ⚠️ **§23 → `ship-class-flag-imo-safety-operations-and-losses`. Read these — outstanding investigations** |
| **Larsson & Eliasson, *Principles of Yacht Design*** | §21 → `ship-class-flag-imo-safety-operations-and-losses` |

---

## §28. Quick Reference

### 28.1 Picker
| Question | Where |
|---|---|
| Will it float? | ⚠️ **Displacement = weight** (§2 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Will it float UPRIGHT? | ⚠️ **A different calculation. GM and the GZ curve** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Ship rolling violently | ⚠️ **GM too high, or synchronous rolling** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`, §7 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Sudden list with no weight change | ⚠️ **Free surface, or cargo shift** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) |
| Rolling heavily in head seas | ⚠️ **Parametric rolling. Change course or speed** (§7 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| How do I cut fuel? | ⚠️ **Slow down — it's cubic. Then clean the hull** (§5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`, §22 → `ship-class-flag-imo-safety-operations-and-losses`) |
| Propeller eroding and noisy | ⚠️ **Cavitation** (§6 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Why can't it stop? | ⚠️ **No brakes; reversing kills steering** (§8 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) |
| Where does hull strength come from? | ⚠️ **Deck and bottom plating — box girder** (§9 → `ship-structure-materials-machinery-systems-and-types`) |
| Why build in blocks? | ⚠️ **Downhand welding and pre-outfitting** (§14 → `ship-shipyard-build-welding-launch-and-naval-vessels`) |
| Blocks don't fit at erection | ⚠️ **Weld distortion and accuracy control** (§14 → `ship-shipyard-build-welding-launch-and-naval-vessels`, §16 → `ship-shipyard-build-welding-launch-and-naval-vessels`) |
| Who actually sets the rules? | ⚠️ **Class + flag + IMO, and they interlock** (§19 → `ship-class-flag-imo-safety-operations-and-losses`) |
| What fuel should we order? | ⚠️ **Currently a portfolio bet, not a single one** (§24.2) |
| Is carbon pricing coming? | ⚠️ **Regionally it's already here** (§24.1) |

### 28.2 Design sanity checks
- [ ] ⚠️ **Displacement and deadweight reconciled with the weight estimate** (§1 → `ship-design-spiral-hydrostatics-stability-and-hull-form`, §2 → `ship-design-spiral-hydrostatics-stability-and-hull-form`)
- [ ] ⚠️ **Intact stability across ALL loading conditions, not just full load** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`)
- [ ] ⚠️ **Free surface accounted for in every partially filled tank** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`)
- [ ] Damage stability and subdivision to the applicable standard (§20 → `ship-class-flag-imo-safety-operations-and-losses`)
- [ ] ⚠️ **GZ curve checked at large angles, not just initial GM** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`)
- [ ] Powering with realistic sea and fouling margins (§5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`)
- [ ] ⚠️ **Propeller checked for cavitation at the design condition** (§6 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`)
- [ ] ⚠️ **Longitudinal strength for hogging AND sagging, and for the worst loading** (§9 → `ship-structure-materials-machinery-systems-and-types`)
- [ ] Fatigue-critical details reviewed (§9 → `ship-structure-materials-machinery-systems-and-types`)
- [ ] Corrosion allowance and coating strategy specified (§10 → `ship-structure-materials-machinery-systems-and-types`)
- [ ] ⚠️ **Build strategy and block breakdown agreed with production EARLY** (§14 → `ship-shipyard-build-welding-launch-and-naval-vessels`, §15 → `ship-shipyard-build-welding-launch-and-naval-vessels`)
- [ ] ⚠️ **Regulatory exposure over a 25-year life considered, not just today's rules** (§24)

---

## §29. Method

**§1–§23 → `ship-design-spiral-hydrostatics-stability-and-hull-form`, `ship-resistance-propulsion-seakeeping-and-manoeuvring`, `ship-structure-materials-machinery-systems-and-types`, `ship-shipyard-build-welding-launch-and-naval-vessels`, `ship-class-flag-imo-safety-operations-and-losses` rests on settled naval architecture and standard shipbuilding practice** —
**hydrostatics and stability theory, Froude's resistance scaling, propeller and cavitation
physics, longitudinal strength as a box girder, block construction, and the class/flag/IMO
architecture.** ⚠️ **None of it needed verification; Archimedes and the metacentre have not
moved.**

**Two searches were run in August 2026**, on **IMO carbon regulation** and the
**alternative fuel orderbook** — ⚠️ **chosen because between them they determine what a ship
ordered today will be designed to burn, and because both changed materially in the last
twelve months.**

**Confidence.** **High** in §3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`, which is the section I'd most want read. ⚠️ **The separation
of buoyancy from stability, and specifically that FREE SURFACE EFFECT destroys stability
without adding any weight and scales with the cube of tank breadth, is the single most
consequential idea here — it is the mechanism behind a large share of capsizes and it is
genuinely counterintuitive.** ⚠️ **§9 → `ship-structure-materials-machinery-systems-and-types`'s box-girder framing and §5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`'s cubic power law are the
close seconds: the first explains why ships break where they do, the second explains why
slow steaming is the cheapest decarbonization lever anyone has.**

**High** on §24.1's procedural record, which comes from IMO's own press briefing, DNV, and
several independent law-firm summaries that agree on the specifics: ⚠️ **MEPC 83 approval
in April 2025, the 14–17 October 2025 extraordinary session, the 57–49 adjournment vote,
and MEPC 84's outcome moving adoption to early December 2026.**
⚠️ **I have deliberately attributed rather than asserted the political characterization —
"bully-boy tactics" is Carbon Brief's reporting of an accusation, and the NGO framing comes
from the Clean Shipping Coalition, which is an advocacy body.** ⚠️ **Note also a live
inconsistency I've flagged in-section: older sources say the resumed session is October
2026, newer ones say early December, and the difference reflects MEPC 84.**

**High** on §24.2's DNV figures, which recur consistently across DNV's own releases and
independent trade coverage: ⚠️ **515 → 275 → 137 orders, the 47% 2025 decline, the
methanol collapse from 40 to 2 in H1, LPG's rise from 17 to 55, and the 95%/99%
conventional-fleet figures.**
⚠️ **DNV is a classification society with a commercial interest in the fuel transition and
in its own platform, which I've noted — but AFI is the industry data standard and free to
access, which is the best available situation.** ⚠️ **The order counts vary slightly between
reports depending on cut-off and retrofit treatment, so I've presented them as directional
rather than exact.**
**⚠️ The orders-versus-deliveries distinction is the analytical point I'd most defend in
that section: strong 2026 deliveries reflect 2022–23 decisions, and reading them as current
demand gets the direction of travel exactly backwards.**
