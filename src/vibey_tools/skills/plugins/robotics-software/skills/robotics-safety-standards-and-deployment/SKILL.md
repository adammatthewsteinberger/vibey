---
name: robotics-safety-standards-and-deployment
description: "Use when a robot has real-world consequences: real-time and safety-critical engineering, testing, debugging and field deployment, functional safety and standards including the ISO 10218:2025 revision and the humanoid gap, and the aerospace flight-software practices at the far end of the rigour spectrum including DO-178C, formal methods and redundancy."
---

# Robotics Software: Real-Time and Safety-Critical Engineering, Testing, Standards, and Aerospace

> **Part 4 of 5** of the *Robotics Software* reference (plugin `robotics-software`), covering §11–§14. Sibling skills: `robotics-stack-ros2-and-perception` (§0–§4), `robotics-planning-control-and-manipulation` (§5–§7), `robotics-learning-simulation-and-fleets` (§8–§10), `robotics-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `robotics-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference for engineers building robots that operate in the
> physical world with real consequences — deliberately distinct from a hobbyist kit
> reference. Three markers:
> - **[DURABLE]** — control theory, estimation, architecture, and safety discipline.
>   Most of this document.
> - **[VERSIONED]** — frameworks, models, standards, tooling.
> - **[CONTESTED]** — genuine and active disagreement, of which this field currently has
>   a lot.
>
> **⚠️ GOTCHA** boxes mark the failures that damage hardware, or people.
>
> **The three framings that organize everything below:**
> 1. **Physics doesn't have an undo button.** A web service that fails returns a 500;
>    a robot that fails puts mass through space. **This single asymmetry justifies every
>    piece of apparently excessive rigour below** — the redundancy, the state machines,
>    the simulation, the safety cases (§11, §13).
> 2. **⚠️ Robotics is an integration discipline, and the integration is where it fails.**
>    Perception, estimation, planning, and control each work in isolation and break at
>    the seams — timing, coordinate frames, latency, and units. **The classic robotics bug
>    is not a bad algorithm; it's a transform published 40ms late** (§3.4 → `robotics-stack-ros2-and-perception`, §12).
> 3. **The field is in the middle of a genuine methodological argument** between
>    classical model-based robotics and learned end-to-end policies (§8 → `robotics-learning-simulation-and-fleets`, §16.1 → `robotics-reference`).
>    **Neither side has won, production systems are overwhelmingly hybrid, and anyone
>    telling you the argument is settled is selling something.**

---

## §11. Real-Time and Safety-Critical Engineering

**[DURABLE] "Real-time" means deterministic, not fast.** A system that responds in 10ms
every single time is real-time; one that averages 1ms and occasionally takes 100ms is not.
**Hard real-time** means a missed deadline is a system failure.

**How you actually get it**: **PREEMPT_RT** (mainlined into Linux, and the common
foundation), a genuine **RTOS** (QNX, VxWorks, Zephyr, FreeRTOS) for the hard layers,
**⚠️ CPU isolation and shielding** (`isolcpus`, IRQ affinity) so your control thread owns a
core, **memory locking** (`mlockall`) and **no allocation in the control loop**,
**priority inheritance** on any shared mutex, and **⚠️ lock-free structures for
producer-consumer across priority levels.**

> **⚠️ GOTCHA — the things that silently destroy determinism:** dynamic memory allocation,
> unbounded loops, `printf` and logging in the hot path, page faults, garbage collection,
> **CPU frequency scaling and thermal throttling**, network stack processing on your
> control core, and **priority inversion**. ⚠️ **Measure worst-case, not average — the
> distribution's tail is the whole specification.**

**Architecturally**: separate the **safety-critical** path from the **mission** path, and
run them at different assurance levels. ⚠️ **A watchdog with an independent path to
actuator power is the last line of defence and it must not depend on the software it's
watching.**

---

## §12. Testing, Debugging, and Deployment

**[DURABLE] The testing pyramid, robotics edition:**
```
Unit                     pure logic, no hardware. Fast, and undervalued
Component-in-sim         one node against simulated inputs
Integration-in-sim       full stack, scripted scenarios, in CI
Hardware-in-the-loop     real compute + real timing, simulated world  ⚠️ high value
Real hardware, safe env  cage, tether, E-stop, reduced speed/power
Field trials             real environment, safety operator
Production               with monitoring, and a rollback path
```

**⚠️ HIL is the most under-invested rung** and catches the timing and driver bugs that
pure simulation cannot.

**[DURABLE] Debugging discipline specific to robots:**
- **⚠️ Record everything, always.** `rosbag`/MCAP of every run, including failures.
  **A robot failure you didn't record is a failure you cannot fix**, because you may not
  reproduce it.
- **Deterministic replay** from logs — the single most valuable debugging capability in
  the field.
- **Visualize** — rviz2 and Foxglove. ⚠️ **Most perception and transform bugs are obvious
  the moment you look at them and invisible in numbers** (§3.4 → `robotics-stack-ros2-and-perception`).
- **Check the transform tree and timestamps first.** §3.4 → `robotics-stack-ros2-and-perception` is genuinely the first
  hypothesis, not the last.
- **Bisect the stack**: replay recorded sensor data into a live planner; feed synthetic
  perfect perception into control. **Isolate which layer is lying.**
- **⚠️ Watch for correlated failures.** Robots fail in cascades — a perception dropout
  causes a planner stall causes a controller timeout causes an E-stop.

**Field deployment**: staged rollout, ⚠️ **shadow mode** (run the new policy without
letting it actuate, and compare), extensive telemetry, remote diagnostics,
**a rollback path that works without physical access**, and **an incident process
that treats near-misses as reportable.**

---

## §13. Functional Safety and Standards

**[VERSIONED — and this regime changed substantially in 2025, which many practitioners
have not caught up with.]**

### 13.1 ⚠️ The ISO 10218:2025 revision

**ISO 10218-1:2025** (robot manufacturers) and **ISO 10218-2:2025** (integrators,
applications, and cells) were **published February 2025 and came into force 1 April 2025**
— **the first major revision since 2011**, taking experts from **20+ countries nearly
eight years**.

**What changed, and why it matters:**
- ⚠️ **ISO/TS 15066 no longer exists as a standalone specification.** Its power-and-force-
  limiting and collaborative-application requirements were **folded directly into
  ISO 10218-2**. **There is no separate cobot standard to cite anymore.**
- ⚠️ **The terms "collaborative robot" and "collaborative operation" do not appear in the
  revised standard.** **Collaboration is a property of the *application*, not the robot** —
  only an application can be assessed. **This kills the "we bought a collaborative robot,
  therefore we're safe" reasoning outright**, and that reasoning was extremely common.
- **Functional safety requirements are now explicit rather than implied**, with a
  robot **classification scheme** (Class I / Class II).
- ⚠️ **Cybersecurity requirements were added** — for the first time, on the reasoning that
  millions of networked industrial robots exist.
- Manual load/unload and end-effector guidance folded in from separate technical reports.
- **ISO 10218-2:2025 nearly tripled in length.**

**The standards stack around it**: **ISO 12100** (risk assessment methodology) and
**ISO 13849-1:2023** (safety-related control systems, PL/categories) underneath;
**ANSI/A3 R15.06-2025** and **CSA Z434** as the North American adoptions;
**IEC 61508** for general functional safety; **ISO 26262** (automotive) and **ISO 21448
/ SOTIF** (⚠️ **safety of the intended function — hazards from performance limitations
rather than faults, which is exactly the right frame for learned perception**).

**⚠️ On enforceability**: ISO standards are voluntary in themselves. **They become binding
through contracts and through harmonisation** — in the EU under **Machinery Regulation
2023/1230, which applies from 20 January 2027**. In the US, OSHA enforcement provides the
pressure.

### 13.2 ⚠️ The humanoid gap

**[VERSIONED and genuinely unresolved.]** The 2025 revision **explicitly leaves regulatory
gaps around AI, humanoids, and mobile manipulation.** ISO/TS 15066's contact-force model
addressed **stationary arms**; **humanoids walk, balance, and carry energy-dense
batteries** — different hazards entirely (fall zones, dynamic stability, thermal events).
**ISO 25785-1 is under development for dynamically stable robots**, and until it lands,
**humanoid deployments are being certified against a standard that wasn't written for
them.** ⚠️ **If you are deploying humanoids, this gap is your problem, not the standard's.**

### 13.3 [DURABLE] The engineering practices
**Risk assessment first** (ISO 12100 methodology), **safety functions on rated hardware**
(⚠️ **a safety-rated stop is not `if (bad) stop();` in your application code**),
**redundancy and diversity** for safety functions, **safe states designed rather than
inherited**, **E-stop reachable from anywhere in the workspace**, **speed and separation
monitoring** or **power and force limiting** as the collaborative strategies, and
**⚠️ a written safety case** — the artifact that says what the system will not do and why
you believe it.

---

## §14. Aerospace Flight Software

**[DURABLE] The far end of the rigour spectrum, and worth knowing even if you never work
there — because it shows what "we cannot fail" looks like as engineering practice.**

**Standards**: **DO-178C** (airborne software, DAL A–E; ⚠️ **DAL A demands MC/DC coverage
and full requirements traceability**), **DO-254** (hardware), **ECSS** (European space),
**NASA NPR 7150.2** and the **NASA/JPL Power of 10** coding rules, **MISRA C/C++** in
adjacent industries.

**The architectural patterns**: **triple modular redundancy with voting**,
**radiation-hardened or rad-tolerant compute** (⚠️ **and the flight computer is often
generations behind consumer silicon precisely because it's qualified**), **watchdogs at
multiple levels**, **partitioned RTOS** (ARINC 653), **NASA cFS** as a reusable flight
software framework, **no dynamic allocation after initialization**, **bounded loops and
bounded recursion**, and **extensive formal analysis**.

**⚠️ The cultural practices are as important as the technical ones**: exhaustive
requirements traceability, independent verification and validation, **change control that
would feel absurd anywhere else**, hardware-in-the-loop and flatsat testing,
**anomaly review boards**, and the doctrine that **every in-flight anomaly is investigated
to root cause and fed back into process.**

**[DURABLE] The transferable lesson for ordinary robotics**: **the practices scale down.**
Requirements traceability, deterministic execution, resource bounds, comprehensive logging,
and a written safety case are all achievable outside aerospace and all improve reliability.
⚠️ **You don't need DO-178C to adopt bounded loops and a no-allocation control path.**
