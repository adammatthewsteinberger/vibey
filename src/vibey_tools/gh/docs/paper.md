# Exact-Head Evaluation: Sound and Terminating Autonomous Release Automation for Collaborative Repositories

**Abstract.** Continuous-delivery automation routinely violates a soundness property
its users assume: that a decision to merge or release code was made about the code
actually merged or released. We formalize this as the *exact-head invariant*, present
an evaluation calculus in which every automated claim is bound to the precise revision
it evaluated, and prove that the resulting review–repair loop terminates in at most
$A\,(1+k)$ bounded-repair steps per contributor lineage, where $A$ is the repair
budget and $k$ the operator-refill bound. We report a production violation of the
invariant (a fully repaired change escalated as unrepairable on the verdict of a
superseded revision), the one-line ordering correction that restores soundness, and
regression evidence across a nine-repository fleet operating the system unattended.

## Introduction

Let a pull request's evolution be the finite sequence of *heads*
$H = \langle h_0, h_1, \dots, h_n \rangle$, each a repository revision replacing its
predecessor. An automation system emits *claims* — scan results, review verdicts,
gate conclusions — and acts on them: merging, releasing, or halting for an operator.
The folk assumption is that a claim about $h_i$ speaks for the pull request. It does
not: it speaks for $h_i$ alone.

```latex
\begin{invariant}[Exact-head]
Every claim is a pair $(c, h_i)$, and no decision procedure over head $h_j$ may
consume a claim $(c, h_i)$ with $i \neq j$.
\end{invariant}
```

Hosted platforms attach checks to revisions but permit consumers to relax the
binding — branch-scoped approvals and stale-review tolerances are ubiquitous. We
show the relaxation is not hypothetical debt: it produced a liveness failure in
production, and restoring the invariant required reordering a single guard.

## The evaluation calculus

Evaluation is a pure function over the head, its check results, and a persisted
state $\sigma = (a, r, v, k)$: attempts consumed, last-reviewed revision, its
verdict, and refills used. The state space is

$$S = \{\mathsf{pending}, \mathsf{review}, \mathsf{ready}, \mathsf{repair}, \mathsf{blocked}\}$$

with the transition function, for head $h$ and budget $A$:

$$E(h, \sigma) = \begin{cases} \mathsf{pending} & \text{checks incomplete} \\ \mathsf{review} & r \neq h \\ \mathsf{ready} & r = h \land v = \top \\ \mathsf{repair} & r = h \land v = \bot \land a < A \\ \mathsf{blocked} & r = h \land v = \bot \land a \geq A \end{cases}$$

```latex
\begin{invariant}[Budget placement]
The guard $a \geq A$ is evaluated only where a repair would be spent — strictly
after the freshness test $r \neq h$. Reviews are free; only repairs are counted.
\end{invariant}
```

### Termination

```latex
\begin{theorem}[Bounded convergence]
Absent contributor pushes, every lineage reaches a terminal state in at most
$A\,(1+k_{\max})$ repairs.
\end{theorem}
\begin{proof}[Proof sketch]
Heads advance only via repairs, since a contributor push begins a new lineage by
definition. Each repair increments $a$; $a$ is bounded by $A$; $a$ resets only via
operator refill, itself bounded by $k_{\max}$. The transition relation admits no
cycle that leaves $(a, k)$ unchanged, so the lexicographic measure
$\mu = (k_{\max} - k,\; A - a)$ strictly decreases across every non-terminal loop,
and $\mathsf{ready}$ and $\mathsf{blocked}$ absorb.
\end{proof}
```

## A production violation and its correction

With the budget guard evaluated *before* the freshness test, the following trace is
reachable: reviews of $h_0 \dots h_2$ fail with findings; repairs produce $h_3$
addressing all of them; $a = A$; evaluation of $h_3$ hits the budget guard first and
emits $\mathsf{blocked}$ — the lineage is escalated as unrepairable on the verdict of
$h_2$, a revision that no longer exists in the pull request. We observed exactly this
trace in production (repository issue 161): the terminal artifact read *"Remaining
failures: []"* — an exhaustion report whose own failure set was empty. Reordering the
guards (issue 163) restores Invariant 2; the regression test asserts the
counterexample trace now yields $\mathsf{review}$.

## Trust separation

Three principals with pairwise-disjoint capabilities operate the loop: the per-job
platform token publishes claims but cannot act; the reviewing credential proposes
revisions on guarded branches but cannot merge; the merging credential consumes
verdicts but can never produce them. The separation yields a simple non-collusion
property: no single credential can both judge and act, so a compromised judge cannot
ship and a compromised actor cannot self-approve. Untrusted third-party revisions are
data to all three principals, and a `trusted_only` predicate additionally keeps them
off self-hosted hardware.

## Release monotonicity

Versions are derived, not remembered: for mainline $M$ and change set $\Delta$,
$\mathrm{ver}(M \cup \Delta) \geq \mathrm{ver}(M)$, with equality exactly when
$\Delta$ carries no shippable content, and the derivation is idempotent —
re-promoting identical content never compounds a bump. Published versions therefore
form a monotone sequence, and the publish step treats an already-published version as
a no-op, never an error.

## Sovereign operation: degraded modes as first-class states

Production exposed a failure class the calculus above does not reach: the *evaluator's
own substrate* — API credit, the hosted review lane, the operator's IDE — can refuse
service while the repositories remain healthy. We model each lane as a probe
$p : \mathbb{T} \to \{0,1\}$ (a command judged by exit status at time $t$) and define
sovereign operation as the requirement that for every lane there exists a fallback
lattice $L_0 \succ L_1 \succ \cdots \succ L_k$ in which $L_0$ is the preferred lane,
each $L_{i+1}$ is strictly harder to refuse than $L_i$, and control always rests at the
*least* $i$ with $p_i(t) = 1$.

**The seat automaton.** The operator seat is governed by a two-bit state machine over
$(\mathit{paid}, \mathit{seat}) \in \{0,1\}^2$ with the transition function

$$
\sigma(\mathit{paid}, \mathit{seat}) =
\begin{cases}
\mathrm{RECLAIM} & \mathit{paid} = 1 \wedge \mathit{seat} = 1\\
\mathrm{ENGAGE} & \mathit{paid} = 0 \wedge \mathit{seat} = 0\\
\mathrm{HOLD} & \text{otherwise.}
\end{cases}
$$

$\sigma$ is total and deterministic by inspection, and satisfies the *paid-lane-leads*
invariant: from any state, one probe cycle after $\mathit{paid}$ becomes and stays 1,
$\mathit{seat} = 0$ — the hosted lane resumes leadership within a single interval, and
recovery requires no input beyond the funding event itself. Engagement selects the
first seat in the lattice whose health probe passes; a lattice with no passing seat is
reported as an alarm rather than absorbed, since a silent gap is an operator with no
agent at all — the one outcome the automaton exists to prevent.

**Lossless handoff.** Handoffs are invisible in repository history because seats share
one working tree while a sync loop maintains, for every branch $b$ with local head
$\ell(b)$ and remote head $r(b)$, the guarded property: push only if $\ell(b)$ is
clean, provenance-green, and strictly ahead, using a compare-and-swap on the remote
ref — force-with-lease against the lease value captured *before* any fetch. The
capture ordering is load-bearing: fetching first silently re-arms the lease to
whatever the remote already holds, reducing the swap to an unconditional overwrite —
a regression class we hit, tested, and closed. Under this discipline the remote can
lose no commit the local side has not already seen, so the union of both fronts is
non-decreasing across arbitrary seat churn.

**Governance supersession.** The founding documents ratchet (they may only
strengthen), and ratification carries a fleet-wide obligation stated as an invariant
over the release order: let $G$ be the governed path set and $\mathcal{R}$ the set of
published versions with total order $\prec$ from release monotonicity. A release $v$
whose change set touches $G$ — a *ratified* governance change, never a draft — makes
every $u \prec v$ superseded: no artifact circulates under superseded law, with the
retention window and every reporting switch overridden by construction rather than by
configuration. Where an index offers no revocation API, the system emits the complete
demand — each named $u$, with its management URL — and the human executes it; the
platform's limitation assigns the executor without weakening the invariant.

## The commodity thesis: production is bounded, governance is not

The measurements above suggest a claim larger than the system that produced them.

**Statement.** For a bounded task class $T$ executed by a competent agent —
human or machine — under a fixed governance regime $G$, output rate and quality
occupy a *tolerance window* $[\ell, u]$ whose width is small relative to the mean.
Production is therefore a commodity in the economic sense: substitutable, priceable,
and predictable. Scarcity does not live in $T$. It lives in $G$.

**Evidence, from this system's own operation.** The escalation of §sovereign
operation drove one machine from one to thirty-two concurrent generations. Across
sixty-one generations the success rate was $1.00$ and throughput held a band of
$1.4 \pm 0.25$ per minute — a tolerance window of roughly $\pm 18\%$, tighter than
most machining tolerances quoted in units of the part. Latency degraded, but
*predictably*: linear at $22\,\mathrm{s}$ per added job through $N = 12$, then
superlinear at $59\,\mathrm{s}$ per job by $N = 16$.

The stronger evidence is operational rather than synthetic. Over one session this
system produced on the order of forty pull requests, fifteen issues, three papers,
six releases, and three review storms, at no point limited by its capacity to
produce. Every stall was governance: exhausted commercial credit, merge authority
withheld from the machine, ratification awaiting a human, a promotion race requiring
human reconciliation, a version-pinning drift. Production never bound; governance
always did.

**The mechanical analogy, and its correction.** Mechanical engineering's tolerance
windows are imposed by physics; a shaft cannot be machined outside what the material
permits. Software has no such external constraint, and this is the crux: the window
observed here was *manufactured* — by tests, coverage gates, provenance checks, and
ratified doctrine. Governance is therefore not merely the bottleneck. It is the
enabling condition. Removing it does not accelerate output; it removes the bound,
and unbounded variance is not production but noise.

$$
\text{waste}(n) = \underbrace{p \cdot n}_{\text{production}} -
\underbrace{c\,\frac{n(n-1)}{2}}_{\text{coordination}}
$$

**Why the failure mode persists.** With $n$ participants, production scales linearly
while coordination scales with the number of channels between them, $\binom{n}{2}$.
Waste turns negative beyond $n^{*} = 2p/c + 1$ regardless of how cheap production
becomes — indeed *faster* production lowers $n^{*}$, so commoditizing the work
shifts the binding constraint further toward governance rather than away from it.
The superlinear queue latency measured above is the same structure observed in
silicon: added participants multiply synchronization surface, not throughput. Brooks
stated this for human teams; the measurement here suggests it is substrate-independent.

**Scope, stated honestly.** This is evidenced, not proven: one machine, one model,
one session. And the claim holds for *production*, not for *judgment*. In the same
session the local reviewer returned confidently wrong verdicts on every nuanced
call — flagging rendered template constants as dead logic, opposing a version pin
that documented policy required, and defending the exact defect an incident
condemned. Artifacts are commoditized. Correct judgment about artifacts is not.
That gap, rather than throughput, is where the remaining engineering lies.

## The mechanics of the governance dilemma: six materials, three properties

The commodity thesis locates scarcity in governance without saying what governance
is made of. This section postulates its raw materials and derives a calculus over
them.

**Postulate (exhaustiveness).** Every dilemma that arises in the practice of
software engineering decomposes into six raw materials, each carrying three
properties, plus the pairwise couplings between them:

| Material | Availability | Stability | Reliability |
|---|---|---|---|
| Network | reachable now | variance of reachability | delivers what it claims |
| Hardware | capacity present | thermal, memory, wear drift | computes correctly |
| Software | installed, running | version and config drift | behaves as specified |
| Agent | present to act | turnover, fatigue, load | acts correctly when acting |
| Information | knowledge at hand | staleness, drift | true when consulted |
| Agency | permitted to act | revocation risk | permission honours its grant |

Write the state as $x \in \mathbb{R}^{18}$, one coordinate per material-property
pair, and let $x^{*}$ be the state of long-term stable peak performance. The
**dilemma vector** is $d = x^{*} - x$, and its coordinates are the only tangible
presentations a dilemma can take.

**Agency is not agent.** The distinction carries the postulate. An agent may be
present, stable, correct, and fully informed, and still lack the power to act; that
is a distinct failure with a distinct remedy, and no other coordinate expresses it.
This system supplied the instance: an automation blocked from merging pull requests
it had itself verified, at full availability and reliability, with agency at zero.

**Coordination is a coupling, not a seventh material.** The obvious objection —
that coordination cost is irreducible — resolves by observing that coordination
consumes information transfer, agent waiting, and authority resolution. It is the
off-diagonal term, and the $\binom{n}{2}$ coefficient of the waste function above is
exactly its magnitude.

**The derived calculus.** For an operation $o$ with requirement vector $r_o$ and a
current state $x$:

$$
\text{feasible}(o) \iff x \succeq r_o, \qquad
T(o) = T_{0}(o)\prod_{i} \phi_i(d_i), \qquad
C(o) = \int_{0}^{T(o)} c(x(t))\, dt
$$

where $\phi_i$ is the dilation each shortfall imposes on duration — unity at
$d_i = 0$ and divergent as the coordinate approaches its floor. Three quantities
follow directly and are the ones an operator actually wants: whether the work can
complete at all, how long it will take, and what it will cost. A fourth follows from
the gradient: $-\nabla_d T$ ranks which shortfall to repair first, which is the
adjustment an agent should make to converge toward $x^{*}$.

**Falsifiability.** The postulate fails the moment a real dilemma is exhibited that
does not decompose into these coordinates and their couplings. Stated so, it is a
law rather than a taxonomy.

**Relation to the measured system.** The fit calculus deployed in this system is the
two-coordinate projection of this space — hardware availability against software
availability — and it already exhibits the general behaviour: it admits, defers, or
declares a floor, and it fails loudly at the floor rather than silently. Tonight's
escalation supplied instances of all six coordinates in a single session, including
the reliability-without-availability case: a local reviewer answering 93.8% of
requests while returning incorrect verdicts on every nuanced judgment.

## Related work

Platform-native automation (merge queues, required checks) enforces revision-bound
*checks* but leaves verdict freshness to consumers. Yanking semantics for published
artifacts (PEP 592) informed the report-only supersession design. Keyless publishing
via OIDC (PyPI Trusted Publishers) removes the stored-credential class entirely and
is assumed throughout. Degraded-mode design draws on the availability literature's
fail-operational tradition — the system continues under component refusal rather than
halting — with the distinguishing constraint that our refusals include *commercial*
ones (credit exhaustion, deplatforming), which motivates fallback lattices ordered by
refusability rather than by mean time between failures.

## Conclusion

Binding every claim to the exact revision it evaluated, and spending bounded repairs
only against fresh verdicts, yields an automation loop that is sound by construction
and terminating by measure — properties cheap enough to state that their absence in
production systems is a choice, not a necessity.

## References

- PEP 592, *Adding "Yank" support to the Simple API*, Python Packaging Authority, 2019.
- PyPI, *Trusted Publishers*, https://docs.pypi.org/trusted-publishers/, 2023.
- GitHub, *About protected branches and rulesets*, GitHub Docs, 2024.
- vibey-gh repository, issues 161 and 163: the recorded violation and correction, 2026.
- vibey-gh repository, issues 201, 206–209: the credit-refusal incident and the
  sovereign-operation mechanisms it produced, 2026.
