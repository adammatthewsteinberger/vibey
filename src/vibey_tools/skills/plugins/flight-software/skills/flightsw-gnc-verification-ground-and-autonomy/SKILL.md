---
name: flightsw-gnc-verification-ground-and-autonomy
description: "Use when working on guidance software, proving the system correct, or learning from what went wrong: GNC software structure and its numerical concerns, verification and validation including hardware-in-the-loop and processor-in-the-loop testing, the ground segment and operations tooling, onboard autonomy and AI and where it is actually appropriate, and the failure case studies that produced the rules."
---

# Flight Software: GNC, Verification and Validation, Ground Segment, Autonomy, and Failure Cases

> **Part 4 of 5** of the *Flight Software* reference (plugin `flight-software`), covering §12–§16. Sibling skills: `flightsw-architecture-languages-and-standards` (§0–§3), `flightsw-processors-radiation-and-real-time` (§4–§7), `flightsw-fdir-time-telemetry-and-updates` (§8–§11), `flightsw-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The discipline and standards are stable; flight processors and framework releases moved materially in 2025-26. See §17 → `flightsw-reference` for what is dated and what is genuinely contested.

> **How to read this.** This is the deep treatment of flight software. It supersedes the
> compressed flight-software section in a robotics-software reference; **spacecraft systems
> engineering is in a space-exploration reference, and launch physics in a rocket-science
> reference.**
>
> Two markers:
> - **[DURABLE]** — the discipline, architecture, and standards. Most of this.
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark what has actually destroyed vehicles.
>
> **The three properties that make this domain different from all other software:**
> 1. **⚠️ You cannot patch your way out.** Uplink is bandwidth-limited, latency-bound, and
>    sometimes impossible. **A bug that bricks the receiver ends the mission** — which is
>    why §11 → `flightsw-fdir-time-telemetry-and-updates`'s update mechanism is designed before the software it updates.
> 2. **⚠️ The hardware is actively hostile.** Radiation flips bits in RAM and registers
>    with no warning and no error signal. **Software must assume its own memory is
>    corrupting underneath it** (§4 → `flightsw-processors-radiation-and-real-time`, §5 → `flightsw-processors-radiation-and-real-time`).
> 3. **⚠️ Correct-but-late is wrong.** A control loop that misses its deadline has failed
>    regardless of the answer it eventually produces. **Determinism outranks throughput,
>    and this inverts almost every instinct from server-side engineering** (§6 → `flightsw-processors-radiation-and-real-time`).

---

## §12. GNC Software

**[DURABLE] The mathematics is in a rocket-science reference §11; this is the software
practice.**

**The loop**: sensors (IMU, star tracker, GPS) → **estimation** (⚠️ **Kalman filter
variants — EKF, UKF; and numerical conditioning matters: use square-root or UD
factorization forms, because covariance matrices lose positive-definiteness in single
precision**) → guidance → control law → actuators.

**⚠️ Model-based development is the norm here and it changes the workflow**: algorithms are
developed in Simulink or equivalent, then **autocoded to C** (DO-331 covers this for
certification). **The benefit is that the model is the specification and it is executable;
the risk is that the generated code's WCET and stack behaviour must still be analysed** —
autocoding does not exempt you from §6 → `flightsw-processors-radiation-and-real-time`.

**⚠️ Numerical hazards specific to flight:**
- **Single vs double precision** — ⚠️ **a real trade on constrained hardware, and the wrong
  choice destroyed Ariane 501** (§16.2).
- **Angle wrapping** at ±180°, and **quaternion sign ambiguity** (⚠️ **q and −q are the same
  rotation; a naive interpolation or comparison takes the long way round**).
- **⚠️ Gimbal lock in Euler angles** — use quaternions internally, convert only for display.
- **Filter divergence** — ⚠️ **an over-confident covariance stops believing measurements.**
  Bound it.
- **Integrator windup** in controllers with saturating actuators — clamp.
- **Units. Always units.** §16.3.

---

## §13. Verification and Validation

**[DURABLE] The layered campaign:**
```
Static analysis   ⚠️ multiple tools daily (Power of 10 rule 10) — Coverity,
                  Polyspace, CBMC, clang analyzer
Unit test         with coverage requirements up to MC/DC (§3.3)
Integration       component interactions on the software bus
SIL               software-in-the-loop against a simulated environment
PIL / HIL         ⚠️ processor- and hardware-in-the-loop — the flight code on the
                  flight processor
Testbed           ⚠️ a full engineering-model spacecraft on the ground
Day-in-the-life   realistic operational sequences end to end
Fault injection   ⚠️ deliberately corrupt memory, hang devices, drop messages
```

**⚠️ Formal methods are used here more than anywhere else in industry**, because the cost
of failure justifies it: **SPARK/Ada** for provable absence of runtime errors, **model
checking** (⚠️ **SPIN, developed by Holzmann at JPL, verified concurrency logic for
several missions**), **abstract interpretation** (Astrée), and **theorem proving** for
critical algorithms. **DO-333 provides the certification credit path.**

**13.3 ⚠️ The testbed is where flight software actually gets validated**, and its fidelity
is a mission-level risk. **Discrepancies between testbed and flight configuration are a
recurring source of anomalies** — different EEPROM contents, different table values,
different device firmware revision. **Configuration control of the testbed is as important
as of the flight article.**

**⚠️ And the irreducible gap: you cannot test in flight conditions.** You cannot produce
zero-g, the real radiation environment, or the real thermal-vacuum dynamics simultaneously.
**This is why fault injection and formal methods carry so much weight — they cover what the
test campaign structurally cannot.**

---

## §14. Ground Segment

**⚠️ Ground software is where most of the code is, and it gets a fraction of the attention.**

**Components**: mission planning and sequence generation (⚠️ **with constraint checking —
the ground tool that catches an illegal command sequence is worth more than the onboard
check that rejects it**), command generation and uplink, **telemetry processing,
decommutation and archiving**, monitoring and alarm display, trending and anomaly
analysis, **simulators**, and flight dynamics.

**Open source worth knowing**: **NASA OpenMCT** (mission control visualization),
**COSMOS/OpenC3** (command and control), **Yamcs** (mission control framework),
**SatNOGS** (ground station network). ⚠️ **The commercial and institutional systems are
mostly bespoke, which is exactly the reuse problem cFS solved on the flight side and
nobody has fully solved on the ground side.**

**⚠️ Operational practice**: **procedures for everything**, **anomaly response teams and
on-call rotations**, **the command approval chain** (⚠️ **two-person review for hazardous
commands is standard for good reason**), and **long-term archiving in PDS** for planetary
missions.

---

## §15. Autonomy and Onboard AI

**[DURABLE] Autonomy is forced by light-time** (a space-exploration reference §5.3), not
chosen.

**The ladder**: time-tagged sequences → event-driven sequencing → onboard planning
(⚠️ **Remote Agent on Deep Space 1, 1999, was the first onboard planner in control of a
spacecraft**) → autonomous science (**AEGIS** selects and targets spectroscopy on the Mars
rovers without ground involvement) → **fully autonomous EDL.**

**⚠️ Onboard ML is arriving and the verification problem is unsolved.** cFS's planned
2026 Gov Alpha explicitly targets AI/ML integration, and HPSC (§4 → `flightsw-processors-radiation-and-real-time`) provides the compute.
**The engineering-honest position:**
- **⚠️ Use learned components for perception and classification, not for the safety-critical
  control path.** The architecture that works is a learned layer inside a classical
  envelope with deterministic limits — see a robotics-software reference §8.3 for the same
  pattern in robotics.
- **⚠️ There is no accepted certification path for a neural network at DO-178C DAL A.**
  Saying otherwise is marketing.
- **Bounded compute and bounded latency still apply** (§6 → `flightsw-processors-radiation-and-real-time`) — an inference that occasionally
  takes 3× as long has violated a deadline.

---

## §16. Failure Case Studies

**[DURABLE] Each of these produced a rule that is now standard practice. This is how the
discipline was built.**

**16.1 ⚠️ Mars Pathfinder (1997) — priority inversion, in flight, on Mars.**
The lander began experiencing total system resets on the surface. **Cause: a high-priority
bus management task blocked on a mutex held by a low-priority meteorological task, which
was preempted by a medium-priority communications task.** The watchdog fired and reset the
system. **⚠️ The fix was uplinked: enable priority inheritance on that mutex — a flag that
existed in VxWorks and was off.** **The lesson: priority inheritance is not optional, and
the ability to debug and patch in flight saved the mission** (§11 → `flightsw-fdir-time-telemetry-and-updates`).

**16.2 ⚠️ Ariane 501 (1996) — reuse without re-validation.**
A 64-bit float horizontal-velocity value was converted to a 16-bit signed integer. The
Ariane 5 trajectory produced a value that overflowed; **the exception was unhandled, both
(identical, redundant) inertial reference systems shut down, the backup failed first and
the primary a moment later, and the vehicle self-destructed 37 seconds after liftoff.**
⚠️ **The computation was Ariane 4 alignment code that served no purpose after liftoff on
Ariane 5.** **Lessons: identical redundancy does not protect against a design fault;
inherited code must be re-validated against the new operating envelope; and dead code
should be dead.**

**16.3 ⚠️ Mars Climate Orbiter (1999) — units at an interface.**
Ground software produced impulse in **pound-force-seconds**; the navigation software
expected **newton-seconds.** Trajectory errors accumulated across the cruise and the
spacecraft entered the atmosphere too low. **Lesson: interfaces need explicitly specified
units, and unit-typed values in code where the language permits it.**

**16.4 ⚠️ Mars Polar Lander (1999) — a sensor transient believed too readily.**
Leg-deployment vibration is believed to have generated a spurious touchdown signal; the
software latched it and **cut the descent engines ~40 m above the surface.** ⚠️ **Lesson:
plausibility-check sensor inputs against other state — touchdown at 40 m altitude was
physically impossible and could have been rejected.**

**16.5 ⚠️ Therac-25 (1985–87) — outside aerospace, and required reading anyway.**
Race conditions in a radiation therapy machine's software, with hardware interlocks removed
in favour of software checks, caused massive overdoses and deaths. **Lesson: removing
hardware interlocks because "the software handles it" is a specific and recurring failure
mode, and concurrency bugs are not theoretical.**

**16.6 ⚠️ Boeing Starliner OFT-1 (2019) — clock initialization.**
The mission elapsed timer initialized from the launch vehicle at the wrong point,
**offset by 11 hours**, causing the spacecraft to burn propellant in the wrong mission
phase. ⚠️ **A second, separate software defect in the service module separation sequence
was found and patched during the flight** — which would have caused a destructive
recontact. **Lesson: end-to-end integrated testing of the full sequence, not
subsystem-by-subsystem.**

**⚠️ The pattern across all of them**: none was an exotic algorithmic error. **They were
interfaces, initialization, inherited assumptions, concurrency, and inadequate integrated
testing.** That is where flight software actually fails.
