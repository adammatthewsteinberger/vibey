---
name: robotics-stack-ros2-and-perception
description: "Use when architecting a robot stack or working on its sensing layer: the layers of a real robot stack and behaviour orchestration, ROS 2 and what it actually is — the distributions, DDS and the middleware layer, and the alternatives — perception and sensor fusion across cameras, lidar, radar and depth, the eternal time-and-transform bugs, and state estimation and SLAM. Includes the router for the whole robotics-software reference."
---

# Robotics Software: The Stack, ROS 2, Perception, and State Estimation

> **Part 1 of 5** of the *Robotics Software* reference (plugin `robotics-software`), covering §0–§4. Sibling skills: `robotics-planning-control-and-manipulation` (§5–§7), `robotics-learning-simulation-and-fleets` (§8–§10), `robotics-safety-standards-and-deployment` (§11–§14), `robotics-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    is not a bad algorithm; it's a transform published 40ms late** (§3.4, §12 → `robotics-safety-standards-and-deployment`).
> 3. **The field is in the middle of a genuine methodological argument** between
>    classical model-based robotics and learned end-to-end policies (§8 → `robotics-learning-simulation-and-fleets`, §16.1 → `robotics-reference`).
>    **Neither side has won, production systems are overwhelmingly hybrid, and anyone
>    telling you the argument is settled is selling something.**

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| The overall stack architecture | §1 |
| ROS 2, middleware, and alternatives | §2 |
| Perception and sensors | §3 |
| State estimation, SLAM, localization | §4 |
| Motion planning | §5 → `robotics-planning-control-and-manipulation` |
| **Control — PID through whole-body** | **§6 → `robotics-planning-control-and-manipulation`** |
| Manipulation and grasping | §7 → `robotics-planning-control-and-manipulation` |
| **Learning: RL, imitation, and VLA models** | **§8 → `robotics-learning-simulation-and-fleets`** |
| Simulation and sim-to-real | §9 → `robotics-learning-simulation-and-fleets` |
| Multi-robot and fleets | §10 → `robotics-learning-simulation-and-fleets` |
| Real-time and safety-critical engineering | §11 → `robotics-safety-standards-and-deployment` |
| Testing, debugging, field deployment | §12 → `robotics-safety-standards-and-deployment` |
| **Functional safety and standards** | **§13 → `robotics-safety-standards-and-deployment`** |
| Aerospace flight software | §14 → `robotics-safety-standards-and-deployment` |
| "Don't do this" | §15 → `robotics-reference` |
| "Which side is right?" | §16 → `robotics-reference` |
| "Is this still current?" | §17 → `robotics-reference` |
| Books, courses, people | §18 → `robotics-reference` |

---

## §1. The Stack

**[DURABLE] Every serious robot stack has these layers, whatever the vendor calls them:**

```
   MISSION / TASK PLANNING     what should the robot accomplish?      (§1.2)
            ↓
   BEHAVIOUR / EXECUTIVE        behaviour trees, state machines       (§1.2)
            ↓
   MOTION PLANNING              collision-free trajectories           (§5)
            ↓
   CONTROL                      track the trajectory. 100Hz–10kHz     (§6)
            ↓
   HARDWARE ABSTRACTION         drivers, EtherCAT, CAN, actuators
   ─────────────────────────────────────────────────────────────
   PERCEPTION → STATE ESTIMATION feeds every layer above       (§3, §4)
   ─────────────────────────────────────────────────────────────
   SAFETY LAYER                 ⚠️ independent, often separate silicon (§13)
```

**[DURABLE] The rate hierarchy is the thing to internalize**, because it dictates
architecture: **control loops run at 100Hz–10kHz with hard deadlines; state estimation at
50–500Hz; perception at 10–60Hz; planning at 1–10Hz; mission planning whenever.**
⚠️ **The layers must be decoupled such that a slow planner cannot stall a fast controller** —
that decoupling is the single most important structural decision in the stack.

### 1.2 Behaviour orchestration
**Finite state machines** — explicit, verifiable, ⚠️ **and they explode combinatorially**
as behaviours multiply. **Behaviour trees** — ⚠️ **the modern default**, because they're
modular, reactive, and composable; `BehaviorTree.CPP` and Nav2's BT navigator are the
common implementations. **Task and motion planning (TAMP)** integrates symbolic planning
with geometric feasibility. **⚠️ LLM/VLM-driven task planning** is the newest layer (§8.2 → `robotics-learning-simulation-and-fleets`)
and the least mature.

**[DURABLE] Whatever you use, the requirement is the same: at any moment you must be able
to say what the robot is doing and why, and you must be able to stop it.**

---

## §2. ROS 2 and Middleware

### 2.1 What ROS actually is

**[DURABLE] Despite the name, ROS is not an operating system** — it's an SDK plus a
middleware plus a package ecosystem. **The value was never the message passing; it's that
thousands of drivers, algorithms, and tools speak the same interfaces.**

**⚠️ The ROS 1 → ROS 2 change that matters**: ROS 1 had a **central `rosmaster`** — a
single point of failure with custom TCP/UDP transports, no security, and no real-time
guarantees. **ROS 2 has no master**; discovery is distributed via **DDS**, the
publish-subscribe standard used in aerospace and defence. **ROS 1 support ended May 2025.
New work is ROS 2, without qualification.**

### 2.2 [VERSIONED] The distributions

**Release cadence: one release every year on 23 May.** **Even years are LTS with five
years of support; odd years get 18 months.** Each release targets exactly one Ubuntu LTS.

| Distro | Status |
|---|---|
| **Lyrical Luth** (May 2026) | ⚠️ **Current release**, on Ubuntu 26.04. Patch releases through 2026 |
| **Kilted Kaiju** (May 2025) | Supported to **~Nov/Dec 2026**. First release with **Zenoh as Tier 1 middleware** |
| **Jazzy Jalisco** (May 2024) | ⚠️ **The LTS most production systems are on** — supported to 2029, Ubuntu 24.04 |
| **Humble Hawksbill** (2022) | Still patched (Patch Release 14, Feb 2026); Ubuntu 22.04 |

**[DURABLE] For production, target the LTS.** Jazzy today; the next LTS lands May 2028.

### 2.3 The middleware layer

**RMW implementations** are pluggable: **Fast DDS** (default; ⚠️ **note `fastrtps` was
renamed `fastdds` in Kilted**), **Cyclone DDS** (⚠️ **widely preferred for reliability and
simplicity**), **RTI Connext** (commercial, aerospace/defence pedigree, safety-certified
variants), and **Zenoh** — ⚠️ **a genuine shift: Tier 1 from Kilted, expected to be more
efficient and more secure than DDS, and notably better across complex network
environments** where DDS multicast discovery struggles.

> **⚠️ GOTCHA — the ROS 2 problems that bite in production:**
> - **DDS discovery on large networks.** ⚠️ **Multicast discovery floods, and it's the
>   most common "why is my robot fleet slow" cause.** Use discovery servers, or Zenoh.
> - **QoS profile mismatches.** ⚠️ **Publisher and subscriber with incompatible QoS
>   silently don't connect** — no error, just no data. Check `ros2 topic info -v` first.
> - **Executor behaviour.** The default single-threaded executor gives you unpredictable
>   callback scheduling. **For anything timing-sensitive, use multi-threaded or
>   real-time executors and set thread priorities deliberately.**
> - **ROS 2 is not real-time by itself.** §11 → `robotics-safety-standards-and-deployment`.
> - **Serialization cost.** Use intra-process communication and zero-copy for
>   high-bandwidth topics (camera, point cloud) or you'll burn CPU on copies.
> - **`ament_target_dependencies()` is deprecated** in favour of modern CMake targets.

### 2.4 The rest of the ecosystem and the alternatives
**Nav2** (navigation), **MoveIt 2** (manipulation planning), **ros2_control** (hardware
abstraction and controller lifecycle), **tf2** (⚠️ **coordinate transforms — see §3.4**),
**rviz2**, **Foxglove** (⚠️ **the better visualization and log-inspection tool for
serious work**), **rosbag2**, **micro-ROS** (microcontrollers).

**⚠️ Not everyone uses ROS, and the reasons are legitimate.** Boston Dynamics, most
autonomous-vehicle stacks, and aerospace flight software use bespoke internal frameworks —
because they need certified real-time behaviour, tighter control over scheduling and
memory, or a safety case ROS can't currently support. **The alternatives worth knowing**:
**LCM**, **Zenoh standalone**, **eProsima/DDS directly**, **Cyphal/UAVCAN** (⚠️ **the
standard for drone and spacecraft component buses**), and **PX4/ArduPilot** for
flight control.

---

## §3. Perception

**[DURABLE] Sensor modalities and their honest failure modes** — and the failure modes
matter more than the specs:

| Sensor | Gives you | ⚠️ Fails at |
|---|---|---|
| **Camera (mono)** | Rich semantics, cheap | No metric scale; ⚠️ **motion blur, low light, direct sun, glass** |
| **Stereo** | Depth by disparity | ⚠️ **Textureless surfaces — a blank wall has no disparity** |
| **RGB-D** (structured light / ToF) | Dense depth, short range | ⚠️ **Sunlight destroys structured light**; multipath on ToF |
| **LiDAR** | Precise 3D geometry | ⚠️ **Rain, fog, dust, and retroreflectors**; sparse at range; expensive |
| **Radar** | Velocity directly (Doppler), all-weather | Low angular resolution; ⚠️ **multipath and ghost targets** |
| **IMU** | High-rate acceleration and angular rate | ⚠️ **Drifts. Always. It is a relative sensor** (§4) |
| **Wheel odometry** | Cheap relative motion | ⚠️ **Slip makes it lie confidently** |
| **F/T sensors** | Contact forces | Drift, temperature sensitivity |
| **GNSS/RTK** | Global position | ⚠️ **Urban canyon, indoors, multipath, jamming/spoofing** |

**[DURABLE] The design principle: every sensor fails in a specific, knowable way, and
good perception is chosen so that the failure modes don't correlate.** Camera + LiDAR is a
strong pairing because sun blinds one and rain degrades the other. **Two cameras is not
redundancy.**

**The processing stack**: detection and segmentation (⚠️ **now overwhelmingly learned, and
the practical constraint is latency at the edge**), 3D detection over point clouds,
tracking (Kalman/particle filters plus data association — ⚠️ **association is the hard
part, not filtering**), and increasingly **BEV (bird's-eye-view) fusion** and
**occupancy networks** as the AV-derived approach to multi-sensor fusion.

### 3.4 ⚠️ Time and transforms — the two eternal bugs

> **⚠️ GOTCHA — these two cause more robotics bugs than every algorithm combined.**
>
> **Coordinate frames.** Every measurement is in *some* frame. **`map` → `odom` → `base_link`
> → `sensor`** is the ROS convention, and **⚠️ mixing them up produces plausible, wrong
> behaviour rather than an error.** Use tf2 rigorously; **never hand-compose transforms**;
> and know your conventions — ⚠️ **REP-103 says x-forward, y-left, z-up, and quaternions
> are (x,y,z,w) in ROS and (w,x,y,z) in several libraries.** That one has cost the field
> thousands of hours.
>
> **Timestamps.** ⚠️ **Sensor data is always stale by the time you use it.** Every message
> must carry the time the measurement was *taken*, not published. Clocks across devices
> must be synchronized (**PTP** where it matters, NTP otherwise), and **latency must be
> budgeted end to end** — sensor → driver → processing → planning → control → actuator.
> **A control loop acting on 200ms-old state is a control loop with 200ms of dead time,
> and dead time destabilizes controllers** (§6 → `robotics-planning-control-and-manipulation`).

---

## §4. State Estimation and SLAM

**[DURABLE] The core insight of the whole field: you never know where you are; you have a
probability distribution over where you might be.** Engineering that distribution well
*is* state estimation.

**The filter family**: **Kalman filter** (optimal for linear-Gaussian), **EKF**
(linearize; ⚠️ **diverges when the linearization is poor**), **UKF** (sigma points,
better for strong nonlinearity), **particle filter** (arbitrary distributions,
⚠️ **suffers particle depletion**; the basis of AMCL), and **factor graphs / pose graph
optimization** — ⚠️ **which is what modern SLAM actually uses**, via GTSAM, g2o, or Ceres.

**[DURABLE] The move from filtering to smoothing (factor graphs) is one of the genuine
methodological advances of the last two decades**: keeping and re-optimizing a window of
history beats propagating a single mean and covariance forward.

**SLAM in practice**: **visual** (ORB-SLAM3, and the classic), **visual-inertial**
(VINS-Fusion, OKVIS — ⚠️ **IMU + camera is strongly complementary: the IMU covers fast
motion and the camera bounds drift**), **LiDAR** (LOAM family, FAST-LIO2, KISS-ICP),
**LIO** (LiDAR-inertial), and increasingly **learned front-ends with classical back-ends**.

**⚠️ The problems that actually bite**: **loop closure** (recognizing you've been here
before — and ⚠️ **a false positive corrupts the whole map**), **the kidnapped robot
problem**, **long-term map maintenance in changing environments** (⚠️ **the underrated
one: your warehouse map is wrong the moment someone moves a pallet**), **degenerate
geometry** (a long featureless corridor is unobservable along its axis), and
**scale drift** in monocular systems.
