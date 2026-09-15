---
name: robotics-planning-control-and-manipulation
description: "Use when making the robot move: motion planning with sampling-based planners, trajectory optimization and collision checking; control from PID through LQR, MPC and whole-body control and what actually matters in practice rather than in theory; and manipulation — grasping, force control, and compliant behaviour."
---

# Robotics Software: Motion Planning, Control, and Manipulation

> **Part 2 of 5** of the *Robotics Software* reference (plugin `robotics-software`), covering §5–§7. Sibling skills: `robotics-stack-ros2-and-perception` (§0–§4), `robotics-learning-simulation-and-fleets` (§8–§10), `robotics-safety-standards-and-deployment` (§11–§14), `robotics-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    the simulation, the safety cases (§11 → `robotics-safety-standards-and-deployment`, §13 → `robotics-safety-standards-and-deployment`).
> 2. **⚠️ Robotics is an integration discipline, and the integration is where it fails.**
>    Perception, estimation, planning, and control each work in isolation and break at
>    the seams — timing, coordinate frames, latency, and units. **The classic robotics bug
>    is not a bad algorithm; it's a transform published 40ms late** (§3.4 → `robotics-stack-ros2-and-perception`, §12 → `robotics-safety-standards-and-deployment`).
> 3. **The field is in the middle of a genuine methodological argument** between
>    classical model-based robotics and learned end-to-end policies (§8 → `robotics-learning-simulation-and-fleets`, §16.1 → `robotics-reference`).
>    **Neither side has won, production systems are overwhelmingly hybrid, and anyone
>    telling you the argument is settled is selling something.**

---

## §5. Motion Planning

**[DURABLE] The configuration-space framing**: planning happens in the space of robot
configurations, not in the workspace, and obstacles map into C-space as forbidden regions.
**Dimensionality is the enemy** — a 7-DOF arm plans in 7 dimensions.

| Family | Notes |
|---|---|
| **Grid/graph search** — A\*, D\* Lite, hybrid A\* | ⚠️ **Optimal and complete in the discretization**; the standard for ground vehicles. Hybrid A\* handles nonholonomic constraints |
| **Sampling-based** — RRT, RRT\*, PRM, BIT\*, informed RRT\* | ⚠️ **Probabilistically complete, scales to high DOF, non-deterministic.** The default for arms (OMPL) |
| **Optimization-based** — CHOMP, STOMP, TrajOpt | Smooth trajectories, ⚠️ **local minima** |
| **Reactive** — DWA, TEB, potential fields, VO/ORCA | Fast local avoidance. ⚠️ **Potential fields have local minima and everyone rediscovers this** |
| **Learned** | §8 → `robotics-learning-simulation-and-fleets` |

**[DURABLE] The distinction that structures every navigation stack**: a **global planner**
(slow, complete, over a known map) and a **local planner/controller** (fast, reactive,
over live sensor data). **Nav2's architecture is this made explicit.**

**⚠️ The constraints that make real planning hard**: **kinodynamic limits** (a car can't
move sideways; an arm has torque limits), **differential constraints**, **time-varying
obstacles**, ⚠️ **planning under uncertainty** — the plan must be robust to the fact that
§4 → `robotics-stack-ros2-and-perception`'s estimate is wrong — and **replanning latency**, because a plan computed for where you
were is worthless.

---

## §6. Control

**[DURABLE] The most durable body of theory in this document. None of it has changed in
decades and none of it will.**

### 6.1 The ladder

| Controller | Use | ⚠️ Watch |
|---|---|---|
| **PID** | ⚠️ **Still the workhorse of industrial robotics** | Integral windup; derivative noise amplification; **needs retuning as the plant changes** |
| **Feedforward + feedback** | ⚠️ **The single biggest practical improvement over pure PID** — model what you can, correct the rest | Requires a model |
| **LQR** | Optimal for linear systems with quadratic cost | Linear assumption |
| **iLQR / DDP** | Nonlinear trajectory optimization | Local |
| **MPC** | ⚠️ **Handles constraints explicitly, and that's why it won** — the standard for AVs, legged robots, and drones | Compute cost; needs a good model and a solver that hits the deadline |
| **Impedance / admittance** | ⚠️ **Contact tasks.** Controls the *relationship* between force and motion rather than either alone | Stability at stiff contact |
| **Whole-body control** | Humanoids and legged systems — hierarchical QP over all joints subject to balance and contact constraints | Serious complexity |
| **Adaptive / robust (H∞, sliding mode)** | Uncertain or varying plants | Chatter; conservatism |
| **Learned policies** | §8 → `robotics-learning-simulation-and-fleets` | ⚠️ **No stability guarantees** |

### 6.2 What actually matters in practice

**[DURABLE] The system-level facts that dominate controller performance:**
- **⚠️ Latency and dead time destabilize.** Every millisecond between measurement and
  actuation reduces achievable bandwidth. **This is why §3.4 → `robotics-stack-ros2-and-perception` matters to §6.**
- **Jitter is worse than latency.** A consistent 5ms delay can be compensated; a delay
  varying 1–20ms cannot. ⚠️ **Determinism beats speed** (§11 → `robotics-safety-standards-and-deployment`).
- **Actuator saturation** invalidates your linear analysis, and **integral windup is what
  happens next.** Clamp it.
- **Discretization**: your continuous-time design is running at a finite rate.
  ⚠️ **Sample at least 10–20× your bandwidth of interest.**
- **Backlash, friction, and compliance** are what separate the model from the machine.
  Stiction in particular is nonlinear and nasty.
- **⚠️ Series-elastic and torque-controlled actuators changed what's possible** in legged
  and contact-rich robotics — they make force controllable rather than merely position.
- **Safety limits belong in a separate layer** that can't be argued with by the controller
  (§13 → `robotics-safety-standards-and-deployment`).

---

## §7. Manipulation

**[DURABLE] Manipulation is harder than navigation, and the reason is contact.** Free-space
motion is smooth and modellable; **contact is discontinuous, high-bandwidth, and where the
models stop working.**

**Kinematics**: forward (joint angles → pose, easy), **inverse** (pose → joint angles;
⚠️ **multiple solutions, singularities, and no closed form for many arms** — IKFast,
TRAC-IK, or numerical), **Jacobians** (velocity mapping; ⚠️ **singularities are where it
loses rank and joint velocities blow up**), and **redundancy resolution** for 7-DOF arms.

**Grasping**: analytic (force closure, wrench space) vs. **learned** (⚠️ **now dominant
for unstructured objects** — GraspNet, Contact-GraspNet, Dex-Net), and the hard cases are
**deformables, transparent and reflective objects** (⚠️ **which defeat depth sensors
outright**), and **cluttered bins**.

**⚠️ The practical reality: the last centimetre is the hard part.** Getting near the object
is solved; the final approach, contact, and force regulation is where systems fail —
which is exactly why §8 → `robotics-learning-simulation-and-fleets`'s learned policies got traction here first.
