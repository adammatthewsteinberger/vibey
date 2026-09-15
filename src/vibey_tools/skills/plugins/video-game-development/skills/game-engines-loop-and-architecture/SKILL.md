---
name: game-engines-loop-and-architecture
description: "Use when starting a game or structuring its code: the engine decision (Unity, Unreal, Godot, custom), licensing as an engineering risk, market reality, the game loop structure (fixed vs variable time step, interpolation) and determinism, the architecture progression, ECS and when it pays off, the patterns that earn their keep (observer, command, object pool), and separating game logic from the engine. Includes the router for the whole video-game-development reference."
---

# Game Development: Engines, the Game Loop, and Code Architecture

> **Part 1 of 5** of the *Video Game Development* reference (plugin `video-game-development`), covering §0–§3. Sibling skills: `game-rendering-physics-animation-and-audio` (§4–§7), `game-ai-networking-and-tools` (§8–§10), `game-performance-feel-and-shipping` (§11–§15), `game-development-reference` (§16–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The question router

| Asked about... | Go to |
|---|---|
| Which engine, and what it costs | §1 |
| The game loop, time step, determinism | §2 |
| Code architecture: ECS, components, objects | §3 |
| Rendering: pipelines, graphics APIs, shaders | §4 → `game-rendering-physics-animation-and-audio` |
| Physics and collision | §5 → `game-rendering-physics-animation-and-audio` |
| Animation | §6 → `game-rendering-physics-animation-and-audio` |
| Audio | §7 → `game-rendering-physics-animation-and-audio` |
| Gameplay AI and pathfinding | §8 → `game-ai-networking-and-tools` |
| Networking and multiplayer | §9 → `game-ai-networking-and-tools` |
| Tools, content pipeline, iteration | §10 → `game-ai-networking-and-tools` |
| Performance, frame budget, memory | §11 → `game-performance-feel-and-shipping` |
| Game feel, juice, input latency | §12 → `game-performance-feel-and-shipping` |
| Build, test, QA, certification | §13 → `game-performance-feel-and-shipping` |
| Production, scope, and shipping | §14 → `game-performance-feel-and-shipping` |
| Business: monetization, live ops, platforms | §15 → `game-performance-feel-and-shipping` |
| Accessibility | §16.7 → `game-development-reference` and below |
| "Don't do this" | §15.4 → `game-performance-feel-and-shipping` / §15.5 → `game-performance-feel-and-shipping` → see §15 → `game-performance-feel-and-shipping` table |
| "Which approach is better?" | §16 → `game-development-reference` (contested) |
| "Is this still current?" | §17 → `game-development-reference` |
| Books, talks, people | §18 → `game-development-reference` |

*(Anti-patterns are consolidated in the table at the end of §15 → `game-performance-feel-and-shipping`.)*

---

## §1. Engines

### 1.1 The decision

**[DURABLE] Use an existing engine.** Writing your own is justified when you have an
unusual technical requirement no engine serves, a large experienced team, or the engine
*is* the product. "I'll learn more" is a fine reason for a hobby project and a poor reason
for a commercial one.

**[VERSIONED — mid-2026 landscape.]**

| Engine | Language | Cost model | Best at |
|---|---|---|---|
| **Unreal Engine 5.x** | C++ / Blueprints | Free to **$1M lifetime gross**, then **5%** royalty | High-fidelity 3D, AAA, photoreal. **Nanite** (virtualized geometry) and **Lumen** (real-time GI) eliminate traditional LOD and light-baking work |
| **Unity 6.x** | C# | Seat-based subscription; **Personal free under $200K/yr revenue**, Pro above | Mobile (~**70% of top-grossing mobile titles**), cross-platform breadth, 2D, XR |
| **Godot 4.x** | GDScript / C# / C++ | **MIT — free forever, no royalty, no revenue threshold** | 2D (best-in-class workflow), small teams, licence-risk-averse studios |
| **GameMaker** | GML | Tiered | 2D, beginners, fast prototyping |
| **Bevy / raylib / SDL / MonoGame / LÖVE** | Rust / C / C# / Lua | Open source | Custom engines, jams, programmers who want control |
| **In-house** | — | Your salaries | ~14% of surveyed developers. Justified at scale or for a unique requirement |

### 1.2 Licensing is an engineering risk, not just a finance question

**[DURABLE, learned the hard way] Your engine licence can change under you mid-project,
and that is a real technical risk requiring a real mitigation.** The canonical case:

Unity's 2019 Terms-of-Service change (which blocked SpatialOS) prompted enough backlash
that Unity added a protective commitment — if terms changed adversely, developers could
elect to continue under the prior terms. **That clause was quietly removed on 3 April
2023**, five months before the runtime fee was announced. In September 2023 Unity
announced a **per-install runtime fee of up to $0.20**; the backlash was severe, the CEO
departed, and **new CEO Matt Bromberg cancelled it entirely in September 2024**, reverting
to seat-based subscriptions.

The consequences are still visible in 2026: measurable migration to Godot and Unreal, and
a persistent trust deficit that shows up in *new-project* engine selection more than in
existing projects.

**What to actually do about it:** read the current licence rather than the summary you
remember; **archive the version of the terms you agreed to**; keep gameplay logic
separated from engine-specific APIs where cheap (§3.4); and treat "could we port this if
we had to?" as a question with a real answer. Godot's structural pitch is precisely this —
**a nonprofit foundation and an MIT licence, so there is no pricing model that can change**.

### 1.3 Market reality

**[VERSIONED]** The numbers that matter for hiring, asset availability, and community
support as of 2026:
- **Unreal out-earned Unity on Steam for the first time since 2018** — 31% of 2024 Steam
  revenue vs. Unity's 26% (Video Game Insights) — while **Unity still ships the most games**
  (51% of 2024 Steam releases).
- **Developer mindshare has flipped**: **42% named Unreal their primary engine vs. 30% for
  Unity** (GDC State of the Game Industry 2026).
- **Godot is the fastest-growing engine by every open metric**: Steam releases grew from
  618 (2023–24) to **2,864 (2025–26), roughly 4.6×**; ~114,700 GitHub stars as of mid-2026.
- **Unity remains dominant on mobile** — roughly half of all mobile games, ~70% of the
  top-grossing.

**[DURABLE] Read those as "where the ecosystem is," not "which is better."** Asset store
depth, tutorial coverage, hireable experience, and middleware support follow market share,
and those are often worth more than a feature comparison.

---

## §2. The Game Loop

### 2.1 The structure

```
while (running) {
    processInput();
    while (accumulator >= FIXED_DT) {   // fixed-step simulation
        update(FIXED_DT);
        accumulator -= FIXED_DT;
    }
    render(accumulator / FIXED_DT);      // interpolate between sim states
}
```

**[DURABLE] "Fix Your Timestep!" (Glenn Fiedler) is the single most-referenced article in
game programming, and for good reason.** The variants and their failure modes:

| Approach | Problem |
|---|---|
| **Variable delta time everywhere** | Physics behaves differently at different framerates. Non-deterministic. **Tunneling at low fps.** Simple, and wrong for anything with physics |
| **Fixed timestep, no interpolation** | Deterministic but produces visible judder when render rate ≠ sim rate |
| **Fixed timestep + accumulator + render interpolation** | **The standard correct answer.** Deterministic sim, smooth render |
| **Semi-fixed with a max frame time clamp** | Necessary in practice — prevents the "spiral of death" |

> **⚠️ GOTCHA — the spiral of death.** If a frame takes longer than real time, the
> accumulator grows, so you run more sim steps, so the frame takes longer still. **Always
> clamp the maximum accumulated time** (e.g. never simulate more than 5 steps in one
> frame) and accept slow-motion over a freeze. Every engine that skips this eventually
> hangs on someone's machine.

### 2.2 Determinism

**[DURABLE] You need determinism for**: rollback netcode (§9.3 → `game-ai-networking-and-tools`), replays, lockstep
multiplayer, reproducible bug reports, and automated testing. It is much easier to design
in than to add later.

Requirements: **fixed timestep**, **fixed iteration order** (⚠️ hash-map iteration order is
the classic determinism bug), a **seeded, explicitly-managed RNG** (separate streams for
simulation and cosmetics), and **no floating-point divergence** across platforms — which
is the hard one, since compiler flags, `x87` vs. SSE, FMA contraction, and library
implementations of `sin`/`cos` all differ. **Fixed-point arithmetic** is the sledgehammer
answer, used by many fighting games and RTSs for exactly this reason.

---

## §3. Code Architecture

### 3.1 The progression

```
God object            → everything in one Player class. Fine for a jam
Inheritance hierarchy → GameObject → Character → Enemy → FlyingEnemy...
                        ⚠️ collapses at the "flying enemy that swims" problem
Component composition → an entity HAS a Transform, a Renderer, a Health...
                        Unity's GameObject/MonoBehaviour model
ECS (data-oriented)   → entities are IDs, components are plain data in packed arrays,
                        systems are functions over component queries
```

**[DURABLE] Composition over inheritance is the one architectural lesson the industry has
fully internalized.** Deep inheritance hierarchies for game entities fail predictably and
always for the same reason: real games need arbitrary combinations of behaviours that the
tree can't express.

### 3.2 ECS

**Why it exists**: cache locality (§11.3 → `game-performance-feel-and-shipping`), trivially parallel systems, and runtime
composition.
```
Entity 42  = just an integer ID
Components: Position[42], Velocity[42], Health[42]      ← packed contiguous arrays
System:     for each entity with (Position, Velocity): pos += vel * dt
```

**[CONTESTED] How much ECS you need.** *For*: measurable performance on entity-heavy
simulations, clean parallelism, and no inheritance tangles. *Against*: real overhead in
indirection and mental model, worse for one-off entities and complex singular systems,
and cross-component logic gets awkward. **The honest synthesis: use ECS where you have
many similar things (particles, units, bullets, crowds); use plain objects for the few
special things (the player, the camera, the UI).** Most shipped games are hybrids, and
purity here is a much smaller win than its advocates suggest.

Unity's DOTS is the mainstream version, now production-ready after a long and
often-criticized maturation; Bevy is ECS-native; EnTT and flecs are the C++ standards.

### 3.3 Patterns that earn their keep

**Game Programming Patterns** (Robert Nystrom, free online — §18 → `game-development-reference`) is the canonical
reference. The ones you'll actually use: **Update Method**, **Component**,
**Object Pool** (⚠️ **essential** — allocating during gameplay causes hitches, §11.4 → `game-performance-feel-and-shipping`),
**State machine** and **hierarchical state machine** (the backbone of character control),
**Observer/event bus** (decouples systems; ⚠️ becomes untraceable spaghetti if
overused), **Service Locator**, **Command** (input remapping, undo, replay, netcode),
**Spatial Partition** (§5.2 → `game-rendering-physics-animation-and-audio`), **Dirty Flag**, and **Data Locality**.

### 3.4 Separating game logic from engine

**[DURABLE] Worth doing to a moderate degree, not religiously.** Keeping your rules,
economy, and state machines in engine-agnostic code makes them unit-testable, portable,
and usable in a headless server. Wrapping every engine call in an abstraction layer is
over-engineering that will cost you more than it saves. **The test: could you run your
combat resolution in a console app with no renderer?** If yes, you've drawn the line in
about the right place.
