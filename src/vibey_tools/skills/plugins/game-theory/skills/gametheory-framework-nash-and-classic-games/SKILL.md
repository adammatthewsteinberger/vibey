---
name: gametheory-framework-nash-and-classic-games
description: "Use when setting up or reading a game: what defines a game and what 'rational' actually assumes, normal and extensive form representations, dominance and iterated elimination, Nash equilibrium including existence, mixed strategies and — importantly — what Nash equilibrium is not, and the classic games from the Prisoner's Dilemma through the other four worth knowing. Includes the router for the whole game-theory reference."
---

# Game Theory: The Framework, Representations, Dominance, Nash Equilibrium, and the Classic Games

> **Part 1 of 5** of the *Game Theory* reference (plugin `game-theory`), covering §0–§5. Sibling skills: `gametheory-zero-sum-sequential-repeated-and-information` (§6–§9), `gametheory-bargaining-cooperative-mechanism-design-and-matching` (§10–§13), `gametheory-evolutionary-empirical-limits-and-computation` (§14–§16), `gametheory-reference` (§17–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    something the theory doesn't claim (§1.2).
> 2. **⚠️ Equilibrium is a consistency condition, not a prediction and not a
>    recommendation.** Nash equilibrium says no one can gain by unilateral deviation.
>    **It does not say the outcome is good, or that players will find it** (§4.3).
> 3. **⚠️ The interesting results are mostly impossibility theorems.** Arrow,
>    Gibbard-Satterthwaite, Myerson-Satterthwaite, the folk theorem's
>    anything-goes conclusion. **Game theory's deepest contribution is telling you what
>    cannot be achieved** (§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **The framework and its assumptions** | **§1** |
| Representations | §2 |
| Dominance | §3 |
| **Nash equilibrium** | **§4** |
| **The classic games** | **§5** |
| Zero-sum and minimax | §6 → `gametheory-zero-sum-sequential-repeated-and-information` |
| **Sequential games** | **§7 → `gametheory-zero-sum-sequential-repeated-and-information`** |
| **Repeated games** | **§8 → `gametheory-zero-sum-sequential-repeated-and-information`** |
| Incomplete information and signalling | §9 → `gametheory-zero-sum-sequential-repeated-and-information` |
| Bargaining | §10 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` |
| Cooperative game theory | §11 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` |
| **Mechanism design and auctions** | **§12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching`** |
| Matching markets | §13 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` |
| Evolutionary game theory | §14 → `gametheory-evolutionary-empirical-limits-and-computation` |
| **Where the theory fails empirically** | **§15 → `gametheory-evolutionary-empirical-limits-and-computation`** |
| **Computational game theory** | **§16 → `gametheory-evolutionary-empirical-limits-and-computation`** |
| Misconceptions | §17 → `gametheory-reference` |
| Formulas | §18 → `gametheory-reference` |
| Books | §19 → `gametheory-reference` |
| Quick reference | §20 → `gametheory-reference` |

---

## §1. The Framework

### 1.1 What defines a game
```
Players        who decides
Strategies     ⚠️ a COMPLETE contingent plan — what to do at every point you might act
Payoffs        utility over outcomes
Information    who knows what, when
Timing         simultaneous or sequential
```
**⚠️ "Strategy" is a technical term and it trips people up**: it is not a single move. **In
chess, a strategy specifies your response to every possible position** — an astronomically
large object. **This matters because equilibrium is defined over strategies, not moves.**

**Common knowledge** — ⚠️ **everyone knows X, everyone knows everyone knows X, ad
infinitum.** **This is far stronger than "everyone knows"** and it does real work in the
theory (§18 → `gametheory-reference`'s electronic mail game).

### 1.2 ⚠️ What "rational" actually assumes
**A rational player has a complete, transitive preference ordering and maximizes expected
utility with respect to it** (von Neumann-Morgenstern, 1944, from four axioms:
completeness, transitivity, continuity, independence).

> **⚠️ GOTCHA — this is the most misunderstood point in the subject.**
> ⚠️ **Rationality does NOT mean selfish, money-maximizing, cold, or unemotional.** **A
> player whose utility function values their child's welfare above their own is rational.
> A player who derives utility from punishing unfairness is rational.**
> **The assumption is *consistency*, not *content*.**
>
> ⚠️ **The real limitation is different and worth stating precisely**: the theory assumes
> **unlimited computational ability**, **correct beliefs about others' payoffs**, and
> **common knowledge of rationality.** **Those are the assumptions that actually fail**
> (§15 → `gametheory-evolutionary-empirical-limits-and-computation`, §16 → `gametheory-evolutionary-empirical-limits-and-computation`).

**⚠️ Utility is ordinal in preference and cardinal only up to positive affine
transformation.** **Interpersonal comparison of utility is not licensed by the
framework** — which is why §11 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` and §12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` have to work hard to say anything about fairness.

---

## §2. Representations

**Normal (strategic) form** — a payoff matrix; assumes simultaneous choice.
**Extensive form** — a game tree with nodes, branches, and **information sets** (⚠️ **a set
of nodes a player cannot distinguish between — this is how you represent imperfect
information, and a simultaneous game is just a tree with a big information set**).

**⚠️ Perfect vs complete information — routinely confused:**
- **Perfect information**: every player knows the full history when they move. ⚠️ **Chess
  has it; poker does not.**
- **Complete information**: everyone knows everyone's payoff functions. ⚠️ **An auction
  with private valuations lacks it.**
**They are independent.** **§7 → `gametheory-zero-sum-sequential-repeated-and-information` handles imperfect; §9 → `gametheory-zero-sum-sequential-repeated-and-information` handles incomplete.**

---

## §3. Dominance

**Strictly dominated** — worse than another strategy against *every* opponent profile.
⚠️ **A rational player never plays one, so you can delete it — and iterated elimination of
strictly dominated strategies is order-independent.**
**Weakly dominated** — never better, sometimes worse. ⚠️ **Iterated elimination of *weakly*
dominated strategies IS order-dependent, and can eliminate legitimate equilibria. Handle
with care.**

**Dominant strategy equilibrium** — everyone has a single best strategy regardless of
others. ⚠️ **Rare and extremely strong when it exists** — it needs no beliefs about others
at all, which is exactly why §12 → `gametheory-bargaining-cooperative-mechanism-design-and-matching` prizes dominant-strategy mechanisms.

**Rationalizability** — ⚠️ **the weaker solution concept: strategies surviving iterated
elimination of never-best-responses.** **Every Nash equilibrium is rationalizable; the
converse fails.**

---

## §4. Nash Equilibrium

### 4.1 Definition and existence
**⚠️ A strategy profile where no player can improve by unilaterally deviating.** Each
player's strategy is a best response to the others'.

**Nash (1950)**: ⚠️ **every finite game has at least one equilibrium in mixed strategies.**
**The proof is a fixed-point argument (Kakutani/Brouwer)** — ⚠️ **which is why it's
non-constructive, and why §16 → `gametheory-evolutionary-empirical-limits-and-computation`'s complexity results are not a contradiction: existence is
guaranteed, finding it is hard.**

### 4.2 Mixed strategies
**Randomizing over pure strategies.** ⚠️ **The defining property people miss: in a mixed
equilibrium, you are indifferent among all strategies you play with positive
probability.**
> **⚠️ GOTCHA — this produces the most counterintuitive result in basic game theory.**
> ⚠️ **Your equilibrium mixing probabilities are determined by making your OPPONENT
> indifferent, not by optimizing your own payoff.** **Consequence: if a player's payoffs
> change, it is the *other* player's equilibrium mix that shifts, not their own.**
> **This routinely surprises people and it's a good test of whether you've understood
> mixed equilibrium.**

**Interpretations**: deliberate randomization (⚠️ **genuinely correct in poker and
penalty kicks**), **population frequencies** (§14 → `gametheory-evolutionary-empirical-limits-and-computation`), or **beliefs about an opponent's
type** (Harsanyi purification).

### 4.3 ⚠️ What Nash equilibrium is not
- **⚠️ Not necessarily efficient.** The Prisoner's Dilemma's unique equilibrium is Pareto-
  dominated (§5.1). **Equilibrium ≠ good outcome.**
- **⚠️ Not unique.** Most games have many; **selecting among them is an unsolved problem**
  (refinements: subgame perfection §7 → `gametheory-zero-sum-sequential-repeated-and-information`, trembling-hand, risk vs payoff dominance).
- **⚠️ Not a prediction of behaviour** without additional assumptions about how players
  reach it. **The theory says where you'd stop, not how you get there.**
- **⚠️ Not a recommendation.** "Play your Nash strategy" is only advice if you believe
  others will too.

**Correlated equilibrium (Aumann)** — ⚠️ **players observe a shared signal and condition
on it.** **Weaker than Nash, can achieve better payoffs, is computationally easy (§16 → `gametheory-evolutionary-empirical-limits-and-computation`),
and is arguably the more natural concept** — a traffic light is a correlating device.

---

## §5. The Classic Games

### 5.1 Prisoner's Dilemma
```
              Cooperate   Defect
Cooperate       3, 3       0, 5
Defect          5, 0       1, 1        ⚠️ unique equilibrium: (Defect, Defect)
```
**⚠️ Defection strictly dominates**, so the equilibrium is unique and Pareto-dominated.
**Individual rationality produces a collectively worse outcome — the canonical statement
that these can conflict.**
> **⚠️ GOTCHA — the Prisoner's Dilemma is enormously over-applied, and the specific error
> is diagnosable.** ⚠️ **It requires `T > R > P > S` AND `2R > T + S`.** **Most real
> situations labelled "a prisoner's dilemma" are actually Stag Hunt (§5.2 — a coordination
> problem with a *good* equilibrium available) or Chicken.**
> **The distinction is not pedantic: a coordination failure needs communication and trust;
> a true PD needs enforcement or repetition** (§8 → `gametheory-zero-sum-sequential-repeated-and-information`). ⚠️ **Prescribing the wrong remedy
> follows directly from misdiagnosing the game.**

### 5.2 The other four you need
```
STAG HUNT (assurance)        Two equilibria: (Stag,Stag) payoff-dominant,
                             (Hare,Hare) risk-dominant. ⚠️ A TRUST problem, not a
                             greed problem — the good outcome IS an equilibrium

CHICKEN (hawk-dove)          Two asymmetric pure equilibria + a mixed one.
                             ⚠️ Commitment wins: visibly removing your own options
                             (throwing away the steering wheel) is a strategic ADVANTAGE

BATTLE OF THE SEXES          Coordination with conflicting preferences.
                             ⚠️ Both want to coordinate; they disagree on where

MATCHING PENNIES             ⚠️ Zero-sum, NO pure equilibrium, unique mixed equilibrium
                             at 50/50. The archetype for §6
```
**⚠️ Commitment as advantage (Schelling) is the deep idea in Chicken**: **in strategic
settings, reducing your own options can improve your outcome** — burning bridges, binding
contracts, publicly irreversible positions. ⚠️ **This inverts the decision-theoretic
intuition that more options are always weakly better, and the inversion is real.**
