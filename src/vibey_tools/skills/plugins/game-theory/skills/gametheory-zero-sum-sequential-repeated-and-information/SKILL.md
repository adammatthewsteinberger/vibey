---
name: gametheory-zero-sum-sequential-repeated-and-information
description: "Use when the game has structure beyond a single simultaneous move: zero-sum games and the minimax theorem, sequential games with backward induction and subgame perfection, repeated games including the folk theorem, trigger strategies and why cooperation can be sustained, and incomplete information with Bayesian games, types and signalling."
---

# Game Theory: Zero-Sum and Minimax, Sequential, Repeated, and Incomplete-Information Games

> **Part 2 of 5** of the *Game Theory* reference (plugin `game-theory`), covering §6–§9. Sibling skills: `gametheory-framework-nash-and-classic-games` (§0–§5), `gametheory-bargaining-cooperative-mechanism-design-and-matching` (§10–§13), `gametheory-evolutionary-empirical-limits-and-computation` (§14–§16), `gametheory-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled mathematics — von Neumann and Morgenstern 1944, Nash 1950, Gale-Shapley 1962, Selten 1965, Harsanyi 1967, Maynard Smith 1973, Myerson-Satterthwaite 1983.

> **Scope.** The mathematics of strategic interaction — situations where your best action
> depends on what others do, and theirs on what you do. ⚠️ **That circularity is the whole
> subject; everything else is machinery for resolving it.**
>
> **⚠️ GOTCHA** boxes mark misconceptions, and game theory attracts a lot of them — §18 → `gametheory-reference`
> consolidates.
>
> **The three ideas that matter most:**
> 1. **⚠️ "Rational" means consistent, not selfish.** A player maximizes their own utility
>    function — **and that function can include other people's welfare, fairness, or
>    spite.** Most criticism of game theory as "assuming people are selfish" attacks
>    something the theory doesn't claim (§1.2 → `gametheory-framework-nash-and-classic-games`).
> 2. **⚠️ Equilibrium is a consistency condition, not a prediction and not a
>    recommendation.** Nash equilibrium says no one can gain by unilateral deviation.
>    **It does not say the outcome is good, or that players will find it** (§4.3 → `gametheory-framework-nash-and-classic-games`).
> 3. **⚠️ The interesting results are mostly impossibility theorems.** Arrow,
>    Gibbard-Satterthwaite, Myerson-Satterthwaite, the folk theorem's
>    anything-goes conclusion. **Game theory's deepest contribution is telling you what
>    cannot be achieved** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`).

---

## §6. Zero-Sum and Minimax

**⚠️ Strictly competitive: one player's gain is exactly the other's loss.**
**von Neumann's minimax theorem (1928)** — ⚠️ **every finite two-player zero-sum game has a
value, and optimal mixed strategies exist.** `max min = min max`.
**⚠️ This is far stronger than Nash equilibrium in general games**: the value is unique,
all equilibria are interchangeable and give the same payoff, and **the equilibrium strategy
is a genuine guarantee — a security level you can achieve regardless of what your opponent
does.** ⚠️ **In non-zero-sum games no such guarantee exists.**

**⚠️ Solvable as a linear program**, which is why zero-sum games are computationally easy
and general games are not (§16 → `gametheory-evolutionary-empirical-limits-and-computation`).

> **⚠️ GOTCHA — most real situations are not zero-sum, and calling them so is a
> consequential error.** ⚠️ **Trade, negotiation, and most business competition have
> gains from cooperation available.** **"Zero-sum thinking" as a cognitive bias is
> precisely the misapplication of this model**, and it forecloses the integrative
> solutions §10 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` exists to find.

---

## §7. Sequential Games

**Backward induction** — ⚠️ **solve the last decision first, then work back.** In finite
games of perfect information, this yields a **subgame perfect equilibrium**, and
**(Zermelo) every such game is strictly determined.**

**Subgame perfect Nash equilibrium (SPNE, Selten 1965)** — ⚠️ **a Nash equilibrium in
every subgame.** **The purpose is eliminating non-credible threats.**
> **⚠️ GOTCHA — Nash equilibrium permits threats no rational player would carry out.**
> ⚠️ **"If you enter my market I'll price below cost forever" can be part of a Nash
> equilibrium while being irrational to execute.** **Subgame perfection rules it out by
> requiring the threat be optimal at the point it would be used.**
> **⚠️ Which is exactly why commitment devices matter (§5.2 → `gametheory-framework-nash-and-classic-games`): they make an
> otherwise-incredible threat credible by removing your ability not to execute it.**

**⚠️ The chain store paradox (Selten)** shows the limits: **backward induction says the
incumbent should never fight entry in a finite sequence of markets — yet fighting
early to build a reputation seems obviously sensible.** ⚠️ **Resolved by adding incomplete
information about the incumbent's type (§9), and it's a good illustration of backward
induction being logically airtight and behaviourally implausible.**

**Extensions**: **perfect Bayesian equilibrium** and **sequential equilibrium** for
imperfect information — ⚠️ **requiring beliefs at every information set, updated by Bayes'
rule where possible, and specified off-path where it isn't. Off-path beliefs are where the
refinement fights happen.**

---

## §8. Repeated Games

**⚠️ Repetition changes everything, because future punishment can sustain present
cooperation.**

**Finitely repeated with a known end** — ⚠️ **backward induction unravels cooperation
completely**: defect in the last round, so defect in the second-last, all the way back.
**The unravelling argument is why "known finite horizon" is such a destructive
assumption.**

**Infinitely repeated (or indefinite horizon)** — ⚠️ **and note the key modelling move:
"infinite" is best read as "the game continues with probability δ each period," which is
just discounting.**
**⚠️ The Folk Theorem**: **for a sufficiently high discount factor, ANY payoff profile
that is individually rational and feasible can be sustained as a subgame perfect
equilibrium.**
> **⚠️ GOTCHA — the folk theorem is usually presented as good news and it is mostly bad
> news for the theory.** ⚠️ **"Anything can happen in equilibrium" means the equilibrium
> concept has almost no predictive power in repeated settings.** **It explains how
> cooperation *can* be sustained; it cannot tell you whether it *will* be.**

**Strategies**: **Grim trigger** (⚠️ **cooperate until any defection, then defect
forever — maximally harsh, and unforgiving of noise**), **Tit-for-tat**, **Tit-for-two-tats**,
**Win-stay-lose-shift (Pavlov)**.
**⚠️ Axelrod's tournaments (1980s)** found tit-for-tat successful and identified the
properties that mattered: **nice** (never defect first), **retaliatory**, **forgiving**,
**clear**.
⚠️ **The important caveat, and it's often dropped: tit-for-tat is fragile to noise.** **A
single mistaken defection triggers endless mutual retaliation.** **Generous tit-for-tat or
contrite strategies handle errors far better**, and in noisy environments they outperform.
**⚠️ And no strategy is universally best — success depends entirely on the population you
face**, which is §14 → `gametheory-evolutionary-empirical-limits-and-computation`'s point.

---

## §9. Incomplete Information

**⚠️ Harsanyi's transformation (1967) is the foundational move**: convert incomplete
information (uncertainty about payoffs) into imperfect information (uncertainty about a
chance move) by introducing **types** drawn by Nature from a commonly known prior.
**⚠️ This made the whole area tractable and is why "Bayesian game" is the standard
framework.**

**Bayesian Nash equilibrium** — each type best-responds given beliefs about others' types.

**Signalling** (Spence) — ⚠️ **an informed party takes a costly action to reveal type.**
**Education as a signal works only if it is *cheaper for high types*** — the
**single-crossing condition** is doing all the work. **Separating, pooling, and
semi-separating equilibria; refinements (Cho-Kreps intuitive criterion) prune implausible
off-path beliefs.**
**Screening** — the uninformed party moves first, offering a menu that induces
self-selection. ⚠️ **Insurance deductibles and airline fare classes are screening
devices.**

**⚠️ Adverse selection (Akerlof's lemons)**: when quality is unobservable, **the market
price reflects average quality, driving out above-average sellers, lowering the average,
and potentially collapsing the market entirely.** **The mechanism is a cascade, not a
one-step effect.**
**Moral hazard** — hidden *action* rather than hidden *type*; ⚠️ **the principal-agent
problem, and the tension is always between insurance and incentives.**

**⚠️ Winner's curse** — in a common-value auction, **the winner is the bidder who most
overestimated the value.** **Rational bidders must shade their bids downward to
compensate**, and failing to do so is a documented, expensive error in oil-lease and
spectrum auctions.
