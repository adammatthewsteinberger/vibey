---
name: robotics-reference
description: "Use when checking a robotics anti-pattern, weighing a contested question, confirming whether a claim about the learning layer, hardware or safety standards is still current (snapshot verified August 2026), finding the books, primary sources and groups, or needing the tool picker, the when-the-robot-misbehaves list, and the facts worth holding. Companion to the other robotics-software skills."
---

# Robotics Software: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Robotics Software* reference (plugin `robotics-software`), covering §15–§20. Sibling skills: `robotics-stack-ros2-and-perception` (§0–§4), `robotics-planning-control-and-manipulation` (§5–§7), `robotics-learning-simulation-and-fleets` (§8–§10), `robotics-safety-standards-and-deployment` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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
>    the simulation, the safety cases (§11 → `robotics-safety-standards-and-deployment`, §13 → `robotics-safety-standards-and-deployment`).
> 2. **⚠️ Robotics is an integration discipline, and the integration is where it fails.**
>    Perception, estimation, planning, and control each work in isolation and break at
>    the seams — timing, coordinate frames, latency, and units. **The classic robotics bug
>    is not a bad algorithm; it's a transform published 40ms late** (§3.4 → `robotics-stack-ros2-and-perception`, §12 → `robotics-safety-standards-and-deployment`).
> 3. **The field is in the middle of a genuine methodological argument** between
>    classical model-based robotics and learned end-to-end policies (§8 → `robotics-learning-simulation-and-fleets`, §16.1).
>    **Neither side has won, production systems are overwhelmingly hybrid, and anyone
>    telling you the argument is settled is selling something.**

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Debugging the algorithm before checking transforms and timestamps | ⚠️ **The most common robotics bug, by a wide margin** (§3.4 → `robotics-stack-ros2-and-perception`) |
| Mixing coordinate frames by hand | Produces plausible wrong behaviour, not errors (§3.4 → `robotics-stack-ros2-and-perception`) |
| Ignoring quaternion ordering conventions | (x,y,z,w) in ROS, (w,x,y,z) elsewhere (§3.4 → `robotics-stack-ros2-and-perception`) |
| Timestamping at publish rather than measurement | Corrupts every downstream filter (§3.4 → `robotics-stack-ros2-and-perception`) |
| Unsynchronized clocks across compute nodes | Fusion silently degrades (§3.4 → `robotics-stack-ros2-and-perception`) |
| Not budgeting end-to-end latency | ⚠️ **Dead time destabilizes controllers** (§6.2 → `robotics-planning-control-and-manipulation`) |
| Optimizing average latency, ignoring jitter | ⚠️ **Determinism beats speed** (§6.2 → `robotics-planning-control-and-manipulation`, §11 → `robotics-safety-standards-and-deployment`) |
| Two cameras and calling it redundancy | Correlated failure modes (§3 → `robotics-stack-ros2-and-perception`) |
| Trusting wheel odometry | It lies confidently under slip (§3 → `robotics-stack-ros2-and-perception`) |
| Treating an IMU as an absolute sensor | It drifts. Always (§3 → `robotics-stack-ros2-and-perception`) |
| Planning without kinodynamic constraints | Plans the robot can't execute (§5 → `robotics-planning-control-and-manipulation`) |
| Potential fields for anything nontrivial | Local minima; everyone rediscovers this (§5 → `robotics-planning-control-and-manipulation`) |
| No integral windup clamping | Saturation → windup → overshoot (§6.2 → `robotics-planning-control-and-manipulation`) |
| Allocation, logging, or unbounded loops in the control path | ⚠️ **Destroys determinism** (§11 → `robotics-safety-standards-and-deployment`) |
| Safety logic inside the application controller | ⚠️ **Must be an independent rated layer** (§13.3 → `robotics-safety-standards-and-deployment`) |
| A watchdog that depends on the software it watches | Not a watchdog (§11 → `robotics-safety-standards-and-deployment`) |
| "We bought a collaborative robot, so it's safe" | ⚠️ **ISO 10218:2025 removed the term — safety is a property of the application** (§13.1 → `robotics-safety-standards-and-deployment`) |
| Citing ISO/TS 15066 as a standalone standard | ⚠️ **Absorbed into ISO 10218-2:2025** (§13.1 → `robotics-safety-standards-and-deployment`) |
| Deploying humanoids against arm-shaped safety standards | ⚠️ **The gap is real and it's yours** (§13.2 → `robotics-safety-standards-and-deployment`) |
| Learned policy with no classical safety layer beneath | No safety case is possible (§8.3 → `robotics-learning-simulation-and-fleets`, §13 → `robotics-safety-standards-and-deployment`) |
| Sim-only validation | Ships things that only work in sim (§9 → `robotics-learning-simulation-and-fleets`) |
| Domain randomization that omits latency | Under-done and disproportionately costly (§9 → `robotics-learning-simulation-and-fleets`) |
| Not recording every run | ⚠️ **An unrecorded failure may be unreproducible** (§12 → `robotics-safety-standards-and-deployment`) |
| No deterministic replay capability | The most valuable debugging tool, absent (§12 → `robotics-safety-standards-and-deployment`) |
| Skipping hardware-in-the-loop | The most under-invested test rung (§12 → `robotics-safety-standards-and-deployment`) |
| No defined behaviour on fleet-manager disconnect | The actuators keep moving during a partition (§10 → `robotics-learning-simulation-and-fleets`) |
| OTA update with no staged rollout or rollback | You can brick a fleet (§10 → `robotics-learning-simulation-and-fleets`) |
| ROS 2 QoS mismatch | ⚠️ **Silently no connection, no error** (§2.3 → `robotics-stack-ros2-and-perception`) |
| Default single-threaded executor for timing-sensitive work | Unpredictable callback scheduling (§2.3 → `robotics-stack-ros2-and-perception`) |
| Assuming ROS 2 is real-time out of the box | It is not (§2.3 → `robotics-stack-ros2-and-perception`, §11 → `robotics-safety-standards-and-deployment`) |
| Multicast DDS discovery on a large fleet network | Floods; use discovery servers or Zenoh (§2.3 → `robotics-stack-ros2-and-perception`) |
| Targeting a non-LTS ROS distro for production | 18 months of support (§2.2 → `robotics-stack-ros2-and-perception`) |
| Quoting VLA benchmark numbers as deployment readiness | ⚠️ **Evaluation transfers poorly** (§8.3 → `robotics-learning-simulation-and-fleets`) |

---

## §16. Contested Questions

**16.1 End-to-end learning vs. modular classical stacks.** ⚠️ **The field's central live
argument.** *For learning*: hand-engineered pipelines don't generalize to the long tail,
and VLAs demonstrably do semantic generalization classical systems cannot. *For classical*:
**guarantees, interpretability, debuggability, and the ability to write a safety case** —
and when a learned system fails you often cannot say why. **[CONTESTED. Production systems
are overwhelmingly hybrid, and §8.3 → `robotics-learning-simulation-and-fleets`'s split — learned perception and policy, classical
control and safety — is where the evidence currently sits.]**

**16.2 Is ROS 2 the right foundation for production?** *For*: the ecosystem is
irreplaceable, and rebuilding drivers and tooling is enormous undeveloped work.
*Against*: **the companies with the highest reliability requirements — Boston Dynamics,
most AV stacks, aerospace — largely don't use it**, for real-time and certification
reasons. **⚠️ A defensible read: ROS 2 for the mission layer, something else for the
hard real-time and safety layers.**

**16.3 Are humanoids the right form factor?** *For*: the world is built for human
morphology, and one platform could serve many tasks. *Against*: ⚠️ **bipedal locomotion is
an enormous cost paid to solve a problem wheels solved**, and task-specific robots
outperform generalists at almost everything today. **The honest position: the bet is on
future generality and data network effects, not on current capability.**

**16.4 Simulation-first or hardware-first?** *Sim*: parallel, cheap, safe, and the only
way RL is tractable. *Hardware*: ⚠️ **the gap is real and sim-validated systems fail in
ways sim cannot show.** **The synthesis everyone converges on is sim for coverage,
hardware for truth, and HIL bridging them.**

**16.5 How much does foundation-model progress transfer to robots?** *Optimistic*:
Open X-Embodiment showed cross-embodiment transfer, and the scaling story has held so far.
*Sceptical*: ⚠️ **robotics has no internet-scale data and cannot easily get it; the
bottleneck is physical interaction data, not model capacity.** ⚠️ **World models and
synthetic data generation are the field's current bet on escaping that**, and whether it
works is genuinely open.

**16.6 Should safety-critical robotics use learned components at all?** *For*: learned
perception already outperforms classical on most metrics, and refusing it forfeits
capability. *Against*: **no current method produces the evidence a safety case needs.**
**⚠️ SOTIF (ISO 21448) is the standards world's attempt to grapple with this**, and it's
incomplete. **Live and unresolved.**

---

## §17. Currency Snapshot — verified August 2026

**[DURABLE] §4–§7 → `robotics-stack-ros2-and-perception`, `robotics-planning-control-and-manipulation`'s theory, §11 → `robotics-safety-standards-and-deployment`'s real-time practice, and §12 → `robotics-safety-standards-and-deployment`'s testing discipline do not
move.** What follows is what does.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **ROS 2 releases** | **One release each 23 May. Even years = LTS, 5 years support; odd years = 18 months.** **Lyrical Luth (May 2026, Ubuntu 26.04)** is current — Patch Release 2 on 2026/08/07. **Kilted Kaiju (May 2025)** supported to ~Nov/Dec 2026. **Jazzy Jalisco (May 2024, Ubuntu 24.04)** the production LTS, to 2029. **Humble** still patched (PR14, Feb 2026). **ROS 1 support ended May 2025** | Medium |
| **ROS 2 middleware** | ⚠️ **Kilted was the first release with Eclipse Zenoh as Tier 1 middleware** (Zenoh 1.0), expected **more efficient and secure than DDS**, particularly for universities and complex network environments. Options: Fast DDS (default; **`fastrtps` renamed `fastdds`**), Cyclone DDS, RTI Connext (7.3.0; ⚠️ **Connext Micro RMW deprecated in Kilted, removal planned**). Kilted also brought OpenCV 4.12 native support, rosbag2 recorder/player as rclcpp components, and **`ament_target_dependencies()` deprecation**. Recommended Gazebo for Kilted: **Ionic** | Medium |
| **⚠️ ISO 10218:2025** | **Parts 1 and 2 published Feb 2025, in force 1 April 2025** — first revision since 2011, ~8 years of work across 20+ countries. ⚠️ **ISO/TS 15066 absorbed into Part 2 — no standalone cobot standard.** ⚠️ **The terms "collaborative robot" and "collaborative operation" removed — collaboration is a property of the application, not the robot.** Added: **explicit functional safety**, **robot classification (Class I/II)**, ⚠️ **cybersecurity requirements**, EOAT and manual load/unload guidance. **Part 2 nearly tripled in length.** Adopted as **ANSI/A3 R15.06-2025** and CSA Z434 | Low |
| **Enforceability** | ISO standards voluntary in themselves; binding via contract and harmonisation. ⚠️ **EU Machinery Regulation 2023/1230 applies from 20 January 2027.** US pressure via OSHA penalties | Medium |
| **⚠️ Humanoid standards gap** | The 2025 revision **explicitly leaves gaps on AI, humanoids, and mobile manipulation.** **ISO 25785-1 under development for dynamically stable robots.** Humanoid-specific hazards — fall zones, dynamic balance, energy-dense hot-swap batteries — **not covered by arm-derived contact-force models** | **High** |
| **⚠️ VLA frontier** | **π₀ / π₀.₅ / π₀.₇** (Physical Intelligence; π₀.₅ targets open-world generalization). **Gemini Robotics / 1.5** (DeepMind) — "thinking before acting," embodied reasoning, **motion transfer**; on-device variant adapts with **50–100 demonstrations**, trained primarily on ALOHA and adapted to bi-arm Franka FR3 and Apptronik Apollo; **trusted-tester availability, not general release**. **GR00T N-series** (NVIDIA) — ⚠️ **dual-system: VLM System 2 + diffusion-transformer System 1 at 120Hz, jointly trained**; **N1.7 at General Availability, Apache 2.0**, Cosmos-Reason2-2B/Qwen3-VL backbone; adopters include AeiRobot, Foxlink, NEURA, Lightwheel. **Helix** (Figure) uses a 7B VLM hierarchically | **High** |
| **VLA architecture constraint** | ⚠️ **π₀ and GR00T N1 both ~2B-parameter backbones — small models required for on-device inference and real-time latency.** Hierarchical designs run a larger VLM at lower frequency. Cloud-hosted (Gemini Robotics) trades latency and connectivity | **High** |
| **Data and world models** | **Open X-Embodiment / RT-X** and **DROID** the reference cross-embodiment datasets. **NVIDIA Cosmos** generates synthetic trajectories (GR00T-Dreams blueprint: vast trajectory data **from a single image and language instruction**). **World-action models** — pretrain to imagine, fine-tune to act — an active 2026 direction. Open models: OpenVLA, RDT-1B, X-VLA, **LingBot-VLA (Ant Group, 20K hours real dual-arm data, open-sourced)**, Xiaomi-Robotics-0 | **High** |

**Goes stale fastest:** §8 → `robotics-learning-simulation-and-fleets` and §17's VLA rows — assume monthly movement. **Essentially
never stale:** §3.4 → `robotics-stack-ros2-and-perception`, §4 → `robotics-stack-ros2-and-perception`, §5 → `robotics-planning-control-and-manipulation`, §6 → `robotics-planning-control-and-manipulation`, §7 → `robotics-planning-control-and-manipulation`, §11 → `robotics-safety-standards-and-deployment`, §12 → `robotics-safety-standards-and-deployment`, §15.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Thrun, Burgard & Fox** | ***Probabilistic Robotics*** | ⚠️ **The foundational text for §4 → `robotics-stack-ros2-and-perception`.** Still unmatched |
| **Siciliano & Khatib (eds.)** | *Springer Handbook of Robotics* | The comprehensive reference |
| **Lynch & Park** | ***Modern Robotics*** | ⚠️ **Free PDF, excellent companion course. The best modern kinematics/dynamics text** |
| **LaValle** | ***Planning Algorithms*** | Free online. §5 → `robotics-planning-control-and-manipulation`, definitively |
| **Corke** | *Robotics, Vision and Control* | Practical, MATLAB/Python, very readable |
| **Siciliano et al.** | *Robotics: Modelling, Planning and Control* | The standard graduate text |
| **Åström & Murray** | ***Feedback Systems*** | Free. ⚠️ **The best control-theory introduction for engineers** |
| **Rawlings, Mayne & Diehl** | *Model Predictive Control* | §6 → `robotics-planning-control-and-manipulation`'s MPC, rigorously |
| **Sutton & Barto** | *Reinforcement Learning* | Free. The foundation for §8 → `robotics-learning-simulation-and-fleets` |
| **Barfoot** | *State Estimation for Robotics* | Free. Modern, factor-graph-oriented |
| **Kirk** | *The Reasoned Schemer*-adjacent — no; **Nancy Leveson**, *Engineering a Safer World* | ⚠️ **The best book on system safety thinking, and it reframes §13 → `robotics-safety-standards-and-deployment`** |

### 18.2 Primary sources and tooling
**ROS 2 documentation and REPs** (⚠️ **REP-103 on units and conventions is the one to read
before your first transform bug**), **Nav2** and **MoveIt 2** docs, **OMPL**, **Drake**,
**MuJoCo**, **Isaac Lab**, **GTSAM** and **Ceres**, **PX4/ArduPilot**, **NASA cFS** and
the **JPL Power of 10 rules**, **ISO/A3** for the standards themselves (⚠️ **buy the
standard; do not work from summaries, including this one**), **Open X-Embodiment** and
**LeRobot** (HuggingFace's robotics stack).

**Conferences worth tracking**: **ICRA**, **IROS**, **RSS**, **CoRL** (⚠️ **CoRL is where
the learning-side work lands first**), **Humanoids**, **ROSCon**.

### 18.3 People and groups
**Sebastian Thrun**, **Dieter Fox**, **Pieter Abbeel**, **Sergey Levine** and **Chelsea
Finn** (⚠️ **the learning side; Physical Intelligence's π-series**), **Russ Tedrake**
(⚠️ **MIT/TRI — *Underactuated Robotics* is a superb free course, and he is unusually
candid about what learning does and doesn't solve**), **Marc Raibert** (Boston Dynamics,
now the Boston Dynamics AI Institute), **Aaron Ames** (formal safety, control barrier
functions), **Nancy Leveson** (system safety, STPA), **Steve LaValle**, **Frank Dellaert**
(factor graphs, GTSAM), **Nathan Ratliff** and **Jim Mainprice** (optimization-based
planning), **Open Robotics / OSRF** and **Tully Foote** (ROS), **Brian Gerkey**.

---

## §19. Quick Reference

### 19.1 Picking the tool
| Need | Use |
|---|---|
| Middleware for a new production robot | **ROS 2 Jazzy (LTS)**; Zenoh or Cyclone DDS (§2 → `robotics-stack-ros2-and-perception`) |
| Hard real-time control loop | ⚠️ **Not ROS. PREEMPT_RT or an RTOS, isolated core** (§11 → `robotics-safety-standards-and-deployment`) |
| Navigation stack | Nav2 (§5 → `robotics-planning-control-and-manipulation`) |
| Arm motion planning | MoveIt 2 + OMPL (§5 → `robotics-planning-control-and-manipulation`) |
| Trajectory optimization | Drake, iLQR, or a QP-based MPC (§6 → `robotics-planning-control-and-manipulation`) |
| Contact-rich control | Impedance/admittance control (§6 → `robotics-planning-control-and-manipulation`) |
| Legged locomotion | MPC + whole-body control, or RL trained in Isaac Lab (§6 → `robotics-planning-control-and-manipulation`, §8 → `robotics-learning-simulation-and-fleets`) |
| SLAM, LiDAR | FAST-LIO2 / KISS-ICP (§4 → `robotics-stack-ros2-and-perception`) |
| SLAM, visual-inertial | VINS-Fusion / ORB-SLAM3 (§4 → `robotics-stack-ros2-and-perception`) |
| Pose graph back-end | GTSAM or Ceres (§4 → `robotics-stack-ros2-and-perception`) |
| RL training at scale | Isaac Lab (§9 → `robotics-learning-simulation-and-fleets`) |
| Contact-accurate research sim | MuJoCo or Drake (§9 → `robotics-learning-simulation-and-fleets`) |
| Manipulation policy from demos | Diffusion policy; or fine-tune a VLA (§8 → `robotics-learning-simulation-and-fleets`) |
| Generalist manipulation baseline | GR00T N1.7 (Apache 2.0) or OpenVLA (§8 → `robotics-learning-simulation-and-fleets`) |
| Log inspection and visualization | Foxglove (§12 → `robotics-safety-standards-and-deployment`) |
| Fleet interop | Open-RMF (§10 → `robotics-learning-simulation-and-fleets`) |

### 19.2 When the robot misbehaves
1. **Check the transform tree.** Frames right? (§3.4 → `robotics-stack-ros2-and-perception`)
2. **Check timestamps and clock sync.** (§3.4 → `robotics-stack-ros2-and-perception`)
3. **Check end-to-end latency** and its jitter. (§6.2 → `robotics-planning-control-and-manipulation`)
4. **Check QoS** — is the topic actually connected? (§2.3 → `robotics-stack-ros2-and-perception`)
5. **Visualize the perception output.** Does it see what you think? (§12 → `robotics-safety-standards-and-deployment`)
6. **Replay the bag** with the suspect layer isolated. (§12 → `robotics-safety-standards-and-deployment`)
7. **Check for saturation and windup** in the controller. (§6.2 → `robotics-planning-control-and-manipulation`)
8. **Then** consider the algorithm.

### 19.3 Facts worth holding
- **Control 100Hz–10kHz; estimation 50–500Hz; perception 10–60Hz; planning 1–10Hz.**
- **Sample at 10–20× your control bandwidth.**
- ⚠️ **Jitter is worse than latency.**
- **REP-103: x-forward, y-left, z-up.** ROS quaternions are **(x,y,z,w)**.
- **ISO/TS 15066 no longer stands alone** — it's inside ISO 10218-2:2025.
- ⚠️ **"Collaborative" describes the application, not the robot.**
- **EU Machinery Regulation 2023/1230 applies 20 January 2027.**
- **GR00T: System 2 VLM plans, System 1 diffusion transformer acts at 120Hz.**
- **VLA backbones ~2B parameters** — latency, not capability, sets the ceiling.

---

## §20. Sources and Method

**Method.** Narrative review, written for engineers building robots with real physical
consequences, and deliberately distinct from a hobbyist-kit reference. **§4–§7 → `robotics-stack-ros2-and-perception`, `robotics-planning-control-and-manipulation`'s theory
(estimation, planning, control, kinematics), §11 → `robotics-safety-standards-and-deployment`'s real-time practice, and §12 → `robotics-safety-standards-and-deployment`'s testing
and debugging discipline are decades stable** and rest on the standard literature — Thrun/
Burgard/Fox, LaValle, Lynch & Park, Åström & Murray, Rawlings — rather than on anything
searched; they were not web-verified because they do not need to be. Four targeted searches
were run in **August 2026** on the parts that move: the ROS 2 release state, the
vision-language-action frontier, and the safety-standards regime.

**Search log** (August 2026): ROS 2 distributions, Kilted/Lyrical, Zenoh and DDS ·
vision-language-action and robot foundation models (π-series, Gemini Robotics, GR00T) ·
ISO 10218:2025 revision, ISO/TS 15066 absorption, and humanoid safety standards.

**Primary and near-primary sources consulted (selected):**
- **Open Robotics' own release announcements and ROS 2 documentation** for the Kilted and
  Lyrical release details, Zenoh Tier 1 status, RMW changes and deprecations; the
  **ros2/ros2 GitHub releases page** for current patch releases; **endoflife.date** and
  **LWN's** ROS overview for the support-cadence rules
- **arXiv primary papers** for the VLA lineage — **GR00T N1 (2503.14734)**, **π₀
  (2410.24164)**, **π₀.₅ (2504.16054)**, **Gemini Robotics (2503.20020)** and
  **Gemini Robotics 1.5 (2510.03342)** — plus **NVIDIA's Isaac-GR00T repository** for the
  N1.7 GA status and backbone, and NVIDIA's own technical blog on world-action models
- **A3/Automate's ISO 10218 FAQ**, **The Robot Report**, **ANSI's blog**, **TÜV Rheinland**
  and **IDEC's** analysis series for the 2025 revision's scope, the ISO/TS 15066
  absorption, the terminology change, and the cybersecurity additions; a **ScienceDirect
  comparative analysis (2026)** for the identified regulatory gaps in AI, humanoids and
  mobile manipulation

**Confidence statement.** **Very high confidence** in §3.4 → `robotics-stack-ros2-and-perception`, §4 → `robotics-stack-ros2-and-perception`, §5 → `robotics-planning-control-and-manipulation`, §6 → `robotics-planning-control-and-manipulation`, §7 → `robotics-planning-control-and-manipulation`, §11 → `robotics-safety-standards-and-deployment`, §12 → `robotics-safety-standards-and-deployment` and
§15 — control theory, estimation, and the integration failure modes are settled and
consistently reported across decades of literature and practice. **High confidence in the
ROS 2 facts** (§2 → `robotics-stack-ros2-and-perception`), which come from Open Robotics' own announcements and documentation.
**High confidence in the ISO 10218:2025 changes** (§13.1 → `robotics-safety-standards-and-deployment`) — the terminology change, the
ISO/TS 15066 absorption, the cybersecurity addition and the April 2025 in-force date are
corroborated across A3, ANSI, TÜV and multiple independent legal-technical analyses.
⚠️ **But I read summaries and analyses, not the standards themselves** — ISO standards are
paywalled, and **§18.2's advice to buy the standard rather than work from summaries
applies to this document too.** If you are building a safety case, this section is a
pointer, not a source.

⚠️ **Lower confidence, deliberately, on §8 → `robotics-learning-simulation-and-fleets` and §17's VLA rows.** Model versions, backbones,
and availability status change monthly; several capability claims (demonstration counts,
generalization results) come from **the developing labs' own papers and blog posts, which
are not disinterested and rarely include failure analysis**; and §8.3 → `robotics-learning-simulation-and-fleets`'s assessment of what
is *not* working is my synthesis of the gap between published results and reported
deployment experience rather than a measured finding. **The §16.1 argument is genuinely
unresolved and I have tried to represent both sides rather than adjudicate.** The §13.2 → `robotics-safety-standards-and-deployment`
humanoid-standards gap is corroborated by the academic comparative analysis but the
practical consequences are still being worked out in industry, and anyone deploying should
seek current professional advice rather than rely on this.
