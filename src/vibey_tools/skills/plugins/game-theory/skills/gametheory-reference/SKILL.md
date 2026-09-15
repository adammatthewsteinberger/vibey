---
name: gametheory-reference
description: "Use when correcting a game-theory misconception, looking up a solution concept, formula or standard result, finding the canon, or needing a picker and a modelling checklist to run before claiming a strategic situation is a particular game. Companion to the other game-theory skills."
---

# Game Theory: Misconceptions, Formulas, and Canon

> **Part 5 of 5** of the *Game Theory* reference (plugin `game-theory`), covering §17–§21. Sibling skills: `gametheory-framework-nash-and-classic-games` (§0–§5), `gametheory-zero-sum-sequential-repeated-and-information` (§6–§9), `gametheory-bargaining-cooperative-mechanism-design-and-matching` (§10–§13), `gametheory-evolutionary-empirical-limits-and-computation` (§14–§16). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled mathematics — von Neumann and Morgenstern 1944, Nash 1950, Gale-Shapley 1962, Selten 1965, Harsanyi 1967, Maynard Smith 1973, Myerson-Satterthwaite 1983.

> **Scope.** The mathematics of strategic interaction — situations where your best action
> depends on what others do, and theirs on what you do. ⚠️ **That circularity is the whole
> subject; everything else is machinery for resolving it.**
>
> **⚠️ GOTCHA** boxes mark misconceptions, and game theory attracts a lot of them — §18
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

## §17. Misconceptions

| Misconception | Correction |
|---|---|
| Rational means selfish | ⚠️ **Means consistent. Utility can include anyone's welfare** (§1.2 → `gametheory-framework-nash-and-classic-games`) |
| Game theory assumes people are cold calculators | ⚠️ **It assumes consistency; the failing assumptions are computational** (§1.2 → `gametheory-framework-nash-and-classic-games`, §15 → `gametheory-evolutionary-empirical-limits-and-computation`) |
| Nash equilibrium is the optimal outcome | ⚠️ **The PD's equilibrium is Pareto-dominated** (§4.3 → `gametheory-framework-nash-and-classic-games`) |
| Nash equilibrium is unique | Most games have many; selection is unsolved (§4.3 → `gametheory-framework-nash-and-classic-games`) |
| Nash equilibrium predicts behaviour | ⚠️ **It's a consistency condition, not a dynamic theory** (§4.3 → `gametheory-framework-nash-and-classic-games`) |
| In a mixed equilibrium you optimize your own payoff | ⚠️ **Your mix makes your OPPONENT indifferent** (§4.2 → `gametheory-framework-nash-and-classic-games`) |
| Most situations are prisoner's dilemmas | ⚠️ **Usually Stag Hunt or Chicken. Check T>R>P>S and 2R>T+S** (§5.1 → `gametheory-framework-nash-and-classic-games`) |
| Most competition is zero-sum | ⚠️ **Rarely. Zero-sum thinking is a named bias** (§6 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| More options are always better | ⚠️ **Commitment — removing options — can win** (§5.2 → `gametheory-framework-nash-and-classic-games`) |
| A threat in a Nash equilibrium is credible | ⚠️ **Subgame perfection exists to exclude these** (§7 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Cooperation is impossible among self-interested agents | ⚠️ **Repetition, reputation, structure all sustain it** (§8 → `gametheory-zero-sum-sequential-repeated-and-information`, §14 → `gametheory-evolutionary-empirical-limits-and-computation`) |
| The folk theorem shows cooperation emerges | ⚠️ **It shows ANYTHING can be an equilibrium — that's weak, not strong** (§8 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Tit-for-tat is the best strategy | ⚠️ **Fragile to noise; no strategy is universally best** (§8 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Second-price auctions are always truthful in practice | ⚠️ **Requires private values and a trusted auctioneer** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| A better voting system could be non-manipulable | ⚠️ **Gibbard-Satterthwaite says no** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Efficient trade can always be arranged | ⚠️ **Myerson-Satterthwaite says no** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Which side proposes in matching is a detail | ⚠️ **It determines who gets their best stable match** (§13 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Adding capacity to a network helps | ⚠️ **Braess's paradox** (§16 → `gametheory-evolutionary-empirical-limits-and-computation`) |
| Equilibria are what players will compute | ⚠️ **General Nash is PPAD-complete** (§16 → `gametheory-evolutionary-empirical-limits-and-computation`) |
| Evolutionary game theory needs rational agents | ⚠️ **It needs none. Selection replaces reasoning** (§14 → `gametheory-evolutionary-empirical-limits-and-computation`) |

---

## §18. Formulas and Facts

```
NASH EQUILIBRIUM
sᵢ* ∈ argmax uᵢ(sᵢ, s₋ᵢ*)  for all i
⚠️ Every finite game has a mixed equilibrium (Nash 1950, via fixed point)
⚠️ Mixed equilibrium: you are indifferent over your support

ZERO-SUM
⚠️ max min = min max (von Neumann 1928); solvable by LP

REPEATED GAMES
Cooperation sustainable when δ ≥ (T−R)/(T−P)   [grim trigger, PD]
⚠️ Folk theorem: any individually rational feasible payoff, for δ high enough

BARGAINING
Nash solution: max (u₁−d₁)(u₂−d₂)
⚠️ Rubinstein: more patient player gets more

COOPERATIVE
Shapley: φᵢ = Σ_S [|S|!(n−|S|−1)!/n!] · [v(S∪{i}) − v(S)]
⚠️ = average marginal contribution over arrival orders

AUCTIONS
⚠️ Second-price: bid your true value (dominant)
First-price: shade below value
⚠️ Revenue equivalence under private/independent values, risk neutrality, symmetry

COMPLEXITY ⚠️
Zero-sum Nash: P · General Nash: PPAD-complete
Correlated equilibrium: P · Shapley value: #P-hard
Price of Anarchy, selfish routing with linear latency: 4/3

EVOLUTIONARY
Replicator: ẋᵢ = xᵢ(fᵢ − f̄)
⚠️ ESS ⟹ Nash, but not conversely

EXPERIMENTAL ⚠️
Ultimatum: modal offers ~40–50%; offers <20% often rejected
p-beauty contest: equilibrium 0; observed 1–3 levels of reasoning
```

---

## §19. Books

| Author | Work | Why |
|---|---|---|
| **Osborne & Rubinstein** | ***A Course in Game Theory*** | ⚠️ **The rigorous standard. Free from Osborne's site** |
| **Fudenberg & Tirole** | ***Game Theory*** | The graduate reference |
| **Osborne** | *An Introduction to Game Theory* | ⚠️ **The accessible entry point** |
| **Schelling** | ***The Strategy of Conflict*** | ⚠️ **Commitment, focal points, credibility. Almost no mathematics and one of the most influential books in the field** |
| **von Neumann & Morgenstern** | *Theory of Games and Economic Behavior* (1944) | The founding text |
| **Camerer** | ***Behavioral Game Theory*** | ⚠️ **§15 → `gametheory-evolutionary-empirical-limits-and-computation`, definitively** |
| **Roth** | ***Who Gets What — and Why*** | ⚠️ **§13 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` from the person who built the markets; Nobel work, readable** |
| **Krishna** | *Auction Theory* | §12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` |
| **Nisan, Roughgarden, Tardos, Vazirani** | ***Algorithmic Game Theory*** | ⚠️ **§16 → `gametheory-evolutionary-empirical-limits-and-computation`. Free online** |
| **Maynard Smith** | *Evolution and the Theory of Games* | §14 → `gametheory-evolutionary-empirical-limits-and-computation`, foundational |
| **Nowak** | *Evolutionary Dynamics* | §14 → `gametheory-evolutionary-empirical-limits-and-computation`, modern |
| **Dixit & Nalebuff** | *The Art of Strategy* | ⚠️ **Popular, genuinely good on intuition** |
| **Axelrod** | *The Evolution of Cooperation* | §8 → `gametheory-zero-sum-sequential-repeated-and-information`, and read the noise critiques alongside |

---

## §20. Quick Reference

### 20.1 Picker
| Situation | Tool |
|---|---|
| Simultaneous, complete information | **Nash equilibrium; check dominance first** (§3 → `gametheory-framework-nash-and-classic-games`, §4 → `gametheory-framework-nash-and-classic-games`) |
| Strictly competitive | ⚠️ **Minimax — you get a genuine guarantee** (§6 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Sequential, perfect information | **Backward induction → SPNE** (§7 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Non-credible threats in the solution | ⚠️ **Apply subgame perfection** (§7 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Ongoing relationship | ⚠️ **Repeated game; check the discount factor** (§8 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Asymmetric information about types | **Bayesian game; signalling or screening** (§9 → `gametheory-zero-sum-sequential-repeated-and-information`) |
| Splitting a surplus | **Nash bargaining or Rubinstein; ⚠️ improve your BATNA** (§10 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Allocating joint costs or credit | ⚠️ **Shapley value** (§11 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Designing rules for self-interested agents | **Mechanism design; ⚠️ check the impossibility theorems first** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Selling a single item | **Second-price for truthfulness; ⚠️ check revenue-equivalence assumptions** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Two-sided allocation without prices | ⚠️ **Deferred acceptance; decide who proposes** (§13 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`) |
| Populations without deliberation | **Replicator dynamics, ESS** (§14 → `gametheory-evolutionary-empirical-limits-and-computation`) |
| Predicting real human play | ⚠️ **QRE, level-k — not plain Nash** (§15 → `gametheory-evolutionary-empirical-limits-and-computation`) |
| Solving a large game computationally | ⚠️ **No-regret learning (CFR), not equilibrium solvers** (§16 → `gametheory-evolutionary-empirical-limits-and-computation`) |

### 20.2 Modelling checklist
- [ ] Who are the players, and is the relevant set actually larger? (§1 → `gametheory-framework-nash-and-classic-games`)
- [ ] Are strategies complete contingent plans, or am I listing moves? (§1.1 → `gametheory-framework-nash-and-classic-games`)
- [ ] Are payoffs *utilities*, including non-monetary concerns? (§1.2 → `gametheory-framework-nash-and-classic-games`)
- [ ] Perfect vs complete information — which am I assuming? (§2 → `gametheory-framework-nash-and-classic-games`)
- [ ] Is this genuinely a PD, or a coordination game? ⚠️ **Check the inequalities** (§5.1 → `gametheory-framework-nash-and-classic-games`)
- [ ] One-shot or repeated, and is the horizon known? (§8 → `gametheory-zero-sum-sequential-repeated-and-information`)
- [ ] Does my solution rely on a non-credible threat? (§7 → `gametheory-zero-sum-sequential-repeated-and-information`)
- [ ] Is the equilibrium unique — and if not, what selects among them? (§4.3 → `gametheory-framework-nash-and-classic-games`)
- [ ] Would real people play this way? (§15 → `gametheory-evolutionary-empirical-limits-and-computation`)
- [ ] Could the players actually compute this? (§16 → `gametheory-evolutionary-empirical-limits-and-computation`)

---

## §21. Method

**No searches were run; none would have helped.** ⚠️ **This is settled mathematics.**
**von Neumann's minimax theorem (1928)**, **von Neumann & Morgenstern (1944)**, **Nash
(1950)**, **Arrow (1951)**, **Gale-Shapley (1962)**, **Selten (1965)**, **Harsanyi
(1967)**, **Gibbard-Satterthwaite (1973)**, **Maynard Smith & Price (1973)**, **Rubinstein
(1982)**, **Myerson-Satterthwaite (1983)**. ⚠️ **The theorems have not changed.**

**Sources** are the references in §19 — chiefly **Osborne & Rubinstein** and **Fudenberg &
Tirole** for §1–§12 → `gametheory-framework-nash-and-classic-games`, `gametheory-zero-sum-sequential-repeated-and-information`, `gametheory-bargaining-cooperative-mechanism-design-and-matching`, **Roth** for §13 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`, **Nowak** and **Maynard Smith** for §14 → `gametheory-evolutionary-empirical-limits-and-computation`,
**Camerer** for §15 → `gametheory-evolutionary-empirical-limits-and-computation`, and **Nisan et al.** for §16 → `gametheory-evolutionary-empirical-limits-and-computation`.

**Confidence: high on the mathematics**, and ⚠️ **I have stated theorems with their
hypotheses throughout, because in this field the hypotheses are where the content is** —
**revenue equivalence, the folk theorem, and second-price truthfulness are all routinely
invoked outside the conditions under which they hold, and §12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` and §17 flag each case.**

⚠️ **Three places I've taken a position rather than reporting neutrally.**

**§5.1 → `gametheory-framework-nash-and-classic-games`'s warning about the Prisoner's Dilemma is deliberate and I'd defend it strongly.**
⚠️ **The PD is the most over-applied model in social science, and the misdiagnosis has
practical consequences**: **a Stag Hunt is a trust problem where the good outcome is
already an equilibrium and communication may suffice; a true PD requires enforcement or
repetition.** **Prescribing the wrong remedy follows directly from naming the wrong game**,
and the inequality test in §5.1 → `gametheory-framework-nash-and-classic-games` takes thirty seconds.

**§8 → `gametheory-zero-sum-sequential-repeated-and-information`'s framing of the folk theorem as bad news** is the standard view among theorists and
the opposite of how it's usually popularized. ⚠️ **"Anything can be sustained in
equilibrium" is a statement that the concept has lost its predictive content in that
setting**, and presenting it as "game theory explains cooperation" overstates it.

**§16 → `gametheory-evolutionary-empirical-limits-and-computation`'s complexity concern I treat as substantive rather than technical.** ⚠️ **If
computing an equilibrium is PPAD-complete, the claim that players locate it needs
defending**, and **correlated equilibrium's tractability plus its reachability by simple
no-regret learning is a genuine argument for preferring it.** **The practical successes in
§16 → `gametheory-evolutionary-empirical-limits-and-computation` are no-regret learning methods, not equilibrium solvers** — ⚠️ **which I'd read as the
field's computational results being vindicated in practice rather than worked around.**

**§15 → `gametheory-evolutionary-empirical-limits-and-computation` I've tried to state fairly in both directions**: the experimental failures are real
and large, ⚠️ **and they mostly indict the auxiliary assumptions rather than the
framework** — which is why the behavioural variants fit inside it.
