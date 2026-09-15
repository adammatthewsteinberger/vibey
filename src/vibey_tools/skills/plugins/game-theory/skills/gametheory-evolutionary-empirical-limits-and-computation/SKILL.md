---
name: gametheory-evolutionary-empirical-limits-and-computation
description: "Use when applying the theory to real populations, real people, or real algorithms: evolutionary game theory with evolutionarily stable strategies and replicator dynamics, where the theory fails empirically and what the experimental evidence actually shows, and computational game theory including equilibrium computation complexity, regret minimization and self-play."
---

# Game Theory: Evolutionary Game Theory, Empirical Failures, and Computation

> **Part 4 of 5** of the *Game Theory* reference (plugin `game-theory`), covering §14–§16. Sibling skills: `gametheory-framework-nash-and-classic-games` (§0–§5), `gametheory-zero-sum-sequential-repeated-and-information` (§6–§9), `gametheory-bargaining-cooperative-mechanism-design-and-matching` (§10–§13), `gametheory-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §14. Evolutionary Game Theory

**⚠️ The reframing that removes the rationality assumption entirely.** **Strategies are
inherited or imitated; payoff is reproductive fitness; selection replaces reasoning.**
⚠️ **You get equilibrium-like outcomes with no cognition at all**, which is a strong
response to §15's critique.

**Evolutionarily stable strategy (ESS, Maynard Smith & Price 1973)** — ⚠️ **a strategy
that, once common, cannot be invaded by a rare mutant.** **Stronger than Nash: every ESS
is a Nash equilibrium; not every Nash equilibrium is an ESS.**

**Replicator dynamics** — `ẋᵢ = xᵢ(fᵢ − f̄)`: strategies growing faster than average
increase in frequency.
⚠️ **The dynamics need not converge**: cycles (rock-paper-scissors) and chaos both occur —
**see a chaos-theory reference.**

**⚠️ Mechanisms for cooperation** (Nowak's five rules): **kin selection**, **direct
reciprocity** (§8 → `gametheory-zero-sum-sequential-repeated-and-information`), **indirect reciprocity** (reputation), **network reciprocity**
(⚠️ **spatial structure lets cooperators cluster and support each other — structure alone
can sustain cooperation**), **group selection.**
**Hawk-Dove** gives a stable mixed population; **the Price equation** decomposes selection
formally.

---

## §15. Where the Theory Fails Empirically

**⚠️ The experimental evidence is substantial and it does not favour the standard model.**

**Ultimatum game** — one player proposes a split, the other accepts or rejects; rejection
gives both nothing. ⚠️ **Subgame perfection predicts an offer of the smallest possible
amount, accepted.** **Observed: modal offers around 40–50%, and offers below ~20% are
routinely rejected.** ⚠️ **Rejecting free money is not consistent with money-maximization —
though it *is* consistent with a utility function including fairness or spite** (§1.2 → `gametheory-framework-nash-and-classic-games`).
**⚠️ Cross-cultural variation is large, which points at social norms rather than a
universal constant.**

**Dictator game** — no rejection possible, and ⚠️ **people still give away money, though
much less.** **The difference between the two games separates fairness preference from
strategic anticipation of rejection.**

**Public goods games** — ⚠️ **contributions start well above zero and decay with
repetition**, and **punishment opportunities sustain them** (⚠️ **including costly
altruistic punishment, which is itself a puzzle for the standard model**).

**Beauty contest / p-beauty** — "pick a number, closest to ⅔ of the average wins."
⚠️ **Nash equilibrium is 0. Observed answers cluster at levels of iterated reasoning
(level-1, level-2), typically 1–3 steps deep.** **This is direct evidence that common
knowledge of rationality fails, and it motivated level-k and cognitive hierarchy models.**

**⚠️ Responses within the theory**: **behavioural game theory** (⚠️ **inequity aversion —
Fehr-Schmidt; reciprocity; social preferences — all of which fit inside the utility
framework**), **quantal response equilibrium** (⚠️ **players best-respond noisily, with
better responses more likely — a clean generalization of Nash**), **level-k / cognitive
hierarchy**, and **learning models** (fictitious play, reinforcement, experience-weighted
attraction).

> **⚠️ GOTCHA — read the evidence precisely.** ⚠️ **The failures are mostly of the
> auxiliary assumptions — unlimited computation, common knowledge of rationality, and
> narrowly self-interested payoffs — not of the framework itself.** **Game theory adapted
> by relaxing these**, and the adapted models fit far better. **"Game theory is wrong
> because people aren't selfish" is a critique of a strawman** (§1.2 → `gametheory-framework-nash-and-classic-games`); **"equilibrium
> concepts assume more reasoning than people do" is the substantive critique**, and it's
> the one §16 makes formally.

---

## §16. Computational Game Theory

**⚠️ Complexity results that constrain how seriously to take equilibrium as a prediction:**
```
Two-player ZERO-SUM Nash    ⚠️ polynomial (linear programming) — easy
General two-player Nash     ⚠️ PPAD-COMPLETE (Daskalakis, Goldberg, Papadimitriou;
                            Chen & Deng) — believed intractable
Correlated equilibrium      ⚠️ polynomial (linear programming) — easy
Optimal Nash (max welfare)  NP-hard
Shapley value               #P-hard in general (§11)
```
> **⚠️ GOTCHA — this is a serious conceptual problem, not a technical footnote.** ⚠️ **If
> computing an equilibrium is intractable, it is hard to argue that players find it.**
> **As Papadimitriou put it, a concept that cannot be computed efficiently is suspect as a
> model of what happens in the world.** **Nash's existence theorem being non-constructive
> (§4.1 → `gametheory-framework-nash-and-classic-games`) turns out to have been a warning.**
>
> ⚠️ **Correlated equilibrium's tractability is the strongest argument in its favour** —
> **and notably, simple no-regret learning dynamics converge to the set of correlated
> equilibria.** **A concept that is both computationally easy and reachable by naive
> learning has a much better claim to describing reality.**

**Algorithmic game theory**: **Price of Anarchy** — ⚠️ **the ratio of worst equilibrium
welfare to optimal welfare.** **Selfish routing on networks has a Price of Anarchy of 4/3
for linear latency (Roughgarden-Tardos)** — ⚠️ **a reassuringly small bound, and the reason
that result is famous.**
**⚠️ Braess's paradox** — **adding a road to a network can make everyone's commute
longer.** **Documented in real road networks, and a direct consequence of equilibrium
routing.**

**⚠️ Practical algorithms that work despite the theory**: **counterfactual regret
minimization (CFR)** solved heads-up limit poker and underlies superhuman no-limit poker
agents; **double oracle** and **PSRO** for large games; **self-play reinforcement
learning**. ⚠️ **Note the pattern: these are no-regret learning methods, not equilibrium
solvers** — **and in two-player zero-sum, no-regret play converges to the minimax value
(§6 → `gametheory-zero-sum-sequential-repeated-and-information`), which is exactly why poker fell and general multi-agent settings are harder.**
