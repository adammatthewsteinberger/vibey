---
name: gametheory-bargaining-cooperative-mechanism-design-and-matching
description: "Use when designing rules rather than playing under them: bargaining and the Nash bargaining solution, cooperative game theory with the core and the Shapley value, mechanism design and auctions including incentive compatibility, revenue equivalence, the VCG mechanism and the impossibility results, and matching markets including deferred acceptance and stability."
---

# Game Theory: Bargaining, Cooperative Theory, Mechanism Design and Auctions, and Matching Markets

> **Part 3 of 5** of the *Game Theory* reference (plugin `game-theory`), covering §10–§13. Sibling skills: `gametheory-framework-nash-and-classic-games` (§0–§5), `gametheory-zero-sum-sequential-repeated-and-information` (§6–§9), `gametheory-evolutionary-empirical-limits-and-computation` (§14–§16), `gametheory-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    cannot be achieved** (§12).

---

## §10. Bargaining

**Nash bargaining solution (1950)** — ⚠️ **maximize the product of gains over disagreement
points: `max (u₁−d₁)(u₂−d₂)`.** **Derived axiomatically from Pareto efficiency, symmetry,
invariance to affine transformations, and independence of irrelevant alternatives.**
⚠️ **The IIA axiom is the contested one; the Kalai-Smorodinsky solution replaces it with
monotonicity and gets a different answer.**

**Rubinstein alternating offers (1982)** — ⚠️ **the strategic (non-axiomatic) model, and
it has a unique subgame perfect equilibrium.** **The player who is more patient — lower
discount rate — gets more.** ⚠️ **As the time between offers goes to zero with equal
patience, it converges to the Nash solution, which is a satisfying bridge between the
axiomatic and strategic approaches.**

**⚠️ The practically important variable is the disagreement point (BATNA).** **Your
bargaining power is determined by what happens if you walk away, not by your need or your
argument.** ⚠️ **Improving your outside option improves your terms without any change in
negotiating skill.**

---

## §11. Cooperative Game Theory

**⚠️ Different question entirely: assume binding agreements are possible, and ask how to
divide the gains.** **The primitive is the characteristic function `v(S)` — what each
coalition can guarantee itself.**

**The Core** — allocations no coalition can improve on by defecting. ⚠️ **May be empty**
(⚠️ **an empty core means the grand coalition is inherently unstable — a genuinely useful
diagnostic**) **and may be large.**

**Shapley value** — ⚠️ **the unique allocation satisfying efficiency, symmetry, null
player, and additivity.** **Computed as each player's average marginal contribution over
all orderings of arrival.**
⚠️ **It always exists and is unique — unlike the core — which is why it's the standard
tool for cost allocation, and why it has been adopted in machine learning as SHAP for
feature attribution.** **The same axioms, a different application.**
**⚠️ Computing it exactly is exponential in the number of players; sampling approximations
are standard.**

**Also**: **nucleolus**, **bargaining set**, **Banzhaf power index** (⚠️ **for voting
power — and it shows that voting weight and voting power diverge sharply; a party with 49%
of votes may have the same power as one with 26%**).

---

## §12. Mechanism Design and Auctions

**⚠️ "Reverse game theory": design the rules so that self-interested play produces the
outcome you want.**

**Revelation principle** — ⚠️ **any outcome achievable by any mechanism is achievable by a
direct mechanism in which truth-telling is optimal.** **This is a massive simplification:
you can restrict attention to incentive-compatible direct mechanisms without loss.**

**⚠️ The impossibility results are the substance of the field:**
```
ARROW (1951)                 ⚠️ No voting rule over ≥3 alternatives satisfies
                             unanimity, IIA, and non-dictatorship
GIBBARD-SATTERTHWAITE (1973) ⚠️ Any non-dictatorial deterministic voting rule over
                             ≥3 alternatives is MANIPULABLE. Strategic voting is
                             unavoidable, not a design flaw
MYERSON-SATTERTHWAITE (1983) ⚠️ No mechanism for bilateral trade with private values
                             is simultaneously efficient, individually rational, and
                             budget-balanced. SOME EFFICIENT TRADES CANNOT HAPPEN
HURWICZ                      Incentive compatibility and efficiency conflict generally
```
**⚠️ These are the results to internalize.** **They mean certain design goals are not
merely hard but provably unattainable**, and a proposal that claims all of them is wrong
somewhere.

**VCG (Vickrey-Clarke-Groves)** — ⚠️ **each participant pays the externality they impose on
others; truth-telling is a dominant strategy and the outcome is efficient.** **The
catches**: ⚠️ **not budget-balanced (may require outside subsidy), vulnerable to collusion
and false-name bidding, computationally demanding, and the prices can look
politically indefensible** — which is why it's rarer in practice than its theoretical
prominence suggests.

**Auctions:**
```
English (ascending)     ⚠️ strategically equivalent to second-price for private values
Dutch (descending)      ⚠️ strategically equivalent to first-price
First-price sealed bid  ⚠️ bid BELOW your value; optimal shading depends on beliefs
Second-price (Vickrey)  ⚠️ TRUTHFUL BIDDING IS DOMINANT — the headline result
All-pay                 everyone pays; models lobbying, R&D races, conflict
```
**⚠️ Revenue equivalence theorem**: under private independent values, risk neutrality, and
symmetry, **all four standard auctions yield the same expected revenue.**
⚠️ **The theorem's value is in its assumptions**: **when auctions differ in practice — and
they do — it's because one of those assumptions failed** (risk aversion, correlated values,
asymmetry, budget constraints, collusion). **That's the diagnostic.**

**⚠️ Practical note on second-price auctions**: truthful bidding is dominant only under
private values and a trustworthy auctioneer. **The seller can inflate the second price;
the winner's curse (§9 → `gametheory-zero-sum-sequential-repeated-and-information`) bites under common values.** **The theory is clean; deployment
requires trust in the mechanism operator.**

---

## §13. Matching Markets

**⚠️ Markets without prices — where money can't or shouldn't clear the market.**

**Gale-Shapley deferred acceptance (1962)** — ⚠️ **always produces a stable matching, in
polynomial time.**
**Properties worth knowing precisely:**
- ⚠️ **The side that *proposes* gets their best achievable stable match; the receiving side
  gets their worst.** **Which side proposes is a distributional choice, not a technical
  detail.**
- **Truth-telling is dominant for the proposing side; the receiving side can
  manipulate.**
- ⚠️ **Stability — no pair who'd both rather be with each other — is the property that
  makes matching markets survive.** **Roth's empirical work showed that unstable
  clearinghouses historically unravelled and stable ones persisted.**

**Applications**: **medical residency matching (NRMP)**, **school choice** (⚠️ **and the
Boston mechanism's replacement by deferred acceptance is a real policy win from theory**),
**kidney exchange** (⚠️ **cycles and chains in a directed graph — Roth, Sönmez, Ünver, and
it has saved thousands of lives**).
**⚠️ Top trading cycles** for allocation with existing endowments.
