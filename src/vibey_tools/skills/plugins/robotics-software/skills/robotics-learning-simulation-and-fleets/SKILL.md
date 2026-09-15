---
name: robotics-learning-simulation-and-fleets
description: "Use when working on the learning layer or on simulation: reinforcement learning and imitation learning, vision-language-action foundation models and an honest assessment of where they actually are, simulation and the sim-to-real gap including domain randomization, Isaac Sim, Gazebo and MuJoCo, and multi-robot systems and fleet management."
---

# Robotics Software: The Learning Layer, Simulation and Sim-to-Real, and Fleets

> **Part 3 of 5** of the *Robotics Software* reference (plugin `robotics-software`), covering §8–§10. Sibling skills: `robotics-stack-ros2-and-perception` (§0–§4), `robotics-planning-control-and-manipulation` (§5–§7), `robotics-safety-standards-and-deployment` (§11–§14), `robotics-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    classical model-based robotics and learned end-to-end policies (§8, §16.1 → `robotics-reference`).
>    **Neither side has won, production systems are overwhelmingly hybrid, and anyone
>    telling you the argument is settled is selling something.**

---

## §8. The Learning Layer

**[VERSIONED — the fastest-moving material in robotics, and the subject of §16.1 → `robotics-reference`'s genuine
argument.]**

### 8.1 The approaches

**Reinforcement learning** — ⚠️ **overwhelmingly trained in simulation** (§9), because
real-world sample complexity is prohibitive. **Massively parallel sim (Isaac Gym/Lab) made
legged locomotion RL practical** and is arguably its clearest success story.
**Imitation learning / behaviour cloning** — learn from demonstrations. ⚠️ **The
distribution-shift problem is fundamental**: the policy visits states the demonstrator
never did. **Diffusion policies** became the strong default for manipulation.
**Learning from human video** — sidesteps teleoperation cost; active research.

### 8.2 ⚠️ Vision-Language-Action models

**[VERSIONED] The development that changed the field's trajectory since 2023.** A VLA
takes a pretrained vision-language model and adapts it to output robot actions —
importing internet-scale semantic knowledge into a domain that has almost no data.

**The lineage**: **RT-1** (2022) → **RT-2** → **Open X-Embodiment / RT-X** (a
cross-institution dataset that demonstrated positive transfer *across robot embodiments* —
arguably the field's ImageNet moment) → the current frontier.

**[VERSIONED] The frontier systems as of 2026:**

| Model | Notes |
|---|---|
| **π₀ / π₀.₅ / π₀.₇** (Physical Intelligence) | Flow-matching VLA for general robot control; **π₀.₅ targets open-world generalization** |
| **Gemini Robotics / 1.5** (DeepMind) | Built on Gemini; ⚠️ **"thinking before acting" — internal natural-language reasoning before action**; 1.5 adds embodied reasoning and **motion transfer across embodiments**. An on-device variant exists for latency/connectivity-constrained settings, adapting to new tasks with **as few as 50–100 demonstrations** |
| **GR00T N-series** (NVIDIA) | Open foundation model for humanoids. ⚠️ **Dual-system architecture: System 2 is a VLM that reasons and plans; System 1 is a diffusion transformer producing smooth motor actions at 120Hz** — tightly coupled and jointly trained. **N1.7 reached General Availability (Apache 2.0)** with a Cosmos-Reason2-2B/Qwen3-VL backbone |
| **Helix** (Figure) | Hierarchical: a larger VLM at low frequency over a fast action module |
| **Open models** | OpenVLA, RDT-1B, X-VLA, LingBot-VLA (⚠️ **20K hours of real dual-arm data, fully open-sourced**), Xiaomi-Robotics-0 |

**⚠️ The architectural constraint worth understanding**: **models are small by LLM
standards — π₀ and GR00T N1 both use ~2B-parameter backbones — because on-device inference
and real-time latency demand it.** Hierarchical designs escape this by running a larger
VLM slowly over a fast local policy. **Cloud-hosted models can be bigger but inherit
network latency and a connectivity dependency**, which is a safety consideration, not just
a performance one.

**World models** are the adjacent development: **NVIDIA Cosmos** generates synthetic
trajectory data rather than acting as a policy, and **world-action models** pretrained to
predict then fine-tuned to act are an active 2026 direction.

### 8.3 ⚠️ The honest assessment

**[CONTESTED, and I'll state the disagreement rather than resolve it.]**

**What's genuinely working**: semantic generalization (⚠️ **"pick up the thing that holds
coffee" is a query classical pipelines could not answer**), long-tail object handling,
task specification in natural language, and cross-embodiment transfer.

**⚠️ What is not solved, and the gaps matter**: **no formal guarantees** — you cannot
write a safety case around a VLA's behaviour today; **evaluation is genuinely hard** and
benchmark numbers translate poorly to deployments; **reliability at the tail** is far
below what industrial deployment requires; **data remains the bottleneck** (robot data is
expensive and embodiment-specific); **latency** constrains model size; and
**failure modes are unpredictable in a way that classical stacks' are not.**

**[DURABLE] The production pattern almost everyone actually uses is hybrid**: learned
perception and high-level policy, **classical control and a classical safety layer
underneath.** ⚠️ **The safety layer is not learned.** That's not conservatism; it's the
only current way to make an argument about what the system will not do (§13 → `robotics-safety-standards-and-deployment`).

---

## §9. Simulation and Sim-to-Real

**[DURABLE] Simulation is not optional at this point** — it's where RL training, CI,
regression testing, and scenario coverage happen.

| Simulator | Position |
|---|---|
| **Isaac Sim / Isaac Lab** | ⚠️ **GPU-parallel, photorealistic, the RL training standard.** NVIDIA-coupled |
| **MuJoCo** | ⚠️ **Fast, accurate contact dynamics, now free and open.** The research default for manipulation and locomotion |
| **Gazebo** (Harmonic/Ionic) | ROS-native, general-purpose. Ionic is the recommended pairing for Kilted |
| **PyBullet** | Lightweight, accessible, widely used in research |
| **Drake** (TRI) | ⚠️ **Rigorous multibody dynamics and optimization**; strong on contact and verification |
| **CARLA / AWSIM** | Autonomous driving |
| **Genesis, Newton** | Newer generative/differentiable physics efforts |

> **⚠️ GOTCHA — the sim-to-real gap, which is the field's permanent tax.** Simulators get
> **contact, friction, deformables, and sensor noise wrong**, and those are exactly the
> things that matter. **The mitigations that work**:
> - **Domain randomization** — randomize masses, friction, latencies, textures, and
>   lighting so the policy can't overfit to sim's specifics. ⚠️ **Randomizing *latency* is
>   under-done and disproportionately valuable.**
> - **System identification** — measure your actual robot's parameters and put them in the
>   sim.
> - **Sim-to-real-to-sim** — use real rollouts to correct the simulator.
> - **⚠️ Keep a real-hardware regression suite.** Sim-only validation always eventually
>   ships something that only works in sim.

---

## §10. Multi-Robot and Fleets

**Coordination**: centralized (optimal, ⚠️ **single point of failure**) vs. decentralized
(robust, suboptimal) vs. market/auction-based task allocation. **Multi-agent path finding**
(CBS and variants) for warehouse-scale routing. **Traffic management** and deadlock
avoidance — ⚠️ **deadlock in a fleet of AMRs is a real and recurring production problem**,
not a theoretical one.

**[DURABLE] Fleet software is a distributed systems problem wearing a robotics costume** —
everything a cloud reference says about consensus, partition tolerance, idempotency and
at-least-once delivery applies, **with the added constraint that the actuators keep moving
during a partition.** ⚠️ **Design what a robot does when it loses contact with the fleet
manager, explicitly.**

**Also**: **Open-RMF** for heterogeneous fleet interop, **OTA update strategy** (⚠️ **with
staged rollout and rollback — you cannot brick a fleet**), remote operation and
teleoperation fallback, and observability across a fleet.
