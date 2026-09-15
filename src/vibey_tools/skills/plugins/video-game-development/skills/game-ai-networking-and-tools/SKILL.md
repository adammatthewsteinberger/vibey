---
name: game-ai-networking-and-tools
description: "Use when building gameplay AI, multiplayer, or the content pipeline: the decision-making toolbox (FSMs, utility AI, GOAP), pathfinding (navmesh, A*, flow fields), making AI feel right, the networking models (peer-to-peer, client-server, lockstep), client-server done properly (authoritative server, prediction, reconciliation, lag compensation, interest management), rollback netcode specifics, and tools and the content pipeline."
---

# Game Development: Gameplay AI, Networking, and Tools and Pipeline

> **Part 3 of 5** of the *Video Game Development* reference (plugin `video-game-development`), covering §8–§10. Sibling skills: `game-engines-loop-and-architecture` (§0–§3), `game-rendering-physics-animation-and-audio` (§4–§7), `game-performance-feel-and-shipping` (§11–§15), `game-development-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `game-development-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — real-time systems reality, human perception, or a lesson the industry
>   has relearned every console generation. Does not expire.
> - **[VERSIONED]** — specific to an engine version, API, platform, or market condition.
>   Verify before relying on it.
> - **[CONTESTED]** — practitioners genuinely disagree, usually because the right answer
>   depends on team size and genre.
>
> **⚠️ GOTCHA** boxes mark the mistakes that ship broken games, blow the frame budget, or
> destroy a studio's schedule.
>
> **The three framings that organize everything below:**
> 1. **A game is a soft-real-time simulation with a hard deadline, 60 times a second.**
>    16.67 ms at 60 fps, 8.33 ms at 120. Everything — rendering, physics, AI, audio,
>    networking, streaming, GC — shares that budget. **Consistency beats peak framerate**;
>    a stable 30 feels better than a 60 that stutters.
> 2. **Games are content pipelines with a game attached.** On any team above about five
>    people, the tools, build system, and iteration loop determine your output more than
>    your engine code does. Ten-minute iteration times will cost you the game.
> 3. **Scope is the thing that kills projects, not technology.** The overwhelming majority
>    of unfinished games died of ambition, not of a hard technical problem. §14 → `game-performance-feel-and-shipping` is the
>    section most people need and skip.

---

## §8. Gameplay AI

**[DURABLE] Game AI is not machine learning; it is the craft of producing believable,
readable, *beatable* behaviour.** The goal is a good opponent from the player's
perspective, not an optimal agent. **An AI that is too good is a design failure.**

### 8.1 The decision-making toolbox

| Technique | Use |
|---|---|
| **Finite state machine** | Simple agents. Readable, debuggable, and it explodes combinatorially past ~10 states |
| **Hierarchical FSM** | Nested states — a real improvement for character control |
| **Behaviour tree** | **The industry default.** Composable, designer-authorable, good tooling in every engine |
| **Utility AI** | Score each option, pick the best. Excellent for sims and many-option agents (*The Sims*) |
| **GOAP** (goal-oriented action planning) | Plans a sequence of actions to reach a goal. *F.E.A.R.*'s famous squad AI |
| **HTN planning** | Hierarchical task networks. *Horizon Zero Dawn*, *Transformers* |
| **Steering behaviours** | Seek, flee, arrive, separate, flock (Reynolds' boids) — the movement layer beneath everything |

### 8.2 Pathfinding

**A\*** on a navmesh (or grid) is still the answer. **Navmesh generation** (Recast is the
open-source standard, and is what most engines use or imitate). Then the practical layer:
**hierarchical pathfinding** for large maps, **string pulling / funnel algorithm** to
smooth the path off the mesh polygon centers, **local avoidance** (RVO/ORCA) so agents
don't collide, **path caching and request budgeting** (⚠️ don't path 500 agents in one
frame — amortize across frames), and **flow fields** when many agents share a destination
(the standard RTS answer).

### 8.3 Making AI *feel* right

**[DURABLE] The techniques that make AI good are mostly about legibility, not
intelligence:** telegraphed attacks with wind-up frames; **deliberately imperfect
accuracy** (and the near-universal "first shot always misses" rule); **reaction delays**
so the player can respond; **barks and animation that externalize internal state** so the
player can read what the AI is doing; **attack tokens** so only one or two enemies engage
at a time regardless of how many are present; and **cheating in the player's favour**
(hidden last-hit-point buffers, ammo drops when low). *F.E.A.R.*'s AI is remembered as
brilliant largely because the agents **announce their plans out loud**.

---

## §9. Networking

**[DURABLE] Multiplayer is not a feature you add. It is an architectural decision made on
day one**, and retrofitting it onto a single-player codebase is one of the most reliable
ways to destroy a schedule.

### 9.1 The models

| Model | How | Trade-off |
|---|---|---|
| **Lockstep / deterministic** | Send only inputs; every peer simulates identically | Tiny bandwidth, scales to thousands of units (RTS). **Requires perfect determinism (§2.2 → `game-engines-loop-and-architecture`)**; one desync ruins the match; latency = worst player |
| **Client-server, authoritative** | Server simulates; clients send input and render state | **The standard for action games.** Cheat-resistant. Costs server infrastructure |
| **Peer-to-peer** | Direct connections | No server cost; NAT traversal pain, and trivially cheatable |
| **Rollback** | Predict remote inputs, roll back and re-simulate on mismatch | **The fighting-game standard (GGPO).** Superb feel; demands determinism and cheap re-simulation |

### 9.2 Client-server, done properly

The canonical stack — from the Quake/Source lineage and still correct:
1. **Client-side prediction** — apply your own input immediately, don't wait for the
   server round trip.
2. **Server reconciliation** — server sends authoritative state with the last-processed
   input sequence number; client rewinds and replays unacknowledged inputs.
3. **Entity interpolation** — render other players slightly in the past (~100 ms) to
   smooth their motion.
4. **Lag compensation** — the server rewinds other players to where the shooter *saw* them
   when validating a hit.

> **⚠️ GOTCHA — lag compensation is a design decision, not a technical one.** It makes
> shooting feel right for the shooter and produces the "I got shot behind cover"
> experience for the target. **You are choosing whose experience to privilege**, and every
> shooter makes that call explicitly. There is no setting that satisfies both.

**Also**: **snapshot delta compression** and **interest management / relevancy** (don't
send what the client can't see) are what make bandwidth tractable; **UDP with your own
reliability layer** for game traffic (TCP head-of-line blocking is fatal), with TCP or
HTTPS for lobby, matchmaking, and commerce.

**⚠️ Never trust the client.** Validate movement, rate-limit actions, keep the inventory
and economy server-side. Anti-cheat is an arms race with real anti-cheat middleware
(EAC, BattlEye), and kernel-level anti-cheat is itself contested for privacy and stability
reasons.

### 9.3 Rollback specifics

Rollback needs: full deterministic simulation, cheap **save/restore of game state**
(usually a compact struct you can memcpy), simulation fast enough to run **7–10 frames of
re-simulation inside one frame's budget**, and input delay tuning. It's the reason modern
fighting games feel dramatically better online than the delay-based generation did — and
it's essentially impossible to bolt onto a game whose state lives scattered across engine
objects.

---

## §10. Tools and Pipeline

**[DURABLE] On any team past a few people, tools and iteration time determine your output
more than your engine choice does.** This is the most consistently under-invested area in
game development.

- **Iteration time is the metric that matters.** From "change a value" to "see it in the
  game": target **seconds**. A 10-minute rebuild-and-reload loop doesn't slow you by
  10 minutes — it eliminates the experimentation that finds the fun.
- **Hot reload** for scripts, shaders, and assets. Worth building.
- **Asset pipeline**: source assets (`.psd`, `.blend`, `.wav`) → **deterministic,
  cacheable import** → platform-optimized runtime format. **Never ship source formats.**
- **Content authoring in data, not code**, so designers can work without programmers and
  without a rebuild.
- **In-game debug tooling**: console, cheat commands, free camera, state visualizers,
  hitbox and navmesh overlays, AI state readouts, performance HUD. **Build these early;
  they pay for themselves within weeks.**
- **Version control**: **Perforce** remains the industry standard for large binary assets;
  **Git with LFS** works for smaller projects. ⚠️ Git handles large binaries badly and
  cannot lock files, which matters enormously when two artists edit the same `.uasset`.
- **Build system and CI**: automated builds per commit, on every target platform, with
  automated smoke tests. **A broken build blocks the whole team.**
